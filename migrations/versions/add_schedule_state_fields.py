"""Add schedule state management fields to Unit model

Revision ID: add_schedule_state_fields
Revises: update_swap_request_model
Create Date: 2025-01-27 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_schedule_state_fields'
down_revision = 'update_swap_request_model'
branch_labels = None
depends_on = None


def upgrade():
    # Create ScheduleStatus enum
    op.execute("CREATE TYPE schedulestatus AS ENUM ('draft', 'published', 'unpublished')")
    
    # Add new columns to unit table
    op.add_column('unit', sa.Column('schedule_status', sa.Enum('draft', 'published', 'unpublished', name='schedulestatus'), nullable=False, server_default='draft'))
    op.add_column('unit', sa.Column('published_at', sa.DateTime(), nullable=True))
    op.add_column('unit', sa.Column('unpublished_at', sa.DateTime(), nullable=True))
    op.add_column('unit', sa.Column('unpublished_by', sa.Integer(), nullable=True))
    op.add_column('unit', sa.Column('unpublish_reason', sa.Text(), nullable=True))
    op.add_column('unit', sa.Column('version_history', sa.Text(), nullable=True))
    
    # Add foreign key constraint for unpublished_by
    op.create_foreign_key('fk_unit_unpublished_by', 'unit', 'user', ['unpublished_by'], ['id'])


def downgrade():
    # Remove foreign key constraint
    op.drop_constraint('fk_unit_unpublished_by', 'unit', type_='foreignkey')
    
    # Remove columns
    op.drop_column('unit', 'version_history')
    op.drop_column('unit', 'unpublish_reason')
    op.drop_column('unit', 'unpublished_by')
    op.drop_column('unit', 'unpublished_at')
    op.drop_column('unit', 'published_at')
    op.drop_column('unit', 'schedule_status')
    
    # Drop enum type
    op.execute("DROP TYPE schedulestatus")
