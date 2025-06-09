# AI-Sound Backend 本地开发环境设置

## 🎯 环境要求

- **Python 3.9-3.11** （推荐3.10）
- **PostgreSQL** 或 **Docker** （用于数据库）
- **Redis** 或 **Docker** （用于缓存）

## 🚀 快速启动

### 方式1：自动化脚本（推荐）

```powershell
# 进入后端目录
cd platform/backend

# 1. 创建虚拟环境
.\setup-venv.ps1 -Action create

# 2. 安装依赖
.\setup-venv.ps1 -Action install

# 3. 启动服务
.\setup-venv.ps1 -Action run
```

### 方式2：手动设置

```powershell
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 3. 安装依赖（使用轻量级版本）
pip install -r requirements-dev.txt

# 4. 启动服务
python main.py
```

## 🔧 服务依赖

### 数据库（二选一）
```powershell
# 方式1: Docker运行PostgreSQL
docker run -d \
  --name ai-sound-db \
  -e POSTGRES_DB=ai_sound \
  -e POSTGRES_USER=ai_sound_user \
  -e POSTGRES_PASSWORD=ai_sound_password \
  -p 5432:5432 \
  postgres:15-alpine

# 方式2: 本地安装PostgreSQL
# 下载安装：https://www.postgresql.org/download/windows/
```

### 缓存（二选一）
```powershell
# 方式1: Docker运行Redis
docker run -d \
  --name ai-sound-redis \
  -p 6379:6379 \
  redis:7-alpine

# 方式2: 本地安装Redis
# 下载安装：https://github.com/tporadowski/redis/releases
```

### TTS服务（MegaTTS）
```powershell
# MegaTTS在独立容器中运行，不影响后端环境
docker run -d \
  --name ai-sound-megatts3 \
  -p 7929:7929 \
  megatts3:latest
```

## 📋 环境变量

创建 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=postgresql://ai_sound_user:ai_sound_password@localhost:5432/ai_sound

# TTS服务配置
MEGATTS3_URL=http://localhost:7929

# 文件路径配置
AUDIO_DIR=./data/audio
UPLOADS_DIR=./data/uploads
VOICE_PROFILES_DIR=./data/voice_profiles

# 开发模式
DEBUG=true
```

## 🎉 验证安装

启动成功后访问：
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 🛠 常用命令

```powershell
# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 退出虚拟环境
deactivate

# 安装新依赖
pip install package_name

# 更新依赖文件
pip freeze > requirements-dev.txt

# 数据库迁移
alembic upgrade head

# 运行测试
pytest

# 代码格式化
black .
isort .
```

## 🚨 常见问题

### Python环境问题
```powershell
# 检查Python版本
python --version

# 检查pip版本
pip --version

# 如果python命令不存在，尝试
py --version
```

### 依赖安装失败
```powershell
# 升级pip
python -m pip install --upgrade pip

# 清理缓存
pip cache purge

# 重新安装
pip install -r requirements-dev.txt --force-reinstall
```

### 数据库连接失败
- 检查PostgreSQL是否启动
- 检查连接字符串配置
- 检查防火墙设置

## 💡 开发技巧

1. **使用开发依赖文件** (`requirements-dev.txt`) 避免与MegaTTS冲突
2. **MegaTTS独立运行**，不需要在本地安装TTS相关依赖
3. **使用Docker运行数据库和Redis**，简化环境配置
4. **开启DEBUG模式**，便于调试和热重载 