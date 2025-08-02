"""add character consistency fields to image_generation_tasks

Revision ID: 20250202_add_character_consistency_fields
Revises: add_chinese_prompt_fields_simple
Create Date: 2025-02-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250202_add_character_consistency_fields'
down_revision = 'add_chinese_prompt_fields_simple'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加角色一致性字段到image_generation_tasks表"""
    # 添加角色一致性相关字段
    op.add_column('image_generation_tasks', sa.Column('character_consistency_enabled', sa.Boolean(), nullable=True, default=False, comment='是否启用角色一致性'))
    op.add_column('image_generation_tasks', sa.Column('character_id', sa.Integer(), nullable=True, comment='关联的角色ID'))
    
    # 为现有记录设置默认值
    op.execute("UPDATE image_generation_tasks SET character_consistency_enabled = false WHERE character_consistency_enabled IS NULL")
    
    # 设置字段为非空
    op.alter_column('image_generation_tasks', 'character_consistency_enabled', nullable=False)
    
    # 添加外键约束（如果characters表存在）
    try:
        op.create_foreign_key(
            'fk_image_generation_tasks_character_id',
            'image_generation_tasks',
            'characters',
            ['character_id'],
            ['id'],
            ondelete='SET NULL'
        )
    except Exception:
        # 如果characters表不存在，忽略外键约束
        pass


def downgrade() -> None:
    """移除角色一致性字段"""
    # 删除外键约束
    try:
        op.drop_constraint('fk_image_generation_tasks_character_id', 'image_generation_tasks', type_='foreignkey')
    except Exception:
        pass
    
    # 删除字段
    op.drop_column('image_generation_tasks', 'character_id')
    op.drop_column('image_generation_tasks', 'character_consistency_enabled')