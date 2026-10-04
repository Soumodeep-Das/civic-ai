from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.datastructures import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from civicai import ownership, service
from civicai.auth import (
    DUMMY_PASSWORD_HASH, AdminAuth, CsrfAuth, OperatorAuth, create_login_session,
    create_user, record_audit, token_digest, utc_now, verify_password, update_user,
)
from civicai.database import get_session
from civicai.citizen_auth import optional_citizen_context
from civicai.geocoding import Geocoder
from civicai.evidence import validate_key
from civicai.schemas import (
    AdminComplaintDetail, AdminComplaintPage, AdminComplaintRead, ComplaintCreate, ComplaintRead,
    ComplaintSubmissionRead, CitizenComplaintStatusRead,
    ComplaintStatusEventRead, ComplaintStatusUpdate, DashboardStatistics,
    LocationCapabilities, LocationReverseRequest, LocationSearchRequest, LocationSearchResult,
    AuthSessionRead, LoginRequest, MunicipalUserCreate, MunicipalUserRead, MunicipalUserUpdate,
    MunicipalDepartmentCreate, MunicipalDepartmentRead, MunicipalDepartmentUpdate,
    DepartmentMembershipCreate, DepartmentMemberRead, DepartmentSummary,
    ComplaintAssignmentEventRead, ComplaintAssignmentUpdate, ComplaintClaimRequest,
    WorkQueueStatistics,
)
from civicai.domain import ComplaintStatus
from civicai.models import Complaint, MunicipalDepartment, MunicipalSession, MunicipalUser
from civicai.uploads import MAX_IMAGE_BYTES, save_image
from civicai.tracking import tracking_token, valid_tracking_token

router = APIRouter(tags=["complaints"])
DatabaseSession = Annotated[Session, Depends(get_session)]


def department_read(session: Session, department: MunicipalDepartment) -> MunicipalDepartmentRead:
    members = [DepartmentMemberRead.model_validate({
        "user_id": user.user_id, "username": user.username, "role": user.role, "is_active": user.is_active,
    }) for user in ownership.department_members(session, department.department_id)]
    values = MunicipalDepartmentRead.model_validate(department).model_dump()
    values["members"] = members
    return MunicipalDepartmentRead(**values)


def admin_complaint_read(session: Session, complaint) -> AdminComplaintRead:
    department = session.get(MunicipalDepartment, complaint.department_id) if complaint.department_id else None
    assignee = session.get(MunicipalUser, complaint.assignee_user_id) if complaint.assignee_user_id else None
    return AdminComplaintRead(
        **ComplaintRead.model_validate(complaint).model_dump(),
        department=DepartmentSummary.model_validate(department) if department else None,
        assignee={"user_id": assignee.user_id, "username": assignee.username, "is_active": assignee.is_active} if assignee else None,
    )


def get_geocoder(request: Request) -> Geocoder:
    return request.app.state.geocoder


@router.post("/api/v1/auth/login", response_model=AuthSessionRead, tags=["municipal authentication"])
def login(data: LoginRequest, request: Request, response: Response, session: DatabaseSession):
    username_key = f"username:{data.username}"
    client_host = request.client.host if request.client else "unknown"
    ip_key = f"ip:{client_host}"
    request.app.state.login_throttle.check(username_key, ip_key)
    user = session.scalar(select(MunicipalUser).where(MunicipalUser.username == data.username))
    password_valid = verify_password(user.password_hash if user else DUMMY_PASSWORD_HASH, data.password)
    if user is None or not password_valid or not user.is_active:
        request.app.state.login_throttle.record_failure(username_key, ip_key)
        raise HTTPException(401, "Invalid username or password.")
    request.app.state.login_throttle.clear_username(username_key)
    raw_token, auth_session = create_login_session(session, user, request.app.state.auth_settings)
    settings = request.app.state.auth_settings
    response.set_cookie(
        settings.cookie_name, raw_token, max_age=settings.session_hours * 3600,
        expires=auth_session.expires_at.astimezone(timezone.utc), path="/", secure=settings.cookie_secure,
        httponly=True, samesite="strict",
    )
    return AuthSessionRead(user=user, csrf_token=auth_session.csrf_token, expires_at=auth_session.expires_at)


