"""Store experimental assessments and separate municipal reviews."""
from alembic import op
import sqlalchemy as sa
revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('complaint_assessments',
        sa.Column('assessment_id',sa.Uuid(),primary_key=True),
        sa.Column('complaint_id',sa.Uuid(),sa.ForeignKey('complaints.complaint_id',ondelete='RESTRICT'),nullable=False),
        sa.Column('payload',sa.Text(),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
    op.create_index('ix_complaint_assessments_complaint_id','complaint_assessments',['complaint_id'])
    op.create_table('complaint_assessment_reviews',
        sa.Column('review_id',sa.Uuid(),primary_key=True),
        sa.Column('assessment_id',sa.Uuid(),sa.ForeignKey('complaint_assessments.assessment_id',ondelete='RESTRICT'),nullable=False),
        sa.Column('actor_id',sa.Uuid(),sa.ForeignKey('municipal_users.user_id',ondelete='RESTRICT'),nullable=False),
        sa.Column('payload',sa.Text(),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
    op.create_index('ix_complaint_assessment_reviews_assessment_id','complaint_assessment_reviews',['assessment_id'])


def downgrade():
    op.drop_table('complaint_assessment_reviews')
    op.drop_table('complaint_assessments')
