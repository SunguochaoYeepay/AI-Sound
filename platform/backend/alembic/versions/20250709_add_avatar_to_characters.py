"""add avatar to characters

Revision ID: 20250709_add_avatar_to_characters
Revises: 20250709_add_timestamps_to_characters
Create Date: 2025-07-09 21:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250709_add_avatar_to_characters'
down_revision = '20250709_add_timestamps_to_characters'
branch_labels = None
depends_on = None


def upgrade():
    """添加头像字段到characters表"""
    # 添加avatar_path字段
    op.add_column('characters', sa.Column('avatar_path', sa.String(500), nullable=True, comment='头像图片路径'))


def downgrade():
    """移除头像字段"""
    op.drop_column('characters', 'avatar_path') 