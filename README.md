# 🎵 AI-Sound

AI-Sound 是一个基于 MegaTTS3 的企业级语音合成平台，提供高质量的语音克隆和多角色朗读服务。

## ✨ 项目特点

- **🚀 MegaTTS3引擎**：集成最新的 MegaTTS3 语音合成引擎
- **🎭 智能角色分配**：基于角色名称自动分配合适的声音类型
- **📖 多角色朗读**：支持小说文本的智能分段和多角色语音合成
- **🎵 音频资源库**：统一管理所有生成的音频文件
- **📊 实时监控**：完善的系统状态监控和日志记录
- **🐳 容器化部署**：支持Docker一键部署，生产环境就绪

## 🏗️ 系统架构

### 当前架构（生产部署）

```mermaid
graph TB
    User[用户] --> Nginx[Nginx 反向代理]
    Nginx --> StaticFiles[前端静态文件<br/>Vue3构建结果]
    Nginx --> Backend[后端API<br/>FastAPI + Python]
    Backend --> Database[PostgreSQL数据库]
    Backend --> Redis[Redis缓存]
    Backend --> MegaTTS3[MegaTTS3引擎]
    Nginx --> AudioFiles[音频文件存储]
    Nginx --> VoiceProfiles[声音配置文件]
    
    subgraph "Docker容器集群"
        Nginx
        Backend
        Database
        Redis
    end
    
    subgraph "外部服务"
        MegaTTS3
    end
    
    subgraph "数据持久化"
        AudioFiles
        VoiceProfiles
        Database
    end
```

### 开发架构（可选）

```mermaid
graph TB
    User[用户] --> NginxGW[Nginx网关:80]
    NginxGW --> Frontend[前端容器:3000<br/>Nginx + Vue3]
    NginxGW --> Backend[后端容器:8000<br/>FastAPI]
    Backend --> Database[PostgreSQL:5432]
    Backend --> Redis[Redis:6379]
    Backend --> MegaTTS3[MegaTTS3:9000]
    
    subgraph "微服务容器集群"
        Frontend
        Backend
        Database
        Redis
        NginxGW
    end
```

## 🚀 快速开始

### 前置要求
- Docker 20.0+
- Docker Compose 2.0+
- 系统内存 ≥ 4GB
- 磁盘空间 ≥ 10GB
- NVIDIA GPU（可选，用于MegaTTS3加速）

### 方式一：自动化部署（推荐）⭐

使用内置脚本一键部署，包含完整的检查、构建和启动流程。

```bash
# Linux/macOS - 一键部署
./scripts/deploy.sh

# Windows - 一键部署  
.\scripts\deploy.bat

# 开发模式部署（支持热重载）
./scripts/deploy.sh dev

# 清理环境
./scripts/deploy.sh clean

# 健康检查
./scripts/megatts3_health.sh
```

### 方式二：手动生产部署

适用于需要自定义配置的生产环境。

```bash
# 1. 克隆项目
git clone https://github.com/your-org/AI-Sound.git
cd AI-Sound

# 2. 创建数据目录
mkdir -p data/{audio,database,logs,uploads,voice_profiles,cache,config,backups,temp}

# 3. 构建前端静态文件
cd platform/frontend
npm install
npm run build
cp -r dist/* ../../nginx-dist/

# 4. 启动服务
cd ../..
docker-compose up -d

# 5. 检查服务状态
docker-compose ps
```

### 方式三：容器化开发部署

适用于开发环境，前端作为独立容器运行，支持热重载。

```bash
# 1. 使用完整配置启动
docker-compose -f docker-compose.full.yml up -d

# 2. 查看所有服务
docker-compose -f docker-compose.full.yml ps
```

### 方式四：本地开发

```bash
# 后端服务
cd platform/backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 前端服务（新终端）
cd platform/frontend
npm install
npm run dev
```

## 📁 项目结构

