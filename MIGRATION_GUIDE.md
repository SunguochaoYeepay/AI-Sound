
# 迁移到本地PostgreSQL指南

## 步骤1: 设置本地PostgreSQL
1. 确保PostgreSQL服务正在运行
2. 使用pgAdmin或命令行连接到PostgreSQL
3. 执行以下SQL命令：

```sql
CREATE DATABASE ai_sound_local;
```

## 步骤2: 初始化数据库
```bash
cd platform/backend
alembic upgrade head
```

## 步骤3: 重启后端服务
```bash
cd platform/backend
python main.py
```

## 步骤4: 测试功能
访问 http://localhost:4000 测试各项功能

## 可选: 停止Docker数据库
```bash
docker stop ai-sound-db
```

## 恢复Docker数据库（如果需要）
1. 恢复配置文件: platform/backend/app/config/environment.py.backup
2. 重启Docker数据库: docker start ai-sound-db
