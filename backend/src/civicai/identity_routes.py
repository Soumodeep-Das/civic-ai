from __future__ import annotations

import secrets
from datetime import timedelta, timezone
from math import ceil
from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from civicai.auth import AdminAuth, CsrfAuth, hash_password, record_audit, token_digest, utc_now, verify_password
from civicai.citizen_auth import (
    CitizenAuth, CitizenCsrfAuth, authenticate_citizen, citizen_audit, consume_token,
    create_citizen, create_citizen_session, hash_citizen_password, issue_token,
    normalize_email, revoke_citizen_sessions,
)
from civicai.database import get_session
from civicai.models import (
    CitizenAccount, CitizenPasswordCredential, Complaint, ComplaintStatusEvent, FederatedIdentity, IdentityToken, OIDCFlow,
    MunicipalDepartment, MunicipalDepartmentMembership, MunicipalSession, MunicipalUser,
    StaffInvitation, StaffInvitationDepartment,
)
from civicai.schemas import (
    CitizenAccountRead, CitizenComplaintPage, CitizenLoginRequest, CitizenOwnedComplaintRead,
    CitizenSessionRead, CitizenSignupRequest, CitizenStatusEventRead, EmailRequest,
    PasswordChangeRequest, ResetPasswordRequest, StaffInvitationAccept, StaffInvitationCreate,
    StaffInvitationRead, TokenRequest,
)
from civicai.tracking import valid_tracking_token

identity_router = APIRouter()


DatabaseSession = Annotated[Session, Depends(get_session)]


def _client_key(request: Request, namespace: str, identity: str = "") -> tuple[str, str]:
    host = request.client.host if request.client else "unknown"
    return f"{namespace}:ip:{host}", f"{namespace}:identity:{identity}"


def _set_session_cookie(response: Response, request: Request, raw: str, expires_at) -> None:
    settings = request.app.state.auth_settings
    response.set_cookie(
        settings.cookie_name, raw, max_age=settings.session_hours * 3600,
        expires=expires_at.astimezone(timezone.utc), path="/", secure=settings.cookie_secure,
        httponly=True, samesite="strict",
    )


def _citizen_session_read(account, auth_session, google_connected: bool = False, has_password: bool = False) -> CitizenSessionRead:
    values = CitizenAccountRead.model_validate(account).model_dump()
    values["google_connected"] = google_connected
    values["has_password"] = has_password
    return CitizenSessionRead(account=CitizenAccountRead(**values), csrf_token=auth_session.csrf_token, expires_at=auth_session.expires_at)


@identity_router.get("/api/v1/citizen-auth/google/start", tags=["citizen identity"])
def google_start(request: Request, session: DatabaseSession):
    client = request.app.state.oidc_client
    if not client.configured:
        raise HTTPException(503, "Google sign-in is not configured.")
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    session.add(OIDCFlow(
        state_hash=token_digest(state), nonce_hash=token_digest(nonce),
        expires_at=utc_now() + timedelta(minutes=10),
    ))
    session.commit()
    response = RedirectResponse(client.authorization_url(state=state, nonce=nonce), status_code=302)
    secure = request.app.state.auth_settings.cookie_secure
    response.set_cookie("civicai_oidc_state", state, max_age=600, path="/api/v1/citizen-auth/google/callback", secure=secure, httponly=True, samesite="lax")
    response.set_cookie("civicai_oidc_nonce", nonce, max_age=600, path="/api/v1/citizen-auth/google/callback", secure=secure, httponly=True, samesite="lax")
    return response


