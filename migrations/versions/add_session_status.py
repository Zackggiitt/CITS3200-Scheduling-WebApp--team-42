"""Add status field to Session model

Revision ID: add_session_status
Revises: 
Create Date: 2025-01-13

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_session_status'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add status column to session table with default value 'draft'
    op.add_column('session', sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'))


def downgrade():
    # Remove status column from session table
    op.drop_column('session', 'status')
