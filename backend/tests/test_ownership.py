from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session

from civicai.models import Complaint, ComplaintAssignmentEvent, MunicipalDepartmentMembership, MunicipalUser


def db(client):
    return Session(bind=client.app.state.test_connection, join_transaction_mode="create_savepoint")


def complaint(client, description="Issue 11 synthetic complaint"):
    response = client.post("/api/v1/complaints", files={"description": (None, description)})
    assert response.status_code == 201
    return response.json()


def department(client, slug="drainage", name="Drainage & Sewerage"):
    response = client.post("/api/v1/admin/departments", json={"slug": slug, "display_name": name, "description": "Synthetic operational department"})
    assert response.status_code == 201
    return response.json()


def assign(client, item, department_id, assignee_id=None, reason="Issue 11 test assignment"):
    return client.patch(f"/api/v1/admin/complaints/{item['complaint_id']}/assignment", json={
        "department_id": department_id, "assignee_user_id": assignee_id,
        "expected_updated_at": item["updated_at"], "reason": reason,
    })


def current_user(client):
    return client.get("/api/v1/auth/me").json()["user"]


def test_department_lifecycle_validation_and_duplicate(admin_client):
    created = department(admin_client)
    assert created["slug"] == "drainage" and created["is_active"] is True
    assert admin_client.post("/api/v1/admin/departments", json={"slug": "other", "display_name": "  Drainage   & Sewerage  "}).status_code == 409
    assert admin_client.post("/api/v1/admin/departments", json={"slug": "Bad Slug", "display_name": "Roads"}).status_code == 422
    renamed = admin_client.patch(f"/api/v1/admin/departments/{created['department_id']}", json={"display_name": "Drainage Operations"})
    assert renamed.status_code == 200 and renamed.json()["slug"] == "drainage"
    assert admin_client.patch(f"/api/v1/admin/departments/{created['department_id']}", json={"is_active": False}).status_code == 200
    assert admin_client.patch(f"/api/v1/admin/departments/{created['department_id']}", json={"is_active": True}).json()["is_active"] is True


def test_membership_is_idempotent_and_disabled_user_is_rejected(admin_client):
    dept = department(admin_client)
    me = current_user(admin_client)
    first = admin_client.post(f"/api/v1/admin/departments/{dept['department_id']}/members", json={"user_id": me["user_id"]})
    second = admin_client.post(f"/api/v1/admin/departments/{dept['department_id']}/members", json={"user_id": me["user_id"]})
    assert first.status_code == second.status_code == 200
    user = admin_client.post("/api/v1/admin/users", json={"username": "disabled.operator", "password": "a-defensible-demo-password", "role": "municipal_operator"}).json()
    admin_client.patch(f"/api/v1/admin/users/{user['user_id']}", json={"is_active": False})
    response = admin_client.post(f"/api/v1/admin/departments/{dept['department_id']}/members", json={"user_id": user["user_id"]})
    assert response.status_code == 409 and response.json()["code"] == "inactive_operator"


def test_assignment_history_retry_privacy_and_stale_conflict(admin_client):
    item = complaint(admin_client)
    dept = department(admin_client)
    me = current_user(admin_client)
    admin_client.post(f"/api/v1/admin/departments/{dept['department_id']}/members", json={"user_id": me["user_id"]})
    assigned = assign(admin_client, item, dept["department_id"])
    assert assigned.status_code == 200 and assigned.json()["department"]["display_name"] == dept["display_name"]
    retry = assign(admin_client, item, dept["department_id"])
    assert retry.status_code == 200 and retry.json()["updated_at"] == assigned.json()["updated_at"]
    with db(admin_client) as session:
        events = list(session.scalars(select(ComplaintAssignmentEvent).where(ComplaintAssignmentEvent.complaint_id == item["complaint_id"])))
        assert len(events) == 1
    stale = assign(admin_client, item, dept["department_id"], me["user_id"])
    assert stale.status_code == 409 and stale.json()["code"] == "stale_complaint_update"
    citizen = admin_client.get(f"/api/v1/complaints/{item['complaint_id']}")
    assert "department" not in citizen.text and "assignee" not in citizen.text and "assignment_history" not in citizen.text


def test_operator_self_claim_and_filtered_queues(admin_client):
    item = complaint(admin_client)
    dept = department(admin_client)
    me = current_user(admin_client)
    admin_client.post(f"/api/v1/admin/departments/{dept['department_id']}/members", json={"user_id": me["user_id"]})
    owned = assign(admin_client, item, dept["department_id"]).json()
    with db(admin_client) as session:
        user = session.get(MunicipalUser, me["user_id"]); user.role = "municipal_operator"; session.commit()
    before = admin_client.get("/api/v1/admin/complaints?queue=my_departments_unassigned").json()
    assert before["total"] == 1
    claimed = admin_client.post(f"/api/v1/admin/complaints/{item['complaint_id']}/claim", json={"expected_updated_at": owned["updated_at"]})
    assert claimed.status_code == 200 and claimed.json()["assignee"]["user_id"] == me["user_id"]
    assert admin_client.get("/api/v1/admin/complaints?queue=mine").json()["total"] == 1
    summary = admin_client.get("/api/v1/admin/work-summary").json()
    assert summary["assigned_to_me"] == 1 and summary["unassigned_in_my_departments"] == 0
    retry = admin_client.post(f"/api/v1/admin/complaints/{item['complaint_id']}/claim", json={"expected_updated_at": owned["updated_at"]})
    assert retry.status_code == 200
    assert admin_client.get("/api/v1/admin/complaints?queue=unassigned").status_code == 403


