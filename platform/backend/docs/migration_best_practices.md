# Alembic迁移最佳实践指南

## 问题背景

AI-Sound项目在迁移管理中遇到了以下问题：
- 迁移文件重复运行导致"already exists"错误
- 多个head导致迁移链混乱
- 缺乏幂等性检查

## 解决方案

### 1. 迁移工具函数 (`migration_utils.py`)

我们创建了一套工具函数来确保迁移的幂等性：

```python
from migration_utils import (
    safe_create_table, safe_drop_table,
    safe_add_column, safe_drop_column,
    safe_create_index, safe_drop_index,
    safe_create_foreign_key, safe_drop_constraint,
    safe_execute
)
```

### 2. 标准迁移文件格式

使用 `migration_template.py` 作为模板创建新的迁移文件：

```python
"""迁移描述

Revision ID: [REVISION_ID]
Revises: [DOWN_REVISION]
Create Date: [CREATE_DATE]
"""
from alembic import op
import sqlalchemy as sa
import sys
import os

# 导入工具函数
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from migration_utils import safe_add_column, safe_drop_column

def upgrade():
    # 使用safe_*函数确保幂等性
    safe_add_column('table_name', 
        sa.Column('new_column', sa.String(100), nullable=True))

def downgrade():
    safe_drop_column('table_name', 'new_column')
```

### 3. 迁移管理工具 (`migration_manager.py`)

提供以下命令：

```bash
# 查看迁移状态
python migration_manager.py status

# 检查迁移文件一致性
python migration_manager.py check

# 安全升级（跳过已存在的对象）
python migration_manager.py safe-upgrade

# 重置多个head到单一head
python migration_manager.py reset-heads

# 验证所有迁移文件
python migration_manager.py validate
```

## 最佳实践

### 1. 创建新迁移文件

1. 复制 `migration_template.py`
2. 重命名为新的迁移文件（格式：`YYYYMMDD_description.py`）
3. 修改revision、down_revision等信息
4. 使用safe_*函数编写upgrade和downgrade逻辑

### 2. 幂等性原则

所有迁移操作都应该是幂等的，即：
- 多次运行同一个迁移文件应该产生相同的结果
- 不应该因为对象已存在而失败
- 使用safe_*函数自动处理这些情况

### 3. 测试迁移

在应用迁移前：

```bash
# 1. 检查状态
python migration_manager.py status

# 2. 验证迁移文件
python migration_manager.py validate

# 3. 安全升级
python migration_manager.py safe-upgrade
```

### 4. 处理多个head

如果出现多个head：

```bash
# 自动合并head
python migration_manager.py reset-heads
```

### 5. 回滚策略

每个迁移文件都应该提供完整的downgrade函数：

```python
def downgrade():
    # 按相反顺序撤销upgrade中的操作
    safe_drop_constraint('fk_name', 'table_name', type_='foreignkey')
    safe_drop_index('idx_name')
    safe_drop_column('table_name', 'column_name')
    safe_drop_table('table_name')
```

## 常见问题解决

### 问题1：字段已存在错误

**错误信息**：`column "field_name" of relation "table_name" already exists`

**解决方案**：使用 `safe_add_column` 替代 `op.add_column`

### 问题2：表已存在错误

**错误信息**：`relation "table_name" already exists`

**解决方案**：使用 `safe_create_table` 替代 `op.create_table`

### 问题3：多个head

**错误信息**：`Multiple heads are present`

**解决方案**：
```bash
python migration_manager.py reset-heads
```

### 问题4：迁移链断裂

**错误信息**：`Can't locate revision identified by 'revision_id'`

**解决方案**：
1. 检查迁移文件的down_revision是否正确
2. 使用 `python migration_manager.py check` 检查一致性
3. 手动修复迁移链

## 开发流程

### 新功能开发

1. **开发阶段**：
   ```bash
   # 创建新迁移
   alembic revision -m "add_new_feature"
   # 编辑迁移文件，使用safe_*函数
   # 测试迁移
   python migration_manager.py safe-upgrade
   ```

2. **测试阶段**：
   ```bash
   # 验证迁移
   python migration_manager.py validate
   # 测试回滚
   alembic downgrade -1
   # 重新升级
   python migration_manager.py safe-upgrade
   ```

3. **部署阶段**：
   ```bash
   # 检查状态
   python migration_manager.py status
   # 安全升级
   python migration_manager.py safe-upgrade
   ```

## 注意事项

1. **永远不要直接修改已经提交的迁移文件**
2. **在生产环境部署前先在测试环境验证**
3. **保持迁移文件的原子性，一个迁移文件只做一件事**
4. **为重要的数据变更提供数据迁移脚本**
5. **定期清理旧的迁移文件（在确保不再需要回滚的情况下）**

## 故障恢复

如果迁移出现严重问题：

1. **回滚到已知良好状态**：
   ```bash
   alembic downgrade <revision_id>
   ```

2. **重置迁移状态**：
   ```bash
   alembic stamp head
   ```

3. **手动修复数据库结构**：
   - 使用数据库管理工具手动调整
   - 创建新的迁移文件同步状态

4. **重新开始**：
   ```bash
   python migration_manager.py safe-upgrade
   ``` 