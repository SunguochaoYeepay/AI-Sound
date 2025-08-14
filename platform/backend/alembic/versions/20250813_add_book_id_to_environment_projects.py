"""add book_id to environment_projects

Revision ID: 20250813_add_book_id
Revises: 5c31d42c13e8
Create Date: 2025-08-13 19:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250813_add_book_id'
down_revision = '5c31d42c13e8'
branch_labels = None
depends_on = None


def upgrade():
    # 添加book_id字段到environment_projects表
    op.add_column('environment_projects', sa.Column('book_id', sa.Integer(), nullable=True, comment='书籍ID'))


def downgrade():
    # 删除book_id字段
    op.drop_column('environment_projects', 'book_id')
