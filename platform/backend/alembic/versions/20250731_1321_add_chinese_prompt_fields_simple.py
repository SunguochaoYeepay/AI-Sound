"""Add Chinese prompt fields to ImageGenerationTask - Simple version

Revision ID: add_chinese_prompt_fields_simple
Revises: 20250201_add_character_id_to_audio_files
Create Date: 2025-07-31 13:21:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_chinese_prompt_fields_simple'
down_revision = '20250201_add_character_id_to_audio_files'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add Chinese prompt fields to image_generation_tasks table
    op.add_column('image_generation_tasks', sa.Column('generated_prompt_chinese', sa.Text(), nullable=True, comment='中文提示词（用于前端显示）'))
    op.add_column('image_generation_tasks', sa.Column('negative_prompt_chinese', sa.Text(), nullable=True, comment='中文负面提示词（用于前端显示）'))


def downgrade() -> None:
    # Remove Chinese prompt fields from image_generation_tasks table
    op.drop_column('image_generation_tasks', 'negative_prompt_chinese')
    op.drop_column('image_generation_tasks', 'generated_prompt_chinese')