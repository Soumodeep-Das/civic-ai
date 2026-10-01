import os
from dataclasses import dataclass

from dotenv import load_dotenv
from sqlalchemy.engine import make_url


def database_url() -> str:
    load_dotenv()
    value = os.environ.get("DATABASE_URL")
    if not value:
        raise RuntimeError("Set DATABASE_URL before starting CivicAI or running migrations")
    if make_url(value).drivername != "postgresql+psycopg":
        raise ValueError("DATABASE_URL must use postgresql+psycopg")
    return value


@dataclass(frozen=True)
class GeocodingSettings:
    provider: str
    base_url: str
    user_agent: str
    country_codes: str
    maptiler_base_url: str
    maptiler_api_key: str
    proximity: str


@dataclass(frozen=True)
class AuthSettings:
    session_hours: int
    cookie_name: str
    cookie_secure: bool
    allowed_origins: frozenset[str]


def _boolean(name: str, default: bool = False) -> bool:
    value = os.environ.get(name, str(default)).strip().lower()
    if value not in {"true", "false"}:
        raise RuntimeError(f"{name} must be true or false")
    return value == "true"


def auth_settings() -> AuthSettings:
    load_dotenv()
    environment = os.environ.get("APP_ENV", "development").strip().lower()
    secure = _boolean("AUTH_COOKIE_SECURE")
    if environment == "production" and not secure:
        raise RuntimeError("Production requires AUTH_COOKIE_SECURE=true")
    hours = int(os.environ.get("AUTH_SESSION_HOURS", "8"))
    if hours < 1 or hours > 24:
        raise RuntimeError("AUTH_SESSION_HOURS must be between 1 and 24")
    cookie_name = os.environ.get("AUTH_COOKIE_NAME", "civicai_session").strip()
    if not cookie_name:
        raise RuntimeError("AUTH_COOKIE_NAME must not be empty")
    origins = frozenset(
        value.strip().rstrip("/")
        for value in os.environ.get(
            "AUTH_ALLOWED_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173"
        ).split(",")
        if value.strip()
    )
    return AuthSettings(hours, cookie_name, secure, origins)


def geocoding_settings() -> GeocodingSettings:
    load_dotenv()
    return GeocodingSettings(
        provider=os.environ.get("GEOCODING_PROVIDER", "nominatim").strip().lower(),
        base_url=os.environ.get("GEOCODING_BASE_URL", "https://nominatim.openstreetmap.org"),
        user_agent=os.environ.get("GEOCODING_USER_AGENT", "CivicAI-MCA/0.1 educational-local-prototype"),
        country_codes=os.environ.get("GEOCODING_COUNTRY_CODES", "in"),
        maptiler_base_url=os.environ.get("MAPTILER_BASE_URL", "https://api.maptiler.com"),
        maptiler_api_key=os.environ.get("MAPTILER_API_KEY", "").strip(),
        proximity=os.environ.get("GEOCODING_PROXIMITY", "").strip(),
    )
