"""add error_message to novel_projects

Revision ID: 20250621_add_error_message
Revises: 20250125_env_gen_001
Create Date: 2025-06-21 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250621_add_error_message'
down_revision = '20250125_env_gen_001'
branch_labels = None
depends_on = None


def upgrade():
    """添加error_message字段到novel_projects表"""
    
    # 添加error_message字段
    op.add_column('novel_projects', sa.Column('error_message', sa.Text(), nullable=True))
    
    print("✅ 已添加 error_message 字段到 novel_projects 表")


def downgrade():
    """移除error_message字段"""
    
    # 移除error_message字段
    op.drop_column('novel_projects', 'error_message')
    
    print("✅ 已从 novel_projects 表移除 error_message 字段") 