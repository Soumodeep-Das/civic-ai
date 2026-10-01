from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from time import monotonic
from typing import Annotated
from uuid import UUID

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import Depends, HTTPException, Request
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from civicai.config import AuthSettings
from civicai.database import get_session
from civicai.domain import MunicipalRole
from civicai.models import MunicipalSession, MunicipalUser, SecurityAuditEvent
from civicai.schemas import MunicipalUserCreate, MunicipalUserUpdate

PASSWORD_HASHER = PasswordHasher(
    time_cost=2, memory_cost=19_456, parallelism=1, hash_len=32, salt_len=16, type=Type.ID
)
DUMMY_PASSWORD_HASH = PASSWORD_HASHER.hash("civicai-dummy-password-never-used")
USERNAME_PATTERN = re.compile(r"^[a-z0-9._-]{3,64}$")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_username(value: str) -> str:
    username = value.strip().lower()
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValueError("Username must be 3-64 lowercase letters, numbers, dots, underscores or hyphens")
    return username


def validate_password(value: str) -> None:
    if len(value) < 12 or len(value) > 128:
        raise ValueError("Password must be between 12 and 128 characters")


def hash_password(value: str) -> str:
    validate_password(value)
    return PASSWORD_HASHER.hash(value)


def verify_password(stored_hash: str, candidate: str) -> bool:
    try:
        return PASSWORD_HASHER.verify(stored_hash, candidate)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def token_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class LoginThrottle:
    """Small, bounded process-local throttle for this single-instance prototype."""

    def __init__(self, limit: int = 5, window_seconds: int = 600, max_keys: int = 5000):
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        self._attempts: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _trim(self, values: deque[float], now: float) -> None:
        while values and values[0] <= now - self.window_seconds:
            values.popleft()

    def check(self, *keys: str) -> None:
        now = monotonic()
        with self._lock:
            for key in keys:
                values = self._attempts[key]
                self._trim(values, now)
                if len(values) >= self.limit:
                    raise HTTPException(429, "Too many login attempts. Try again later.")

    def record_failure(self, *keys: str) -> None:
        now = monotonic()
        with self._lock:
            if len(self._attempts) > self.max_keys:
                self._attempts = defaultdict(deque, {
                    key: values for key, values in self._attempts.items()
                    if values and values[-1] > now - self.window_seconds
                })
            for key in keys:
                values = self._attempts[key]
                self._trim(values, now)
                values.append(now)

    def clear_username(self, key: str) -> None:
        with self._lock:
            self._attempts.pop(key, None)


@dataclass(frozen=True)
class AuthContext:
    user: MunicipalUser
    session: MunicipalSession


def create_user(session: Session, data: MunicipalUserCreate) -> MunicipalUser:
    user = MunicipalUser(
        username=normalize_username(data.username),
        password_hash=hash_password(data.password),
        role=data.role.value,
        is_active=True,
    )
    session.add(user)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(409, "A municipal account with that username already exists.") from exc
    return user


def record_audit(
    session: Session, event_type: str, *, actor_id: UUID | None, subject_id: UUID | None
) -> None:
    session.add(SecurityAuditEvent(
        event_type=event_type, actor_user_id=actor_id, subject_user_id=subject_id
    ))


def create_login_session(
    session: Session, user: MunicipalUser, settings: AuthSettings
) -> tuple[str, MunicipalSession]:
    raw_token = secrets.token_urlsafe(32)
    auth_session = MunicipalSession(
        user_id=user.user_id,
        token_hash=token_digest(raw_token),
        csrf_token=secrets.token_urlsafe(32),
        expires_at=utc_now() + timedelta(hours=settings.session_hours),
    )
    user.last_login_at = utc_now()
    session.add(auth_session)
    record_audit(session, "login_succeeded", actor_id=user.user_id, subject_id=user.user_id)
    session.commit()
    session.refresh(auth_session)
    session.refresh(user)
    return raw_token, auth_session


def get_auth_context(request: Request, session: Annotated[Session, Depends(get_session)]) -> AuthContext:
    settings: AuthSettings = request.app.state.auth_settings
    raw_token = request.cookies.get(settings.cookie_name)
    if not raw_token:
        raise HTTPException(401, "Authentication required.")
    auth_session = session.scalar(select(MunicipalSession).where(
        MunicipalSession.token_hash == token_digest(raw_token),
        MunicipalSession.revoked_at.is_(None),
        MunicipalSession.expires_at > func.now(),
    ))
    if auth_session is None:
        raise HTTPException(401, "Authentication required.")
    user = session.get(MunicipalUser, auth_session.user_id)
    if user is None or not user.is_active:
        raise HTTPException(401, "Authentication required.")
    return AuthContext(user, auth_session)


CurrentAuth = Annotated[AuthContext, Depends(get_auth_context)]


def require_operator(context: CurrentAuth) -> AuthContext:
    if context.user.role not in {MunicipalRole.OPERATOR.value, MunicipalRole.ADMIN.value}:
        raise HTTPException(403, "Insufficient permission.")
    return context


def require_admin(context: CurrentAuth) -> AuthContext:
    if context.user.role != MunicipalRole.ADMIN.value:
        raise HTTPException(403, "Administrator permission required.")
    return context


OperatorAuth = Annotated[AuthContext, Depends(require_operator)]
AdminAuth = Annotated[AuthContext, Depends(require_admin)]


def require_csrf(request: Request, context: CurrentAuth) -> AuthContext:
    supplied = request.headers.get("x-csrf-token", "")
    if not supplied or not hmac.compare_digest(supplied, context.session.csrf_token):
        raise HTTPException(403, "Invalid CSRF token.")
    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") not in request.app.state.auth_settings.allowed_origins:
        raise HTTPException(403, "Origin is not allowed.")
    return context


CsrfAuth = Annotated[AuthContext, Depends(require_csrf)]


def update_user(
    session: Session, target: MunicipalUser, data: MunicipalUserUpdate, actor: MunicipalUser
) -> MunicipalUser:
    new_role = data.role.value if data.role is not None else target.role
    new_active = data.is_active if data.is_active is not None else target.is_active
    removing_admin = (
        target.role == MunicipalRole.ADMIN.value
        and target.is_active
        and (new_role != MunicipalRole.ADMIN.value or not new_active)
    )
    if target.user_id == actor.user_id and not new_active:
        raise HTTPException(409, "You cannot disable your own account.")
    if target.user_id == actor.user_id and new_role != MunicipalRole.ADMIN.value:
        raise HTTPException(409, "You cannot remove your own administrator role.")
    if removing_admin:
        active_admins = session.scalar(select(func.count()).select_from(MunicipalUser).where(
            MunicipalUser.role == MunicipalRole.ADMIN.value,
            MunicipalUser.is_active.is_(True),
        )) or 0
        if active_admins <= 1:
            raise HTTPException(409, "The final active municipal administrator cannot be removed.")
    if target.role != new_role:
        target.role = new_role
        record_audit(session, "role_changed", actor_id=actor.user_id, subject_id=target.user_id)
    if target.is_active != new_active:
        target.is_active = new_active
        record_audit(
            session, "account_reactivated" if new_active else "account_disabled",
            actor_id=actor.user_id, subject_id=target.user_id,
        )
        if not new_active:
            session.execute(update(MunicipalSession).where(
                MunicipalSession.user_id == target.user_id,
                MunicipalSession.revoked_at.is_(None),
            ).values(revoked_at=utc_now()))
    target.updated_at = utc_now()
    session.commit()
    session.refresh(target)
    return target
