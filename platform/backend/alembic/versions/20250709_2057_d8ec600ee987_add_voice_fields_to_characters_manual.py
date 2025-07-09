"""add_voice_fields_to_characters_manual

Revision ID: d8ec600ee987
Revises: 6ac123a0d10f
Create Date: 2025-01-09 20:57:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd8ec600ee987'
down_revision = '6ac123a0d10f'
branch_labels = None
depends_on = None


def upgrade():
    """手动迁移已完成，这里记录为空操作"""
    # 字段已通过手动迁移添加，包括：
    # - voice_type VARCHAR(50) DEFAULT 'custom'
    # - color VARCHAR(20) DEFAULT '#8b5cf6'  
    # - reference_audio_path VARCHAR(500)
    # - latent_file_path VARCHAR(500)
    # - voice_parameters JSON
    # - tags JSON
    # - quality_score FLOAT
    # - usage_count INTEGER DEFAULT 0
    # - status VARCHAR(50) DEFAULT 'unconfigured'
    pass


def downgrade():
    """移除手动添加的字段"""
    op.drop_column('characters', 'status')
    op.drop_column('characters', 'usage_count')
    op.drop_column('characters', 'quality_score')
    op.drop_column('characters', 'tags')
    op.drop_column('characters', 'voice_parameters')
    op.drop_column('characters', 'latent_file_path')
    op.drop_column('characters', 'reference_audio_path')
    op.drop_column('characters', 'color')
    op.drop_column('characters', 'voice_type') 