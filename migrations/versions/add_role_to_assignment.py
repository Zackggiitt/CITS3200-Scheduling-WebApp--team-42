"""Add role field to Assignment model

Revision ID: add_role_to_assignment
Revises: 
Create Date: 2025-10-12 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_role_to_assignment'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add role column to assignment table with default value 'lead'
    op.add_column('assignment', sa.Column('role', sa.String(length=20), nullable=True))
    
    # Set default value for existing records
    op.execute("UPDATE assignment SET role = 'lead' WHERE role IS NULL")
    
    # Make column non-nullable after setting defaults
    op.alter_column('assignment', 'role', nullable=False, server_default='lead')


def downgrade():
    # Remove role column
    op.drop_column('assignment', 'role')

