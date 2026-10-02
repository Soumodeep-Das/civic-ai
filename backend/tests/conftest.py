import os
import secrets
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from civicai.database import get_session
from civicai.auth import DUMMY_PASSWORD_HASH, token_digest, utc_now
from civicai.domain import LocationPrecision
from civicai.geocoding import LocationCandidate
from civicai.main import create_app
from civicai.models import MunicipalSession, MunicipalUser

ROOT = Path(__file__).resolve().parents[2]


class StubGeocoder:
    autocomplete_supported = True

    async def search(self, query):
        return [LocationCandidate(
            provider_id="101",
            label="Baranagar, North 24 Parganas, West Bengal, India",
            latitude=22.641,
            longitude=88.377,
            precision=LocationPrecision.BROAD,
        )]

    async def reverse(self, latitude, longitude):
        return LocationCandidate(
            provider_id="reverse-101",
            label="Selected road, Baranagar, West Bengal, India",
            latitude=latitude,
            longitude=longitude,
            precision=LocationPrecision.APPROXIMATE,
        )


@pytest.fixture(scope="session")
def migrated_engine():
    load_dotenv(ROOT / ".env")
    value = os.environ.get("TEST_DATABASE_URL")
    if not value:
        pytest.fail("Set TEST_DATABASE_URL to a dedicated PostgreSQL database ending in _test")
    url = make_url(value)
    if url.drivername != "postgresql+psycopg" or not (url.database or "").endswith("_test"):
        pytest.fail("Tests require postgresql+psycopg and a database name ending in _test")
    developer_url = os.environ.get("DATABASE_URL")
    if developer_url:
        dev = make_url(developer_url)
        if (url.host, url.port or 5432, url.database) == (dev.host, dev.port or 5432, dev.database):
            pytest.fail("TEST_DATABASE_URL must not identify the developer database")
    schema = "test_" + uuid4().hex
    admin = create_engine(url)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    scoped_url = url.update_query_dict({"options": f"-csearch_path={schema} -ctimezone=UTC"})
    engine = create_engine(scoped_url)
    try:
        config = Config(str(ROOT / "alembic.ini"))
        config.attributes["database_url"] = scoped_url
        command.upgrade(config, "head")
        yield engine
    finally:
        engine.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


@pytest.fixture
def client(migrated_engine, tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("AUTH_ALLOWED_ORIGINS", "http://testserver")
    with migrated_engine.connect() as connection:
        transaction = connection.begin()
        app = create_app(migrated_engine.url, geocoder=StubGeocoder())

        def test_session():
            with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
                yield session

        app.dependency_overrides[get_session] = test_session
        app.state.test_connection = connection
        try:
            with TestClient(app) as test_client:
                raw_token = secrets.token_urlsafe(32)
                csrf_token = secrets.token_urlsafe(32)
                with Session(bind=connection, join_transaction_mode="create_savepoint") as seed:
                    user = MunicipalUser(
                        username="test.operator", password_hash=DUMMY_PASSWORD_HASH,
                        role="municipal_admin", is_active=True,
                    )
                    seed.add(user)
                    seed.flush()
                    seed.add(MunicipalSession(
                        user_id=user.user_id, token_hash=token_digest(raw_token),
                        csrf_token=csrf_token, expires_at=utc_now() + timedelta(hours=1),
                    ))
                    seed.commit()
                test_client.cookies.set("civicai_session", raw_token)
                test_client.headers.update({"X-CSRF-Token": csrf_token, "Origin": "http://testserver"})
                yield test_client
        finally:
            transaction.rollback()


@pytest.fixture
def anonymous_client(client):
    client.cookies.clear()
    client.headers.pop("X-CSRF-Token", None)
    client.headers.pop("Origin", None)
    return client


@pytest.fixture
def admin_client(client):
    return client


@pytest.fixture
def operator_client(client):
    with Session(bind=client.app.state.test_connection, join_transaction_mode="create_savepoint") as session:
        user = session.scalar(select(MunicipalUser).where(MunicipalUser.username == "test.operator"))
        user.role = "municipal_operator"
        session.commit()
    return client
