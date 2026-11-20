"""Persist attributed priority snapshots and separate review events."""
from alembic import op
import sqlalchemy as sa
revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('complaint_priority_events',
        sa.Column('event_id', sa.Uuid(), primary_key=True),
        sa.Column('complaint_id', sa.Uuid(), sa.ForeignKey('complaints.complaint_id', ondelete='RESTRICT'), nullable=False),
        sa.Column('actor_id', sa.Uuid(), sa.ForeignKey('municipal_users.user_id', ondelete='RESTRICT'), nullable=False),
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.clock_timestamp(), nullable=False))
    op.create_index('ix_complaint_priority_events_complaint_id', 'complaint_priority_events', ['complaint_id'])

def downgrade():
    op.drop_table('complaint_priority_events')
