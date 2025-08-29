# 数据库维护与预防指南

## 🚨 问题背景

数据库结构不匹配导致的API错误是一个反复出现的问题，主要原因是：
1. 手动修改数据库结构
2. 不同环境间的结构差异
3. 缺乏自动化的结构验证

## 🛠️ 预防方案

### 1. 自动健康检查系统

#### 启动时检查
系统启动时会自动执行数据库健康检查：
```python
# 在 main.py 中自动调用
from database_health import startup_database_check
health_check_success = startup_database_check()
```

#### API接口检查
```bash
# 检查数据库健康状况
curl http://localhost:3001/api/database/health

# 自动修复数据库结构
curl -X POST http://localhost:3001/api/database/fix
```

### 2. 命令行工具

#### 安装使用
```bash
cd platform/backend

# 检查数据库健康状况
python scripts/migrate_database.py check

# 自动修复数据库结构
python scripts/migrate_database.py fix --backup

# 备份数据库
python scripts/migrate_database.py backup
```

### 3. Docker环境维护

#### 数据库重置（开发环境）
```bash
# 停止服务
docker-compose down

# 删除数据库卷（⚠️ 会丢失数据）
docker volume rm ai-sound_postgres_data

# 重新启动
docker-compose up -d

# 检查健康状况
python scripts/migrate_database.py check
```

#### 数据库备份和恢复
```bash
# 自动备份
python scripts/migrate_database.py backup

# 手动备份
docker exec ai-sound-db pg_dump -U ai_sound_user -d ai_sound > backup.sql

# 恢复备份
docker exec -i ai-sound-db psql -U ai_sound_user -d ai_sound < backup.sql
```

## 🔧 开发流程规范

### 1. 数据库结构修改流程

**❌ 错误做法：**
```bash
# 直接修改数据库
docker exec ai-sound-db psql -U ai_sound_user -d ai_sound -c "ALTER TABLE ..."
```

**✅ 正确做法：**
1. 修改 `models.py` 中的模型定义
2. 更新 `database_health.py` 中的 `critical_columns`
3. 运行健康检查验证
4. 提交代码变更

### 2. 部署前检查清单

```bash
# 1. 备份生产数据库
python scripts/migrate_database.py backup

# 2. 检查数据库健康状况
python scripts/migrate_database.py check

# 3. 如有问题，自动修复
python scripts/migrate_database.py fix --backup

# 4. 重启服务
docker-compose restart ai-sound-backend

# 5. 验证服务状态
curl http://localhost:3001/health
curl http://localhost:3001/api/database/health
```

### 3. 开发环境同步

```bash
# 获取最新代码后
git pull

# 检查并修复数据库结构
python scripts/migrate_database.py fix --force

# 重启开发服务
docker-compose restart ai-sound-backend
```

## 📊 监控和告警

### 1. 健康检查API返回格式

```json
{
  "status": "healthy|warning|unhealthy|error",
  "timestamp": "2025-01-01T00:00:00",
  "issues": ["问题描述"],
  "suggestions": ["修复建议"],
  "tables": {
    "table_name": {
      "row_count": 100,
      "exists": true
    }
  }
}
```

### 2. 常见问题和解决方案

#### 问题1：列不存在错误
```
psycopg2.errors.UndefinedColumn: column "initial_characters" does not exist
```

**解决方案：**
```bash
python scripts/migrate_database.py fix
```

#### 问题2：表不存在错误
```
psycopg2.errors.UndefinedTable: relation "voice_characters" does not exist
```

**解决方案：**
```bash
# 重新初始化数据库
python scripts/migrate_database.py check
python scripts/migrate_database.py fix --backup
```

#### 问题3：外键约束错误
```
psycopg2.errors.ForeignKeyViolation
```

**解决方案：**
1. 检查数据完整性
2. 清理无效的关联数据
3. 重建外键约束

### 3. 预防性维护计划

#### 每日检查（自动化）
- 启动时健康检查
- API响应监控
- 错误日志分析

#### 每周检查（手动）
```bash
# 完整健康检查
python scripts/migrate_database.py check

# 数据库备份
python scripts/migrate_database.py backup

# 清理日志文件
find ../data/logs -name "*.log" -mtime +7 -delete
```

#### 每月维护（计划）
- 数据库性能分析
- 存储空间清理
- 备份文件归档
- 安全更新检查

## 🚀 最佳实践

### 1. 代码变更
- 所有数据库结构变更必须通过代码实现
- 禁止直接在生产数据库执行DDL语句
- 使用版本控制跟踪模型变更

### 2. 测试验证
- 本地测试所有数据库变更
- 使用健康检查API验证结构
- 部署前进行完整的功能测试

### 3. 备份策略
- 重要操作前必须备份
- 保留至少7天的备份文件
- 定期测试备份恢复功能

### 4. 监控告警
- 集成到现有监控系统
- 设置关键API的健康检查
- 及时响应数据库异常

## 📞 故障处理

### 紧急情况处理步骤
1. **立即备份当前状态**
2. **检查问题严重程度**
3. **尝试自动修复**
4. **如修复失败，回滚到备份**
5. **分析根本原因**
6. **制定预防措施**

### 联系信息
- 开发团队：[开发人员联系方式]
- 运维团队：[运维人员联系方式]
- 紧急联系：[紧急联系方式] 