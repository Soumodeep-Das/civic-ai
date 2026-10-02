from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from civicai.domain import AssignmentConflict, AssignmentEventType, ComplaintNotFound, DepartmentNotFound, MunicipalRole, StaleComplaintUpdate
from civicai.models import (
    Complaint, ComplaintAssignmentEvent, DepartmentMembershipEvent, MunicipalDepartment,
    MunicipalDepartmentMembership, MunicipalUser,
)
from civicai.schemas import ComplaintAssignmentUpdate, MunicipalDepartmentCreate, MunicipalDepartmentUpdate

UNRESOLVED_STATUSES = ("submitted", "under_review", "in_progress")
CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f-\x9f]")


def _clean_text(value: str, field: str) -> str:
    normalized = " ".join(unicodedata.normalize("NFKC", value).split())
    if CONTROL_CHARACTERS.search(normalized):
        raise HTTPException(422, f"{field} must not contain control characters.")
    return normalized


def _name_key(value: str) -> str:
    return _clean_text(value, "Department name").casefold()


def list_departments(session: Session, include_inactive: bool = True) -> list[MunicipalDepartment]:
    statement = select(MunicipalDepartment)
    if not include_inactive:
        statement = statement.where(MunicipalDepartment.is_active.is_(True))
    return list(session.scalars(statement.order_by(MunicipalDepartment.display_name, MunicipalDepartment.department_id)))


def create_department(session: Session, data: MunicipalDepartmentCreate) -> MunicipalDepartment:
    department = MunicipalDepartment(
        slug=data.slug,
        display_name=_clean_text(data.display_name, "Department name"),
        name_key=_name_key(data.display_name),
        description=_clean_text(data.description, "Department description") if data.description else None,
    )
    session.add(department)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(409, "A department with that name or slug already exists.") from exc
    session.refresh(department)
    return department


def get_department(session: Session, department_id: UUID) -> MunicipalDepartment:
    department = session.get(MunicipalDepartment, department_id)
    if department is None:
        raise DepartmentNotFound
    return department


def update_department(session: Session, department_id: UUID, data: MunicipalDepartmentUpdate) -> MunicipalDepartment:
    department = get_department(session, department_id)
    if data.is_active is False and department.is_active:
        unresolved = session.scalar(select(func.count()).select_from(Complaint).where(
            Complaint.department_id == department_id, Complaint.status.in_(UNRESOLVED_STATUSES)
        )) or 0
        if unresolved:
            raise AssignmentConflict("department_has_unresolved_complaints", "Reassign or resolve the department's unresolved complaints before deactivating it.")
    if data.display_name is not None:
        department.display_name = _clean_text(data.display_name, "Department name")
        department.name_key = _name_key(data.display_name)
    if data.description is not None:
        department.description = _clean_text(data.description, "Department description")
    if data.is_active is not None:
        department.is_active = data.is_active
    department.updated_at = func.clock_timestamp()
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(409, "A department with that name already exists.") from exc
    session.refresh(department)
    return department


def department_members(session: Session, department_id: UUID) -> list[MunicipalUser]:
    get_department(session, department_id)
    return list(session.scalars(
        select(MunicipalUser).join(MunicipalDepartmentMembership, MunicipalDepartmentMembership.user_id == MunicipalUser.user_id)
        .where(MunicipalDepartmentMembership.department_id == department_id)
        .order_by(MunicipalUser.username)
    ))


def add_membership(session: Session, department_id: UUID, user_id: UUID, actor_id: UUID) -> MunicipalUser:
    department = get_department(session, department_id)
    if not department.is_active:
        raise AssignmentConflict("inactive_department", "Membership cannot be added to an inactive department.")
    user = session.get(MunicipalUser, user_id)
    if user is None:
        raise HTTPException(404, "Municipal account not found.")
    if not user.is_active:
        raise AssignmentConflict("inactive_operator", "A disabled municipal account cannot be added to a department.")
    existing = session.get(MunicipalDepartmentMembership, (department_id, user_id))
    if existing is not None:
        return user
    session.add(MunicipalDepartmentMembership(department_id=department_id, user_id=user_id, created_by_user_id=actor_id))
    session.add(DepartmentMembershipEvent(department_id=department_id, user_id=user_id, event_type="membership_added", actor_user_id=actor_id))
    session.commit()
    return user


