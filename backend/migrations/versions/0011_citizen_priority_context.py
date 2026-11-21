"""Allow anonymous citizen-reported priority context events."""
from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "complaint_priority_events",
        "actor_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )


def downgrade():
    op.execute("DELETE FROM complaint_priority_events WHERE actor_id IS NULL")
    op.alter_column(
        "complaint_priority_events",
        "actor_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )
