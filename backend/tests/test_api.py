from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from civicai.main import create_app


def post_complaint(client, values):
    fields = {key: (None, str(value)) for key, value in values.items() if value is not None}
    # Empty multipart still needs a boundary for missing-description validation.
    return client.post("/api/v1/complaints", files=fields or {"latitude": (None, "0")})


def test_health_without_database():
    with TestClient(create_app("postgresql+psycopg://unused@127.0.0.1:1/unused")) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_persist(client):
    response = post_complaint(client, {
        "description": "  Large pothole near the school entrance  ",
        "latitude": 22.5726, "longitude": 88.3639,
    })
    assert response.status_code == 201
    body = response.json()
    assert UUID(body["complaint_id"]).version == 4
    assert body["description"] == "Large pothole near the school entrance"
    assert body["latitude"] == 22.5726
    assert body["longitude"] == 88.3639
    assert body["status"] == "submitted"
    assert set(body) == {"complaint_id", "description", "latitude", "longitude", "status", "created_at", "updated_at", "image_ref"}
    for field in ("created_at", "updated_at"):
        assert datetime.fromisoformat(body[field]).utcoffset() == timedelta(0)
    assert body["created_at"] == body["updated_at"]
    # A new HTTP request opens a different Session and reads persisted state.
    fetched = client.get(f'/api/v1/complaints/{body["complaint_id"]}')
    assert fetched.status_code == 200
    assert fetched.json() == body


@pytest.mark.parametrize("description", ["", " ", "\t\n", None])
def test_invalid_description(client, description):
    response = post_complaint(client, {"description": description})
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


@pytest.mark.parametrize("field,value", [("latitude", -90.1), ("latitude", 90.1), ("longitude", -180.1), ("longitude", 180.1)])
def test_invalid_coordinate(client, field, value):
    assert post_complaint(client, {"description": "Issue", field: value}).status_code == 422


def test_required_description(client):
    assert post_complaint(client, {}).status_code == 422


def test_optional_coordinates(client):
    response = post_complaint(client, {"description": "Issue"})
    assert response.status_code == 201
    assert response.json()["latitude"] is None
    assert response.json()["longitude"] is None


@pytest.mark.parametrize("latitude,longitude", [(-90, -180), (90, 180)])
def test_coordinate_boundaries(client, latitude, longitude):
    assert post_complaint(client, {"description": "Issue", "latitude": latitude, "longitude": longitude}).status_code == 201


def test_missing_complaint(client):
    response = client.get(f"/api/v1/complaints/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["code"] == "complaint_not_found"


def test_invalid_uuid(client):
    assert client.get("/api/v1/complaints/not-a-uuid").status_code == 422


def test_list(client):
    assert client.get("/api/v1/complaints").json() == []
    created = [post_complaint(client, {"description": item}).json() for item in ("First", "Second")]
    response = client.get("/api/v1/complaints")
    assert response.status_code == 200
    assert {item["complaint_id"] for item in response.json()} == {item["complaint_id"] for item in created}


@pytest.mark.parametrize("field", ["status", "priority", "reporter_id", "category_label"])
def test_server_owned_and_future_fields_rejected(client, field):
    assert post_complaint(client, {"description": "Issue", field: "value"}).status_code == 422


def test_database_unavailable():
    with TestClient(create_app("postgresql+psycopg://unused@127.0.0.1:1/unused?connect_timeout=1")) as client:
        response = client.get("/api/v1/complaints")
    assert response.status_code == 503
    assert response.json() == {"code": "database_unavailable", "message": "Database temporarily unavailable"}