def remove_membership(session: Session, department_id: UUID, user_id: UUID, actor_id: UUID) -> None:
    get_department(session, department_id)
    membership = session.get(MunicipalDepartmentMembership, (department_id, user_id))
    if membership is None:
        raise HTTPException(404, "Department membership not found.")
    unresolved = session.scalar(select(func.count()).select_from(Complaint).where(
        Complaint.department_id == department_id,
        Complaint.assignee_user_id == user_id,
        Complaint.status.in_(UNRESOLVED_STATUSES),
    )) or 0
    if unresolved:
        raise AssignmentConflict("operator_has_unresolved_assignments", "Reassign this operator's unresolved complaints before removing the membership.")
    session.delete(membership)
    session.add(DepartmentMembershipEvent(department_id=department_id, user_id=user_id, event_type="membership_removed", actor_user_id=actor_id))
    session.commit()


def membership_ids(session: Session, user_id: UUID) -> set[UUID]:
    return set(session.scalars(select(MunicipalDepartmentMembership.department_id).where(MunicipalDepartmentMembership.user_id == user_id)))


def work_queue_statistics(session: Session, actor: MunicipalUser) -> dict:
    memberships = membership_ids(session, actor.user_id)
    departments = list_departments(session) if actor.role == MunicipalRole.ADMIN.value else [
        item for item in list_departments(session) if item.department_id in memberships
    ]
    rows = []
    for department in departments:
        unresolved = session.scalar(select(func.count()).select_from(Complaint).where(
            Complaint.department_id == department.department_id, Complaint.status.in_(UNRESOLVED_STATUSES)
        )) or 0
        assigned = session.scalar(select(func.count()).select_from(Complaint).where(
            Complaint.department_id == department.department_id, Complaint.assignee_user_id.is_not(None)
        )) or 0
        unassigned = session.scalar(select(func.count()).select_from(Complaint).where(
            Complaint.department_id == department.department_id, Complaint.assignee_user_id.is_(None)
        )) or 0
        rows.append({"department": department, "unresolved": unresolved, "assigned": assigned, "unassigned": unassigned})
    return {
        "unassigned_department": (session.scalar(select(func.count()).select_from(Complaint).where(Complaint.department_id.is_(None))) or 0) if actor.role == MunicipalRole.ADMIN.value else 0,
        "assigned_to_me": session.scalar(select(func.count()).select_from(Complaint).where(Complaint.assignee_user_id == actor.user_id)) or 0,
        "unassigned_in_my_departments": session.scalar(select(func.count()).select_from(Complaint).where(
            Complaint.department_id.in_(memberships) if memberships else False, Complaint.assignee_user_id.is_(None)
        )) or 0,
        "in_progress_assigned_to_me": session.scalar(select(func.count()).select_from(Complaint).where(
            Complaint.assignee_user_id == actor.user_id, Complaint.status == "in_progress"
        )) or 0,
        "departments": rows,
    }


def can_view_complaint(session: Session, user: MunicipalUser, complaint: Complaint) -> bool:
    if user.role == MunicipalRole.ADMIN.value:
        return True
    if complaint.assignee_user_id == user.user_id:
        return True
    return complaint.department_id is not None and complaint.department_id in membership_ids(session, user.user_id)


def require_complaint_access(session: Session, user: MunicipalUser, complaint: Complaint) -> None:
    if not can_view_complaint(session, user, complaint):
        raise HTTPException(403, "This complaint is outside your authorized department queues.")


def assignment_history(session: Session, complaint_id: UUID) -> list[ComplaintAssignmentEvent]:
    return list(session.scalars(select(ComplaintAssignmentEvent).where(
        ComplaintAssignmentEvent.complaint_id == complaint_id
    ).order_by(ComplaintAssignmentEvent.occurred_at, ComplaintAssignmentEvent.event_id)))


