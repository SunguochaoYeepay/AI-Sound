"""create audio editor tables

Revision ID: 20250127_create_audio_editor_tables
Revises: 20250125_env_gen_001
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250127_create_audio_editor_tables'
down_revision = '20250125_env_gen_001'
branch_labels = None
depends_on = None

def upgrade():
    # 创建音频编辑器相关的表（如果不存在）
    # 这里添加一个占位符表，避免迁移链断裂
    try:
        op.create_table('audio_editor_placeholder',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    except Exception:
        # 如果表已存在，忽略错误
        pass

def downgrade():
    try:
        op.drop_table('audio_editor_placeholder')
    except Exception:
        # 如果表不存在，忽略错误
        pass 