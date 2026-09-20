"""Add optional, truthful issue-location context without changing legacy rows."""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("complaints", sa.Column("location_label", sa.String(300), nullable=True))
    op.add_column("complaints", sa.Column("location_precision", sa.String(20), nullable=True))
    op.add_column("complaints", sa.Column("location_details", sa.String(500), nullable=True))
    op.create_check_constraint(
        "ck_complaints_location_precision",
        "complaints",
        "location_precision IS NULL OR location_precision IN ('exact', 'approximate', 'broad')",
    )
    op.create_check_constraint(
        "ck_complaints_location_label",
        "complaints",
        "location_label IS NULL OR location_label ~ '[^[:space:]]'",
    )
    op.create_check_constraint(
        "ck_complaints_location_details",
        "complaints",
        "location_details IS NULL OR location_details ~ '[^[:space:]]'",
    )
    op.create_check_constraint(
        "ck_complaints_location_context",
        "complaints",
        "(location_label IS NULL AND location_precision IS NULL AND location_details IS NULL) OR "
        "(latitude IS NOT NULL AND longitude IS NOT NULL AND "
        "location_label IS NOT NULL AND location_precision IS NOT NULL)",
    )


def downgrade():
    op.drop_constraint("ck_complaints_location_context", "complaints", type_="check")
    op.drop_constraint("ck_complaints_location_details", "complaints", type_="check")
    op.drop_constraint("ck_complaints_location_label", "complaints", type_="check")
    op.drop_constraint("ck_complaints_location_precision", "complaints", type_="check")
    op.drop_column("complaints", "location_details")
    op.drop_column("complaints", "location_precision")
    op.drop_column("complaints", "location_label")
