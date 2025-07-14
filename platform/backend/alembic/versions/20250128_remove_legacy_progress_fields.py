"""Remove legacy progress fields from novel_projects

Revision ID: 20250128_remove_legacy_progress_fields
Revises: 20250127_add_name_to_music_generation_tasks
Create Date: 2025-01-28 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '20250128_remove_legacy_progress_fields'
down_revision = '20250127_add_name_to_music_generation_tasks'
branch_labels = None
depends_on = None


def upgrade():
    """升级：移除旧的进度字段"""
    # 移除 total_segments 字段
    op.drop_column('novel_projects', 'total_segments')
    
    # 移除 processed_segments 字段
    op.drop_column('novel_projects', 'processed_segments')
    
    # 移除 current_segment 字段
    op.drop_column('novel_projects', 'current_segment')


def downgrade():
    """降级：恢复旧的进度字段"""
    # 恢复 total_segments 字段
    op.add_column('novel_projects', sa.Column('total_segments', sa.INTEGER(), nullable=True, default=0))
    
    # 恢复 processed_segments 字段
    op.add_column('novel_projects', sa.Column('processed_segments', sa.INTEGER(), nullable=True, default=0))
    
    # 恢复 current_segment 字段
    op.add_column('novel_projects', sa.Column('current_segment', sa.INTEGER(), nullable=True, default=0)) 