def _event_type(old_department, new_department, old_assignee, new_assignee, self_claim: bool) -> AssignmentEventType:
    if self_claim:
        return AssignmentEventType.OPERATOR_SELF_ASSIGNED
    if old_department != new_department:
        return AssignmentEventType.DEPARTMENT_ASSIGNED if old_department is None else AssignmentEventType.DEPARTMENT_REASSIGNED
    if old_assignee is None and new_assignee is not None:
        return AssignmentEventType.OPERATOR_ASSIGNED
    if old_assignee is not None and new_assignee is None:
        return AssignmentEventType.RETURNED_TO_DEPARTMENT_QUEUE
    return AssignmentEventType.OPERATOR_CHANGED


def update_assignment(
    session: Session, complaint_id: UUID, data: ComplaintAssignmentUpdate, actor: MunicipalUser,
    *, self_claim: bool = False,
) -> Complaint:
    complaint = session.get(Complaint, complaint_id)
    if complaint is None:
        raise ComplaintNotFound
    if actor.role != MunicipalRole.ADMIN.value:
        require_complaint_access(session, actor, complaint)

    desired_department = data.department_id
    desired_assignee = data.assignee_user_id
    # Exact same desired state is naturally idempotent, including a retry whose response was lost.
    if complaint.department_id == desired_department and complaint.assignee_user_id == desired_assignee:
        return complaint
    if complaint.updated_at.astimezone(timezone.utc) != data.expected_updated_at.astimezone(timezone.utc):
        raise StaleComplaintUpdate
    if desired_department is None and desired_assignee is not None:
        raise AssignmentConflict("assignee_requires_department", "An operator cannot be assigned without an owning department.")
    if desired_department is not None:
        department = get_department(session, desired_department)
        if not department.is_active:
            raise AssignmentConflict("inactive_department", "New work cannot be assigned to an inactive department.")
    if desired_assignee is not None:
        assignee = session.get(MunicipalUser, desired_assignee)
        if assignee is None:
            raise HTTPException(404, "Municipal account not found.")
        if not assignee.is_active:
            raise AssignmentConflict("inactive_operator", "A disabled operator cannot receive an assignment.")
        if session.get(MunicipalDepartmentMembership, (desired_department, desired_assignee)) is None:
            raise AssignmentConflict("operator_not_department_member", "The selected operator is not a member of the owning department.")
    if self_claim:
        if desired_assignee != actor.user_id or desired_department != complaint.department_id or complaint.assignee_user_id is not None:
            raise AssignmentConflict("claim_not_available", "This complaint is no longer available to claim.")
        if session.get(MunicipalDepartmentMembership, (desired_department, actor.user_id)) is None:
            raise HTTPException(403, "You may claim only work in your active department memberships.")

    old_department, old_assignee = complaint.department_id, complaint.assignee_user_id
    result = session.execute(
        update(Complaint).where(
            Complaint.complaint_id == complaint_id,
            Complaint.updated_at == data.expected_updated_at,
            *([Complaint.assignee_user_id.is_(None)] if self_claim else []),
        ).values(
            department_id=desired_department,
            assignee_user_id=desired_assignee,
            updated_at=func.clock_timestamp(),
        ).returning(Complaint)
    ).scalars().one_or_none()
    if result is None:
        raise StaleComplaintUpdate
    session.add(ComplaintAssignmentEvent(
        complaint_id=complaint_id,
        event_type=_event_type(old_department, desired_department, old_assignee, desired_assignee, self_claim).value,
        previous_department_id=old_department,
        new_department_id=desired_department,
        previous_assignee_user_id=old_assignee,
        new_assignee_user_id=desired_assignee,
        actor_user_id=actor.user_id,
        reason=data.reason,
    ))
    session.commit()
    session.refresh(result)
    return result


def claim_complaint(session: Session, complaint_id: UUID, expected_updated_at: datetime, actor: MunicipalUser) -> Complaint:
    complaint = session.get(Complaint, complaint_id)
    if complaint is None:
        raise ComplaintNotFound
    if complaint.department_id is None:
        raise AssignmentConflict("claim_not_available", "A complaint must belong to a department before it can be claimed.")
    return update_assignment(session, complaint_id, ComplaintAssignmentUpdate(
        department_id=complaint.department_id,
        assignee_user_id=actor.user_id,
        expected_updated_at=expected_updated_at,
    ), actor, self_claim=True)
