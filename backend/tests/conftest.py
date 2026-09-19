import os
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from civicai.database import get_session
from civicai.main import create_app

ROOT = Path(__file__).resolve().parents[2]


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
def client(migrated_engine):
    with migrated_engine.connect() as connection:
        transaction = connection.begin()
        app = create_app(migrated_engine.url)

        def test_session():
            with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
                yield session

        app.dependency_overrides[get_session] = test_session
        try:
            with TestClient(app) as test_client:
                yield test_client
        finally:
            transaction.rollback()
