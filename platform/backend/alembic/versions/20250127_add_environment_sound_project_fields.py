"""add environment sound project fields

Revision ID: 20250127_add_environment_sound_project_fields
Revises: 20250127_add_name_to_music_generation_tasks
Create Date: 2025-01-27 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250127_add_environment_sound_project_fields'
down_revision = '20250127_add_name_to_music_generation_tasks'
branch_labels = None
depends_on = None


def upgrade():
    """添加环境音项目关联字段"""
    # 添加项目关联字段
    op.add_column('environment_sounds', sa.Column('environment_project_id', sa.Integer(), nullable=True, comment='关联的环境音项目ID'))
    op.add_column('environment_sounds', sa.Column('track_index', sa.Integer(), nullable=True, comment='轨道索引'))
    op.add_column('environment_sounds', sa.Column('chapter_id', sa.Integer(), nullable=True, comment='章节ID'))
    op.add_column('environment_sounds', sa.Column('novel_project_id', sa.Integer(), nullable=True, comment='关联的合成项目ID'))
    
    # 创建索引以提高查询性能
    op.create_index(op.f('ix_environment_sounds_environment_project_id'), 'environment_sounds', ['environment_project_id'], unique=False)
    op.create_index(op.f('ix_environment_sounds_novel_project_id'), 'environment_sounds', ['novel_project_id'], unique=False)
    op.create_index(op.f('ix_environment_sounds_track_index'), 'environment_sounds', ['track_index'], unique=False)
    op.create_index(op.f('ix_environment_sounds_chapter_id'), 'environment_sounds', ['chapter_id'], unique=False)


def downgrade():
    """回滚环境音项目关联字段"""
    # 删除索引
    op.drop_index(op.f('ix_environment_sounds_chapter_id'), table_name='environment_sounds')
    op.drop_index(op.f('ix_environment_sounds_track_index'), table_name='environment_sounds')
    op.drop_index(op.f('ix_environment_sounds_novel_project_id'), table_name='environment_sounds')
    op.drop_index(op.f('ix_environment_sounds_environment_project_id'), table_name='environment_sounds')
    
    # 删除字段
    op.drop_column('environment_sounds', 'novel_project_id')
    op.drop_column('environment_sounds', 'chapter_id')
    op.drop_column('environment_sounds', 'track_index')
    op.drop_column('environment_sounds', 'environment_project_id')
