from uuid import uuid4

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from civicai.database import Base


def test_migration_matches_models(migrated_engine):
    with migrated_engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0007"
        context = MigrationContext.configure(connection)
        assert compare_metadata(context, Base.metadata) == []


@pytest.mark.parametrize("description,latitude,longitude,status", [
    (" ", None, None, "submitted"),
    ("Issue", 91, None, "submitted"),
    ("Issue", None, 181, "submitted"),
    ("Issue", None, None, "unknown"),
])
def test_database_constraints(migrated_engine, description, latitude, longitude, status):
    with pytest.raises(IntegrityError):
        with migrated_engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO complaints (complaint_id, description, latitude, longitude, status) "
                "VALUES (:id, :description, :latitude, :longitude, :status)"
            ), {"id": uuid4(), "description": description, "latitude": latitude, "longitude": longitude, "status": status})


@pytest.mark.parametrize("values", [
    {"latitude": 22.6, "longitude": 88.4, "location_label": "Place", "location_precision": "surveyed", "location_details": None},
    {"latitude": None, "longitude": None, "location_label": "Place", "location_precision": "broad", "location_details": None},
    {"latitude": 22.6, "longitude": 88.4, "location_label": None, "location_precision": "broad", "location_details": None},
    {"latitude": 22.6, "longitude": 88.4, "location_label": "Place", "location_precision": "broad", "location_details": " "},
])
def test_database_location_context_constraints(migrated_engine, values):
    with pytest.raises(IntegrityError):
        with migrated_engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO complaints "
                "(complaint_id, description, latitude, longitude, location_label, location_precision, location_details) "
                "VALUES (:id, 'Issue', :latitude, :longitude, :location_label, :location_precision, :location_details)"
            ), {"id": uuid4(), **values})


@pytest.mark.parametrize("values", [
    {"location_source": "gps", "location_accuracy_m": None},
    {"location_source": "search", "location_accuracy_m": 5},
    {"location_source": "device", "location_accuracy_m": -1},
    {"location_source": "device", "location_accuracy_m": 100001},
])
def test_database_location_quality_constraints(migrated_engine, values):
    with pytest.raises(IntegrityError):
        with migrated_engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO complaints "
                "(complaint_id, description, latitude, longitude, location_label, location_precision, "
                "location_source, location_accuracy_m) "
                "VALUES (:id, 'Issue', 22.6, 88.4, 'Place', 'exact', :location_source, :location_accuracy_m)"
            ), {"id": uuid4(), **values})


def test_status_history_rows_are_database_immutable(migrated_engine):
    complaint_id = uuid4()
    event_id = uuid4()
    with migrated_engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(text(
                "INSERT INTO complaints (complaint_id, description, status) "
                "VALUES (:complaint_id, 'History trigger test', 'submitted')"
            ), {"complaint_id": complaint_id})
            connection.execute(text(
                "INSERT INTO complaint_status_events "
                "(event_id, complaint_id, event_type, previous_status, new_status) "
                "VALUES (:event_id, :complaint_id, 'created', NULL, 'submitted')"
            ), {"event_id": event_id, "complaint_id": complaint_id})
            savepoint = connection.begin_nested()
            with pytest.raises(DBAPIError, match="complaint status history is immutable"):
                connection.execute(text(
                    "UPDATE complaint_status_events SET new_status = 'resolved' "
                    "WHERE event_id = :event_id"
                ), {"event_id": event_id})
            savepoint.rollback()
        finally:
            transaction.rollback()
