"""add novel_project_id to environment_projects

Revision ID: 20250127_001
Revises: 20250127_add_name_to_music_generation_tasks
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250127_001'
down_revision = '20250127_add_name_to_music_generation_tasks'
branch_labels = None
depends_on = None


def upgrade():
    """升级：添加novel_project_id字段"""
    # 添加novel_project_id字段
    op.add_column('environment_projects', sa.Column('novel_project_id', sa.Integer(), nullable=True))
    
    # 添加外键约束
    op.create_foreign_key(
        'fk_environment_projects_novel_project_id',
        'environment_projects', 'novel_projects',
        ['novel_project_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # 创建索引
    op.create_index('ix_environment_projects_novel_project_id', 'environment_projects', ['novel_project_id'])


def downgrade():
    """降级：移除novel_project_id字段"""
    # 删除外键约束
    op.drop_constraint('fk_environment_projects_novel_project_id', 'environment_projects', type_='foreignkey')
    
    # 删除索引
    op.drop_index('ix_environment_projects_novel_project_id', table_name='environment_projects')
    
    # 删除字段
    op.drop_column('environment_projects', 'novel_project_id')
