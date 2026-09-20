from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.datastructures import UploadFile
from sqlalchemy.orm import Session

from civicai import service
from civicai.database import get_session
from civicai.schemas import ComplaintCreate, ComplaintRead
from civicai.uploads import MAX_IMAGE_BYTES, save_image, image_path

router = APIRouter(tags=["complaints"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.post("/api/v1/complaints", response_model=ComplaintRead, status_code=201,
             openapi_extra={"requestBody": {"required": True, "content": {"multipart/form-data": {
                 "schema": {"type": "object", "required": ["description"], "additionalProperties": False,
                            "properties": {"description": {"type": "string", "minLength": 1},
                                           "latitude": {"type": "number", "minimum": -90, "maximum": 90},
                                           "longitude": {"type": "number", "minimum": -180, "maximum": 180},
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
    async with parsed.form(max_files=1, max_fields=4, max_part_size=64 * 1024) as form:
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
            image_ref = save_image(content, upload.content_type, request.app.state.upload_directory)
        try:
            return service.create_complaint(session, data, image_ref)
        except Exception:
            session.rollback()
            if image_ref is not None:
                (request.app.state.upload_directory / image_ref.rsplit("/", 1)[1]).unlink(missing_ok=True)
            raise


@router.get("/api/v1/complaints", response_model=list[ComplaintRead])
def list_all(session: DatabaseSession):
    return service.list_complaints(session)


@router.get("/api/v1/complaints/{complaint_id}", response_model=ComplaintRead)
def get_one(complaint_id: UUID, session: DatabaseSession):
    return service.get_complaint(session, complaint_id)


@router.get("/api/v1/complaint-images/{filename}")
def get_image(filename: str, request: Request):
    path = image_path(request.app.state.upload_directory, filename)
    return FileResponse(path, media_type="image/png" if path.suffix == ".png" else "image/jpeg",
                        headers={"X-Content-Type-Options": "nosniff", "Content-Security-Policy": "default-src 'none'"})
