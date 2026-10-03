import json
import logging

import pytest

from civicai.config import runtime_settings


def production_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "true")
    monkeypatch.setenv("AUTH_ALLOWED_ORIGINS", "https://civicai.example.org")
    monkeypatch.setenv("PUBLIC_TRACKING_SECRET", "a-unique-production-tracking-secret-123456")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path.resolve()))
    monkeypatch.setenv("RELEASE_ID", "abc1234")


def test_production_configuration_fails_closed(monkeypatch, tmp_path):
    production_environment(monkeypatch, tmp_path)
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    with pytest.raises(RuntimeError, match="AUTH_COOKIE_SECURE"):
        runtime_settings()
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "true")
    monkeypatch.setenv("PUBLIC_TRACKING_SECRET", "short")
    with pytest.raises(RuntimeError, match="PUBLIC_TRACKING_SECRET"):
        runtime_settings()
    monkeypatch.setenv("PUBLIC_TRACKING_SECRET", "a-unique-production-tracking-secret-123456")
    monkeypatch.setenv("AUTH_ALLOWED_ORIGINS", "http://civicai.example.org")
    with pytest.raises(RuntimeError, match="HTTPS"):
        runtime_settings()


def test_readiness_checks_database_schema_and_storage(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "release": "development"}


def test_readiness_fails_when_evidence_storage_is_unavailable(client, monkeypatch):
    monkeypatch.setattr("civicai.main.os.access", lambda *args: False)
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "reason": "evidence_storage"}


def test_security_headers_and_normalized_privacy_safe_log(client, caplog):
    caplog.set_level(logging.INFO, logger="civicai.requests")
    created = client.post("/api/v1/complaints", files={"description": (None, "Secret complaint body")}).json()
    response = client.get(f"/api/v1/complaints/{created['complaint_id']}?tracking_token={created['tracking_token']}")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "geolocation=(self)" in response.headers["permissions-policy"]
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    messages = [record.getMessage() for record in caplog.records if "http_request" in record.getMessage()]
    parsed = [json.loads(message) for message in messages]
    assert any(item["route"] == "/api/v1/complaints/{complaint_id}" for item in parsed)
    assert all(created["complaint_id"] not in message and "Secret complaint body" not in message for message in messages)


def test_public_tracking_response_excludes_evidence_and_location(client):
    created = client.post("/api/v1/complaints", files={
        "description": (None, "Private location complaint"),
        "latitude": (None, "22.64"), "longitude": (None, "88.37"),
        "location_label": (None, "Exact private landmark"), "location_precision": (None, "exact"),
    }).json()
    tracked = client.get(
        f"/api/v1/complaints/{created['complaint_id']}?tracking_token={created['tracking_token']}"
    ).json()
    assert set(tracked) == {"complaint_id", "description", "status", "created_at", "updated_at"}
    assert created["image_ref"] is None