```
AI-Sound/
├── 📄 docker-compose.yml          # 生产部署配置
├── 📄 docker-compose.full.yml     # 开发/微服务配置
├── 📄 .env.example               # 环境变量模板
├── 📂 docs/                      # 📚 文档目录
├── 📂 scripts/                   # 🚀 自动化脚本和工具
│   ├── deploy.sh                 # Linux/macOS部署脚本
│   ├── deploy.bat                # Windows部署脚本
│   ├── megatts3_health.sh        # MegaTTS3健康检查
│   ├── analysis/                 # 语音分析工具
│   │   ├── analyze_voice_features.py  # 语音特征分析
│   │   ├── check_npy_shape.py         # NPY文件检查
│   │   └── check_model_load.py        # 模型加载测试
│   └── README.md                 # 脚本使用文档
├── 📂 docker/                    # 🐳 Docker配置
│   ├── nginx/
│   │   ├── nginx.conf            # 生产Nginx配置
│   │   └── ssl/                  # SSL证书
│   ├── frontend/
│   │   ├── Dockerfile            # 前端容器镜像
│   │   └── nginx.conf            # 前端Nginx配置
│   ├── backend/
│   │   └── Dockerfile.correct    # 后端容器镜像
│   ├── database/
│   │   └── init.sql              # 数据库初始化
│   └── docker-compose.full.yml   # 完整微服务编排
├── 📂 platform/                  # 💻 应用代码
│   ├── frontend/                 # 🎨 Vue3前端
│   │   ├── src/
│   │   │   ├── views/            # 页面组件
│   │   │   │   ├── NovelReader.vue     # 多角色朗读
│   │   │   │   ├── Characters.vue      # 声音库管理
│   │   │   │   ├── AudioLibrary.vue    # 音频资源库
│   │   │   │   └── BasicTTS.vue        # 语音克隆测试
│   │   │   ├── components/       # 通用组件
│   │   │   ├── api/              # API接口
│   │   │   └── router/           # 路由配置
│   │   ├── package.json          # 依赖配置
│   │   └── vite.config.js        # 构建配置
│   └── backend/                  # ⚙️ FastAPI后端
│       ├── app/
│       │   ├── main.py           # 主应用入口
│       │   ├── models.py         # 数据模型
│       │   ├── database.py       # 数据库连接
│       │   ├── audio_library.py  # 音频库API
│       │   ├── characters.py     # 声音库API
│       │   ├── novel_reader.py   # 多角色朗读API
│       │   ├── voice_clone.py    # 语音克隆API
│       │   ├── tts_client.py     # MegaTTS3客户端
│       │   └── utils.py          # 工具函数
│       ├── requirements.txt      # Python依赖
│       └── Dockerfile            # 后端镜像
├── 📂 nginx-dist/                # 🌐 前端构建结果（生产）
├── 📂 data/                      # 💾 数据持久化
│   ├── audio/                    # 🎵 生成的音频文件
│   ├── database/                 # 🗄️ 数据库文件
│   ├── logs/                     # 📋 服务日志
│   ├── uploads/                  # 📤 用户上传文件
│   ├── voice_profiles/           # 🎤 声音配置文件
│   ├── cache/                    # ⚡ 缓存数据
│   ├── config/                   # ⚙️ 运行时配置
│   ├── backups/                  # 💾 备份文件
│   └── temp/                     # 🗂️ 临时文件
└── 📂 MegaTTS/                   # 🔥 MegaTTS3引擎（外部）
    └── MegaTTS3/                 # TTS引擎目录
```

## 🚀 自动化脚本

`scripts/`目录提供完整的自动化工具链：

- **🛠️ 一键部署**: `deploy.sh`/`deploy.bat` - 自动检查环境、构建前端、启动服务
- **🔍 健康监控**: `megatts3_health.sh` - GPU状态、系统资源、网络连接检查
- **🔬 分析工具**: `analysis/` - 语音特征分析、NPY文件检查、模型测试

详细使用方法请参考 [scripts/README.md](scripts/README.md)

## 🎯 核心功能

### 🎙️ 语音克隆测试（BasicTTS.vue）
- 上传音频样本进行声音克隆
- 实时预览克隆效果
- 支持多种音频格式（.wav, .mp3, .flac等）
- 自定义合成参数调优

### 🔧 声音库管理（Characters.vue）
- 声音配置文件CRUD操作
- 质量评分和使用统计
- 标签分类和搜索过滤
- 音频文件预览播放

### 👥 多角色朗读（NovelReader.vue）
- 智能文本角色识别
- 项目化管理长文本
- 批量音频生成和合并
- 实时进度监控
- 智能角色声音分配算法

### 🎵 音频资源库（AudioLibrary.vue）
- 统一音频文件管理
- 按项目/类型分组筛选
- 批量下载/删除操作
- 在线播放器和时长显示
- 收藏标记和标签管理

