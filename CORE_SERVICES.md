# AI-Sound 核心服务启动指南

## 🚀 快速启动

### 方式一：一键启动所有服务
```bash
start_all_core.bat
```

### 方式二：分别启动服务
```bash
# 1. 启动数据库（必须先启动）
start_mongodb.bat

# 2. 启动API服务
start_api.bat

# 3. 启动管理界面
start_admin.bat
```

## 🛑 停止服务
```bash
stop_all_core.bat
```

## 📋 服务信息

| 服务 | 地址 | 说明 |
|------|------|------|
| **MongoDB** | `localhost:27017` | 数据库服务 |
| **API** | `localhost:9930` | 后端API服务 |
| **Admin** | `localhost:8080` | 前端管理界面 |

## 🔧 服务依赖关系

```
MongoDB (基础) → API (依赖MongoDB) → Admin (依赖API)
```

## 💾 数据持久化（超牛逼！）

### 🎯 数据存储位置
```
AI-Sound/
└── docker/
    └── volumes/
        └── mongodb/          # MongoDB数据存储目录
            ├── .mongodb/     # MongoDB系统文件
            ├── admin/        # 管理数据库
            ├── ai_sound/     # 应用数据库
            └── ...
```

### ✨ 持久化特性
- ✅ **永不丢失**: 即使删除Docker容器，数据依然保留
- ✅ **本地存储**: 数据存储在项目目录下，方便备份和迁移
- ✅ **类似Dify**: 采用与Dify相同的数据持久化方案
- ✅ **可视化**: 可以直接查看 `docker/volumes/mongodb` 目录

### 🔄 数据备份
```bash
backup_mongodb.bat    # 备份MongoDB数据
```

## 📝 注意事项

1. **启动顺序**：建议按 MongoDB → API → Admin 的顺序启动
2. **Docker要求**：确保Docker Desktop已启动
3. **端口占用**：确保端口 27017、9930、8080 未被占用
4. **数据安全**：数据存储在 `docker/volumes/mongodb`，删除容器不会丢失数据

## 🔍 健康检查

- API健康检查：http://localhost:9930/health
- MongoDB连接测试：使用MongoDB Compass连接 `mongodb://admin:admin123@localhost:27017`

## 🗂️ 核心文件结构

```
AI-Sound/
├── start_mongodb.bat         # MongoDB启动脚本
├── start_api.bat            # API启动脚本  
├── start_admin.bat          # Admin启动脚本
├── start_all_core.bat       # 一键启动所有服务
├── stop_all_core.bat        # 停止所有服务
├── backup_mongodb.bat       # 数据备份脚本
├── check_git_safety.bat     # Git数据安全检查
├── docker/
│   └── volumes/
│       └── mongodb/         # 数据持久化目录 🎯
└── services/
    ├── infrastructure/
    │   └── docker-compose.mongodb.yml
    └── docker-compose.core.yml
```

## 🎉 数据持久化验证

想验证数据持久化是否生效？试试这个：

1. 启动MongoDB: `start_mongodb.bat`
2. 连接数据库并创建一些数据
3. 停止服务: `stop_all_core.bat`
4. 重新启动: `start_mongodb.bat`
5. 数据依然存在！🎊

## 🔒 Git 数据安全（重要！）

### ⚠️ 数据安全原则
- **绝对不要**将MongoDB数据文件提交到Git！
- **绝对不要**将Docker数据卷提交到Git！
- 数据文件可能包含敏感信息且体积巨大

### 🛡️ 安全检查
```bash
check_git_safety.bat    # 检查是否有数据文件被意外跟踪
```

### 📋 已忽略的文件类型
```
# MongoDB数据文件
*.wt, *.lock, *.turtle, *.bson
WiredTiger*, mongod.lock
diagnostic.data/, journal/

# Docker数据卷
docker/volumes/mongodb/
docker/volumes/mongodb_backup/
docker/volumes/*/
```

### 🚨 如果意外提交了数据文件
```bash
# 从Git中移除但保留本地文件
git rm --cached -r docker/volumes/mongodb/
git commit -m "Remove MongoDB data files from Git"
```

**记住：数据持久化 ≠ Git版本控制！数据文件应该通过备份管理，而不是Git！** 