@router.get("/api/v1/auth/me", response_model=AuthSessionRead, tags=["municipal authentication"])
def session_state(auth: OperatorAuth):
    return AuthSessionRead(user=auth.user, csrf_token=auth.session.csrf_token, expires_at=auth.session.expires_at)


@router.post("/api/v1/auth/logout", status_code=204, tags=["municipal authentication"])
def logout(request: Request, response: Response, auth: CsrfAuth, session: DatabaseSession):
    auth.session.revoked_at = utc_now()
    record_audit(session, "logout", actor_id=auth.user.user_id, subject_id=auth.user.user_id)
    session.commit()
    response.delete_cookie(request.app.state.auth_settings.cookie_name, path="/", httponly=True, samesite="strict")
    response.status_code = 204
    return None


@router.post("/api/v1/complaints", response_model=ComplaintSubmissionRead, status_code=201,
             openapi_extra={"requestBody": {"required": True, "content": {"multipart/form-data": {
                 "schema": {"type": "object", "required": ["description"], "additionalProperties": False,
                            "properties": {"description": {"type": "string", "minLength": 1},
                                           "latitude": {"type": "number", "minimum": -90, "maximum": 90},
                                           "longitude": {"type": "number", "minimum": -180, "maximum": 180},
                                           "location_label": {"type": "string", "maxLength": 300},
                                           "location_precision": {"type": "string", "enum": ["exact", "approximate", "broad"]},
                                           "location_details": {"type": "string", "maxLength": 500},
                                           "location_source": {"type": "string", "enum": ["search", "device", "map"]},
                                           "location_accuracy_m": {"type": "number", "minimum": 0, "maximum": 100000},
                                           "image": {"type": "string", "format": "binary"}}}}}}})
async def create(request: Request, session: DatabaseSession):
    if not request.headers.get("content-type", "").startswith("multipart/form-data"):
        raise HTTPException(415, "Use multipart/form-data to submit a complaint.")
    # Bound the entire multipart body before the parser can spool an arbitrary file.
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_IMAGE_BYTES + 256 * 1024:
            raise HTTPException(413, "Complaint upload is too large.")
        body.extend(chunk)
    async def receive():
        return {"type": "http.request", "body": bytes(body), "more_body": False}
    parsed = Request(request.scope, receive)
    async with parsed.form(max_files=1, max_fields=8, max_part_size=64 * 1024) as form:
        values = {}
        upload = None
        for key, value in form.multi_items():
            if key in values or (key == "image" and upload is not None):
                raise HTTPException(422, "Duplicate form fields are not accepted.")
            if key == "image":
                if not isinstance(value, UploadFile):
                    raise HTTPException(422, "Image must be an uploaded file.")
                upload = value
            else:
                if isinstance(value, UploadFile):
                    raise HTTPException(422, "Unexpected file field.")
                values[key] = value
        try:
            data = ComplaintCreate.model_validate(values)
        except ValidationError as exc:
            raise RequestValidationError(exc.errors()) from exc
        image_ref = None
        if upload is not None:
            content = await upload.read(MAX_IMAGE_BYTES + 1)
            try:
                image_ref = save_image(content, upload.content_type, request.app.state.evidence_storage)
            except OSError:
                raise HTTPException(503, "Image storage is temporarily unavailable.") from None
        try:
            citizen = optional_citizen_context(request, session)
            complaint = service.create_complaint(
                session, data, image_ref,
                citizen_account_id=citizen.account.account_id if citizen else None,
            )
            values = ComplaintRead.model_validate(complaint).model_dump()
            values["image_ref"] = None
            values["tracking_token"] = tracking_token(
                complaint.complaint_id, request.app.state.runtime_settings.public_tracking_secret
            )
            return values
        except Exception:
            session.rollback()
            if image_ref is not None:
                try:
                    request.app.state.evidence_storage.delete(image_ref.rsplit("/", 1)[1])
                except OSError:
                    pass
            raise


