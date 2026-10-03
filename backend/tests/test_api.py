from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from civicai.main import create_app
from civicai.geocoding import GeocodingUnavailable


def post_complaint(client, values):
    fields = {key: (None, str(value)) for key, value in values.items() if value is not None}
    # Empty multipart still needs a boundary for missing-description validation.
    return client.post("/api/v1/complaints", files=fields or {"latitude": (None, "0")})


def test_health_without_database():
    with TestClient(create_app("postgresql+psycopg://unused@127.0.0.1:1/unused")) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "release": "development"}


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
    assert set(body) == {
        "complaint_id", "description", "latitude", "longitude", "location_label",
        "location_precision", "location_details", "location_source", "location_accuracy_m",
        "status", "created_at", "updated_at", "image_ref", "tracking_token",
    }
    assert body["location_label"] is None
    assert body["location_precision"] is None
    assert body["location_details"] is None
    assert body["location_source"] is None
    assert body["location_accuracy_m"] is None
    assert len(body["tracking_token"]) == 64
    for field in ("created_at", "updated_at"):
        assert datetime.fromisoformat(body[field]).utcoffset() == timedelta(0)
    assert body["created_at"] == body["updated_at"]
    # A new HTTP request opens a different Session and reads persisted state.
    fetched = client.get(f'/api/v1/complaints/{body["complaint_id"]}?tracking_token={body["tracking_token"]}')
    assert fetched.status_code == 200
    assert set(fetched.json()) == {"complaint_id", "description", "status", "created_at", "updated_at"}


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


def test_location_context_is_persisted(client):
    response = post_complaint(client, {
        "description": "Blocked drain near the municipal office",
        "latitude": 22.641,
        "longitude": 88.377,
        "location_label": "Baranagar Municipality, West Bengal",
        "location_precision": "approximate",
        "location_details": "Opposite the main entrance",
        "location_source": "device",
        "location_accuracy_m": 18.5,
    })
    assert response.status_code == 201
    body = response.json()
    assert body["location_label"] == "Baranagar Municipality, West Bengal"
    assert body["location_precision"] == "approximate"
    assert body["location_details"] == "Opposite the main entrance"
    assert body["location_source"] == "device"
    assert body["location_accuracy_m"] == 18.5
    tracked = client.get(f'/api/v1/complaints/{body["complaint_id"]}?tracking_token={body["tracking_token"]}').json()
    assert tracked["description"] == body["description"]
    assert "latitude" not in tracked and "image_ref" not in tracked


@pytest.mark.parametrize("values", [
    {"location_label": "Baranagar", "location_precision": "broad"},
    {"latitude": 22.641, "longitude": 88.377, "location_label": "Baranagar"},
    {"latitude": 22.641, "longitude": 88.377, "location_precision": "broad"},
    {"latitude": 22.641, "longitude": 88.377, "location_label": "Baranagar", "location_precision": "surveyed"},
    {"latitude": 22.641, "longitude": 88.377, "location_label": "Baranagar", "location_precision": "broad", "location_details": " "},
    {"latitude": 22.641, "longitude": 88.377, "location_label": "Baranagar", "location_precision": "broad", "location_source": "gps"},
    {"latitude": 22.641, "longitude": 88.377, "location_label": "Baranagar", "location_precision": "broad", "location_source": "search", "location_accuracy_m": 5},
    {"latitude": 22.641, "longitude": 88.377, "location_label": "Baranagar", "location_precision": "broad", "location_source": "device", "location_accuracy_m": -1},
])
def test_invalid_location_context(client, values):
    assert post_complaint(client, {"description": "Issue", **values}).status_code == 422


@pytest.mark.parametrize("latitude,longitude", [(-90, -180), (90, 180)])
def test_coordinate_boundaries(client, latitude, longitude):
    assert post_complaint(client, {"description": "Issue", "latitude": latitude, "longitude": longitude}).status_code == 201


def test_missing_complaint(client):
    response = client.get(f"/api/v1/complaints/{uuid4()}?tracking_token={'0' * 64}")
    assert response.status_code == 404
    assert response.json()["code"] == "request_error"


def test_invalid_uuid(client):
    assert client.get("/api/v1/complaints/not-a-uuid").status_code == 422


def test_list(client):
    response = client.get("/api/v1/complaints")
    assert response.status_code == 404
    assert "private tracking link" in response.json()["message"]


def test_tracking_capability_rejects_missing_and_wrong_token(client):
    created = post_complaint(client, {"description": "Private status"}).json()
    path = f'/api/v1/complaints/{created["complaint_id"]}'
    assert client.get(path).status_code == 422
    assert client.get(f"{path}?tracking_token={'0' * 64}").status_code == 404


def test_location_search_returns_normalized_results(client):
    response = client.post("/api/v1/location-search", json={"query": "  Baranagar  "})
    assert response.status_code == 200
    assert response.json() == [{
        "provider_id": "101",
        "label": "Baranagar, North 24 Parganas, West Bengal, India",
        "latitude": 22.641,
        "longitude": 88.377,
        "precision": "broad",
    }]


def test_location_capabilities_reflect_provider(client):
    assert client.get("/api/v1/location-capabilities").json() == {
        "autocomplete": True,
        "reverse_geocoding": True,
    }


def test_location_reverse_returns_normalized_result(client):
    response = client.post("/api/v1/location-reverse", json={"latitude": 22.65, "longitude": 88.38})
    assert response.status_code == 200
    assert response.json() == {
        "provider_id": "reverse-101",
        "label": "Selected road, Baranagar, West Bengal, India",
        "latitude": 22.65,
        "longitude": 88.38,
        "precision": "approximate",
    }


@pytest.mark.parametrize("payload", [
    {}, {"latitude": 91, "longitude": 88}, {"latitude": 22, "longitude": 181},
    {"latitude": 22, "longitude": 88, "query": "extra"},
])
def test_location_reverse_validates_coordinates(client, payload):
    assert client.post("/api/v1/location-reverse", json=payload).status_code == 422


@pytest.mark.parametrize("payload", [
    {}, {"query": "  "}, {"query": "ab"}, {"query": "x" * 201},
    {"query": "Baranagar", "latitude": 22.6},
])
def test_location_search_validates_query(client, payload):
    response = client.post("/api/v1/location-search", json=payload)
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_location_search_provider_failure_is_sanitized():
    class FailingGeocoder:
        autocomplete_supported = False

        async def search(self, query):
            raise GeocodingUnavailable

        async def reverse(self, latitude, longitude):
            raise GeocodingUnavailable

    with TestClient(create_app(
        "postgresql+psycopg://unused@127.0.0.1:1/unused",
        geocoder=FailingGeocoder(),
    )) as client:
        response = client.post("/api/v1/location-search", json={"query": "Baranagar"})
    assert response.status_code == 503
    assert response.json() == {
        "code": "location_search_unavailable",
        "message": "Location search is temporarily unavailable. Your complaint draft is safe; please try again.",
    }


@pytest.mark.parametrize("field", ["status", "priority", "reporter_id", "category_label"])
def test_server_owned_and_future_fields_rejected(client, field):
    assert post_complaint(client, {"description": "Issue", field: "value"}).status_code == 422


def test_database_unavailable():
    with TestClient(create_app("postgresql+psycopg://unused@127.0.0.1:1/unused?connect_timeout=1")) as client:
        response = client.get("/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "reason": "database"}
