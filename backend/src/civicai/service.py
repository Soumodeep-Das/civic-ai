from datetime import datetime, timedelta, timezone
from math import ceil
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.orm import Session

from civicai.domain import (
    ComplaintNotFound, ComplaintStatus, InvalidStatusTransition, StaleComplaintUpdate,
    transition_is_allowed,
)
from civicai.models import Complaint, ComplaintStatusEvent
from civicai.schemas import ComplaintCreate, ComplaintStatusUpdate


def create_complaint(session: Session, data: ComplaintCreate, image_ref: str | None = None) -> Complaint:
    complaint = Complaint(**data.model_dump(), image_ref=image_ref)
    session.add(complaint)
    session.flush()
    session.add(ComplaintStatusEvent(
        complaint_id=complaint.complaint_id,
        event_type="created",
        previous_status=None,
        new_status=ComplaintStatus.SUBMITTED,
        occurred_at=complaint.created_at,
    ))
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


def list_status_history(session: Session, complaint_id: UUID) -> list[ComplaintStatusEvent]:
    get_complaint(session, complaint_id)
    statement = (
        select(ComplaintStatusEvent)
        .where(ComplaintStatusEvent.complaint_id == complaint_id)
        .order_by(ComplaintStatusEvent.occurred_at, ComplaintStatusEvent.event_id)
    )
    return list(session.scalars(statement))


def get_admin_complaint(session: Session, complaint_id: UUID) -> tuple[Complaint, list[ComplaintStatusEvent]]:
    return get_complaint(session, complaint_id), list_status_history(session, complaint_id)


def _escaped_contains(column, value: str):
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return column.ilike(f"%{escaped}%", escape="\\")


def list_admin_complaints(
    session: Session,
    *,
    page: int,
    page_size: int,
    status: ComplaintStatus | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    has_location: bool | None = None,
    has_photo: bool | None = None,
    query: str | None = None,
) -> tuple[list[Complaint], int]:
    filters = []
    if status is not None:
        filters.append(Complaint.status == status)
    if created_from is not None:
        filters.append(Complaint.created_at >= created_from)
    if created_to is not None:
        filters.append(Complaint.created_at <= created_to)
    if has_location is not None:
        location_present = and_(Complaint.latitude.is_not(None), Complaint.longitude.is_not(None))
        filters.append(location_present if has_location else ~location_present)
    if has_photo is not None:
        filters.append(Complaint.image_ref.is_not(None) if has_photo else Complaint.image_ref.is_(None))
    normalized_query = (query or "").strip()
    if normalized_query:
        search_parts = [
            _escaped_contains(Complaint.description, normalized_query),
            _escaped_contains(Complaint.location_label, normalized_query),
            _escaped_contains(Complaint.location_details, normalized_query),
        ]
        try:
            search_parts.append(Complaint.complaint_id == UUID(normalized_query))
        except ValueError:
            pass
        filters.append(or_(*search_parts))

    where = and_(*filters) if filters else True
    total = session.scalar(select(func.count()).select_from(Complaint).where(where)) or 0
    statement = (
        select(Complaint)
        .where(where)
        .order_by(Complaint.created_at.desc(), Complaint.complaint_id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(session.scalars(statement)), total


def update_complaint_status(
    session: Session, complaint_id: UUID, data: ComplaintStatusUpdate
) -> Complaint:
    complaint = get_complaint(session, complaint_id)
    current = ComplaintStatus(complaint.status)
    expected = data.expected_updated_at.astimezone(timezone.utc)
    actual = complaint.updated_at.astimezone(timezone.utc)
    if actual != expected:
        raise StaleComplaintUpdate
    if not transition_is_allowed(current, data.new_status):
        raise InvalidStatusTransition(current, data.new_status)
    if current == data.new_status:
        return complaint

    statement = (
        update(Complaint)
        .where(Complaint.complaint_id == complaint_id, Complaint.updated_at == data.expected_updated_at)
        .values(status=data.new_status, updated_at=func.clock_timestamp())
        .returning(Complaint)
    )
    updated = session.scalars(statement).one_or_none()
    if updated is None:
        if session.get(Complaint, complaint_id) is None:
            raise ComplaintNotFound
        raise StaleComplaintUpdate
    session.add(ComplaintStatusEvent(
        complaint_id=complaint_id,
        event_type="status_changed",
        previous_status=current,
        new_status=data.new_status,
        operator_note=data.operator_note,
        actor_id=None,
    ))
    session.commit()
    session.refresh(updated)
    return updated


def dashboard_statistics(session: Session) -> dict[str, int]:
    recent_boundary = datetime.now(timezone.utc) - timedelta(days=7)
    statement = select(
        func.count().label("total"),
        func.count().filter(Complaint.status == ComplaintStatus.SUBMITTED).label("submitted"),
        func.count().filter(Complaint.status == ComplaintStatus.UNDER_REVIEW).label("under_review"),
        func.count().filter(Complaint.status == ComplaintStatus.IN_PROGRESS).label("in_progress"),
        func.count().filter(Complaint.status == ComplaintStatus.RESOLVED).label("resolved"),
        func.count().filter(Complaint.status == ComplaintStatus.REJECTED).label("rejected"),
        func.count().filter(Complaint.created_at >= recent_boundary).label("submitted_last_7_days"),
        func.count().filter(Complaint.image_ref.is_not(None)).label("with_photo"),
        func.count().filter(and_(Complaint.latitude.is_not(None), Complaint.longitude.is_not(None))).label("with_location"),
    )
    row = session.execute(statement).one()
    return {key: int(value) for key, value in row._mapping.items()}


def page_count(total: int, page_size: int) -> int:
    return ceil(total / page_size) if total else 0
