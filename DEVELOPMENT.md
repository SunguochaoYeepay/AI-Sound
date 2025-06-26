# AI-Sound 开发指南

## 🚀 快速开始

### 开发模式启动
```bash
# Windows
scripts\dev-start.bat

# 或手动启动
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### 生产模式启动
```bash
docker-compose up -d
```

## 🔧 常见问题解决

### 1. 代码修改后不生效
**原因：** Docker构建缓存问题

**解决方案：**
```bash
# 方案1：使用开发模式（推荐）
scripts\dev-start.bat

# 方案2：强制重建
scripts\force-rebuild.bat

# 方案3：手动重建
docker-compose build --no-cache backend
docker-compose restart backend
```

### 2. 检查代码是否同步
```bash
# 检查特定代码
scripts\check-code.bat "book_id.*Optional"

# 查看文件时间戳
scripts\check-code.bat
```

### 3. 容器启动失败
```bash
# 查看日志
docker logs ai-sound-backend

# 查看所有服务状态
docker-compose ps

# 重启特定服务
docker-compose restart backend
```

## 📝 开发最佳实践

### 1. 代码修改流程
1. **开发模式：** 使用 `docker-compose.dev.yml` 自动热重载
2. **测试验证：** 使用 `scripts\check-code.bat` 验证代码同步
3. **问题排查：** 查看 `docker logs ai-sound-backend` 

### 2. 避免缓存问题
- ✅ 使用Volume挂载（开发模式）
- ✅ 定期清理Docker缓存：`docker system prune`
- ✅ 代码修改后验证容器内代码
- ❌ 直接修改生产模式容器内代码

### 3. 环境隔离
- **开发环境：** `docker-compose.dev.yml` - 热重载、调试模式
- **生产环境：** `docker-compose.yml` - 优化构建、稳定运行

## 🛠️ 工具脚本

| 脚本 | 功能 | 使用场景 |
|------|------|----------|
| `dev-start.bat` | 启动开发环境 | 日常开发 |
| `force-rebuild.bat` | 强制重建 | 依赖变更、缓存问题 |
| `check-code.bat` | 检查代码同步 | 验证修改是否生效 |

## 🔍 故障排查

### 问题：API返回"Field required"错误
**原因：** 容器内代码未更新
**解决：** 
1. 使用 `scripts\check-code.bat` 检查
2. 使用 `scripts\force-rebuild.bat` 重建

### 问题：前端无法访问后端
**检查：**
1. 服务状态：`docker-compose ps`
2. 网络连接：`docker logs ai-sound-nginx`
3. 端口映射：访问 http://localhost:3001/health

### 问题：TTS服务连接失败
**检查：**
1. MegaTTS3服务：`docker logs ai-sound-megatts3`
2. 网络配置：确保 `host.docker.internal:7929` 可访问 