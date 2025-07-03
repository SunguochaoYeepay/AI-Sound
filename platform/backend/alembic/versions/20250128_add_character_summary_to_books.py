"""add character_summary to books

Revision ID: add_character_summary_to_books
Revises: 
Create Date: 2025-01-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_character_summary_to_books'
down_revision = None  # 需要根据实际情况修改
branch_labels = None
depends_on = None


def upgrade():
    """添加character_summary字段到books表"""
    # 添加character_summary字段
    op.add_column('books', sa.Column('character_summary', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='角色汇总信息: {characters: [], voice_mappings: {}, last_updated: \'\'}'))


def downgrade():
    """移除character_summary字段"""
    op.drop_column('books', 'character_summary') 