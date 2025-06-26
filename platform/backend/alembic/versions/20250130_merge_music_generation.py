"""合并音乐生成分支

Revision ID: 20250130_merge_music_generation
Revises: 20250127_create_collaboration_export_tables, 20250130_music_generation
Create Date: 2025-01-30 15:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250130_merge_music_generation'
down_revision = ('20250127_create_collaboration_export_tables', '20250130_music_generation')
branch_labels = None
depends_on = None


def upgrade():
    """合并分支，无需额外操作"""
    pass


def downgrade():
    """合并分支回滚，无需额外操作"""
    pass 