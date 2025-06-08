# 🚀 AI-Sound 快速开发指南

## ⚡ 5分钟快速开始

### 1. 克隆并进入项目
```bash
git clone https://github.com/your-org/AI-Sound.git
cd AI-Sound
```

### 2. 启动开发环境
```bash
# Windows用户
scripts\dev-start.bat

# Linux/macOS用户  
chmod +x scripts/dev-start.sh
scripts/dev-start.sh
```

### 3. 访问应用
- 🌐 前端界面：http://localhost:3001
- 🔧 API文档：http://localhost:3001/docs
- ❤️ 健康检查：http://localhost:3001/health

## ⚠️ 避免常见问题

### 🔥 重要：代码修改不生效？

**问题：** 修改Python代码后，API行为没有变化
**原因：** Docker构建缓存问题
**解决：** 

```bash
# 1. 检查代码是否同步
scripts\check-code.bat

# 2. 如果显示不同步，强制重建
scripts\force-rebuild.bat

# 3. 重新启动开发模式
scripts\dev-start.bat
```

### 📋 开发模式 vs 生产模式

| 特性 | 开发模式 | 生产模式 |
|------|----------|----------|
| 代码热重载 | ✅ 支持 | ❌ 不支持 |
| Volume挂载 | ✅ 启用 | ❌ 不启用 |
| 调试日志 | ✅ 详细 | ⚠️ 精简 |
| 构建速度 | 🚀 快速 | 🐌 较慢 |
| 适用场景 | 日常开发 | 生产部署 |

### 🛠️ 常用开发命令

```bash
# 启动开发环境
scripts\dev-start.bat

# 检查代码同步
scripts\check-code.bat

# 查看服务状态  
docker-compose ps

# 查看后端日志
docker logs ai-sound-backend -f

# 强制重建（解决缓存问题）
scripts\force-rebuild.bat

# 停止所有服务
docker-compose down
```

## 🔗 更多资源

- 📖 [完整开发指南](DEVELOPMENT.md)
- 📚 [项目文档](README.md)  
- 🚀 [脚本工具说明](scripts/README.md)
- 🐳 [Docker配置](docker-compose.yml)

---

**记住：开发时优先使用开发模式，避免Docker缓存问题！** 🎯 