@identity_router.get("/api/v1/citizen-auth/google/callback", tags=["citizen identity"])
async def google_callback(request: Request, session: DatabaseSession, code: str = "", state: str = "", error: str = ""):
    base = request.app.state.auth_settings.public_base_url
    failure = lambda reason: RedirectResponse(f"{base}/sign-in?google_error={reason}", status_code=303)
    cookie_state = request.cookies.get("civicai_oidc_state", "")
    nonce = request.cookies.get("civicai_oidc_nonce", "")
    if error:
        return failure("cancelled")
    if not code or not state or not cookie_state or not nonce or not secrets.compare_digest(state, cookie_state):
        return failure("invalid_state")
    flow = session.scalar(select(OIDCFlow).where(OIDCFlow.state_hash == token_digest(state)).with_for_update())
    if flow is None or flow.used_at is not None or flow.expires_at <= utc_now() or not secrets.compare_digest(flow.nonce_hash, token_digest(nonce)):
        return failure("expired_flow")
    flow.used_at = utc_now()
    session.commit()
    try:
        identity = await request.app.state.oidc_client.exchange(code, nonce)
        _, normalized = normalize_email(identity.email)
    except Exception:
        return failure("provider_error")
    linked = session.scalar(select(FederatedIdentity).where(
        FederatedIdentity.provider == "google", FederatedIdentity.issuer == identity.issuer,
        FederatedIdentity.subject == identity.subject,
    ))
    if linked is not None:
        account = session.get(CitizenAccount, linked.account_id)
        if account is None or account.state != "active":
            return failure("account_unavailable")
    else:
        collision = session.scalar(select(CitizenAccount).where(CitizenAccount.email_normalized == normalized))
        if collision is not None:
            return failure("existing_email")
        account = CitizenAccount(
            email=identity.email.strip(), email_normalized=normalized,
            display_name=identity.display_name, state="active", email_verified_at=utc_now(),
        )
        session.add(account)
        session.flush()
        session.add(FederatedIdentity(
            account_id=account.account_id, provider="google",
            issuer=identity.issuer, subject=identity.subject,
        ))
        citizen_audit(session, "citizen_signup", account.account_id)
        citizen_audit(session, "google_identity_linked", account.account_id)
        session.commit()
    raw, auth_session = create_citizen_session(session, account, request.app.state.auth_settings)
    response = RedirectResponse(f"{base}/my-complaints", status_code=303)
    _set_session_cookie(response, request, raw, auth_session.expires_at)
    response.delete_cookie("civicai_oidc_state", path="/api/v1/citizen-auth/google/callback")
    response.delete_cookie("civicai_oidc_nonce", path="/api/v1/citizen-auth/google/callback")
    return response


@identity_router.post("/api/v1/citizen-auth/sign-up", status_code=202, tags=["citizen identity"])
def citizen_signup(data: CitizenSignupRequest, request: Request, session: DatabaseSession):
    try:
        _, normalized = normalize_email(data.email)
        keys = _client_key(request, "citizen-signup", normalized)
        request.app.state.identity_throttle.check(*keys)
        account = create_citizen(session, display_name=data.display_name, email=data.email, password=data.password)
        issue_token(
            session, account, "verify_email",
            timedelta(minutes=request.app.state.auth_settings.verification_minutes),
            request.app.state.email_service, request.app.state.auth_settings.public_base_url,
        )
        return {"message": "Check your email to verify your CivicAI account."}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except HTTPException:
        request.app.state.identity_throttle.record_failure(*keys)
        raise


@identity_router.post("/api/v1/citizen-auth/verify-email", tags=["citizen identity"])
def verify_email(data: TokenRequest, session: DatabaseSession):
    _, account = consume_token(session, data.token, "verify_email")
    account.state = "active"
    account.email_verified_at = utc_now()
    citizen_audit(session, "email_verified", account.account_id)
    session.commit()
    return {"message": "Email verified. You can now sign in."}


@identity_router.post("/api/v1/citizen-auth/resend-verification", status_code=202, tags=["citizen identity"])
def resend_verification(data: EmailRequest, request: Request, session: DatabaseSession):
    try:
        _, normalized = normalize_email(data.email)
    except ValueError:
        normalized = "invalid"
    keys = _client_key(request, "verification-resend", normalized)
    request.app.state.identity_throttle.check(*keys)
    account = session.scalar(select(CitizenAccount).where(CitizenAccount.email_normalized == normalized))
    if account is not None and account.state == "pending_verification":
        issue_token(session, account, "verify_email", timedelta(minutes=request.app.state.auth_settings.verification_minutes), request.app.state.email_service, request.app.state.auth_settings.public_base_url)
    request.app.state.identity_throttle.record_failure(*keys)
    return {"message": "If the account is awaiting verification, a new link has been sent."}


