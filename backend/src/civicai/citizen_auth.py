from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from datetime import timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from civicai.auth import DUMMY_PASSWORD_HASH, PASSWORD_HASHER, hash_password, token_digest, utc_now, verify_password
from civicai.database import get_session
from civicai.emailing import EmailService, OutboundEmail
from civicai.models import (
    CitizenAccount, CitizenPasswordCredential, IdentityToken, MunicipalSession, SecurityAuditEvent,
)

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
COMMON_PASSWORDS = frozenset({
    "passwordpassword", "password123456", "123456789012345", "qwertyuiop12345",
    "letmeinletmein", "civicaicivicaiai", "adminadminadmin", "iloveyouiloveyou",
})


def normalize_email(value: str) -> tuple[str, str]:
    email = value.strip()
    if len(email) > 254 or not EMAIL_PATTERN.fullmatch(email):
        raise ValueError("Enter a valid email address")
    local, domain = email.rsplit("@", 1)
    # CivicAI uses case-insensitive comparison without provider-specific rewriting.
    normalized = f"{local}@{domain}".lower()
    return email, normalized


def validate_citizen_password(value: str) -> None:
    if len(value) < 15 or len(value) > 128:
        raise ValueError("Password must be between 15 and 128 characters")
    if value.casefold() in COMMON_PASSWORDS:
        raise ValueError("Choose a less common password or passphrase")


def hash_citizen_password(value: str) -> str:
    validate_citizen_password(value)
    return PASSWORD_HASHER.hash(value)


def citizen_audit(session: Session, event_type: str, account_id=None) -> None:
    session.add(SecurityAuditEvent(
        event_type=event_type,
        actor_citizen_account_id=account_id,
        subject_citizen_account_id=account_id,
    ))


def create_citizen(session: Session, *, display_name: str, email: str, password: str) -> CitizenAccount:
    clean_email, normalized = normalize_email(email)
    name = display_name.strip()
    if not name or len(name) > 100:
        raise ValueError("Display name must be between 1 and 100 characters")
    account = CitizenAccount(
        email=clean_email, email_normalized=normalized, display_name=name,
        state="pending_verification",
    )
    session.add(account)
    try:
        session.flush()
        session.add(CitizenPasswordCredential(
            account_id=account.account_id, password_hash=hash_citizen_password(password)
        ))
        citizen_audit(session, "citizen_signup", account.account_id)
        session.commit()
        session.refresh(account)
        return account
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(409, "An account cannot be created with those details.") from exc


def issue_token(
    session: Session, account: CitizenAccount, purpose: str, lifetime: timedelta,
    email_service: EmailService, base_url: str,
) -> None:
    now = utc_now()
    session.execute(update(IdentityToken).where(
        IdentityToken.account_id == account.account_id,
        IdentityToken.purpose == purpose,
        IdentityToken.used_at.is_(None),
    ).values(used_at=now))
    raw = secrets.token_urlsafe(32)
    session.add(IdentityToken(
        account_id=account.account_id, purpose=purpose,
        token_hash=token_digest(raw), expires_at=now + lifetime,
    ))
    event = "email_verification_requested" if purpose == "verify_email" else "password_reset_requested"
    citizen_audit(session, event, account.account_id)
    session.commit()
    route = "verify-email" if purpose == "verify_email" else "reset-password"
    subject = "Verify your CivicAI email" if purpose == "verify_email" else "Reset your CivicAI password"
    email_service.send(OutboundEmail(
        account.email, subject,
        f"Open this single-use CivicAI link: {base_url}/{route}?token={raw}\n"
        "If you did not request this, you can ignore this message.",
    ))


def consume_token(session: Session, raw: str, purpose: str) -> tuple[IdentityToken, CitizenAccount]:
    token = session.scalar(select(IdentityToken).where(
        IdentityToken.token_hash == token_digest(raw), IdentityToken.purpose == purpose,
    ).with_for_update())
    if token is None or token.used_at is not None or token.expires_at <= utc_now():
        raise HTTPException(400, "This link is invalid, expired or already used.")
    account = session.get(CitizenAccount, token.account_id)
    if account is None or account.state == "disabled":
        raise HTTPException(400, "This link is invalid, expired or already used.")
    token.used_at = utc_now()
    return token, account


def create_citizen_session(session: Session, account: CitizenAccount, settings) -> tuple[str, MunicipalSession]:
    raw = secrets.token_urlsafe(32)
    auth_session = MunicipalSession(
        user_id=None, citizen_account_id=account.account_id,
        token_hash=token_digest(raw), csrf_token=secrets.token_urlsafe(32),
        expires_at=utc_now() + timedelta(hours=settings.session_hours),
    )
    account.last_login_at = utc_now()
    session.add(auth_session)
    citizen_audit(session, "login_succeeded", account.account_id)
    session.commit()
    session.refresh(auth_session)
    return raw, auth_session


@dataclass(frozen=True)
class CitizenAuthContext:
    account: CitizenAccount
    session: MunicipalSession


def optional_citizen_context(request: Request, session: Session) -> CitizenAuthContext | None:
    settings = request.app.state.auth_settings
    raw = request.cookies.get(settings.cookie_name)
    if not raw:
        return None
    auth_session = session.scalar(select(MunicipalSession).where(
        MunicipalSession.token_hash == token_digest(raw),
        MunicipalSession.citizen_account_id.is_not(None),
        MunicipalSession.revoked_at.is_(None), MunicipalSession.expires_at > func.now(),
    ))
    if auth_session is None:
        return None
    account = session.get(CitizenAccount, auth_session.citizen_account_id)
    if account is None or account.state != "active":
        return None
    return CitizenAuthContext(account, auth_session)


def get_citizen_context(request: Request, session: Annotated[Session, Depends(get_session)]) -> CitizenAuthContext:
    context = optional_citizen_context(request, session)
    if context is None:
        raise HTTPException(401, "Citizen authentication required.")
    return context


CitizenAuth = Annotated[CitizenAuthContext, Depends(get_citizen_context)]


def require_citizen_csrf(request: Request, context: CitizenAuth) -> CitizenAuthContext:
    import hmac
    supplied = request.headers.get("x-csrf-token", "")
    if not supplied or not hmac.compare_digest(supplied, context.session.csrf_token):
        raise HTTPException(403, "Invalid CSRF token.")
    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") not in request.app.state.auth_settings.allowed_origins:
        raise HTTPException(403, "Origin is not allowed.")
    return context


CitizenCsrfAuth = Annotated[CitizenAuthContext, Depends(require_citizen_csrf)]


def authenticate_citizen(session: Session, email: str, password: str) -> CitizenAccount | None:
    try:
        _, normalized = normalize_email(email)
    except ValueError:
        normalized = "invalid"
    account = session.scalar(select(CitizenAccount).where(CitizenAccount.email_normalized == normalized))
    credential = session.get(CitizenPasswordCredential, account.account_id) if account else None
    valid = verify_password(credential.password_hash if credential else DUMMY_PASSWORD_HASH, password)
    if account is None or credential is None or not valid or account.state != "active":
        return None
    return account


def revoke_citizen_sessions(session: Session, account_id, *, except_session_id=None) -> None:
    statement = update(MunicipalSession).where(
        MunicipalSession.citizen_account_id == account_id, MunicipalSession.revoked_at.is_(None),
    )
    if except_session_id is not None:
        statement = statement.where(MunicipalSession.session_id != except_session_id)
    session.execute(statement.values(revoked_at=utc_now()))
