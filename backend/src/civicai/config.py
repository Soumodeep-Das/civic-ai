import os

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