@identity_router.post("/api/v1/citizen-auth/login", response_model=CitizenSessionRead, tags=["citizen identity"])
def citizen_login(data: CitizenLoginRequest, request: Request, response: Response, session: DatabaseSession):
    try:
        _, normalized = normalize_email(data.email)
    except ValueError:
        normalized = "invalid"
    keys = _client_key(request, "citizen-login", normalized)
    request.app.state.identity_throttle.check(*keys)
    account = authenticate_citizen(session, data.email, data.password)
    if account is None:
        request.app.state.identity_throttle.record_failure(*keys)
        raise HTTPException(401, "Email or password is incorrect.")
    request.app.state.identity_throttle.clear_username(keys[1])
    raw, auth_session = create_citizen_session(session, account, request.app.state.auth_settings)
    _set_session_cookie(response, request, raw, auth_session.expires_at)
    google_connected = session.scalar(select(func.count()).select_from(FederatedIdentity).where(FederatedIdentity.account_id == account.account_id)) > 0
    return _citizen_session_read(account, auth_session, google_connected, session.get(CitizenPasswordCredential, account.account_id) is not None)


@identity_router.get("/api/v1/citizen-auth/me", response_model=CitizenSessionRead, tags=["citizen identity"])
def citizen_me(auth: CitizenAuth, session: DatabaseSession):
    google_connected = session.scalar(select(func.count()).select_from(FederatedIdentity).where(FederatedIdentity.account_id == auth.account.account_id)) > 0
    return _citizen_session_read(auth.account, auth.session, google_connected, session.get(CitizenPasswordCredential, auth.account.account_id) is not None)


@identity_router.post("/api/v1/citizen-auth/logout", status_code=204, tags=["citizen identity"])
def citizen_logout(request: Request, response: Response, auth: CitizenCsrfAuth, session: DatabaseSession):
    auth.session.revoked_at = utc_now()
    citizen_audit(session, "logout", auth.account.account_id)
    session.commit()
    response.delete_cookie(request.app.state.auth_settings.cookie_name, path="/", httponly=True, samesite="strict")
    return None


@identity_router.post("/api/v1/citizen-auth/forgot-password", status_code=202, tags=["citizen identity"])
def forgot_password(data: EmailRequest, request: Request, session: DatabaseSession):
    try:
        _, normalized = normalize_email(data.email)
    except ValueError:
        normalized = "invalid"
    keys = _client_key(request, "password-reset-request", normalized)
    request.app.state.identity_throttle.check(*keys)
    account = session.scalar(select(CitizenAccount).where(CitizenAccount.email_normalized == normalized))
    if account is not None and account.state != "disabled" and session.get(CitizenPasswordCredential, account.account_id):
        issue_token(session, account, "reset_password", timedelta(minutes=request.app.state.auth_settings.reset_minutes), request.app.state.email_service, request.app.state.auth_settings.public_base_url)
    else:
        # Keep a real Argon2 operation in the unknown-account path.
        verify_password(request.app.state.dummy_password_hash, data.email)
    request.app.state.identity_throttle.record_failure(*keys)
    return {"message": "If an account exists for that email, a reset link has been sent."}


@identity_router.post("/api/v1/citizen-auth/reset-password", tags=["citizen identity"])
def reset_password(data: ResetPasswordRequest, request: Request, session: DatabaseSession):
    keys = _client_key(request, "password-reset", token_digest(data.token)[:16])
    request.app.state.identity_throttle.check(*keys)
    try:
        _, account = consume_token(session, data.token, "reset_password")
        credential = session.get(CitizenPasswordCredential, account.account_id)
        if credential is None:
            raise HTTPException(400, "This account does not have a password credential.")
        credential.password_hash = hash_citizen_password(data.password)
        credential.updated_at = utc_now()
        revoke_citizen_sessions(session, account.account_id)
        citizen_audit(session, "password_reset_completed", account.account_id)
        session.commit()
        return {"message": "Password reset. Sign in with your new password."}
    except (ValueError, HTTPException) as exc:
        request.app.state.identity_throttle.record_failure(*keys)
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(422, str(exc)) from exc


@identity_router.post("/api/v1/citizen-auth/change-password", tags=["citizen identity"])
def change_password(data: PasswordChangeRequest, auth: CitizenCsrfAuth, session: DatabaseSession):
    credential = session.get(CitizenPasswordCredential, auth.account.account_id)
    if credential is None or not verify_password(credential.password_hash, data.current_password):
        raise HTTPException(400, "Current password is incorrect.")
    try:
        credential.password_hash = hash_citizen_password(data.new_password)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    credential.updated_at = utc_now()
    revoke_citizen_sessions(session, auth.account.account_id, except_session_id=auth.session.session_id)
    citizen_audit(session, "password_changed", auth.account.account_id)
    session.commit()
    return {"message": "Password changed. Other sessions were signed out."}


