"""add error_message to novel_projects

Revision ID: 20250621_add_error_message
Revises: 20250125_env_gen_001
Create Date: 2025-06-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sys
import os

# 添加父目录到路径，以便导入工具函数
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from migration_utils import safe_add_column, safe_drop_column

# revision identifiers, used by Alembic.
revision = '20250621_add_error_message'
down_revision = '20250125_env_gen_001'
branch_labels = None
depends_on = None

def upgrade():
    """添加error_message字段到novel_projects表"""
    safe_add_column('novel_projects', sa.Column('error_message', sa.Text(), nullable=True))

def downgrade():
    """移除error_message字段"""
    safe_drop_column('novel_projects', 'error_message') 