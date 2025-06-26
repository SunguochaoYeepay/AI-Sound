"""合并迁移分支

Revision ID: be9b34de668d
Revises: 20250618_add_status, 20250621_add_error_message, add_system_logs_table
Create Date: 2025-06-21 22:03:12.022284

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'be9b34de668d'
down_revision = ('20250618_add_status', '20250621_add_error_message', 'add_system_logs_table')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 