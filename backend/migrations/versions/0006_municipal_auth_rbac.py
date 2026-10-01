"""Add municipal authentication, roles and server-side sessions.

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-30
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "municipal_users",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("role IN ('municipal_operator', 'municipal_admin')", name="ck_municipal_users_role"),
        sa.CheckConstraint("username = lower(username)", name="ck_municipal_users_username_lower"),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "municipal_sessions",
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("csrf_token", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["municipal_users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_index("ix_municipal_sessions_token_hash", "municipal_sessions", ["token_hash"], unique=True)
    op.create_index("ix_municipal_sessions_expires_at", "municipal_sessions", ["expires_at"])
    op.create_table(
        "security_audit_events",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("subject_user_id", sa.Uuid(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("clock_timestamp()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["municipal_users.user_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["subject_user_id"], ["municipal_users.user_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_security_audit_time", "security_audit_events", ["occurred_at", "event_id"])
    op.create_foreign_key(
        "fk_complaint_status_events_actor_id_municipal_users",
        "complaint_status_events", "municipal_users", ["actor_id"], ["user_id"], ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_complaint_status_events_actor_id_municipal_users", "complaint_status_events", type_="foreignkey")
    op.drop_index("ix_security_audit_time", table_name="security_audit_events")
    op.drop_table("security_audit_events")
    op.drop_index("ix_municipal_sessions_expires_at", table_name="municipal_sessions")
    op.drop_index("ix_municipal_sessions_token_hash", table_name="municipal_sessions")
    op.drop_table("municipal_sessions")
    op.drop_table("municipal_users")
