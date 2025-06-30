"""add name to music generation tasks

Revision ID: 20250127_add_name_to_music_generation_tasks
Revises: 20250127_create_audio_editor_tables
Create Date: 2025-01-27 22:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250127_add_name_to_music_generation_tasks'
down_revision = '20250127_create_audio_editor_tables'
branch_labels = None
depends_on = None

def upgrade():
    """Add name column to music_generation_tasks table"""
    # 添加name字段
    op.add_column('music_generation_tasks', 
                  sa.Column('name', sa.String(200), nullable=True, comment='音乐名称'))
    
    # 为现有记录设置默认名称
    op.execute("""
        UPDATE music_generation_tasks 
        SET name = CONCAT('音乐生成_', id) 
        WHERE name IS NULL
    """)
    
    # 设置字段为非空
    op.alter_column('music_generation_tasks', 'name', nullable=False)

def downgrade():
    """Remove name column from music_generation_tasks table"""
    op.drop_column('music_generation_tasks', 'name') 