"""add character_id to audio_files

Revision ID: 20250201_add_character_id_to_audio_files
Revises: 20250129_add_ai_response_to_music_generation
Create Date: 2025-02-01 20:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250201_add_character_id_to_audio_files'
down_revision = '20250129_add_ai_response_to_music_generation'
branch_labels = None
depends_on = None


def upgrade():
    """添加character_id字段到audio_files表"""
    op.add_column('audio_files', sa.Column('character_id', sa.Integer(), nullable=True, comment='角色ID - 新架构支持'))
    op.create_foreign_key('fk_audio_files_character_id', 'audio_files', 'characters', ['character_id'], ['id'])


def downgrade():
    """移除character_id字段"""
    op.drop_constraint('fk_audio_files_character_id', 'audio_files', type_='foreignkey')
    op.drop_column('audio_files', 'character_id') 