"""Update SwapRequest model for two-step approval process

Revision ID: update_swap_request_model
Revises: replace_availability_with_unavailability
Create Date: 2025-01-27 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'update_swap_request_model'
down_revision = 'replace_availability_with_unavailability'
branch_labels = None
depends_on = None


def upgrade():
    # Update SwapStatus enum to include new statuses
    op.execute("ALTER TYPE swapstatus ADD VALUE 'facilitator_pending'")
    op.execute("ALTER TYPE swapstatus ADD VALUE 'coordinator_pending'")
    op.execute("ALTER TYPE swapstatus ADD VALUE 'facilitator_declined'")
    op.execute("ALTER TYPE swapstatus ADD VALUE 'coordinator_declined'")
    
    # Add new columns to swap_request table
    op.add_column('swap_request', sa.Column('facilitator_confirmed', sa.Boolean(), nullable=True))
    op.add_column('swap_request', sa.Column('facilitator_confirmed_at', sa.DateTime(), nullable=True))
    op.add_column('swap_request', sa.Column('facilitator_decline_reason', sa.Text(), nullable=True))
    op.add_column('swap_request', sa.Column('coordinator_decline_reason', sa.Text(), nullable=True))
    
    # Set default values for existing records
    op.execute("UPDATE swap_request SET facilitator_confirmed = false WHERE facilitator_confirmed IS NULL")
    op.execute("UPDATE swap_request SET status = 'facilitator_pending' WHERE status = 'pending'")
    
    # Make facilitator_confirmed non-nullable
    op.alter_column('swap_request', 'facilitator_confirmed', nullable=False)


def downgrade():
    # Remove the new columns
    op.drop_column('swap_request', 'coordinator_decline_reason')
    op.drop_column('swap_request', 'facilitator_decline_reason')
    op.drop_column('swap_request', 'facilitator_confirmed_at')
    op.drop_column('swap_request', 'facilitator_confirmed')
    
    # Note: We cannot easily remove enum values in PostgreSQL
    # The enum values will remain but won't be used
    # If needed, a more complex migration would be required to recreate the enum
