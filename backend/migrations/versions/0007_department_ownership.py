"""Add departments, memberships and immutable complaint assignment history.

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-02
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "municipal_departments",
        sa.Column("department_id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("name_key", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name="ck_departments_slug"),
        sa.CheckConstraint("length(display_name) BETWEEN 2 AND 100", name="ck_departments_display_name_length"),
        sa.CheckConstraint("display_name ~ '[^[:space:]]'", name="ck_departments_display_name"),
        sa.PrimaryKeyConstraint("department_id"),
        sa.UniqueConstraint("slug"),
        sa.UniqueConstraint("name_key"),
    )
    op.create_table(
        "municipal_department_memberships",
        sa.Column("department_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("clock_timestamp()"), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["municipal_departments.department_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["municipal_users.user_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["municipal_users.user_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("department_id", "user_id"),
    )
    op.create_index("ix_department_memberships_user", "municipal_department_memberships", ["user_id", "department_id"])
    op.create_table(
        "department_membership_events",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("department_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("clock_timestamp()"), nullable=False),
        sa.CheckConstraint("event_type IN ('membership_added', 'membership_removed')", name="ck_membership_events_type"),
        sa.ForeignKeyConstraint(["department_id"], ["municipal_departments.department_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["municipal_users.user_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["municipal_users.user_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.add_column("complaints", sa.Column("department_id", sa.Uuid(), nullable=True))
    op.add_column("complaints", sa.Column("assignee_user_id", sa.Uuid(), nullable=True))
    op.create_foreign_key("fk_complaints_department", "complaints", "municipal_departments", ["department_id"], ["department_id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_complaints_assignee", "complaints", "municipal_users", ["assignee_user_id"], ["user_id"], ondelete="RESTRICT")
    op.create_index("ix_complaints_department_created", "complaints", ["department_id", sa.text("created_at DESC")])
    op.create_index("ix_complaints_assignee_created", "complaints", ["assignee_user_id", sa.text("created_at DESC")])
    op.create_table(
        "complaint_assignment_events",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("complaint_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("previous_department_id", sa.Uuid(), nullable=True),
        sa.Column("new_department_id", sa.Uuid(), nullable=True),
        sa.Column("previous_assignee_user_id", sa.Uuid(), nullable=True),
        sa.Column("new_assignee_user_id", sa.Uuid(), nullable=True),
        sa.Column("actor_user_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.String(1000), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("clock_timestamp()"), nullable=False),
        sa.CheckConstraint("event_type IN ('department_assigned', 'department_reassigned', 'operator_assigned', 'operator_changed', 'operator_self_assigned', 'operator_unassigned', 'returned_to_department_queue')", name="ck_assignment_events_type"),
        sa.CheckConstraint("reason IS NULL OR (length(reason) <= 1000 AND reason ~ '[^[:space:]]')", name="ck_assignment_events_reason"),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.complaint_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["previous_department_id"], ["municipal_departments.department_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["new_department_id"], ["municipal_departments.department_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["previous_assignee_user_id"], ["municipal_users.user_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["new_assignee_user_id"], ["municipal_users.user_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["municipal_users.user_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_assignment_events_complaint_time", "complaint_assignment_events", ["complaint_id", "occurred_at", "event_id"])
    op.execute(sa.text("""
        CREATE FUNCTION civicai_reject_assignment_event_mutation()
        RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'complaint assignment history is immutable'; END;
        $$ LANGUAGE plpgsql
    """))
    op.execute(sa.text("""
        CREATE TRIGGER trg_complaint_assignment_events_immutable
        BEFORE UPDATE OR DELETE ON complaint_assignment_events
        FOR EACH ROW EXECUTE FUNCTION civicai_reject_assignment_event_mutation()
    """))
    op.execute(sa.text("""
        CREATE FUNCTION civicai_reject_membership_event_mutation()
        RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'department membership history is immutable'; END;
        $$ LANGUAGE plpgsql
    """))
    op.execute(sa.text("""
        CREATE TRIGGER trg_department_membership_events_immutable
        BEFORE UPDATE OR DELETE ON department_membership_events
        FOR EACH ROW EXECUTE FUNCTION civicai_reject_membership_event_mutation()
    """))


def downgrade() -> None:
    op.execute("DROP TRIGGER trg_department_membership_events_immutable ON department_membership_events")
    op.execute("DROP FUNCTION civicai_reject_membership_event_mutation()")
    op.execute("DROP TRIGGER trg_complaint_assignment_events_immutable ON complaint_assignment_events")
    op.execute("DROP FUNCTION civicai_reject_assignment_event_mutation()")
    op.drop_index("ix_assignment_events_complaint_time", table_name="complaint_assignment_events")
    op.drop_table("complaint_assignment_events")
    op.drop_index("ix_complaints_assignee_created", table_name="complaints")
    op.drop_index("ix_complaints_department_created", table_name="complaints")
    op.drop_constraint("fk_complaints_assignee", "complaints", type_="foreignkey")
    op.drop_constraint("fk_complaints_department", "complaints", type_="foreignkey")
    op.drop_column("complaints", "assignee_user_id")
    op.drop_column("complaints", "department_id")
    op.drop_table("department_membership_events")
    op.drop_index("ix_department_memberships_user", table_name="municipal_department_memberships")
    op.drop_table("municipal_department_memberships")
    op.drop_table("municipal_departments")
