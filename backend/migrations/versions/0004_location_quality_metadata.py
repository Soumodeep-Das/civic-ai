"""Record how a citizen selected an issue location and device accuracy."""

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("complaints", sa.Column("location_source", sa.String(20), nullable=True))
    op.add_column("complaints", sa.Column("location_accuracy_m", sa.Double(), nullable=True))
    op.create_check_constraint(
        "ck_complaints_location_source",
        "complaints",
        "location_source IS NULL OR location_source IN ('search', 'device', 'map')",
    )
    op.create_check_constraint(
        "ck_complaints_location_accuracy",
        "complaints",
        "location_accuracy_m IS NULL OR (location_accuracy_m >= 0 AND location_accuracy_m <= 100000)",
    )
    op.create_check_constraint(
        "ck_complaints_location_accuracy_source",
        "complaints",
        "location_accuracy_m IS NULL OR location_source = 'device'",
    )
    op.create_check_constraint(
        "ck_complaints_location_quality_context",
        "complaints",
        "(location_source IS NULL AND location_accuracy_m IS NULL) OR "
        "(latitude IS NOT NULL AND longitude IS NOT NULL AND location_label IS NOT NULL "
        "AND location_precision IS NOT NULL AND location_source IS NOT NULL)",
    )


def downgrade():
    op.drop_constraint("ck_complaints_location_quality_context", "complaints", type_="check")
    op.drop_constraint("ck_complaints_location_accuracy_source", "complaints", type_="check")
    op.drop_constraint("ck_complaints_location_accuracy", "complaints", type_="check")
    op.drop_constraint("ck_complaints_location_source", "complaints", type_="check")
    op.drop_column("complaints", "location_accuracy_m")
    op.drop_column("complaints", "location_source")
