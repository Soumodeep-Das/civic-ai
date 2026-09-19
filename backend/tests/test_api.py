from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from civicai.main import create_app


def test_health_without_database():
    with TestClient(create_app("postgresql+psycopg://unused@127.0.0.1:1/unused")) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_persist(client):
    response = client.post("/api/v1/complaints", json={
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
    assert set(body) == {"complaint_id", "description", "latitude", "longitude", "status", "created_at", "updated_at"}
    for field in ("created_at", "updated_at"):
        assert datetime.fromisoformat(body[field]).utcoffset() == timedelta(0)
    assert body["created_at"] == body["updated_at"]
    # A new HTTP request opens a different Session and reads persisted state.
    fetched = client.get(f'/api/v1/complaints/{body["complaint_id"]}')
    assert fetched.status_code == 200
    assert fetched.json() == body


@pytest.mark.parametrize("description", ["", " ", "\t\n", None])
def test_invalid_description(client, description):
    response = client.post("/api/v1/complaints", json={"description": description})
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


@pytest.mark.parametrize("field,value", [("latitude", -90.1), ("latitude", 90.1), ("longitude", -180.1), ("longitude", 180.1)])
def test_invalid_coordinate(client, field, value):
    assert client.post("/api/v1/complaints", json={"description": "Issue", field: value}).status_code == 422


def test_required_description(client):
    assert client.post("/api/v1/complaints", json={}).status_code == 422


def test_optional_coordinates(client):
    response = client.post("/api/v1/complaints", json={"description": "Issue"})
    assert response.status_code == 201
    assert response.json()["latitude"] is None
    assert response.json()["longitude"] is None


@pytest.mark.parametrize("latitude,longitude", [(-90, -180), (90, 180)])
def test_coordinate_boundaries(client, latitude, longitude):
    assert client.post("/api/v1/complaints", json={"description": "Issue", "latitude": latitude, "longitude": longitude}).status_code == 201


def test_missing_complaint(client):
    response = client.get(f"/api/v1/complaints/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["code"] == "complaint_not_found"


def test_invalid_uuid(client):
    assert client.get("/api/v1/complaints/not-a-uuid").status_code == 422


def test_list(client):
    assert client.get("/api/v1/complaints").json() == []
    created = [client.post("/api/v1/complaints", json={"description": item}).json() for item in ("First", "Second")]
    response = client.get("/api/v1/complaints")
    assert response.status_code == 200
    assert {item["complaint_id"] for item in response.json()} == {item["complaint_id"] for item in created}


@pytest.mark.parametrize("field", ["status", "priority", "reporter_id", "category_label"])
def test_server_owned_and_future_fields_rejected(client, field):
    assert client.post("/api/v1/complaints", json={"description": "Issue", field: "value"}).status_code == 422


def test_database_unavailable():
    with TestClient(create_app("postgresql+psycopg://unused@127.0.0.1:1/unused?connect_timeout=1")) as client:
        response = client.get("/api/v1/complaints")
    assert response.status_code == 503
    assert response.json() == {"code": "database_unavailable", "message": "Database temporarily unavailable"}
