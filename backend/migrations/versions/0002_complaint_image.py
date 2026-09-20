"""Add optional image reference, preserving existing complaints."""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("complaints", sa.Column("image_ref", sa.String(200), nullable=True))


def downgrade():
    op.drop_column("complaints", "image_ref")
