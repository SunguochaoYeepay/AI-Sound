"""迁移文件模板

使用方法：
1. 复制此文件并重命名为新的迁移文件
2. 修改revision、down_revision等信息
3. 在upgrade()和downgrade()函数中使用safe_*函数
4. 确保所有操作都是幂等的

Revision ID: [REVISION_ID]
Revises: [DOWN_REVISION]
Create Date: [CREATE_DATE]

"""
from alembic import op
import sqlalchemy as sa
import sys
import os

# 添加父目录到路径，以便导入工具函数
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from migration_utils import (
    safe_create_table, safe_drop_table,
    safe_add_column, safe_drop_column,
    safe_create_index, safe_drop_index,
    safe_create_foreign_key, safe_drop_constraint,
    safe_execute, table_exists, column_exists
)

# revision identifiers, used by Alembic.
revision = '[REVISION_ID]'
down_revision = '[DOWN_REVISION]'
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库结构"""
    
    # 示例：创建表
    # safe_create_table('new_table',
    #     sa.Column('id', sa.Integer(), primary_key=True),
    #     sa.Column('name', sa.String(255), nullable=False),
    #     sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now())
    # )
    
    # 示例：添加列
    # safe_add_column('existing_table', 
    #     sa.Column('new_column', sa.String(100), nullable=True)
    # )
    
    # 示例：创建索引
    # safe_create_index('idx_table_column', 'table_name', ['column_name'])
    
    # 示例：创建外键
    # safe_create_foreign_key('fk_table_ref', 'table_name', 'ref_table', 
    #                        ['ref_id'], ['id'])
    
    # 示例：执行SQL
    # safe_execute("""
    #     UPDATE table_name SET column = 'default_value' 
    #     WHERE column IS NULL
    # """, "设置默认值")
    
    pass


def downgrade():
    """回滚数据库结构"""
    
    # 示例：删除外键
    # safe_drop_constraint('fk_table_ref', 'table_name', type_='foreignkey')
    
    # 示例：删除索引
    # safe_drop_index('idx_table_column')
    
    # 示例：删除列
    # safe_drop_column('existing_table', 'new_column')
    
    # 示例：删除表
    # safe_drop_table('new_table')
    
    pass 