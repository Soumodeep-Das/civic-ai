from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from civicai.domain import ComplaintNotFound
from civicai.models import Complaint
from civicai.schemas import ComplaintCreate


def create_complaint(session: Session, data: ComplaintCreate) -> Complaint:
    complaint = Complaint(**data.model_dump())
    session.add(complaint)
    session.commit()
    session.refresh(complaint)
    return complaint


def get_complaint(session: Session, complaint_id: UUID) -> Complaint:
    complaint = session.get(Complaint, complaint_id)
    if complaint is None:
        raise ComplaintNotFound
    return complaint


def list_complaints(session: Session) -> list[Complaint]:
    statement = select(Complaint).order_by(Complaint.created_at, Complaint.complaint_id)
    return list(session.scalars(statement))