def _owned_read(session: Session, complaint: Complaint) -> CitizenOwnedComplaintRead:
    history = list(session.scalars(select(ComplaintStatusEvent).where(
        ComplaintStatusEvent.complaint_id == complaint.complaint_id
    ).order_by(ComplaintStatusEvent.occurred_at, ComplaintStatusEvent.event_id)))
    return CitizenOwnedComplaintRead(
        **{key: value for key, value in CitizenOwnedComplaintRead.model_validate({**complaint.__dict__, "history": []}).model_dump().items() if key != "history"},
        history=[CitizenStatusEventRead(
            event_type=item.event_type, previous_status=item.previous_status,
            new_status=item.new_status, occurred_at=item.occurred_at,
        ) for item in history],
    )


@identity_router.get("/api/v1/citizen/complaints", response_model=CitizenComplaintPage, tags=["citizen complaints"])
def my_complaints(auth: CitizenAuth, session: DatabaseSession, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=50)):
    condition = Complaint.citizen_account_id == auth.account.account_id
    total = session.scalar(select(func.count()).select_from(Complaint).where(condition)) or 0
    rows = list(session.scalars(select(Complaint).where(condition).order_by(
        Complaint.created_at.desc(), Complaint.complaint_id.desc()
    ).offset((page - 1) * page_size).limit(page_size)))
    return CitizenComplaintPage(items=[_owned_read(session, row) for row in rows], page=page, page_size=page_size, total=total, total_pages=ceil(total / page_size) if total else 0)


@identity_router.get("/api/v1/citizen/complaints/{complaint_id}", response_model=CitizenOwnedComplaintRead, tags=["citizen complaints"])
def my_complaint(complaint_id: UUID, auth: CitizenAuth, session: DatabaseSession):
    complaint = session.scalar(select(Complaint).where(
        Complaint.complaint_id == complaint_id, Complaint.citizen_account_id == auth.account.account_id,
    ))
    if complaint is None:
        raise HTTPException(404, "Complaint not found.")
    return _owned_read(session, complaint)


@identity_router.post("/api/v1/citizen/complaints/{complaint_id}/claim", response_model=CitizenOwnedComplaintRead, tags=["citizen complaints"])
def claim_complaint(complaint_id: UUID, data: TokenRequest, request: Request, auth: CitizenCsrfAuth, session: DatabaseSession):
    if not valid_tracking_token(complaint_id, data.token, request.app.state.runtime_settings.public_tracking_secret):
        raise HTTPException(404, "Complaint not found.")
    complaint = session.scalar(select(Complaint).where(Complaint.complaint_id == complaint_id).with_for_update())
    if complaint is None:
        raise HTTPException(404, "Complaint not found.")
    if complaint.citizen_account_id not in {None, auth.account.account_id}:
        raise HTTPException(409, "This complaint is already linked to another account.")
    if complaint.citizen_account_id is None:
        complaint.citizen_account_id = auth.account.account_id
        citizen_audit(session, "anonymous_complaint_claimed", auth.account.account_id)
        session.commit()
    return _owned_read(session, complaint)


def _invitation_read(session: Session, invitation: StaffInvitation) -> StaffInvitationRead:
    departments = list(session.scalars(select(StaffInvitationDepartment.department_id).where(
        StaffInvitationDepartment.invitation_id == invitation.invitation_id
    )))
    return StaffInvitationRead.model_validate({**invitation.__dict__, "department_ids": departments})


@identity_router.get("/api/v1/admin/staff-invitations", response_model=list[StaffInvitationRead], tags=["municipal staff"])
def list_invitations(session: DatabaseSession, _auth: AdminAuth):
    return [_invitation_read(session, item) for item in session.scalars(select(StaffInvitation).order_by(StaffInvitation.created_at.desc()))]


