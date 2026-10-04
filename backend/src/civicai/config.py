import os
import re
from dataclasses import dataclass
from pathlib import Path

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
    maptiler_request_origin: str
    proximity: str


@dataclass(frozen=True)
class AuthSettings:
    session_hours: int
    cookie_name: str
    cookie_secure: bool
    allowed_origins: frozenset[str]
    public_base_url: str
    verification_minutes: int
    reset_minutes: int
    invitation_hours: int


@dataclass(frozen=True)
class EmailSettings:
    transport: str
    from_address: str
    capture_directory: Path
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_starttls: bool
    brevo_api_key: str
    brevo_api_url: str


@dataclass(frozen=True)
class EvidenceSettings:
    backend: str
    local_directory: Path
    s3_endpoint_url: str
    s3_region: str
    s3_bucket: str
    s3_access_key_id: str
    s3_secret_access_key: str


@dataclass(frozen=True)
class OIDCSettings:
    client_id: str
    client_secret: str
    redirect_uri: str


@dataclass(frozen=True)
class RuntimeSettings:
    environment: str
    release_id: str
    public_tracking_secret: str
    log_level: str


RELEASE_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def _boolean(name: str, default: bool = False) -> bool:
    value = os.environ.get(name, str(default)).strip().lower()
    if value not in {"true", "false"}:
        raise RuntimeError(f"{name} must be true or false")
    return value == "true"


def auth_settings() -> AuthSettings:
    load_dotenv()
    environment = os.environ.get("APP_ENV", "development").strip().lower()
    secure = _boolean("AUTH_COOKIE_SECURE")
    if environment in {"production", "beta"} and not secure:
        raise RuntimeError("Deployed environments require AUTH_COOKIE_SECURE=true")
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
    base_url = os.environ.get("PUBLIC_BASE_URL", "http://127.0.0.1:5173").strip().rstrip("/")
    if environment in {"production", "beta"} and not base_url.startswith("https://"):
        raise RuntimeError("Deployed PUBLIC_BASE_URL must use HTTPS")
    verification_minutes = int(os.environ.get("AUTH_VERIFICATION_MINUTES", "60"))
    reset_minutes = int(os.environ.get("AUTH_RESET_MINUTES", "30"))
    invitation_hours = int(os.environ.get("AUTH_INVITATION_HOURS", "72"))
    if not 5 <= verification_minutes <= 1440:
        raise RuntimeError("AUTH_VERIFICATION_MINUTES must be between 5 and 1440")
    if not 5 <= reset_minutes <= 120:
        raise RuntimeError("AUTH_RESET_MINUTES must be between 5 and 120")
    if not 1 <= invitation_hours <= 168:
        raise RuntimeError("AUTH_INVITATION_HOURS must be between 1 and 168")
    return AuthSettings(
        hours, cookie_name, secure, origins, base_url,
        verification_minutes, reset_minutes, invitation_hours,
    )


def email_settings() -> EmailSettings:
    load_dotenv()
    transport = os.environ.get("EMAIL_TRANSPORT", "capture").strip().lower()
    if transport not in {"capture", "smtp", "brevo", "disabled"}:
        raise RuntimeError("EMAIL_TRANSPORT must be capture, smtp, brevo or disabled")
    environment = os.environ.get("APP_ENV", "development").strip().lower()
    if environment in {"production", "beta"} and transport in {"capture", "disabled"}:
        raise RuntimeError("Deployed environments require a real email transport")
    return EmailSettings(
        transport=transport,
        from_address=os.environ.get("EMAIL_FROM", "no-reply@civicai.local").strip(),
        capture_directory=Path(os.environ.get("EMAIL_CAPTURE_DIR", "tmp/dev-mail")).resolve(),
        smtp_host=os.environ.get("SMTP_HOST", "").strip(),
        smtp_port=int(os.environ.get("SMTP_PORT", "587")),
        smtp_username=os.environ.get("SMTP_USERNAME", "").strip(),
        smtp_password=os.environ.get("SMTP_PASSWORD", ""),
        smtp_starttls=_boolean("SMTP_STARTTLS", True),
        brevo_api_key=os.environ.get("BREVO_API_KEY", "").strip(),
        brevo_api_url=os.environ.get("BREVO_API_URL", "https://api.brevo.com/v3/smtp/email").strip(),
    )


