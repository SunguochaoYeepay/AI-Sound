"""合并所有迁移分支

Revision ID: c2bf04f8d306
Revises: 20250127_add_name_to_music_generation_tasks, 20250130_merge_music_generation, e8318e421078, 571e80c326e8
Create Date: 2025-07-01 09:25:21.609157

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2bf04f8d306'
down_revision = ('20250127_add_name_to_music_generation_tasks', '20250130_merge_music_generation', 'e8318e421078', '571e80c326e8')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 