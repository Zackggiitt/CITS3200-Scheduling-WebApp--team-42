"""Add Unit, Module, and updated FacilitatorSkill models

Revision ID: add_unit_module_facilitator_skill
Revises: 
Create Date: 2025-08-12 12:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_unit_module_facilitator_skill'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create Unit table
    op.create_table('unit',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('unit_code', sa.String(length=20), nullable=False),
        sa.Column('unit_name', sa.String(length=200), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('unit_code')
    )

    # Create Module table
    op.create_table('module',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('unit_id', sa.Integer(), nullable=False),
        sa.Column('module_name', sa.String(length=100), nullable=False),
        sa.Column('module_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['unit_id'], ['unit.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Add new columns to User table
    op.add_column('user', sa.Column('min_hours', sa.Integer(), nullable=True))
    op.add_column('user', sa.Column('max_hours', sa.Integer(), nullable=True))
    
    # Set default values for existing users
    op.execute("UPDATE user SET min_hours = 0 WHERE min_hours IS NULL")
    op.execute("UPDATE user SET max_hours = 20 WHERE max_hours IS NULL")
    
    # Make columns non-nullable
    op.alter_column('user', 'min_hours', nullable=False)
    op.alter_column('user', 'max_hours', nullable=False)

    # Add module_id column to Session table
    op.add_column('session', sa.Column('module_id', sa.Integer(), nullable=False))
    op.add_column('session', sa.Column('day_of_week', sa.Integer(), nullable=True))
    
    # Remove course_name column from Session table
    op.drop_column('session', 'course_name')

    # Add foreign key constraint for module_id in Session table
    op.create_foreign_key(None, 'session', 'module', ['module_id'], ['id'])

    # Add module_id column to FacilitatorSkill table
    op.add_column('facilitator_skill', sa.Column('module_id', sa.Integer(), nullable=False))
    
    # Remove skill_name column from FacilitatorSkill table
    op.drop_column('facilitator_skill', 'skill_name')

    # Add foreign key constraint for module_id in FacilitatorSkill table
    op.create_foreign_key(None, 'facilitator_skill', 'module', ['module_id'], ['id'])

    # Update unique constraint in FacilitatorSkill table
    op.drop_constraint('unique_facilitator_skill', 'facilitator_skill', type_='unique')
    op.create_unique_constraint('unique_facilitator_module_skill', 'facilitator_skill', ['facilitator_id', 'module_id'])


def downgrade():
    # Remove unique constraint in FacilitatorSkill table
    op.drop_constraint('unique_facilitator_module_skill', 'facilitator_skill', type_='unique')
    op.create_unique_constraint('unique_facilitator_skill', 'facilitator_skill', ['facilitator_id', 'skill_name'])

    # Add skill_name column back to FacilitatorSkill table
    op.add_column('facilitator_skill', sa.Column('skill_name', sa.String(length=100), nullable=False))
    
    # Remove module_id column from FacilitatorSkill table
    op.drop_constraint(None, 'facilitator_skill', type_='foreignkey')
    op.drop_column('facilitator_skill', 'module_id')

    # Add course_name column back to Session table
    op.add_column('session', sa.Column('course_name', sa.String(length=200), nullable=False))
    
    # Remove module_id and day_of_week columns from Session table
    op.drop_constraint(None, 'session', type_='foreignkey')
    op.drop_column('session', 'day_of_week')
    op.drop_column('session', 'module_id')

    # Remove min_hours and max_hours columns from User table
    op.drop_column('user', 'max_hours')
    op.drop_column('user', 'min_hours')

    # Drop Module table
    op.drop_table('module')

    # Drop Unit table
    op.drop_table('unit')
