# 🚀 AI-Sound 部署配置总结

## 📋 配置文件重构完成

### ✅ 已完成的标准化工作

1. **README.md 更新**
   - ✅ 更新了系统架构图，区分生产和开发部署
   - ✅ 统一了项目结构说明
   - ✅ 更新了部署方式和访问地址
   - ✅ 修正了API文档和功能描述

2. **Docker配置文件标准化**
   - ✅ `docker-compose.yml` - 当前生产配置
   - ✅ `docker-compose.dev.yml` - 开发环境微服务配置
   - ✅ `docker-compose.prod.yml` - 标准生产模板
   - ✅ 统一了网络配置和健康检查

3. **自动化部署脚本**
   - ✅ `scripts/deploy.sh` - Linux/macOS自动化部署脚本
   - ✅ `scripts/deploy.bat` - Windows自动化部署脚本
   - ✅ 完整的前端构建、健康检查和错误处理

4. **部署文档**
   - ✅ `docs/deployment.md` - 完整的部署指南
   - ✅ 包含生产环境、开发环境、监控维护等完整内容

## 🏗️ 当前架构说明

### 生产环境架构
```
用户 → Nginx:3001 → 静态文件(nginx-dist) + API代理 → Backend:8000 → Database + Redis
                    ↓
                 音频文件直接服务
```

### 开发环境架构  
```
用户 → Nginx网关:80 → Frontend容器:3000 (热重载)
                    ↓
                   Backend容器:8000 → Database + Redis
```

## 📁 配置文件说明

### Docker Compose文件

| 文件 | 用途 | 特点 |
|------|------|------|
| `docker-compose.yml` | 生产部署 | 前端编译为静态文件，性能最优 |
| `docker-compose.dev.yml` | 开发环境 | 前端独立容器，支持热重载 |
| `docker-compose.prod.yml` | 生产模板 | 包含完整的生产配置示例 |

### 部署脚本

| 脚本 | 平台 | 功能 |
|------|------|------|
| `scripts/deploy.sh` | Linux/macOS | 自动化部署，包含健康检查 |
| `scripts/deploy.bat` | Windows | Windows版本的自动化部署 |

## 🚀 快速部署命令

### Linux/macOS
```bash
# 一键部署
./scripts/deploy.sh

# 开发模式
./scripts/deploy.sh dev

# 清理环境
./scripts/deploy.sh clean
```

### Windows
```cmd
# 一键部署
scripts\deploy.bat

# 开发模式（手动）
docker-compose -f docker-compose.dev.yml up -d
```

## 🌐 访问地址

### 生产环境
- **前端界面**: http://localhost:3001
- **API接口**: http://localhost:3001/api  
- **API文档**: http://localhost:3001/docs
- **健康检查**: http://localhost:3001/health

### 开发环境
- **前端界面**: http://localhost:80 (网关)
- **前端容器**: http://localhost:3000 (直接访问)
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 📊 服务状态检查

```bash
# 检查容器状态
docker-compose ps

# 检查健康状态
curl http://localhost:3001/health
curl http://localhost:3001/api/health

# 查看日志
docker-compose logs -f
docker-compose logs -f backend
```

## 🔧 维护命令

```bash
# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 更新重启
docker-compose build --no-cache && docker-compose up -d

# 清理系统
docker system prune -f
```

## ⚙️ 环境变量配置

核心环境变量：
```bash
# 数据库配置
DATABASE_URL=postgresql://ai_sound_user:ai_sound_password@database:5432/ai_sound

# MegaTTS3配置
MEGATTS3_URL=http://host.docker.internal:9000

# 文件路径
AUDIO_DIR=/app/data/audio
UPLOADS_DIR=/app/data/uploads
VOICE_PROFILES_DIR=/app/data/voice_profiles

# 调试模式
DEBUG=false
```

## 🗂️ 数据目录结构

```
data/
├── audio/              # 生成的音频文件
├── database/           # PostgreSQL数据文件
├── logs/              # 服务日志
│   ├── nginx/         # Nginx日志
│   └── backend/       # 后端日志
├── uploads/           # 用户上传文件
├── voice_profiles/    # 声音配置文件
├── cache/             # Redis缓存数据
├── config/            # 运行时配置
├── backups/           # 备份文件
└── temp/              # 临时文件
```

## 🐛 常见问题解决

### 1. 502 Bad Gateway
```bash
# 检查后端容器
docker logs ai-sound-backend

# 检查网络连通性
docker exec ai-sound-nginx ping ai-sound-backend
```

### 2. 前端文件404
```bash
# 重新构建前端
cd platform/frontend
npm run build
cp -r dist/* ../../nginx-dist/
```

### 3. 音频文件无法访问
```bash
# 检查文件权限和路径
ls -la data/voice_profiles/
docker exec ai-sound-nginx ls -la /usr/share/nginx/voice_profiles/
```

## 📈 性能优化建议

1. **生产环境优化**
   - 使用SSD存储
   - 配置PostgreSQL连接池
   - 启用Nginx缓存
   - 配置CDN（可选）

2. **资源限制**
   - 限制容器内存使用
   - 配置Docker健康检查
   - 设置合理的超时时间

3. **监控告警**
   - 配置日志轮转
   - 监控磁盘空间
   - 定期备份数据

## 📞 技术支持

如有问题，请参考：
- 📋 [详细部署文档](docs/deployment.md)
- 🔧 [故障排查指南](docs/troubleshooting.md)
- 🐛 [GitHub Issues](https://github.com/your-org/AI-Sound/issues)

---

**🎉 配置重构完成，现在架构清晰、部署简单、维护方便！** 