@router.post("/api/v1/location-search", response_model=list[LocationSearchResult])
async def search_locations(
    data: LocationSearchRequest,
    geocoder: Annotated[Geocoder, Depends(get_geocoder)],
):
    return await geocoder.search(data.query)


@router.get("/api/v1/location-capabilities", response_model=LocationCapabilities)
def location_capabilities(geocoder: Annotated[Geocoder, Depends(get_geocoder)]):
    return LocationCapabilities(autocomplete=geocoder.autocomplete_supported)


@router.post("/api/v1/location-reverse", response_model=LocationSearchResult | None)
async def reverse_location(
    data: LocationReverseRequest,
    geocoder: Annotated[Geocoder, Depends(get_geocoder)],
):
    return await geocoder.reverse(data.latitude, data.longitude)


@router.get("/api/v1/complaints")
def list_all():
    raise HTTPException(404, "The public complaint directory is disabled. Use your private tracking link.")


@router.get("/api/v1/complaints/{complaint_id}", response_model=CitizenComplaintStatusRead)
def get_one(
    complaint_id: UUID,
    request: Request,
    session: DatabaseSession,
    tracking_token_value: Annotated[str, Query(alias="tracking_token", min_length=64, max_length=64)],
):
    secret = request.app.state.runtime_settings.public_tracking_secret
    if not valid_tracking_token(complaint_id, tracking_token_value, secret):
        raise HTTPException(404, "Complaint not found.")
    return service.get_complaint(session, complaint_id)


@router.get("/api/v1/admin/complaints", response_model=AdminComplaintPage, tags=["municipal operations"])
def admin_list(
    session: DatabaseSession,
    auth: OperatorAuth,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status: ComplaintStatus | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    has_location: bool | None = None,
    has_photo: bool | None = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
    department_id: UUID | None = None,
    assignee_user_id: UUID | None = None,
    assignment_state: Literal["assigned", "unassigned"] | None = None,
    queue: Literal["unassigned", "mine", "my_departments_unassigned"] | None = None,
):
    if created_from and (created_from.tzinfo is None or created_from.utcoffset() is None):
        raise HTTPException(422, "created_from must include a timezone.")
    if created_to and (created_to.tzinfo is None or created_to.utcoffset() is None):
        raise HTTPException(422, "created_to must include a timezone.")
    if created_from and created_to and created_from > created_to:
        raise HTTPException(422, "created_from must not be after created_to.")
    if queue == "unassigned" and auth.user.role != "municipal_admin":
        raise HTTPException(403, "Only administrators can view the organization-wide unassigned queue.")
    if assignee_user_id is not None and auth.user.role != "municipal_admin" and assignee_user_id != auth.user.user_id:
        raise HTTPException(403, "Operators may filter only their own individual assignments.")
    items, total = service.list_admin_complaints(
        session, page=page, page_size=page_size, status=status,
        created_from=created_from, created_to=created_to,
        has_location=has_location, has_photo=has_photo, query=q, actor=auth.user,
        department_id=department_id, assignee_user_id=assignee_user_id,
        assignment_state=assignment_state, queue=queue,
    )
    return AdminComplaintPage(
        items=[admin_complaint_read(session, item) for item in items], page=page, page_size=page_size, total=total,
        total_pages=service.page_count(total, page_size),
    )


@router.get(
    "/api/v1/admin/complaints/{complaint_id}",
    response_model=AdminComplaintDetail,
    tags=["municipal operations"],
)
def admin_get(complaint_id: UUID, session: DatabaseSession, auth: OperatorAuth):
    complaint, history = service.get_admin_complaint(session, complaint_id)
    ownership.require_complaint_access(session, auth.user, complaint)
    return AdminComplaintDetail(
        **admin_complaint_read(session, complaint).model_dump(), history=history,
        assignment_history=ownership.assignment_history(session, complaint_id),
    )


