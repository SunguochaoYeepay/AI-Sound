# 🚀 AI-Sound 部署指南

本文档提供 AI-Sound 平台的完整部署指南，包括生产环境和开发环境的部署方式。

## 📋 目录

- [系统要求](#系统要求)
- [快速部署](#快速部署)
- [生产环境部署](#生产环境部署)
- [开发环境部署](#开发环境部署)
- [配置说明](#配置说明)
- [监控与维护](#监控与维护)
- [故障排查](#故障排查)

## 🔧 系统要求

### 硬件要求

| 项目 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2核心 | 4核心+ |
| 内存 | 4GB | 8GB+ |
| 存储 | 20GB | 50GB+ |
| 网络 | 10Mbps | 100Mbps+ |

### 软件要求

| 软件 | 版本要求 | 用途 |
|------|----------|------|
| Docker | 20.0+ | 容器运行时 |
| Docker Compose | 2.0+ | 容器编排 |
| Node.js | 18+ | 前端构建 |
| Git | 2.0+ | 代码管理 |

### 可选组件

| 组件 | 描述 | 用途 |
|------|------|------|
| NVIDIA Docker | GPU支持 | MegaTTS3加速 |
| Let's Encrypt | SSL证书 | HTTPS支持 |
| Prometheus | 监控系统 | 性能监控 |

## ⚡ 快速部署

### 一键部署脚本

```bash
# 1. 克隆项目
git clone https://github.com/your-org/AI-Sound.git
cd AI-Sound

# 2. 执行自动化部署
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# 3. 访问服务
# 前端界面: http://localhost:3001
# API文档: http://localhost:3001/docs
```

### 手动快速部署

```bash
# 1. 创建必要目录
mkdir -p data/{audio,database,logs,uploads,voice_profiles,cache,config,backups,temp}
mkdir -p nginx-dist

# 2. 构建前端
cd platform/frontend
npm install && npm run build
cp -r dist/* ../../nginx-dist/
cd ../..

# 3. 启动服务
docker-compose up -d

# 4. 检查状态
docker-compose ps
curl http://localhost:3001/health
```

## 🏭 生产环境部署

### 1. 环境准备

```bash
# 创建专用用户
sudo useradd -m -s /bin/bash aisound
sudo usermod -aG docker aisound
su - aisound

# 创建项目目录
mkdir -p /home/aisound/AI-Sound
cd /home/aisound/AI-Sound
```

### 2. 项目配置

```bash
# 克隆代码
git clone https://github.com/your-org/AI-Sound.git .

# 创建环境变量文件
cp .env.example .env

# 编辑配置文件
nano .env
```

环境变量配置：
```bash
# .env
NODE_ENV=production
DEBUG=false

# 数据库配置
DATABASE_URL=postgresql://ai_sound_user:your_secure_password@database:5432/ai_sound
POSTGRES_PASSWORD=your_secure_password

# MegaTTS3配置
MEGATTS3_URL=http://host.docker.internal:9000

# 安全配置
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# 文件路径配置
AUDIO_DIR=/app/data/audio
UPLOADS_DIR=/app/data/uploads
VOICE_PROFILES_DIR=/app/data/voice_profiles
```

### 3. SSL证书配置

```bash
# 使用Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com

# 复制证书到项目目录
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem docker/nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem docker/nginx/ssl/
sudo chown aisound:aisound docker/nginx/ssl/*
```

### 4. 生产配置文件

创建 `docker-compose.override.yml`：

```yaml
version: '3.8'

services:
  nginx:
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx/ssl:/etc/nginx/ssl:ro
    environment:
      - NGINX_HOST=yourdomain.com

  backend:
    environment:
      - DATABASE_URL=postgresql://ai_sound_user:${POSTGRES_PASSWORD}@database:5432/ai_sound
      - DEBUG=false
      - LOG_LEVEL=info

  database:
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
    driver: local
```

### 5. 部署启动

```bash
# 构建并启动服务
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

# 验证部署
curl https://yourdomain.com/health
```

## 🛠️ 开发环境部署

### 方式一：完整容器化开发

```bash
# 使用开发配置
docker-compose -f docker-compose.dev.yml up -d

# 访问服务
# 前端: http://localhost:3000
# 后端: http://localhost:8000
# 网关: http://localhost:80
```

### 方式二：本地开发

```bash
# 启动基础服务（数据库、Redis）
docker-compose up -d database redis

# 本地启动后端
cd platform/backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 本地启动前端（新终端）
cd platform/frontend
npm install
npm run dev
```

### 开发工具配置

#### VS Code配置

`.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./platform/backend/venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "eslint.workingDirectories": ["platform/frontend"]
}
```

#### Git hooks配置

```bash
# 安装pre-commit
pip install pre-commit
pre-commit install

# 创建配置文件
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.0.0
    hooks:
      - id: eslint
        files: \.js$
        types: [file]
EOF
```

## ⚙️ 配置说明

### Docker Compose配置文件

| 文件 | 用途 | 说明 |
|------|------|------|
| `docker-compose.yml` | 生产部署 | 标准生产配置 |
| `docker-compose.dev.yml` | 开发部署 | 微服务开发配置 |
| `docker-compose.prod.yml` | 生产模板 | 完整生产配置模板 |
| `docker-compose.override.yml` | 环境覆盖 | 本地环境特殊配置 |

### 环境变量

#### 后端环境变量

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `DATABASE_URL` | postgresql://... | PostgreSQL数据库连接字符串 |
| `MEGATTS3_URL` | http://host.docker.internal:9000 | MegaTTS3服务地址 |
| `DEBUG` | false | 调试模式 |
| `LOG_LEVEL` | info | 日志级别 |
| `CORS_ORIGINS` | http://localhost | 允许的跨域源 |
| `AUDIO_DIR` | /app/data/audio | 音频文件目录 |
| `UPLOADS_DIR` | /app/data/uploads | 上传文件目录 |
| `VOICE_PROFILES_DIR` | /app/data/voice_profiles | 声音配置目录 |

#### 数据库环境变量

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `POSTGRES_DB` | ai_sound | 数据库名 |
| `POSTGRES_USER` | ai_sound_user | 数据库用户 |
| `POSTGRES_PASSWORD` | ai_sound_password | 数据库密码 |

### Nginx配置

主要配置项：
- 反向代理到后端API
- 静态文件服务
- 音频文件访问
- SSL终端
- 文件上传限制（100MB）

## 📊 监控与维护

### 健康检查

```bash
# 检查所有容器状态
docker-compose ps

# 检查服务健康状态
curl http://localhost:3001/health
curl http://localhost:3001/api/health

# 检查资源使用
docker stats
```

### 日志管理

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f nginx

# 查看错误日志
docker-compose logs --tail=50 backend | grep ERROR

# 日志轮转配置
echo "*/10 * * * * root docker system prune -f" >> /etc/crontab
```

### 备份策略

#### 自动备份脚本

`scripts/backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/backup/ai-sound"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据文件
tar -czf $BACKUP_DIR/data_$DATE.tar.gz data/

# 备份数据库
docker exec ai-sound-db pg_dump -U ai_sound_user ai_sound > $BACKUP_DIR/database_$DATE.sql

# 清理旧备份（保留30天）
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
```

#### 定时备份

```bash
# 添加到crontab
0 2 * * * /home/aisound/AI-Sound/scripts/backup.sh
```

### 更新升级

#### 服务更新流程

```bash
# 1. 备份数据
./scripts/backup.sh

# 2. 拉取最新代码
git pull origin main

# 3. 重新构建前端
cd platform/frontend
npm run build
cp -r dist/* ../../nginx-dist/
cd ../..

# 4. 更新容器
docker-compose build --no-cache
docker-compose up -d

# 5. 验证更新
curl http://localhost:3001/health
```

#### 回滚策略

```bash
# 停止服务
docker-compose down

# 回滚代码
git checkout HEAD~1

# 恢复数据备份
tar -xzf /backup/ai-sound/data_YYYYMMDD_HHMMSS.tar.gz

# 重新启动
docker-compose up -d
```

## 🐛 故障排查

### 常见问题

#### 1. 502 Bad Gateway

**原因分析**：
- 后端容器未正常启动
- Nginx配置错误
- 网络连接问题

**解决步骤**：
```bash
# 检查后端容器状态
docker logs ai-sound-backend

# 检查网络连通性
docker exec ai-sound-nginx ping ai-sound-backend

# 检查Nginx配置
docker exec ai-sound-nginx nginx -t
```

#### 2. 数据库连接失败

**原因分析**：
- 数据库容器未启动
- 连接字符串错误
- 权限问题

**解决步骤**：
```bash
# 检查数据库状态
docker logs ai-sound-db

# 测试连接
docker exec ai-sound-backend python -c "
import psycopg2
conn = psycopg2.connect('postgresql://ai_sound_user:ai_sound_password@database:5432/ai_sound')
print('连接成功')
"
```

#### 3. 前端文件404

**原因分析**：
- 前端未正确构建
- Nginx配置路径错误
- 文件权限问题

**解决步骤**：
```bash
# 检查前端文件
ls -la nginx-dist/

# 重新构建前端
cd platform/frontend
npm run build
cp -r dist/* ../../nginx-dist/
```

#### 4. 音频文件无法访问

**原因分析**：
- 文件路径配置错误
- 文件不存在
- Nginx路径映射问题

**解决步骤**：
```bash
# 检查文件是否存在
ls -la data/audio/
ls -la data/voice_profiles/

# 检查Nginx配置
docker exec ai-sound-nginx cat /etc/nginx/nginx.conf | grep -A 5 voice_profiles
```

### 性能调优

#### 数据库优化

```sql
-- 创建索引
CREATE INDEX idx_audio_files_project_id ON audio_files(project_id);
CREATE INDEX idx_voice_profiles_type ON voice_profiles(type);

-- 配置参数
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
```

#### Nginx优化

```nginx
# 启用gzip压缩
gzip on;
gzip_types text/plain text/css application/json application/javascript;

# 设置缓存
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 安全配置

#### 防火墙设置

```bash
# 只开放必要端口
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

#### Docker安全

```bash
# 限制容器资源
docker-compose.yml 添加：
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

## 📞 技术支持

如果在部署过程中遇到问题，请参考：

1. 📋 [故障排查文档](troubleshooting.md)
2. 📡 [API文档](api.md)
3. 🐛 [GitHub Issues](https://github.com/your-org/AI-Sound/issues)
4. 💬 [讨论区](https://github.com/your-org/AI-Sound/discussions)

---

**🎉 部署成功后，享受 AI-Sound 带来的高质量语音合成体验吧！** 