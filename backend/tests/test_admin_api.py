from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest


def create_complaint(client, description="Blocked drain", **values):
    files = {"description": (None, description)}
    files.update({key: (None, str(value)) for key, value in values.items()})
    response = client.post("/api/v1/complaints", files=files)
    assert response.status_code == 201
    return response.json()


def change_status(client, complaint, new_status, note=None, expected=None):
    payload = {
        "new_status": new_status,
        "expected_updated_at": expected or complaint["updated_at"],
        "operator_note": note,
    }
    return client.patch(
        f"/api/v1/admin/complaints/{complaint['complaint_id']}/status", json=payload
    )


def test_creation_records_initial_history_and_admin_detail(client):
    complaint = create_complaint(
        client, "Broken streetlight beside school", latitude=22.64, longitude=88.37,
        location_label="Baranagar, West Bengal", location_precision="approximate",
        location_source="search",
    )
    detail = client.get(f"/api/v1/admin/complaints/{complaint['complaint_id']}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["description"] == complaint["description"]
    assert body["history"] == client.get(
        f"/api/v1/admin/complaints/{complaint['complaint_id']}/history"
    ).json()
    assert len(body["history"]) == 1
    assert body["history"][0]["event_type"] == "created"
    assert body["history"][0]["previous_status"] is None
    assert body["history"][0]["new_status"] == "submitted"
    assert body["history"][0]["operator_note"] is None
    assert body["history"][0]["actor_id"] is None


def test_valid_lifecycle_and_history(client):
    complaint = create_complaint(client)
    for status, note in (
        ("under_review", "Site inspection requested"),
        ("in_progress", "Repair crew notified"),
        ("resolved", "Work completed"),
        ("under_review", "Reopened after verification"),
    ):
        response = change_status(client, complaint, status, note)
        assert response.status_code == 200
        complaint = response.json()
        assert complaint["status"] == status

    history = client.get(
        f"/api/v1/admin/complaints/{complaint['complaint_id']}/history"
    ).json()
    assert [event["new_status"] for event in history] == [
        "submitted", "under_review", "in_progress", "resolved", "under_review"
    ]
    assert history[-1]["operator_note"] == "Reopened after verification"
    assert history[0]["actor_id"] is None
    assert all(event["actor_id"] is not None for event in history[1:])


@pytest.mark.parametrize("target", ["in_progress", "resolved"])
def test_invalid_transition_is_rejected_without_history(client, target):
    complaint = create_complaint(client)
    response = change_status(client, complaint, target)
    assert response.status_code == 409
    assert response.json()["code"] == "invalid_status_transition"
    history = client.get(
        f"/api/v1/admin/complaints/{complaint['complaint_id']}/history"
    ).json()
    assert len(history) == 1


def test_rejected_complaint_can_be_restored_to_review(client):
    complaint = create_complaint(client)
    rejected = change_status(client, complaint, "rejected", "Unable to verify").json()
    restored = change_status(client, rejected, "under_review", "New evidence received")
    assert restored.status_code == 200
    assert restored.json()["status"] == "under_review"


def test_repeated_status_is_idempotent_and_does_not_add_event(client):
    complaint = create_complaint(client)
    response = change_status(client, complaint, "submitted")
    assert response.status_code == 200
    assert response.json()["updated_at"] == complaint["updated_at"]
    assert len(client.get(
        f"/api/v1/admin/complaints/{complaint['complaint_id']}/history"
    ).json()) == 1


def test_stale_update_is_rejected(client):
    complaint = create_complaint(client)
    old_timestamp = complaint["updated_at"]
    current = change_status(client, complaint, "under_review").json()
    response = change_status(client, current, "in_progress", expected=old_timestamp)
    assert response.status_code == 409
    assert response.json()["code"] == "stale_complaint_update"
    assert client.get(f"/api/v1/admin/complaints/{complaint['complaint_id']}").json()["status"] == "under_review"


@pytest.mark.parametrize("payload", [
    {"new_status": "unknown", "expected_updated_at": "2026-09-29T00:00:00Z"},
    {"new_status": "under_review", "expected_updated_at": "2026-09-29T00:00:00"},
    {"new_status": "under_review", "expected_updated_at": "2026-09-29T00:00:00Z", "operator_note": " "},
    {"new_status": "under_review", "expected_updated_at": "2026-09-29T00:00:00Z", "operator_note": "x" * 1001},
])
def test_status_update_validation(client, payload):
    complaint = create_complaint(client)
    assert client.patch(
        f"/api/v1/admin/complaints/{complaint['complaint_id']}/status", json=payload
    ).status_code == 422


def test_admin_list_paginates_filters_and_searches(client):
    first = create_complaint(client, "Large pothole at school gate")
    second = create_complaint(
        client, "Overflowing drain near market", latitude=22.65, longitude=88.38,
        location_label="Baranagar market", location_precision="exact", location_source="map",
    )
    change_status(client, second, "under_review")

    page = client.get("/api/v1/admin/complaints?page=1&page_size=1").json()
    assert page["total"] == 2 and page["total_pages"] == 2
    assert len(page["items"]) == 1
    assert client.get("/api/v1/admin/complaints?page=3&page_size=1").json()["items"] == []
    assert client.get("/api/v1/admin/complaints?status=under_review").json()["total"] == 1
    assert client.get("/api/v1/admin/complaints?has_location=true").json()["total"] == 1
    assert client.get("/api/v1/admin/complaints?has_location=false").json()["total"] == 1
    assert client.get("/api/v1/admin/complaints?q=market").json()["items"][0]["complaint_id"] == second["complaint_id"]
    assert client.get(f"/api/v1/admin/complaints?q={first['complaint_id']}").json()["total"] == 1
    assert client.get("/api/v1/admin/complaints?q=%25_%5C").json()["total"] == 0
    assert client.get("/api/v1/admin/complaints?q=%20%20%20").json()["total"] == 2
    assert client.get("/api/v1/admin/complaints?page_size=101").status_code == 422


def test_admin_date_filters_validate_ranges(client):
    complaint = create_complaint(client)
    created = datetime.fromisoformat(complaint["created_at"].replace("Z", "+00:00"))
    before = (created - timedelta(seconds=1)).isoformat()
    after = (created + timedelta(seconds=1)).isoformat()
    assert client.get("/api/v1/admin/complaints", params={"created_from": before}).json()["total"] == 1
    assert client.get("/api/v1/admin/complaints", params={"created_to": after}).json()["total"] == 1
    assert client.get(
        "/api/v1/admin/complaints", params={"created_from": after, "created_to": before}
    ).status_code == 422


def test_dashboard_uses_real_stored_counts(client):
    submitted = create_complaint(client, "One")
    reviewed = create_complaint(client, "Two")
    change_status(client, reviewed, "under_review")
    stats = client.get("/api/v1/admin/dashboard")
    assert stats.status_code == 200
    assert stats.json() == {
        "total": 2, "submitted": 1, "under_review": 1, "in_progress": 0,
        "resolved": 0, "rejected": 0, "submitted_last_7_days": 2,
        "with_photo": 0, "with_location": 0,
    }


def test_admin_missing_and_invalid_ids(client):
    missing = client.get(f"/api/v1/admin/complaints/{uuid4()}")
    assert missing.status_code == 404
    assert client.get("/api/v1/admin/complaints/not-a-uuid").status_code == 422


def test_citizen_private_tracking_shows_truthful_minimal_status(client):
    complaint = create_complaint(client)
    updated = change_status(client, complaint, "under_review").json()
    response = client.get(
        f"/api/v1/complaints/{complaint['complaint_id']}",
        params={"tracking_token": complaint["tracking_token"]},
    )
    assert response.status_code == 200
    assert response.json() == {
        "complaint_id": updated["complaint_id"],
        "description": updated["description"],
        "status": "under_review",
        "created_at": updated["created_at"],
        "updated_at": updated["updated_at"],
    }
    assert client.get("/api/v1/complaints").status_code == 404


def test_missing_image_returns_clean_404(client):
    response = client.get("/api/v1/complaint-images/missing.png")
    assert response.status_code == 404
    assert response.json()["message"] == "Image not found."
