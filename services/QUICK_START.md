# 🚀 AI-Sound 快速开始指南

## 📋 核心文件说明

```
services/
├── docker-compose.yml          # 主配置文件
├── docker-compose.dev.yml      # 开发模式配置
├── dev_mode.bat               # 开发模式启动（推荐）
├── build_api.bat              # 生产环境构建
├── clean_docker.bat           # 环境清理
├── test_health_simple.py      # 健康检查测试
└── DOCKER_SCRIPTS.md          # 详细使用说明
```

## ⚡ 一键启动

### 开发模式（推荐）
```bash
# 代码热重载，修改即生效
dev_mode.bat
```

### 生产模式
```bash
# 完整构建和部署
build_api.bat
docker-compose up -d
```

## 🔧 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api

# 重启服务
docker-compose restart api

# 停止服务
docker-compose down

# 清理环境
clean_docker.bat
```

## 🌐 访问地址

- **API文档**: http://localhost:9930/docs
- **前端界面**: http://localhost:8080
- **健康检查**: http://localhost:9930/health

## 🆘 遇到问题？

1. **服务启动失败**: 运行 `clean_docker.bat` 清理环境
2. **代码修改不生效**: 使用 `dev_mode.bat` 开发模式
3. **端口冲突**: 检查 9930、8080、27017 端口是否被占用
4. **健康检查**: 运行 `python test_health_simple.py`

---
💡 **提示**: 开发时优先使用 `dev_mode.bat`，生产部署使用 `build_api.bat` 