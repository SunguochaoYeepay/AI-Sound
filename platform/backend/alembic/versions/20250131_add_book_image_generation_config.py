"""Add image_generation_config to books table

Revision ID: 20250131_add_book_image_generation_config
Revises: 20250131_add_image_generation_tables
Create Date: 2025-01-31 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250131_add_book_image_generation_config'
down_revision = '20250131_add_image_generation_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Add image_generation_config column to books table"""
    # 添加图片生成配置字段到books表
    op.add_column('books', sa.Column('image_generation_config', sa.JSON(), nullable=True, comment='图片生成配置: {style: "", steps: 20, guidance: 7.5, model: "", seed: -1, batchSize: 1}'))


def downgrade():
    """Remove image_generation_config column from books table"""
    # 删除图片生成配置字段
    op.drop_column('books', 'image_generation_config')