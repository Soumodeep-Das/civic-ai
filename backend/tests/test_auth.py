from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from civicai.auth import utc_now, verify_password
from civicai.models import MunicipalSession, MunicipalUser


PASSWORD = "civicai-dummy-password-never-used"


def database_session(client):
    return Session(bind=client.app.state.test_connection, join_transaction_mode="create_savepoint")


def login(client, username="test.operator", password=PASSWORD):
    return client.post("/api/v1/auth/login", json={"username": username, "password": password})


def test_successful_login_sets_http_only_session_and_returns_no_hash(anonymous_client):
    response = login(anonymous_client)
    assert response.status_code == 200
    assert response.json()["user"]["username"] == "test.operator"
    assert "password" not in response.text
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=strict" in response.headers["set-cookie"]
    assert anonymous_client.get("/api/v1/auth/me").status_code == 200


def test_login_cookie_expiry_is_valid_when_database_uses_non_utc_offset(anonymous_client, monkeypatch):
    from datetime import timezone as datetime_timezone
    from civicai import routes

    original = routes.create_login_session
    def shifted(*args, **kwargs):
        raw_token, auth_session = original(*args, **kwargs)
        auth_session.expires_at = auth_session.expires_at.astimezone(datetime_timezone(timedelta(hours=5, minutes=30)))
        return raw_token, auth_session
    monkeypatch.setattr(routes, "create_login_session", shifted)
    response = login(anonymous_client)
    assert response.status_code == 200
    assert "expires=" in response.headers["set-cookie"].lower()


def test_wrong_and_unknown_credentials_are_generic(anonymous_client):
    wrong = login(anonymous_client, password="wrong-password-value")
    unknown = login(anonymous_client, username="missing.user", password="wrong-password-value")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["message"] == unknown.json()["message"] == "Invalid username or password."


def test_disabled_user_cannot_login_and_existing_session_is_rejected(client):
    with database_session(client) as session:
        user = session.scalar(select(MunicipalUser).where(MunicipalUser.username == "test.operator"))
        user.is_active = False
        session.commit()
    assert client.get("/api/v1/auth/me").status_code == 401
    client.cookies.clear()
    assert login(client).status_code == 401


def test_logout_revokes_server_session(client):
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401


def test_expired_and_missing_sessions_are_rejected(client):
    with database_session(client) as session:
        session.query(MunicipalSession).update({MunicipalSession.expires_at: utc_now() - timedelta(seconds=1)})
        session.commit()
    assert client.get("/api/v1/auth/me").status_code == 401
    client.cookies.clear()
    assert client.get("/api/v1/admin/dashboard").status_code == 401


def test_operator_can_use_operations_but_not_account_management(operator_client):
    assert operator_client.get("/api/v1/admin/dashboard").status_code == 200
    assert operator_client.get("/api/v1/admin/users").status_code == 403
    assert operator_client.post("/api/v1/admin/users", json={
        "username": "new.operator", "password": "a-defensible-demo-password", "role": "municipal_operator"
    }).status_code == 403


def test_csrf_is_required_and_origin_is_checked(client):
    complaint = client.post("/api/v1/complaints", files={"description": (None, "CSRF test")}).json()
    payload = {"new_status": "under_review", "expected_updated_at": complaint["updated_at"]}
    token = client.headers.pop("X-CSRF-Token")
    assert client.patch(f"/api/v1/admin/complaints/{complaint['complaint_id']}/status", json=payload).status_code == 403
    client.headers["X-CSRF-Token"] = token
    client.headers["Origin"] = "https://attacker.example"
    assert client.patch(f"/api/v1/admin/complaints/{complaint['complaint_id']}/status", json=payload).status_code == 403


def test_admin_creates_lists_disables_and_reactivates_operator(admin_client):
    created = admin_client.post("/api/v1/admin/users", json={
        "username": "ward.operator", "password": "a-defensible-demo-password", "role": "municipal_operator"
    })
    assert created.status_code == 201
    body = created.json()
    assert "password" not in created.text
    with database_session(admin_client) as session:
        stored = session.get(MunicipalUser, body["user_id"])
        assert stored.password_hash != "a-defensible-demo-password"
        assert verify_password(stored.password_hash, "a-defensible-demo-password")
    assert any(user["username"] == "ward.operator" for user in admin_client.get("/api/v1/admin/users").json())
    disabled = admin_client.patch(f"/api/v1/admin/users/{body['user_id']}", json={"is_active": False})
    assert disabled.status_code == 200 and disabled.json()["is_active"] is False
    reactivated = admin_client.patch(f"/api/v1/admin/users/{body['user_id']}", json={"is_active": True})
    assert reactivated.status_code == 200 and reactivated.json()["is_active"] is True


def test_duplicate_invalid_role_and_self_disable_are_rejected(admin_client):
    payload = {"username": "ward.operator", "password": "a-defensible-demo-password", "role": "municipal_operator"}
    assert admin_client.post("/api/v1/admin/users", json=payload).status_code == 201
    assert admin_client.post("/api/v1/admin/users", json=payload).status_code == 409
    assert admin_client.post("/api/v1/admin/users", json={**payload, "username": "another.user", "role": "superuser"}).status_code == 422
    me = admin_client.get("/api/v1/auth/me").json()["user"]
    assert admin_client.patch(f"/api/v1/admin/users/{me['user_id']}", json={"is_active": False}).status_code == 409
    assert admin_client.patch(f"/api/v1/admin/users/{me['user_id']}", json={"role": "municipal_operator"}).status_code == 409


def test_authenticated_actor_is_recorded_and_internal_note_stays_private(client):
    complaint = client.post("/api/v1/complaints", files={"description": (None, "Private note boundary")}).json()
    updated = client.patch(f"/api/v1/admin/complaints/{complaint['complaint_id']}/status", json={
        "new_status": "under_review", "expected_updated_at": complaint["updated_at"],
        "operator_note": "Internal inspection note",
    })
    assert updated.status_code == 200
    history = client.get(f"/api/v1/admin/complaints/{complaint['complaint_id']}/history").json()
    assert history[-1]["actor_id"] is not None
    citizen = client.get(f"/api/v1/complaints/{complaint['complaint_id']}")
    assert "history" not in citizen.json()
    assert "Internal inspection note" not in citizen.text


def test_login_throttle_limits_repeated_failures(anonymous_client):
    results = [login(anonymous_client, username="throttle.user", password="wrong-password-value") for _ in range(6)]
    assert [response.status_code for response in results[:5]] == [401] * 5
    assert results[5].status_code == 429


def test_auth_responses_are_not_cached_and_cors_is_not_broadened(client):
    response = client.get("/api/v1/auth/me")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    preflight = client.options(
        "/api/v1/admin/users",
        headers={"Origin": "https://attacker.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in preflight.headers
