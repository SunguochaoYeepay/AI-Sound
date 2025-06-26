"""merge heads

Revision ID: 571e80c326e8
Revises: 20250127_create_audio_editor_tables, add_system_logs_table
Create Date: 2025-06-23 07:11:27.054862

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '571e80c326e8'
down_revision = ('20250127_create_audio_editor_tables', 'add_system_logs_table')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 