"""Add municipal complaint lifecycle and immutable status history.

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-29
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_complaints_status", "complaints", type_="check")
    op.create_check_constraint(
        "ck_complaints_status",
        "complaints",
        "status IN ('submitted', 'under_review', 'in_progress', 'resolved', 'rejected')",
    )
    op.create_index(
        "ix_complaints_created_id_desc",
        "complaints",
        [sa.text("created_at DESC"), sa.text("complaint_id DESC")],
    )
    op.create_index(
        "ix_complaints_status_created_desc",
        "complaints",
        ["status", sa.text("created_at DESC")],
    )
    op.create_table(
        "complaint_status_events",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("complaint_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("previous_status", sa.String(length=20), nullable=True),
        sa.Column("new_status", sa.String(length=20), nullable=False),
        sa.Column("operator_note", sa.String(length=1000), nullable=True),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column(
            "occurred_at", sa.DateTime(timezone=True),
            server_default=sa.text("clock_timestamp()"), nullable=False,
        ),
        sa.CheckConstraint(
            "event_type IN ('created', 'status_changed')", name="ck_complaint_events_type"
        ),
        sa.CheckConstraint(
            "previous_status IS NULL OR previous_status IN "
            "('submitted', 'under_review', 'in_progress', 'resolved', 'rejected')",
            name="ck_complaint_events_previous_status",
        ),
        sa.CheckConstraint(
            "new_status IN ('submitted', 'under_review', 'in_progress', 'resolved', 'rejected')",
            name="ck_complaint_events_new_status",
        ),
        sa.CheckConstraint(
            "operator_note IS NULL OR "
            "(length(operator_note) <= 1000 AND operator_note ~ '[^[:space:]]')",
            name="ck_complaint_events_note",
        ),
        sa.ForeignKeyConstraint(
            ["complaint_id"], ["complaints.complaint_id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index(
        "ix_complaint_events_complaint_time",
        "complaint_status_events",
        ["complaint_id", "occurred_at", "event_id"],
    )
    op.execute(sa.text("""
        INSERT INTO complaint_status_events
            (event_id, complaint_id, event_type, previous_status, new_status, operator_note, actor_id, occurred_at)
        SELECT gen_random_uuid(), complaint_id, 'created', NULL, status, NULL, NULL, created_at
        FROM complaints
    """))
    op.execute(sa.text("""
        CREATE FUNCTION civicai_reject_status_event_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'complaint status history is immutable';
        END;
        $$ LANGUAGE plpgsql
    """))
    op.execute(sa.text("""
        CREATE TRIGGER trg_complaint_status_events_immutable
        BEFORE UPDATE OR DELETE ON complaint_status_events
        FOR EACH ROW EXECUTE FUNCTION civicai_reject_status_event_mutation()
    """))


def downgrade() -> None:
    op.execute("DROP TRIGGER trg_complaint_status_events_immutable ON complaint_status_events")
    op.execute("DROP FUNCTION civicai_reject_status_event_mutation()")
    op.drop_index("ix_complaint_events_complaint_time", table_name="complaint_status_events")
    op.drop_table("complaint_status_events")
    op.drop_index("ix_complaints_status_created_desc", table_name="complaints")
    op.drop_index("ix_complaints_created_id_desc", table_name="complaints")
    op.drop_constraint("ck_complaints_status", "complaints", type_="check")
    op.execute("UPDATE complaints SET status = 'submitted', updated_at = clock_timestamp() WHERE status <> 'submitted'")
    op.create_check_constraint("ck_complaints_status", "complaints", "status = 'submitted'")
