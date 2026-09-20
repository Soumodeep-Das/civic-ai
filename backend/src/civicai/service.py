from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from civicai.domain import ComplaintNotFound
from civicai.models import Complaint
from civicai.schemas import ComplaintCreate


def create_complaint(session: Session, data: ComplaintCreate, image_ref: str | None = None) -> Complaint:
    complaint = Complaint(**data.model_dump(), image_ref=image_ref)
    session.add(complaint)
    session.flush()
    session.refresh(complaint)
    # Load server defaults before commit so a later refresh failure cannot trigger
    # removal of an image whose database row was already successfully committed.
    expire_on_commit = session.expire_on_commit
    session.expire_on_commit = False
    try:
        session.commit()
    finally:
        session.expire_on_commit = expire_on_commit
    return complaint


def get_complaint(session: Session, complaint_id: UUID) -> Complaint:
    complaint = session.get(Complaint, complaint_id)
    if complaint is None:
        raise ComplaintNotFound
    return complaint


def list_complaints(session: Session) -> list[Complaint]:
    statement = select(Complaint).order_by(Complaint.created_at, Complaint.complaint_id)
    return list(session.scalars(statement))
