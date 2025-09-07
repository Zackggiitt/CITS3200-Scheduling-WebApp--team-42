"""Replace Availability model with Unavailability model

Revision ID: replace_availability_with_unavailability
Revises: add_unit_module_facilitator_skill
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'replace_availability_with_unavailability'
down_revision = 'add_unit_module_facilitator_skill'
branch_labels = None
depends_on = None


def upgrade():
    # Create the new Unavailability table
    op.create_table('unavailability',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('unit_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=True),
        sa.Column('end_time', sa.Time(), nullable=True),
        sa.Column('is_full_day', sa.Boolean(), nullable=True),
        sa.Column('recurring_pattern', sa.Enum('DAILY', 'WEEKLY', 'MONTHLY', 'CUSTOM', name='recurringpattern'), nullable=True),
        sa.Column('recurring_end_date', sa.Date(), nullable=True),
        sa.Column('recurring_interval', sa.Integer(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['unit_id'], ['unit.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'unit_id', 'date', 'start_time', 'end_time', name='unique_unavailability_slot')
    )
    
    # Set default values for boolean and integer columns
    op.execute("UPDATE unavailability SET is_full_day = false WHERE is_full_day IS NULL")
    op.execute("UPDATE unavailability SET recurring_interval = 1 WHERE recurring_interval IS NULL")
    
    # Make columns non-nullable after setting defaults
    op.alter_column('unavailability', 'is_full_day', nullable=False)
    op.alter_column('unavailability', 'recurring_interval', nullable=False)
    
    # Drop the old Availability table
    op.drop_table('availability')


def downgrade():
    # Recreate the old Availability table
    op.create_table('availability',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('is_available', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Set default value for is_available column
    op.execute("UPDATE availability SET is_available = true WHERE is_available IS NULL")
    
    # Make is_available column non-nullable
    op.alter_column('availability', 'is_available', nullable=False)
    
    # Drop the Unavailability table
    op.drop_table('unavailability')
