from __future__ import annotations

from dataclasses import dataclass
from time import time
from urllib.parse import urlencode

import httpx
from joserfc import jwt
from joserfc.jwk import KeySet

from civicai.config import OIDCSettings

GOOGLE_ISSUERS = {"https://accounts.google.com", "accounts.google.com"}
DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"


@dataclass(frozen=True)
class OIDCIdentity:
    issuer: str
    subject: str
    email: str
    email_verified: bool
    display_name: str


def validate_oidc_claims(claims: dict, *, client_id: str, nonce: str, now: int | None = None) -> OIDCIdentity:
    current = int(time()) if now is None else now
    if claims.get("iss") not in GOOGLE_ISSUERS:
        raise ValueError("invalid issuer")
    audience = claims.get("aud")
    if not (audience == client_id or isinstance(audience, list) and client_id in audience):
        raise ValueError("invalid audience")
    if not isinstance(claims.get("exp"), int) or claims["exp"] <= current:
        raise ValueError("expired token")
    if claims.get("nonce") != nonce:
        raise ValueError("invalid nonce")
    if not claims.get("sub") or not claims.get("email") or claims.get("email_verified") is not True:
        raise ValueError("required identity claims missing")
    return OIDCIdentity(
        issuer=claims["iss"], subject=claims["sub"], email=claims["email"],
        email_verified=True, display_name=(claims.get("name") or claims["email"].split("@", 1)[0])[:100],
    )


class GoogleOIDCClient:
    def __init__(self, settings: OIDCSettings):
        self.settings = settings

    @property
    def configured(self) -> bool:
        return bool(self.settings.client_id and self.settings.client_secret and self.settings.redirect_uri)

    def authorization_url(self, *, state: str, nonce: str) -> str:
        if not self.configured:
            raise RuntimeError("Google sign-in is not configured")
        return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
            "client_id": self.settings.client_id,
            "redirect_uri": self.settings.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "nonce": nonce,
            "prompt": "select_account",
        })

    async def exchange(self, code: str, nonce: str) -> OIDCIdentity:
        if not self.configured:
            raise RuntimeError("Google sign-in is not configured")
        async with httpx.AsyncClient(timeout=10) as client:
            discovery = (await client.get(DISCOVERY_URL)).raise_for_status().json()
            token_response = await client.post(discovery["token_endpoint"], data={
                "code": code, "client_id": self.settings.client_id,
                "client_secret": self.settings.client_secret,
                "redirect_uri": self.settings.redirect_uri, "grant_type": "authorization_code",
            })
            token_data = token_response.raise_for_status().json()
            id_token = token_data.get("id_token")
            if not id_token:
                raise ValueError("missing ID token")
            jwks = (await client.get(discovery["jwks_uri"])).raise_for_status().json()
        token = jwt.decode(id_token, KeySet.import_key_set(jwks), algorithms=["RS256"])
        return validate_oidc_claims(token.claims, client_id=self.settings.client_id, nonce=nonce)
