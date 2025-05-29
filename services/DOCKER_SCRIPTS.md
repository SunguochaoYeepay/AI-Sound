# Docker管理脚本说明

## 📁 核心脚本清单

### 🔨 构建脚本
- **`build_api.bat`** - API服务构建脚本
  - 使用docker-compose build
  - 支持多镜像源备选
  - 自动测试构建结果

### 🧹 清理脚本  
- **`clean_docker.bat`** - Docker环境清理
  - 清理所有缓存、容器、镜像
  - 释放磁盘空间
  - 显示清理结果

### 🚀 开发脚本
- **`dev_mode.bat`** - 开发模式启动
  - 代码热重载，修改即生效
  - 无需重新构建Docker镜像
  - 支持前后端同时开发

### 🧪 测试脚本
- **`test_health_simple.py`** - API健康检查测试
  - 测试基础API功能
  - 验证引擎健康检查
  - 显示详细错误信息

## 🚀 使用流程

### 开发模式（推荐）
```bash
# 启动开发环境（代码热重载）
dev_mode.bat
```

### 生产环境部署
```bash
# 1. 清理环境（可选）
clean_docker.bat

# 2. 构建服务
build_api.bat

# 3. 启动服务
docker-compose up -d

# 4. 测试功能（可选）
python test_health_simple.py
```

### 常用Docker命令
```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api

# 重启单个服务
docker-compose restart api
```

## 📝 注意事项

- **开发阶段**: 使用 `dev_mode.bat` 获得最佳开发体验
- **生产部署**: 使用 `build_api.bat` 进行完整构建
- **环境清理**: 遇到问题时使用 `clean_docker.bat` 重置环境
- **健康检查**: 使用 `test_health_simple.py` 验证服务状态