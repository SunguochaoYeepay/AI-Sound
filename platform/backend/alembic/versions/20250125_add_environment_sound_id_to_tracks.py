"""Add environment_sound_id to environment_track_configs

Revision ID: add_environment_sound_id
Revises: 20250125_env_gen_001
Create Date: 2025-01-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250125_add_environment_sound_id_to_tracks'
down_revision = '20250621_add_error_message'
branch_labels = None
depends_on = None

def upgrade():
    # 添加environment_sound_id字段到environment_track_configs表
    op.add_column('environment_track_configs', 
                  sa.Column('environment_sound_id', sa.Integer(), nullable=True))
    
    # 添加外键约束（如果environment_sounds表存在）
    try:
        op.create_foreign_key(
            'fk_environment_track_configs_environment_sound_id',
            'environment_track_configs', 
            'environment_sounds',
            ['environment_sound_id'], 
            ['id'],
            ondelete='SET NULL'
        )
    except Exception:
        # 如果environment_sounds表不存在，忽略外键约束
        pass

def downgrade():
    # 删除外键约束
    try:
        op.drop_constraint('fk_environment_track_configs_environment_sound_id', 
                          'environment_track_configs', type_='foreignkey')
    except Exception:
        pass
    
    # 删除字段
    op.drop_column('environment_track_configs', 'environment_sound_id') 