@identity_router.post("/api/v1/admin/staff-invitations", response_model=StaffInvitationRead, status_code=201, tags=["municipal staff"])
def invite_staff(data: StaffInvitationCreate, request: Request, session: DatabaseSession, auth: CsrfAuth):
    if auth.user.role != "municipal_admin":
        raise HTTPException(403, "Administrator permission required.")
    try:
        clean_email, normalized = normalize_email(data.email)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if session.scalar(select(MunicipalUser).where(MunicipalUser.email_normalized == normalized)):
        raise HTTPException(409, "That email already belongs to municipal staff.")
    departments = list(session.scalars(select(MunicipalDepartment).where(MunicipalDepartment.department_id.in_(data.department_ids)))) if data.department_ids else []
    if len(departments) != len(set(data.department_ids)) or any(not item.is_active for item in departments):
        raise HTTPException(422, "Every invited department must exist and be active.")
    raw = secrets.token_urlsafe(32)
    invitation = StaffInvitation(
        email=clean_email, email_normalized=normalized, role=data.role.value,
        token_hash=token_digest(raw), invited_by_user_id=auth.user.user_id,
        expires_at=utc_now() + timedelta(hours=request.app.state.auth_settings.invitation_hours),
    )
    session.add(invitation)
    try:
        session.flush()
        session.add_all([StaffInvitationDepartment(invitation_id=invitation.invitation_id, department_id=item.department_id) for item in departments])
        record_audit(session, "staff_invited", actor_id=auth.user.user_id, subject_id=None)
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(409, "A pending invitation already exists for that email.") from exc
    request.app.state.email_service.send(__import__("civicai.emailing", fromlist=["OutboundEmail"]).OutboundEmail(
        clean_email, "Your CivicAI municipal staff invitation",
        f"Accept this single-use invitation: {request.app.state.auth_settings.public_base_url}/staff/accept-invite?token={raw}",
    ))
    session.refresh(invitation)
    return _invitation_read(session, invitation)


@identity_router.post("/api/v1/admin/staff-invitations/{invitation_id}/revoke", response_model=StaffInvitationRead, tags=["municipal staff"])
def revoke_invitation(invitation_id: UUID, session: DatabaseSession, auth: CsrfAuth):
    if auth.user.role != "municipal_admin":
        raise HTTPException(403, "Administrator permission required.")
    invitation = session.get(StaffInvitation, invitation_id)
    if invitation is None:
        raise HTTPException(404, "Invitation not found.")
    if invitation.accepted_at is not None:
        raise HTTPException(409, "An accepted invitation cannot be revoked.")
    invitation.revoked_at = invitation.revoked_at or utc_now()
    record_audit(session, "invitation_revoked", actor_id=auth.user.user_id, subject_id=None)
    session.commit()
    return _invitation_read(session, invitation)


@identity_router.post("/api/v1/staff/accept-invite", status_code=201, tags=["municipal staff"])
def accept_invitation(data: StaffInvitationAccept, request: Request, session: DatabaseSession):
    keys = _client_key(request, "invite-accept", token_digest(data.token)[:16])
    request.app.state.identity_throttle.check(*keys)
    invitation = session.scalar(select(StaffInvitation).where(
        StaffInvitation.token_hash == token_digest(data.token)
    ).with_for_update())
    if invitation is None or invitation.revoked_at is not None or invitation.accepted_at is not None or invitation.expires_at <= utc_now():
        request.app.state.identity_throttle.record_failure(*keys)
        raise HTTPException(400, "This invitation is invalid, expired or already used.")
    inviter = session.get(MunicipalUser, invitation.invited_by_user_id)
    department_ids = list(session.scalars(select(StaffInvitationDepartment.department_id).where(
        StaffInvitationDepartment.invitation_id == invitation.invitation_id
    )))
    departments = list(session.scalars(select(MunicipalDepartment).where(MunicipalDepartment.department_id.in_(department_ids)))) if department_ids else []
    if inviter is None or not inviter.is_active or len(departments) != len(department_ids) or any(not item.is_active for item in departments):
        raise HTTPException(409, "This invitation can no longer be accepted. Contact a municipal administrator.")
    user = MunicipalUser(
        username=data.username, email=invitation.email, email_normalized=invitation.email_normalized,
        display_name=data.display_name, password_hash=hash_password(data.password), role=invitation.role, is_active=True,
    )
    session.add(user)
    try:
        session.flush()
        session.add_all([MunicipalDepartmentMembership(
            department_id=item.department_id, user_id=user.user_id,
            created_by_user_id=invitation.invited_by_user_id,
        ) for item in departments])
        invitation.accepted_at = utc_now()
        invitation.accepted_user_id = user.user_id
        record_audit(session, "staff_invitation_accepted", actor_id=user.user_id, subject_id=user.user_id)
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(409, "The invitation could not create a unique municipal account.") from exc
    return {"message": "Municipal account activated. Sign in through the staff portal.", "username": user.username}