def test_unresolved_work_blocks_membership_removal_and_department_deactivation(admin_client):
    item = complaint(admin_client)
    dept = department(admin_client)
    me = current_user(admin_client)
    admin_client.post(f"/api/v1/admin/departments/{dept['department_id']}/members", json={"user_id": me["user_id"]})
    assigned = assign(admin_client, item, dept["department_id"], me["user_id"])
    assert assigned.status_code == 200
    remove = admin_client.delete(f"/api/v1/admin/departments/{dept['department_id']}/members/{me['user_id']}")
    assert remove.status_code == 409 and remove.json()["code"] == "operator_has_unresolved_assignments"
    deactivate = admin_client.patch(f"/api/v1/admin/departments/{dept['department_id']}", json={"is_active": False})
    assert deactivate.status_code == 409 and deactivate.json()["code"] == "department_has_unresolved_complaints"


def test_assignment_rejects_operator_outside_department_and_inactive_department(admin_client):
    item = complaint(admin_client)
    drainage = department(admin_client)
    roads = department(admin_client, slug="roads", name="Roads")
    operator = admin_client.post("/api/v1/admin/users", json={
        "username": "roads.operator", "password": "a-defensible-demo-password", "role": "municipal_operator",
    }).json()
    admin_client.post(f"/api/v1/admin/departments/{roads['department_id']}/members", json={"user_id": operator["user_id"]})

    cross_department = assign(admin_client, item, drainage["department_id"], operator["user_id"])
    assert cross_department.status_code == 409
    assert cross_department.json()["code"] == "operator_not_department_member"

    deactivated = admin_client.patch(
        f"/api/v1/admin/departments/{drainage['department_id']}", json={"is_active": False},
    )
    assert deactivated.status_code == 200
    inactive = assign(admin_client, item, drainage["department_id"])
    assert inactive.status_code == 409 and inactive.json()["code"] == "inactive_department"


def test_disabling_assignee_preserves_truthful_current_ownership(admin_client):
    item = complaint(admin_client)
    dept = department(admin_client)
    operator = admin_client.post("/api/v1/admin/users", json={
        "username": "preserved.operator", "password": "a-defensible-demo-password", "role": "municipal_operator",
    }).json()
    admin_client.post(f"/api/v1/admin/departments/{dept['department_id']}/members", json={"user_id": operator["user_id"]})
    assigned = assign(admin_client, item, dept["department_id"], operator["user_id"])
    assert assigned.status_code == 200

    disabled = admin_client.patch(f"/api/v1/admin/users/{operator['user_id']}", json={"is_active": False})
    assert disabled.status_code == 200
    detail = admin_client.get(f"/api/v1/admin/complaints/{item['complaint_id']}")
    assert detail.status_code == 200
    assert detail.json()["assignee"]["user_id"] == operator["user_id"]
    assert detail.json()["assignee"]["is_active"] is False


def test_assignment_history_is_database_immutable(admin_client):
    item = complaint(admin_client)
    dept = department(admin_client)
    assign(admin_client, item, dept["department_id"])
    with pytest.raises(DatabaseError), db(admin_client) as session:
        session.execute(text("UPDATE complaint_assignment_events SET reason = 'tampered'"))
        session.commit()


def test_assignment_and_history_roll_back_together_on_event_failure(admin_client, monkeypatch):
    from civicai import ownership
    item = complaint(admin_client)
    dept = department(admin_client)
    invalid = type("InvalidEvent", (), {"value": "invalid_event"})()
    monkeypatch.setattr(ownership, "_event_type", lambda *args, **kwargs: invalid)
    with pytest.raises(DatabaseError):
        assign(admin_client, item, dept["department_id"])
    with db(admin_client) as session:
        stored = session.get(Complaint, item["complaint_id"])
        assert stored.department_id is None and stored.assignee_user_id is None
        assert session.scalar(select(ComplaintAssignmentEvent).where(ComplaintAssignmentEvent.complaint_id == item["complaint_id"])) is None


def test_operator_cannot_manage_departments_or_cross_assign(operator_client):
    assert operator_client.post("/api/v1/admin/departments", json={"slug": "roads", "display_name": "Roads"}).status_code == 403
    item = complaint(operator_client)
    response = operator_client.patch(f"/api/v1/admin/complaints/{item['complaint_id']}/assignment", json={
        "department_id": str(uuid4()), "expected_updated_at": item["updated_at"], "assignee_user_id": None,
    })
    assert response.status_code == 403


def test_request_id_is_validated_and_returned(admin_client):
    safe = admin_client.get("/health", headers={"X-Request-ID": "issue11-test-request"})
    assert safe.headers["X-Request-ID"] == "issue11-test-request"
    generated = admin_client.get("/health", headers={"X-Request-ID": "bad value\n"})
    assert generated.headers["X-Request-ID"] != "bad value\n"
    assert len(generated.headers["X-Request-ID"]) == 32
