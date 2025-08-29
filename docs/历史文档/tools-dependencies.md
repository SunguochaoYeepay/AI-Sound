# AI-Sound 工具依赖文档

## 概述

AI-Sound项目依赖多个外部工具来实现完整功能。本文档详细说明了各个功能模块的工具依赖、安装方法和配置要求。

## 🗄️ 数据库备份工具

### PostgreSQL 客户端工具

**功能模块**: 数据库备份恢复系统  
**依赖工具**: `pg_dump`, `pg_restore`, `psql`  
**必需性**: 数据库备份功能必需

#### 本地开发环境安装

**推荐版本**: PostgreSQL 16 (最新稳定版)

**下载地址**:
- 官方下载页面: https://www.postgresql.org/download/windows/
- PostgreSQL 16 直接下载: https://get.enterprisedb.com/postgresql/postgresql-16.6-1-windows-x64.exe
- PostgreSQL 15 直接下载: https://get.enterprisedb.com/postgresql/postgresql-15.10-1-windows-x64.exe

**安装配置**:
1. 运行安装程序
2. 安装组件选择:
   - ✅ PostgreSQL Server (可选)
   - ✅ **Command Line Tools** (必选 - 包含pg_dump)
   - ✅ pgAdmin 4 (可选 - 图形管理工具)
   - ✅ StackBuilder (可选)
3. 配置参数:
   - 超级用户密码: 设置安全密码
   - 端口: 5432 (默认)
   - 区域设置: Chinese, China
4. 环境变量: 安装程序自动添加到PATH

**安装验证**:
```bash
# 验证pg_dump
pg_dump --version

# 验证psql
psql --version

# 检查PATH
echo $env:PATH | Select-String "PostgreSQL"
```

**预期路径**: `C:\Program Files\PostgreSQL\16\bin\`

#### Docker环境配置

Docker环境已自动配置PostgreSQL客户端工具:

```dockerfile
# 在 docker/backend/Dockerfile 中已配置
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*
```

**验证Docker环境**:
```bash
# 检查容器中的工具
docker exec ai-sound-backend pg_dump --version
```

### 备份功能特性

**环境自动检测**: 系统自动识别Docker/本地环境
**智能错误提示**: 缺少工具时提供详细安装指导
**备份存储**: 
- 本地环境: `./storage/backups/`
- Docker环境: `./data/backups/` (通过卷映射持久化)

## 🎵 语音合成工具

### MegaTTS3

**功能模块**: 高质量语音合成  
**部署方式**: Docker容器  
**GPU要求**: NVIDIA CUDA支持

**配置**:
```yaml
# docker-compose.yml
megatts3:
  image: megatts3:latest
  environment:
    - CUDA_VISIBLE_DEVICES=0
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

### TangoFlux

**功能模块**: 环境音生成  
**部署方式**: Docker容器  
**GPU要求**: NVIDIA CUDA支持

**配置**:
```yaml
# docker-compose.yml
tangoflux:
  environment:
    - TANGOFLUX_MODEL_NAME=declare-lab/TangoFlux
    - TANGOFLUX_DEVICE=cuda
```

## 🤖 AI分析工具

### Ollama (可选)

**功能模块**: 本地大语言模型服务  
**部署方式**: 宿主机服务  
**连接配置**: `http://host.docker.internal:11434`

**安装**:
1. 下载: https://ollama.ai/download
2. 安装模型: `ollama pull llama2`
3. 启动服务: `ollama serve`

## 🔧 系统工具

### Node.js & npm

**功能模块**: 前端构建  
**版本要求**: Node.js 16+

**安装**:
- 官方下载: https://nodejs.org/
- 验证: `node --version && npm --version`

### Docker & Docker Compose

**功能模块**: 容器化部署  
**版本要求**: Docker 20+, Docker Compose 2+

**安装**:
- Docker Desktop: https://www.docker.com/products/docker-desktop
- 验证: `docker --version && docker-compose --version`

### Python

**功能模块**: 后端服务  
**版本要求**: Python 3.10+

**依赖包**: 详见 `platform/backend/requirements.txt`

## 📊 环境检查

### 自动检查功能

AI-Sound提供了自动环境检查功能:

**备份环境检查**:
```python
# 在备份管理中调用
backup_engine.check_backup_environment()
```

**返回信息**:
- pg_dump工具可用性
- 备份目录状态
- 数据库连接状态
- 环境类型 (Docker/本地)
- 修复建议

### 手动检查清单

**开发环境启动前检查**:
- [ ] PostgreSQL客户端工具已安装
- [ ] Python 3.10+ 已安装
- [ ] Node.js 16+ 已安装
- [ ] 数据库服务正常运行

**Docker环境启动前检查**:
- [ ] Docker Desktop 运行正常
- [ ] NVIDIA Docker支持 (如需GPU)
- [ ] 充足磁盘空间 (>20GB)

## 🚨 故障排除

### 常见问题

**1. pg_dump 命令未找到**
```
错误: 'pg_dump' 不是内部或外部命令
解决: 安装PostgreSQL客户端工具并检查PATH环境变量
```

**2. Docker容器中缺少工具**
```
错误: Docker容器中pg_dump不可用
解决: 重新构建Docker镜像确保包含postgresql-client
```

**3. 备份文件权限问题**
```
错误: 无法创建备份文件
解决: 检查备份目录权限和磁盘空间
```

### 日志查看

所有工具相关的操作都会记录到系统日志:
- 访问: AI-Sound管理平台 > 日志监控
- 筛选: 按模块筛选 (SYSTEM, DATABASE, TTS等)
- 级别: ERROR级别查看失败原因

## 📝 更新记录

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2025-01-XX | 1.0 | 初始版本，包含完整工具依赖说明 |
| 2025-01-XX | 1.1 | 添加Docker环境自动配置 |
| 2025-01-XX | 1.2 | 完善故障排除和环境检查功能 |

---

**维护者**: AI-Sound开发团队  
**最后更新**: 2025年1月  
**相关文档**: 
- [部署指南](./deployment.md)
- [故障排除](./troubleshooting.md)
- [系统测试指南](./SYSTEM_TEST_GUIDE.md) 