@router.get(
    "/api/v1/admin/complaints/{complaint_id}/history",
    response_model=list[ComplaintStatusEventRead],
    tags=["municipal operations"],
)
def admin_history(complaint_id: UUID, session: DatabaseSession, auth: OperatorAuth):
    complaint = service.get_complaint(session, complaint_id)
    ownership.require_complaint_access(session, auth.user, complaint)
    return service.list_status_history(session, complaint_id)


@router.patch(
    "/api/v1/admin/complaints/{complaint_id}/status",
    response_model=ComplaintRead,
    tags=["municipal operations"],
)
def admin_update_status(
    complaint_id: UUID, data: ComplaintStatusUpdate, session: DatabaseSession, auth: CsrfAuth
):
    return service.update_complaint_status(session, complaint_id, data, auth.user)


@router.get("/api/v1/admin/departments", response_model=list[MunicipalDepartmentRead], tags=["municipal departments"])
def admin_departments(session: DatabaseSession, auth: OperatorAuth, include_inactive: bool = True):
    departments = ownership.list_departments(session, include_inactive=include_inactive if auth.user.role == "municipal_admin" else False)
    if auth.user.role != "municipal_admin":
        allowed = ownership.membership_ids(session, auth.user.user_id)
        departments = [item for item in departments if item.department_id in allowed]
    return [department_read(session, item) for item in departments]


@router.post("/api/v1/admin/departments", response_model=MunicipalDepartmentRead, status_code=201, tags=["municipal departments"])
def admin_create_department(data: MunicipalDepartmentCreate, session: DatabaseSession, auth: CsrfAuth):
    if auth.user.role != "municipal_admin":
        raise HTTPException(403, "Administrator permission required.")
    return department_read(session, ownership.create_department(session, data))


@router.patch("/api/v1/admin/departments/{department_id}", response_model=MunicipalDepartmentRead, tags=["municipal departments"])
def admin_update_department(department_id: UUID, data: MunicipalDepartmentUpdate, session: DatabaseSession, auth: CsrfAuth):
    if auth.user.role != "municipal_admin":
        raise HTTPException(403, "Administrator permission required.")
    return department_read(session, ownership.update_department(session, department_id, data))


@router.post("/api/v1/admin/departments/{department_id}/members", response_model=DepartmentMemberRead, tags=["municipal departments"])
def admin_add_department_member(department_id: UUID, data: DepartmentMembershipCreate, session: DatabaseSession, auth: CsrfAuth):
    if auth.user.role != "municipal_admin":
        raise HTTPException(403, "Administrator permission required.")
    user = ownership.add_membership(session, department_id, data.user_id, auth.user.user_id)
    return DepartmentMemberRead.model_validate({"user_id": user.user_id, "username": user.username, "role": user.role, "is_active": user.is_active})


@router.delete("/api/v1/admin/departments/{department_id}/members/{user_id}", status_code=204, tags=["municipal departments"])
def admin_remove_department_member(department_id: UUID, user_id: UUID, session: DatabaseSession, auth: CsrfAuth):
    if auth.user.role != "municipal_admin":
        raise HTTPException(403, "Administrator permission required.")
    ownership.remove_membership(session, department_id, user_id, auth.user.user_id)
    return Response(status_code=204)


@router.patch("/api/v1/admin/complaints/{complaint_id}/assignment", response_model=AdminComplaintRead, tags=["municipal operations"])
def admin_update_assignment(complaint_id: UUID, data: ComplaintAssignmentUpdate, session: DatabaseSession, auth: CsrfAuth):
    if auth.user.role != "municipal_admin":
        raise HTTPException(403, "Only administrators can assign or reassign complaints.")
    return admin_complaint_read(session, ownership.update_assignment(session, complaint_id, data, auth.user))


