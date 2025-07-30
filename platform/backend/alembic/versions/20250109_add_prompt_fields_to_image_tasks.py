"""添加原始提示词和后端标签字段到图片生成任务表

Revision ID: add_prompt_fields
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_prompt_fields'
down_revision = 'd8ec600ee987'
branch_labels = None
depends_on = None


def upgrade():
    """添加新字段"""
    # 添加原始提示词字段
    op.add_column('image_generation_tasks', 
                  sa.Column('original_prompt', sa.Text(), nullable=True, comment='用户输入或基础AI生成的提示词'))
    
    # 添加后端添加的标签字段
    op.add_column('image_generation_tasks', 
                  sa.Column('backend_added_tags', postgresql.ARRAY(sa.String()), nullable=True, comment='后端自动添加的质量标签'))


def downgrade():
    """移除新字段"""
    op.drop_column('image_generation_tasks', 'backend_added_tags')
    op.drop_column('image_generation_tasks', 'original_prompt')