"""Make staff_number optional in Facilitator model

Revision ID: make_staff_number_optional
Revises: update_swap_request_model
Create Date: 2025-10-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'make_staff_number_optional'
down_revision = 'update_swap_request_model'
branch_labels = None
depends_on = None


def upgrade():
    # Make staff_number nullable in facilitator table
    with op.batch_alter_table('facilitator', schema=None) as batch_op:
        batch_op.alter_column('staff_number',
                              existing_type=sa.String(length=50),
                              nullable=True)


def downgrade():
    # Revert staff_number to non-nullable
    # Note: This will fail if there are NULL values in the database
    with op.batch_alter_table('facilitator', schema=None) as batch_op:
        batch_op.alter_column('staff_number',
                              existing_type=sa.String(length=50),
                              nullable=False)

