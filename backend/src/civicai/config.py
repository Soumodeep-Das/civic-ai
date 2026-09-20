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
    base_url: str
    user_agent: str
    country_codes: str


def geocoding_settings() -> GeocodingSettings:
    load_dotenv()
    return GeocodingSettings(
        base_url=os.environ.get("GEOCODING_BASE_URL", "https://nominatim.openstreetmap.org"),
        user_agent=os.environ.get("GEOCODING_USER_AGENT", "CivicAI-MCA/0.1 educational-local-prototype"),
        country_codes=os.environ.get("GEOCODING_COUNTRY_CODES", "in"),
    )
