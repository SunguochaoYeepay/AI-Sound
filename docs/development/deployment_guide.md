# AI-Sound 部署指南

本文档提供 AI-Sound 系统的详细部署步骤，包括开发环境部署、测试环境部署和生产环境部署。

## 部署要求

### 硬件要求

- **最低配置**：
  - CPU: 4+ 核心
  - RAM: 8GB+
  - GPU: NVIDIA GPU with 4GB+ VRAM (支持 CUDA)
  - 存储: 20GB+ SSD

- **推荐配置**：
  - CPU: 8+ 核心
  - RAM: 16GB+
  - GPU: NVIDIA GPU with 8GB+ VRAM (支持 CUDA)
  - 存储: 50GB+ SSD

### 软件要求

- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Container Toolkit (用于 GPU 支持)
- Python 3.8+ (本地开发)

## 开发环境部署

### 1. 克隆代码库

```bash
git clone https://github.com/your-org/ai-sound.git
cd ai-sound
```

### 2. 配置开发环境

创建环境变量文件 `.env.dev`：

```
# API服务配置
API_PORT=9930
DEBUG=true
LOG_LEVEL=debug

# TTS引擎服务URL
MEGATTS3_URL=http://megatts3:9931
ESPNET_URL=http://espnet:9932

# 存储配置
STORAGE_PATH=./data/storage
```

### 3. 使用模拟服务（快速开发）

对于快速开发和测试，可以使用模拟服务而不是实际的 TTS 引擎：

```bash
# 创建Docker网络
docker network create ai-sound-network

# 启动模拟服务
cd services/mock_services
python megatts3_mock.py  # 在一个终端中运行
python espnet_mock.py    # 在另一个终端中运行

# 在另一个终端启动API服务
cd services/api
python -m src.main --dev
```

### 4. 使用Docker Compose启动所有服务

```bash
# 创建Docker网络（如果尚未创建）
docker network create ai-sound-network

# 启动所有服务
docker-compose -f docker-compose.dev.yml up -d
```

## 测试环境部署

### 1. 准备环境

```bash
# 克隆代码库
git clone https://github.com/your-org/ai-sound.git
cd ai-sound

# 创建环境变量文件
cp .env.example .env.test
# 编辑 .env.test 设置合适的配置
```

### 2. 创建网络

```bash
./services/create_network.sh  # Linux/Mac
# 或
services\create_network.bat  # Windows
```

### 3. 构建和启动服务

```bash
docker-compose -f docker-compose.test.yml build
docker-compose -f docker-compose.test.yml up -d
```

### 4. 检查服务状态

```bash
docker-compose -f docker-compose.test.yml ps
docker-compose -f docker-compose.test.yml logs -f
```

## 生产环境部署

### 1. 系统准备

确保生产服务器满足所有硬件和软件要求。

```bash
# 安装Docker和Docker Compose（如果尚未安装）
# Ubuntu示例
apt-get update
apt-get install -y docker.io docker-compose

# 安装NVIDIA Container Toolkit（如果使用GPU）
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list
apt-get update
apt-get install -y nvidia-container-toolkit
systemctl restart docker
```

### 2. 获取代码和配置

```bash
# 克隆代码库
git clone https://github.com/your-org/ai-sound.git
cd ai-sound

# 创建环境变量文件
cp .env.example .env.prod
# 编辑 .env.prod 设置生产环境配置
```

配置示例 `.env.prod`：

```
# API服务配置
API_PORT=9930
DEBUG=false
LOG_LEVEL=info

# TTS引擎服务URL
MEGATTS3_URL=http://megatts3:9931
ESPNET_URL=http://espnet:9932

# 存储配置
STORAGE_PATH=/data/ai-sound/storage

# 安全配置
API_KEY=your_secure_api_key
ENABLE_AUTH=true
```

### 3. 创建网络和数据目录

```bash
# 创建网络
./services/create_network.sh  # Linux/Mac

# 创建数据目录
mkdir -p /data/ai-sound/storage
chmod 777 /data/ai-sound/storage  # 确保容器可以访问
```

### 4. 启动服务

```bash
# 构建和启动所有服务
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### 5. 设置反向代理（可选）

如果您需要使用 Nginx 作为反向代理，可以使用以下配置：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8080;  # Web管理界面
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:9930/;  # API服务
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 6. 启用 HTTPS（推荐）

使用 Let's Encrypt 获取 SSL 证书：

```bash
apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

## 多机部署

对于大规模部署，可以考虑将服务分布在多台服务器上：

### 1. 服务器规划

- **服务器1**：API 网关 + Web 管理界面
- **服务器2**：MegaTTS3 引擎
- **服务器3**：ESPnet 引擎
- **服务器4**：存储服务（如果需要）

### 2. 网络配置

使用 Docker Swarm 或 Kubernetes 进行服务发现和负载均衡。

## 监控与维护

### 1. 查看日志

```bash
# 查看所有服务日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.prod.yml logs -f api-gateway
```

### 2. 监控服务状态

访问健康检查端点：

```bash
curl http://your-domain.com/api/health
curl http://your-domain.com/api/health/engines
```

### 3. 备份数据

定期备份配置和数据：

```bash
# 备份脚本示例
#!/bin/bash
BACKUP_DIR="/backups/ai-sound"
DATE=$(date +%Y%m%d-%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份环境变量文件
cp /path/to/ai-sound/.env.prod $BACKUP_DIR/env-$DATE.backup

# 备份存储数据
tar -czf $BACKUP_DIR/storage-$DATE.tar.gz /data/ai-sound/storage

# 保留最近30天的备份
find $BACKUP_DIR -type f -name "*.backup" -mtime +30 -delete
find $BACKUP_DIR -type f -name "*.tar.gz" -mtime +30 -delete
```

### 4. 更新服务

```bash
# 拉取最新代码
cd /path/to/ai-sound
git pull

# 重新构建和启动服务
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

## 故障排除

### 1. Docker 容器无法启动

检查日志：

```bash
docker-compose -f docker-compose.prod.yml logs api-gateway
```

检查环境变量和配置文件是否正确。

### 2. TTS 引擎健康检查失败

- 确保 TTS 引擎容器正在运行
- 检查网络连接
- 检查引擎服务日志查找错误

### 3. GPU 不可用

检查 NVIDIA Docker 配置：

```bash
# 测试 NVIDIA Docker 是否正常工作
docker run --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### 4. 存储问题

检查权限和磁盘空间：

```bash
# 检查磁盘空间
df -h

# 检查权限
ls -la /data/ai-sound/storage
```

## 安全建议

1. **API 保护**：
   - 启用 API 密钥认证
   - 设置 IP 白名单
   - 实施速率限制

2. **数据安全**：
   - 定期备份数据
   - 加密敏感配置
   - 设置适当的文件权限

3. **网络安全**：
   - 使用防火墙限制端口访问
   - 配置 HTTPS
   - 使用内部网络进行服务间通信

## 联系支持

如果您在部署过程中遇到任何问题，请联系：

- 技术支持邮箱：support@ai-sound.org
- 问题报告：https://github.com/your-org/ai-sound/issues