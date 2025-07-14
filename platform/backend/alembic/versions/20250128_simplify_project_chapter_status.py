"""Simplify project and chapter status management

Revision ID: 20250128_simplify_status
Revises: 20250127_add_name_to_music_generation_tasks
Create Date: 2025-01-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250128_simplify_status'
down_revision = '20250127_add_name_to_music_generation_tasks'
branch_labels = None
depends_on = None


def upgrade():
    # 从 book_chapters 表中删除 synthesis_status 字段
    op.drop_column('book_chapters', 'synthesis_status')
    op.drop_index('idx_book_chapters_synthesis_status', table_name='book_chapters')
    
    # 从 novel_projects 表中删除不必要的字段
    op.drop_column('novel_projects', 'final_audio_path')


def downgrade():
    # 恢复 book_chapters 表的 synthesis_status 字段
    op.add_column('book_chapters', sa.Column('synthesis_status', sa.String(20), nullable=True, server_default='pending'))
    op.create_index('idx_book_chapters_synthesis_status', 'book_chapters', ['synthesis_status'])
    
    # 恢复 novel_projects 表的字段
    op.add_column('novel_projects', sa.Column('final_audio_path', sa.String(500), nullable=True)) 