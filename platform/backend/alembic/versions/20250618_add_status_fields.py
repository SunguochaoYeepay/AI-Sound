"""add status fields

Revision ID: 20250618_add_status
Revises: 20250618_add_color
Create Date: 2025-06-18 13:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250618_add_status'
down_revision = '20250618_add_color'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_active column to environment_sound_categories table
    op.add_column('environment_sound_categories', 
                  sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False))
    
    # Add generation_status column to environment_sounds table
    op.add_column('environment_sounds', 
                  sa.Column('generation_status', sa.String(20), server_default='pending', nullable=False))
    
    # Set all existing records to pending
    op.execute("""
        UPDATE environment_sounds 
        SET generation_status = 'pending'
    """)


def downgrade() -> None:
    # Remove columns
    op.drop_column('environment_sounds', 'generation_status')
    op.drop_column('environment_sound_categories', 'is_active') 