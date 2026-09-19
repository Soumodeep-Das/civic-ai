"""Create anonymous complaints."""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "complaints",
        sa.Column("complaint_id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("latitude", sa.Double(), nullable=True),
        sa.Column("longitude", sa.Double(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'submitted'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("description ~ '[^[:space:]]'", name="ck_complaints_description"),
        sa.CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_complaints_latitude"),
        sa.CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_complaints_longitude"),
        sa.CheckConstraint("status = 'submitted'", name="ck_complaints_status"),
    )


def downgrade():
    op.drop_table("complaints")