## 🔧 部署配置

### 环境变量说明

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `DATABASE_URL` | sqlite:///./data/database/ai_sound.db | 数据库连接URL |
| `MEGATTS3_URL` | http://host.docker.internal:9000 | MegaTTS3服务地址 |
| `DEBUG` | false | 调试模式开关 |
| `CORS_ORIGINS` | http://localhost,https://localhost | 允许的跨域源 |

### 生产环境配置

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  database:
    environment:
      - POSTGRES_DB=ai_sound
      - POSTGRES_USER=ai_sound_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  backend:
    environment:
      - DATABASE_URL=postgresql://ai_sound_user:${DB_PASSWORD}@database:5432/ai_sound
      - DEBUG=false
    
  nginx:
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./ssl:/etc/nginx/ssl:ro

volumes:
  postgres_data:
```

## 📊 API 接口

### 核心接口

| 模块 | 接口 | 方法 | 描述 |
|------|------|------|------|
| **语音克隆** | `/api/voice-clone/synthesize` | POST | 语音合成 |
| **多角色朗读** | `/api/novel-reader/projects` | GET/POST | 项目管理 |
| **音频库** | `/api/audio-library/files` | GET | 音频文件列表 |
| **声音库** | `/api/characters/` | GET/POST/PUT/DELETE | 声音库CRUD |
| **系统** | `/health` | GET | 健康检查 |

### 访问地址

#### 生产部署
- **前端界面**: http://localhost:3001
- **API接口**: http://localhost:3001/api
- **API文档**: http://localhost:3001/docs
- **健康检查**: http://localhost:3001/health

#### 开发部署
- **前端界面**: http://localhost:80
- **前端容器**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 🛠️ 维护与监控

### 健康检查

```bash
# 检查所有服务状态
docker-compose ps

# 检查健康状态
curl http://localhost:3001/health
curl http://localhost:3001/api/health

# 检查容器资源使用
docker stats ai-sound-backend ai-sound-nginx ai-sound-db
```

### 日志管理

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f nginx

# 查看最近的错误日志
docker-compose logs --tail=50 backend | grep ERROR
```

### 数据备份

```bash
# 创建完整备份
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# 数据库备份（PostgreSQL）
docker exec ai-sound-db pg_dump -U ai_sound_user ai_sound > backup.sql

# 恢复数据库
docker exec -i ai-sound-db psql -U ai_sound_user ai_sound < backup.sql
```

## 🐛 故障排查

### 常见问题

1. **502 Bad Gateway**
   - 检查后端容器是否正常运行
   - 验证nginx配置中的upstream地址
   - 查看backend容器日志

2. **音频文件404**
   - 检查文件路径映射是否正确
   - 验证nginx中audio和voice_profiles路径配置
   - 确认文件实际存在于data目录

3. **MegaTTS3连接失败**
   - 确认MegaTTS3服务运行在正确端口
   - 检查网络连通性
   - 验证MEGATTS3_URL环境变量

### 诊断命令

```bash
# 检查端口占用
netstat -tulpn | grep :3001
netstat -tulpn | grep :8000

# 测试网络连接
docker exec ai-sound-backend ping ai-sound-db
docker exec ai-sound-nginx ping ai-sound-backend

# 检查磁盘空间
df -h data/
```

## 🔄 更新升级

### 更新服务

```bash
# 1. 备份数据
cp -r data/ backup-$(date +%Y%m%d)/

# 2. 拉取最新代码
git pull origin main

# 3. 重新构建镜像
docker-compose build --no-cache

# 4. 更新服务
docker-compose up -d

# 5. 验证更新
docker-compose ps
curl http://localhost:3001/health
```

### 版本回滚

```bash
# 停止服务
docker-compose down

# 恢复备份
rm -rf data/
mv backup-YYYYMMDD/ data/

# 回滚到指定版本
git checkout v1.0.0
docker-compose up -d
```

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🤝 技术支持

- 📚 **部署文档**: [docs/deployment.md](docs/deployment.md)
- 📡 **API文档**: [docs/api.md](docs/api.md)
- 🔧 **故障排查**: [docs/troubleshooting.md](docs/troubleshooting.md)
- 🐛 **问题反馈**: GitHub Issues
- 💬 **技术交流**: GitHub Discussions

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个星标！**

Made with ❤️ by AI-Sound Team

</div>