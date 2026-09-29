from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.datastructures import UploadFile
from sqlalchemy.orm import Session

from civicai import service
from civicai.database import get_session
from civicai.geocoding import Geocoder
from civicai.schemas import (
    AdminComplaintDetail, AdminComplaintPage, ComplaintCreate, ComplaintRead,
    ComplaintStatusEventRead, ComplaintStatusUpdate, DashboardStatistics,
    LocationCapabilities, LocationReverseRequest, LocationSearchRequest, LocationSearchResult,
)
from civicai.domain import ComplaintStatus
from civicai.uploads import MAX_IMAGE_BYTES, save_image, image_path

router = APIRouter(tags=["complaints"])
DatabaseSession = Annotated[Session, Depends(get_session)]


def get_geocoder(request: Request) -> Geocoder:
    return request.app.state.geocoder


@router.post("/api/v1/complaints", response_model=ComplaintRead, status_code=201,
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
                image_ref = save_image(content, upload.content_type, request.app.state.upload_directory)
            except OSError:
                raise HTTPException(503, "Image storage is temporarily unavailable.") from None
        try:
            return service.create_complaint(session, data, image_ref)
        except Exception:
            session.rollback()
            if image_ref is not None:
                (request.app.state.upload_directory / image_ref.rsplit("/", 1)[1]).unlink(missing_ok=True)
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


@router.get("/api/v1/complaints", response_model=list[ComplaintRead])
def list_all(session: DatabaseSession):
    return service.list_complaints(session)


@router.get("/api/v1/complaints/{complaint_id}", response_model=ComplaintRead)
def get_one(complaint_id: UUID, session: DatabaseSession):
    return service.get_complaint(session, complaint_id)


@router.get("/api/v1/admin/complaints", response_model=AdminComplaintPage, tags=["municipal operations"])
def admin_list(
    session: DatabaseSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status: ComplaintStatus | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    has_location: bool | None = None,
    has_photo: bool | None = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
):
    if created_from and (created_from.tzinfo is None or created_from.utcoffset() is None):
        raise HTTPException(422, "created_from must include a timezone.")
    if created_to and (created_to.tzinfo is None or created_to.utcoffset() is None):
        raise HTTPException(422, "created_to must include a timezone.")
    if created_from and created_to and created_from > created_to:
        raise HTTPException(422, "created_from must not be after created_to.")
    items, total = service.list_admin_complaints(
        session, page=page, page_size=page_size, status=status,
        created_from=created_from, created_to=created_to,
        has_location=has_location, has_photo=has_photo, query=q,
    )
    return AdminComplaintPage(
        items=items, page=page, page_size=page_size, total=total,
        total_pages=service.page_count(total, page_size),
    )


@router.get(
    "/api/v1/admin/complaints/{complaint_id}",
    response_model=AdminComplaintDetail,
    tags=["municipal operations"],
)
def admin_get(complaint_id: UUID, session: DatabaseSession):
    complaint, history = service.get_admin_complaint(session, complaint_id)
    return AdminComplaintDetail(**ComplaintRead.model_validate(complaint).model_dump(), history=history)


@router.get(
    "/api/v1/admin/complaints/{complaint_id}/history",
    response_model=list[ComplaintStatusEventRead],
    tags=["municipal operations"],
)
def admin_history(complaint_id: UUID, session: DatabaseSession):
    return service.list_status_history(session, complaint_id)


@router.patch(
    "/api/v1/admin/complaints/{complaint_id}/status",
    response_model=ComplaintRead,
    tags=["municipal operations"],
)
def admin_update_status(
    complaint_id: UUID, data: ComplaintStatusUpdate, session: DatabaseSession
):
    return service.update_complaint_status(session, complaint_id, data)


@router.get(
    "/api/v1/admin/dashboard", response_model=DashboardStatistics, tags=["municipal operations"]
)
def admin_dashboard(session: DatabaseSession):
    return service.dashboard_statistics(session)


@router.get("/api/v1/complaint-images/{filename}")
def get_image(filename: str, request: Request):
    path = image_path(request.app.state.upload_directory, filename)
    if not path.is_file():
        raise HTTPException(404, "Complaint image not found.")
    return FileResponse(path, media_type="image/png" if path.suffix == ".png" else "image/jpeg",
                        headers={"X-Content-Type-Options": "nosniff", "Content-Security-Policy": "default-src 'none'"})