def evidence_settings() -> EvidenceSettings:
    load_dotenv()
    default = Path(__file__).resolve().parents[3] / "data/uploads/complaints"
    backend = os.environ.get("EVIDENCE_STORAGE_BACKEND", "local").strip().lower()
    if backend not in {"local", "s3"}:
        raise RuntimeError("EVIDENCE_STORAGE_BACKEND must be local or s3")
    settings = EvidenceSettings(
        backend=backend,
        local_directory=Path(os.environ.get("UPLOAD_DIR", str(default))).resolve(),
        s3_endpoint_url=os.environ.get("EVIDENCE_S3_ENDPOINT_URL", "").strip().rstrip("/"),
        s3_region=os.environ.get("EVIDENCE_S3_REGION", "").strip(),
        s3_bucket=os.environ.get("EVIDENCE_S3_BUCKET", "").strip(),
        s3_access_key_id=os.environ.get("EVIDENCE_S3_ACCESS_KEY_ID", "").strip(),
        s3_secret_access_key=os.environ.get("EVIDENCE_S3_SECRET_ACCESS_KEY", "").strip(),
    )
    if backend == "s3" and not all((settings.s3_endpoint_url, settings.s3_region, settings.s3_bucket, settings.s3_access_key_id, settings.s3_secret_access_key)):
        raise RuntimeError("S3 evidence storage requires endpoint, region, bucket, access key and secret key")
    return settings


def oidc_settings() -> OIDCSettings:
    load_dotenv()
    return OIDCSettings(
        client_id=os.environ.get("GOOGLE_OIDC_CLIENT_ID", "").strip(),
        client_secret=os.environ.get("GOOGLE_OIDC_CLIENT_SECRET", "").strip(),
        redirect_uri=os.environ.get("GOOGLE_OIDC_REDIRECT_URI", "http://127.0.0.1:8000/api/v1/citizen-auth/google/callback").strip(),
    )


def runtime_settings() -> RuntimeSettings:
    load_dotenv()
    environment = os.environ.get("APP_ENV", "development").strip().lower()
    if environment not in {"development", "test", "production", "beta"}:
        raise RuntimeError("APP_ENV must be development, test, beta or production")
    release_id = os.environ.get("RELEASE_ID", "development").strip()
    if not RELEASE_PATTERN.fullmatch(release_id):
        raise RuntimeError("RELEASE_ID must contain 1-64 safe identifier characters")
    secret = os.environ.get("PUBLIC_TRACKING_SECRET", "development-only-tracking-secret-change-me").strip()
    log_level = os.environ.get("LOG_LEVEL", "INFO").strip().upper()
    if log_level not in {"INFO", "WARNING", "ERROR"}:
        raise RuntimeError("LOG_LEVEL must be INFO, WARNING or ERROR")
    if environment in {"production", "beta"}:
        if len(secret.encode("utf-8")) < 32 or secret == "development-only-tracking-secret-change-me":
            raise RuntimeError("Deployed environments require a unique PUBLIC_TRACKING_SECRET of at least 32 bytes")
        origins = auth_settings().allowed_origins
        if not origins or any(not origin.startswith("https://") for origin in origins):
            raise RuntimeError("Deployed AUTH_ALLOWED_ORIGINS must contain only HTTPS origins")
        if environment == "production" and evidence_settings().backend == "local":
            configured_upload = os.environ.get("UPLOAD_DIR", "").strip()
            if not configured_upload or not Path(configured_upload).is_absolute():
                raise RuntimeError("Production local storage requires an absolute UPLOAD_DIR")
    return RuntimeSettings(environment, release_id, secret, log_level)


def geocoding_settings() -> GeocodingSettings:
    load_dotenv()
    return GeocodingSettings(
        provider=os.environ.get("GEOCODING_PROVIDER", "nominatim").strip().lower(),
        base_url=os.environ.get("GEOCODING_BASE_URL", "https://nominatim.openstreetmap.org"),
        user_agent=os.environ.get("GEOCODING_USER_AGENT", "CivicAI-MCA/0.1 educational-local-prototype"),
        country_codes=os.environ.get("GEOCODING_COUNTRY_CODES", "in"),
        maptiler_base_url=os.environ.get("MAPTILER_BASE_URL", "https://api.maptiler.com"),
        maptiler_api_key=os.environ.get("MAPTILER_API_KEY", "").strip(),
        maptiler_request_origin=os.environ.get("MAPTILER_REQUEST_ORIGIN", "").strip().rstrip("/"),
        proximity=os.environ.get("GEOCODING_PROXIMITY", "").strip(),
    )
