from uuid import uuid4

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from civicai.database import Base


def test_migration_matches_models(migrated_engine):
    with migrated_engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0002"
        context = MigrationContext.configure(connection)
        assert compare_metadata(context, Base.metadata) == []


@pytest.mark.parametrize("description,latitude,longitude,status", [
    (" ", None, None, "submitted"),
    ("Issue", 91, None, "submitted"),
    ("Issue", None, 181, "submitted"),
    ("Issue", None, None, "resolved"),
])
def test_database_constraints(migrated_engine, description, latitude, longitude, status):
    with pytest.raises(IntegrityError):
        with migrated_engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO complaints (complaint_id, description, latitude, longitude, status) "
                "VALUES (:id, :description, :latitude, :longitude, :status)"
            ), {"id": uuid4(), "description": description, "latitude": latitude, "longitude": longitude, "status": status})
