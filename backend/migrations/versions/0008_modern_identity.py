"""Add citizen identity, shared sessions and staff invitations.

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-03
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "citizen_accounts",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("email_normalized", sa.String(254), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("state", sa.String(24), server_default=sa.text("'pending_verification'"), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("state IN ('pending_verification', 'active', 'disabled')", name="ck_citizen_accounts_state"),
        sa.CheckConstraint("email_normalized = lower(email_normalized)", name="ck_citizen_accounts_email_lower"),
        sa.CheckConstraint("display_name ~ '[^[:space:]]'", name="ck_citizen_accounts_display_name"),
        sa.PrimaryKeyConstraint("account_id"),
        sa.UniqueConstraint("email_normalized"),
    )
    op.create_table(
        "citizen_password_credentials",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["citizen_accounts.account_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("account_id"),
    )
    op.create_table(
        "federated_identities",
        sa.Column("identity_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("issuer", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("provider IN ('google')", name="ck_federated_identities_provider"),
        sa.ForeignKeyConstraint(["account_id"], ["citizen_accounts.account_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("identity_id"),
    )
    op.create_index("uq_federated_identity_subject", "federated_identities", ["provider", "issuer", "subject"], unique=True)
    op.create_table(
        "identity_tokens",
        sa.Column("token_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("purpose", sa.String(32), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("purpose IN ('verify_email', 'reset_password')", name="ck_identity_tokens_purpose"),
        sa.ForeignKeyConstraint(["account_id"], ["citizen_accounts.account_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("token_id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_identity_tokens_account_purpose", "identity_tokens", ["account_id", "purpose"])
    op.create_table(
        "oidc_flows",
        sa.Column("flow_id", sa.Uuid(), nullable=False),
        sa.Column("state_hash", sa.String(64), nullable=False),
        sa.Column("nonce_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("flow_id"),
        sa.UniqueConstraint("state_hash"),
    )
    op.create_index("ix_oidc_flows_expires", "oidc_flows", ["expires_at"])
    op.add_column("municipal_users", sa.Column("email", sa.String(254)))
    op.add_column("municipal_users", sa.Column("email_normalized", sa.String(254)))
    op.add_column("municipal_users", sa.Column("display_name", sa.String(100)))
    op.create_unique_constraint("uq_municipal_users_email_normalized", "municipal_users", ["email_normalized"])
    op.create_table(
        "staff_invitations",
        sa.Column("invitation_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("email_normalized", sa.String(254), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("invited_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("accepted_user_id", sa.Uuid()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("role IN ('municipal_operator', 'municipal_admin')", name="ck_staff_invitations_role"),
        sa.ForeignKeyConstraint(["invited_by_user_id"], ["municipal_users.user_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["accepted_user_id"], ["municipal_users.user_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("invitation_id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_staff_invitations_email", "staff_invitations", ["email_normalized"])
    op.create_index(
        "uq_staff_pending_invitation_email", "staff_invitations", ["email_normalized"], unique=True,
        postgresql_where=sa.text("accepted_at IS NULL AND revoked_at IS NULL"),
    )
    op.create_table(
        "staff_invitation_departments",
        sa.Column("invitation_id", sa.Uuid(), nullable=False),
        sa.Column("department_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["invitation_id"], ["staff_invitations.invitation_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["department_id"], ["municipal_departments.department_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("invitation_id", "department_id"),
    )
    op.add_column("municipal_sessions", sa.Column("citizen_account_id", sa.Uuid()))
    op.alter_column("municipal_sessions", "user_id", existing_type=sa.Uuid(), nullable=True)
    op.create_foreign_key("fk_municipal_sessions_citizen", "municipal_sessions", "citizen_accounts", ["citizen_account_id"], ["account_id"], ondelete="CASCADE")
    op.create_check_constraint(
        "ck_sessions_exactly_one_principal", "municipal_sessions",
        "(user_id IS NOT NULL AND citizen_account_id IS NULL) OR (user_id IS NULL AND citizen_account_id IS NOT NULL)",
    )
    op.create_index("ix_municipal_sessions_citizen", "municipal_sessions", ["citizen_account_id"])
    op.add_column("complaints", sa.Column("citizen_account_id", sa.Uuid()))
    op.create_foreign_key("fk_complaints_citizen", "complaints", "citizen_accounts", ["citizen_account_id"], ["account_id"], ondelete="SET NULL")
    op.create_index("ix_complaints_citizen_created", "complaints", ["citizen_account_id", sa.text("created_at DESC")])
    op.add_column("security_audit_events", sa.Column("actor_citizen_account_id", sa.Uuid()))
    op.add_column("security_audit_events", sa.Column("subject_citizen_account_id", sa.Uuid()))
    op.create_foreign_key("fk_security_audit_actor_citizen", "security_audit_events", "citizen_accounts", ["actor_citizen_account_id"], ["account_id"], ondelete="SET NULL")
    op.create_foreign_key("fk_security_audit_subject_citizen", "security_audit_events", "citizen_accounts", ["subject_citizen_account_id"], ["account_id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_security_audit_subject_citizen", "security_audit_events", type_="foreignkey")
    op.drop_constraint("fk_security_audit_actor_citizen", "security_audit_events", type_="foreignkey")
    op.drop_column("security_audit_events", "subject_citizen_account_id")
    op.drop_column("security_audit_events", "actor_citizen_account_id")
    op.drop_index("ix_complaints_citizen_created", table_name="complaints")
    op.drop_constraint("fk_complaints_citizen", "complaints", type_="foreignkey")
    op.drop_column("complaints", "citizen_account_id")
    op.drop_index("ix_municipal_sessions_citizen", table_name="municipal_sessions")
    op.drop_constraint("ck_sessions_exactly_one_principal", "municipal_sessions", type_="check")
    op.drop_constraint("fk_municipal_sessions_citizen", "municipal_sessions", type_="foreignkey")
    op.alter_column("municipal_sessions", "user_id", existing_type=sa.Uuid(), nullable=False)
    op.drop_column("municipal_sessions", "citizen_account_id")
    op.drop_table("staff_invitation_departments")
    op.drop_index("uq_staff_pending_invitation_email", table_name="staff_invitations")
    op.drop_index("ix_staff_invitations_email", table_name="staff_invitations")
    op.drop_table("staff_invitations")
    op.drop_constraint("uq_municipal_users_email_normalized", "municipal_users", type_="unique")
    op.drop_column("municipal_users", "display_name")
    op.drop_column("municipal_users", "email_normalized")
    op.drop_column("municipal_users", "email")
    op.drop_index("ix_identity_tokens_account_purpose", table_name="identity_tokens")
    op.drop_index("ix_oidc_flows_expires", table_name="oidc_flows")
    op.drop_table("oidc_flows")
    op.drop_table("identity_tokens")
    op.drop_index("uq_federated_identity_subject", table_name="federated_identities")
    op.drop_table("federated_identities")
    op.drop_table("citizen_password_credentials")
    op.drop_table("citizen_accounts")
