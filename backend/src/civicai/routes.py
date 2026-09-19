from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from civicai import service
from civicai.database import get_session
from civicai.schemas import ComplaintCreate, ComplaintRead

router = APIRouter(prefix="/api/v1/complaints", tags=["complaints"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.post("", response_model=ComplaintRead, status_code=201)
def create(data: ComplaintCreate, session: DatabaseSession):
    return service.create_complaint(session, data)


@router.get("", response_model=list[ComplaintRead])
def list_all(session: DatabaseSession):
    return service.list_complaints(session)


@router.get("/{complaint_id}", response_model=ComplaintRead)
def get_one(complaint_id: UUID, session: DatabaseSession):
    return service.get_complaint(session, complaint_id)
