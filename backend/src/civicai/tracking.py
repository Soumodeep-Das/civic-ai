"""Opaque anonymous status capabilities; evidence is never exposed by these tokens."""

import hashlib
import hmac
from uuid import UUID


def tracking_token(complaint_id: UUID, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), complaint_id.bytes, hashlib.sha256).hexdigest()


def valid_tracking_token(complaint_id: UUID, supplied: str, secret: str) -> bool:
    return len(supplied) == 64 and hmac.compare_digest(tracking_token(complaint_id, secret), supplied)
