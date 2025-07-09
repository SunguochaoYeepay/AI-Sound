"""
Alembic迁移工具函数
提供幂等性检查，确保迁移文件可以重复运行
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


def table_exists(table_name: str) -> bool:
    """检查表是否存在"""
    try:
        conn = op.get_bind()
        inspector = inspect(conn)
        return table_name in inspector.get_table_names()
    except Exception:
        return False


def column_exists(table_name: str, column_name: str) -> bool:
    """检查列是否存在"""
    try:
        conn = op.get_bind()
        inspector = inspect(conn)
        columns = inspector.get_columns(table_name)
        return any(col['name'] == column_name for col in columns)
    except Exception:
        return False


def index_exists(index_name: str) -> bool:
    """检查索引是否存在"""
    try:
        conn = op.get_bind()
        inspector = inspect(conn)
        # 获取所有表的索引
        for table_name in inspector.get_table_names():
            indexes = inspector.get_indexes(table_name)
            if any(idx['name'] == index_name for idx in indexes):
                return True
        return False
    except Exception:
        return False


def constraint_exists(table_name: str, constraint_name: str) -> bool:
    """检查约束是否存在"""
    try:
        conn = op.get_bind()
        inspector = inspect(conn)
        
        # 检查外键约束
        foreign_keys = inspector.get_foreign_keys(table_name)
        if any(fk['name'] == constraint_name for fk in foreign_keys):
            return True
            
        # 检查唯一约束
        unique_constraints = inspector.get_unique_constraints(table_name)
        if any(uc['name'] == constraint_name for uc in unique_constraints):
            return True
            
        # 检查检查约束
        check_constraints = inspector.get_check_constraints(table_name)
        if any(cc['name'] == constraint_name for cc in check_constraints):
            return True
            
        return False
    except Exception:
        return False


def safe_create_table(table_name: str, *columns, **kwargs):
    """安全创建表（如果不存在）"""
    if not table_exists(table_name):
        op.create_table(table_name, *columns, **kwargs)
        print(f"✅ 创建表 {table_name}")
    else:
        print(f"ℹ️ 表 {table_name} 已存在，跳过创建")


def safe_drop_table(table_name: str):
    """安全删除表（如果存在）"""
    if table_exists(table_name):
        op.drop_table(table_name)
        print(f"✅ 删除表 {table_name}")
    else:
        print(f"ℹ️ 表 {table_name} 不存在，跳过删除")


def safe_add_column(table_name: str, column: sa.Column):
    """安全添加列（如果不存在）"""
    if not column_exists(table_name, column.name):
        op.add_column(table_name, column)
        print(f"✅ 添加列 {table_name}.{column.name}")
    else:
        print(f"ℹ️ 列 {table_name}.{column.name} 已存在，跳过添加")


def safe_drop_column(table_name: str, column_name: str):
    """安全删除列（如果存在）"""
    if column_exists(table_name, column_name):
        op.drop_column(table_name, column_name)
        print(f"✅ 删除列 {table_name}.{column_name}")
    else:
        print(f"ℹ️ 列 {table_name}.{column_name} 不存在，跳过删除")


def safe_create_index(index_name: str, table_name: str, columns: list):
    """安全创建索引（如果不存在）"""
    if not index_exists(index_name):
        op.create_index(index_name, table_name, columns)
        print(f"✅ 创建索引 {index_name}")
    else:
        print(f"ℹ️ 索引 {index_name} 已存在，跳过创建")


def safe_drop_index(index_name: str):
    """安全删除索引（如果存在）"""
    if index_exists(index_name):
        op.drop_index(index_name)
        print(f"✅ 删除索引 {index_name}")
    else:
        print(f"ℹ️ 索引 {index_name} 不存在，跳过删除")


def safe_create_foreign_key(constraint_name: str, table_name: str, referent_table: str, 
                           local_cols: list, remote_cols: list):
    """安全创建外键约束（如果不存在）"""
    if not constraint_exists(table_name, constraint_name):
        op.create_foreign_key(constraint_name, table_name, referent_table, 
                             local_cols, remote_cols)
        print(f"✅ 创建外键约束 {constraint_name}")
    else:
        print(f"ℹ️ 外键约束 {constraint_name} 已存在，跳过创建")


def safe_drop_constraint(constraint_name: str, table_name: str, type_: str = None):
    """安全删除约束（如果存在）"""
    if constraint_exists(table_name, constraint_name):
        op.drop_constraint(constraint_name, table_name, type_=type_)
        print(f"✅ 删除约束 {constraint_name}")
    else:
        print(f"ℹ️ 约束 {constraint_name} 不存在，跳过删除")


def safe_execute(sql: str, description: str = "执行SQL"):
    """安全执行SQL语句"""
    try:
        op.execute(sql)
        print(f"✅ {description}")
    except Exception as e:
        print(f"⚠️ {description} 失败: {e}") 