@router.post("/api/v1/admin/complaints/{complaint_id}/claim", response_model=AdminComplaintRead, tags=["municipal operations"])
def claim_assignment(complaint_id: UUID, data: ComplaintClaimRequest, session: DatabaseSession, auth: CsrfAuth):
    return admin_complaint_read(session, ownership.claim_complaint(session, complaint_id, data.expected_updated_at, auth.user))


@router.get(
    "/api/v1/admin/dashboard", response_model=DashboardStatistics, tags=["municipal operations"]
)
def admin_dashboard(session: DatabaseSession, auth: OperatorAuth):
    return service.dashboard_statistics(session, auth.user)


@router.get("/api/v1/admin/work-summary", response_model=WorkQueueStatistics, tags=["municipal operations"])
def admin_work_summary(session: DatabaseSession, auth: OperatorAuth):
    return ownership.work_queue_statistics(session, auth.user)


@router.get("/api/v1/admin/users", response_model=list[MunicipalUserRead], tags=["municipal accounts"])
def admin_users(session: DatabaseSession, _auth: AdminAuth):
    return list(session.scalars(select(MunicipalUser).order_by(MunicipalUser.username)))


@router.post("/api/v1/admin/users", response_model=MunicipalUserRead, status_code=201, tags=["municipal accounts"])
def admin_create_user(data: MunicipalUserCreate, session: DatabaseSession, auth: CsrfAuth):
    if auth.user.role != "municipal_admin":
        raise HTTPException(403, "Administrator permission required.")
    user = create_user(session, data)
    record_audit(session, "account_created", actor_id=auth.user.user_id, subject_id=user.user_id)
    session.commit()
    session.refresh(user)
    return user


@router.patch("/api/v1/admin/users/{user_id}", response_model=MunicipalUserRead, tags=["municipal accounts"])
def admin_update_user(
    user_id: UUID, data: MunicipalUserUpdate, session: DatabaseSession, auth: CsrfAuth
):
    if auth.user.role != "municipal_admin":
        raise HTTPException(403, "Administrator permission required.")
    target = session.get(MunicipalUser, user_id)
    if target is None:
        raise HTTPException(404, "Municipal account not found.")
    return update_user(session, target, data, auth.user)


@router.get("/api/v1/complaint-images/{filename}")
def get_image(filename: str, request: Request, session: DatabaseSession):
    try:
        validate_key(filename)
    except FileNotFoundError:
        raise HTTPException(404, "Image not found.") from None
    complaint = session.scalar(select(Complaint).where(
        Complaint.image_ref == f"/api/v1/complaint-images/{filename}"
    ))
    if complaint is None:
        raise HTTPException(404, "Complaint image not found.")
    raw = request.cookies.get(request.app.state.auth_settings.cookie_name, "")
    auth_session = session.scalar(select(MunicipalSession).where(
        MunicipalSession.token_hash == token_digest(raw), MunicipalSession.revoked_at.is_(None),
        MunicipalSession.expires_at > func.now(),
    )) if raw else None
    if auth_session is None:
        raise HTTPException(401, "Authentication required.")
    if auth_session.user_id is not None:
        user = session.get(MunicipalUser, auth_session.user_id)
        if user is None or not user.is_active:
            raise HTTPException(401, "Authentication required.")
        ownership.require_complaint_access(session, user, complaint)
    elif auth_session.citizen_account_id != complaint.citizen_account_id:
        raise HTTPException(404, "Complaint image not found.")
    try:
        content, media_type = request.app.state.evidence_storage.get(filename)
    except (FileNotFoundError, OSError):
        raise HTTPException(404, "Complaint image not found.") from None
    return Response(content=content, media_type=media_type,
                    headers={"X-Content-Type-Options": "nosniff", "Content-Security-Policy": "default-src 'none'", "Cache-Control": "private, no-store"})
