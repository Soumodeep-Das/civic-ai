import re
from time import time
from urllib.parse import parse_qs, urlparse

import pytest

from sqlalchemy import select
from sqlalchemy.orm import Session

from civicai.auth import utc_now
from civicai.models import CitizenAccount, Complaint, IdentityToken, MunicipalDepartment, StaffInvitation, MunicipalUser
from civicai.oidc import OIDCIdentity, validate_oidc_claims


PASSWORD = "correct horse battery staple"


def _token(client, route: str) -> str:
    message = client.app.state.email_service.messages[-1]
    match = re.search(rf"/{route}\?token=([^\s]+)", message.text)
    assert match
    return match.group(1)


def _signup_and_verify(client, email="Citizen@Example.COM", name="Civic Citizen"):
    response = client.post("/api/v1/citizen-auth/sign-up", json={
        "display_name": name, "email": email, "password": PASSWORD,
    })
    assert response.status_code == 202, response.text
    token = _token(client, "verify-email")
    assert client.post("/api/v1/citizen-auth/verify-email", json={"token": token}).status_code == 200
    return token


def _login(client, email="citizen@example.com", password=PASSWORD):
    response = client.post("/api/v1/citizen-auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    client.headers.update({"X-CSRF-Token": response.json()["csrf_token"], "Origin": "http://testserver"})
    return response


def test_signup_normalization_verification_and_reuse(anonymous_client):
    token = _signup_and_verify(anonymous_client)
    with Session(bind=anonymous_client.app.state.test_connection, join_transaction_mode="create_savepoint") as session:
        account = session.scalar(select(CitizenAccount))
        assert account.email_normalized == "citizen@example.com"
        assert account.state == "active"
    reused = anonymous_client.post("/api/v1/citizen-auth/verify-email", json={"token": token})
    assert reused.status_code == 400
    duplicate = anonymous_client.post("/api/v1/citizen-auth/sign-up", json={
        "display_name": "Another", "email": "citizen@example.com", "password": PASSWORD,
    })
    assert duplicate.status_code == 409


def test_password_policy_and_login_errors(anonymous_client):
    weak = anonymous_client.post("/api/v1/citizen-auth/sign-up", json={
        "display_name": "Citizen", "email": "weak@example.com", "password": "short",
    })
    assert weak.status_code == 422
    _signup_and_verify(anonymous_client)
    assert anonymous_client.post("/api/v1/citizen-auth/login", json={
        "email": "citizen@example.com", "password": "the wrong password indeed",
    }).json()["message"] == "Email or password is incorrect."
    assert anonymous_client.post("/api/v1/citizen-auth/login", json={
        "email": "missing@example.com", "password": "the wrong password indeed",
    }).json()["message"] == "Email or password is incorrect."


def test_expired_verification_and_disabled_citizen_are_rejected(anonymous_client):
    response = anonymous_client.post("/api/v1/citizen-auth/sign-up", json={
        "display_name": "Citizen", "email": "disabled@example.com", "password": PASSWORD,
    })
    assert response.status_code == 202
    token = _token(anonymous_client, "verify-email")
    with Session(bind=anonymous_client.app.state.test_connection, join_transaction_mode="create_savepoint") as session:
        row = session.scalar(select(IdentityToken).where(IdentityToken.token_hash.is_not(None)))
        row.expires_at = utc_now()
        session.commit()
    assert anonymous_client.post("/api/v1/citizen-auth/verify-email", json={"token": token}).status_code == 400
    _signup_and_verify(anonymous_client, "active-then-disabled@example.com")
    with Session(bind=anonymous_client.app.state.test_connection, join_transaction_mode="create_savepoint") as session:
        account = session.scalar(select(CitizenAccount).where(CitizenAccount.email_normalized == "active-then-disabled@example.com"))
        account.state = "disabled"
        session.commit()
    assert anonymous_client.post("/api/v1/citizen-auth/login", json={
        "email": "active-then-disabled@example.com", "password": PASSWORD,
    }).status_code == 401


def test_citizen_session_logout_password_change_and_reset(anonymous_client):
    _signup_and_verify(anonymous_client)
    login = _login(anonymous_client)
    assert anonymous_client.get("/api/v1/citizen-auth/me").status_code == 200
    changed = anonymous_client.post("/api/v1/citizen-auth/change-password", json={
        "current_password": PASSWORD, "new_password": "a different long secure passphrase",
    })
    assert changed.status_code == 200
    assert anonymous_client.post("/api/v1/citizen-auth/logout").status_code == 204
    assert anonymous_client.get("/api/v1/citizen-auth/me").status_code == 401
    anonymous_client.headers.pop("X-CSRF-Token", None)
    anonymous_client.headers.pop("Origin", None)
    generic = anonymous_client.post("/api/v1/citizen-auth/forgot-password", json={"email": "CITIZEN@example.com"})
    assert generic.status_code == 202
    reset_token = _token(anonymous_client, "reset-password")
    reset = anonymous_client.post("/api/v1/citizen-auth/reset-password", json={
        "token": reset_token, "password": "third very secure passphrase",
    })
    assert reset.status_code == 200
    assert anonymous_client.post("/api/v1/citizen-auth/reset-password", json={
        "token": reset_token, "password": "fourth very secure passphrase",
    }).status_code == 400


def test_authenticated_submission_my_complaints_and_cross_account_denial(anonymous_client):
    _signup_and_verify(anonymous_client)
    _login(anonymous_client)
    created = anonymous_client.post("/api/v1/complaints", files={
        "description": (None, "Broken drain owned by citizen"),
    })
    assert created.status_code == 201, created.text
    complaint_id = created.json()["complaint_id"]
    listing = anonymous_client.get("/api/v1/citizen/complaints")
    assert listing.status_code == 200
    assert listing.json()["items"][0]["complaint_id"] == complaint_id
    assert listing.json()["items"][0]["history"][0].keys() == {"event_type", "previous_status", "new_status", "occurred_at"}
    assert anonymous_client.get(f"/api/v1/citizen/complaints/{complaint_id}").status_code == 200
    assert anonymous_client.post("/api/v1/citizen-auth/logout").status_code == 204
    anonymous_client.headers.clear()
    _signup_and_verify(anonymous_client, "second@example.com", "Second Citizen")
    _login(anonymous_client, "second@example.com")
    assert anonymous_client.get(f"/api/v1/citizen/complaints/{complaint_id}").status_code == 404
    assert anonymous_client.get("/api/v1/admin/complaints").status_code == 401


def test_anonymous_submission_and_secure_claim(anonymous_client):
    created = anonymous_client.post("/api/v1/complaints", files={"description": (None, "Anonymous issue")})
    complaint_id = created.json()["complaint_id"]
    tracking = created.json()["tracking_token"]
    assert anonymous_client.get(f"/api/v1/complaints/{complaint_id}?tracking_token={tracking}").status_code == 200
    _signup_and_verify(anonymous_client)
    _login(anonymous_client)
    claim = anonymous_client.post(f"/api/v1/citizen/complaints/{complaint_id}/claim", json={"token": tracking})
    assert claim.status_code == 200
    assert anonymous_client.post(f"/api/v1/citizen/complaints/{complaint_id}/claim", json={"token": tracking}).status_code == 200


def test_staff_invitation_role_and_departments_are_admin_controlled(admin_client):
    department = admin_client.post("/api/v1/admin/departments", json={
        "slug": "identity-test", "display_name": "Identity Test",
    }).json()
    invited = admin_client.post("/api/v1/admin/staff-invitations", json={
        "email": "operator@example.com", "role": "municipal_operator",
        "department_ids": [department["department_id"]],
    })
    assert invited.status_code == 201, invited.text
    token = _token(admin_client, "staff/accept-invite")
    admin_client.cookies.clear()
    admin_client.headers.clear()
    accepted = admin_client.post("/api/v1/staff/accept-invite", json={
        "token": token, "display_name": "Invited Operator", "username": "invited.operator",
        "password": "staff-password-is-long",
    })
    assert accepted.status_code == 201, accepted.text
    assert admin_client.post("/api/v1/staff/accept-invite", json={
        "token": token, "display_name": "Replay", "username": "replay.operator",
        "password": "staff-password-is-long",
    }).status_code == 400
    with Session(bind=admin_client.app.state.test_connection, join_transaction_mode="create_savepoint") as session:
        user = session.scalar(select(MunicipalUser).where(MunicipalUser.username == "invited.operator"))
        assert user.role == "municipal_operator"
        assert user.email_normalized == "operator@example.com"


def test_no_public_staff_registration(anonymous_client):
    response = anonymous_client.post("/api/v1/admin/users", json={
        "username": "public.admin", "password": "public-password-is-long", "role": "municipal_admin",
    })
    assert response.status_code == 401


def test_revoked_staff_invitation_cannot_be_accepted(admin_client):
    invited = admin_client.post("/api/v1/admin/staff-invitations", json={
        "email": "revoked@example.com", "role": "municipal_operator", "department_ids": [],
    })
    token = _token(admin_client, "staff/accept-invite")
    assert admin_client.post(f"/api/v1/admin/staff-invitations/{invited.json()['invitation_id']}/revoke").status_code == 200
    admin_client.cookies.clear(); admin_client.headers.clear()
    assert admin_client.post("/api/v1/staff/accept-invite", json={
        "token": token, "display_name": "Revoked", "username": "revoked.staff",
        "password": "staff-password-is-long",
    }).status_code == 400


@pytest.mark.parametrize("change", [
    {"iss": "https://attacker.example"}, {"aud": "wrong-client"}, {"exp": 1}, {"nonce": "wrong"},
])
def test_google_claim_validation_rejects_invalid_identity(change):
    claims = {
        "iss": "https://accounts.google.com", "aud": "client-id", "exp": int(time()) + 300,
        "nonce": "expected", "sub": "google-subject", "email": "oidc@example.com",
        "email_verified": True, "name": "OIDC Citizen",
    }
    claims.update(change)
    with pytest.raises(ValueError):
        validate_oidc_claims(claims, client_id="client-id", nonce="expected")


def test_google_new_citizen_and_existing_email_refusal(anonymous_client):
    class FakeOIDC:
        configured = True
        def authorization_url(self, *, state, nonce):
            return f"https://accounts.example/auth?state={state}&nonce={nonce}"
        async def exchange(self, code, nonce):
            return OIDCIdentity(
                issuer="https://accounts.google.com", subject=f"subject-{code}",
                email="google@example.com", email_verified=True, display_name="Google Citizen",
            )

    anonymous_client.app.state.oidc_client = FakeOIDC()
    start = anonymous_client.get("/api/v1/citizen-auth/google/start", follow_redirects=False)
    assert start.status_code == 302
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
    callback = anonymous_client.get(
        f"/api/v1/citizen-auth/google/callback?code=first&state={state}", follow_redirects=False,
    )
    assert callback.status_code == 303
    assert callback.headers["location"].endswith("/my-complaints")
    assert anonymous_client.get("/api/v1/citizen-auth/me").status_code == 200

    anonymous_client.cookies.clear()
    start = anonymous_client.get("/api/v1/citizen-auth/google/start", follow_redirects=False)
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
    collision = anonymous_client.get(
        f"/api/v1/citizen-auth/google/callback?code=second&state={state}", follow_redirects=False,
    )
    assert collision.status_code == 303
    assert "google_error=existing_email" in collision.headers["location"]
