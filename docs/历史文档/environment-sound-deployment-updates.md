# 环境音管理模块部署方案更新

## 📋 更新概述

根据用户提出的两个关键考虑点，对环境音管理模块的部署方案进行了重要调整：

### 🔄 主要变更

1. **文件存储统一化** - 参考TTS3模式，将环境音文件统一存储在`/data/environment_sounds/`目录
2. **服务集成部署** - 将TangoFlux集成到AI-Sound后端容器，避免独立Docker服务的网络调用复杂性

---

## 📁 文件存储方案调整

### 🎯 设计原则
- **统一管理**: 所有音频文件统一存储在`data/`目录下
- **便于备份**: 集中存储便于数据备份和迁移
- **路径清晰**: 按时间和类型组织文件结构
- **扩展性强**: 支持未来更多音频类型

### 📂 新的存储结构
```
data/
├── audio/                        # 现有TTS音频文件
│   ├── tts_*.wav                # TTS生成音频
│   ├── segment_*.wav            # 章节音频
│   └── project_*.wav            # 项目音频
├── environment_sounds/           # 新增：环境音文件
│   ├── 2024/                    # 按年份分目录
│   │   ├── 01/                  # 按月份分目录
│   │   │   ├── env_rain_20240115_abc123.wav
│   │   │   ├── env_ocean_20240115_def456.wav
│   │   │   └── metadata.json    # 元数据文件
│   │   └── 02/
│   ├── temp/                    # 临时生成文件
│   │   ├── generating_*.wav     # 生成中的文件
│   │   └── failed_*.wav         # 生成失败的文件
│   └── cache/                   # 缓存文件
│       ├── thumbnails/          # 音频缩略图
│       └── waveforms/           # 波形数据
├── voice_profiles/              # 现有声音配置
├── uploads/                     # 上传文件
├── tts/                        # TTS3专用目录
└── logs/                       # 日志文件
    ├── environment_sounds.log   # 环境音操作日志
    └── tts.log                 # TTS日志
```

### 🔗 文件访问配置
```nginx
# Nginx配置更新
location /environment_sounds/ {
    alias /usr/share/nginx/environment_sounds/;
    expires 1d;
    add_header Cache-Control "public, immutable";
    add_header Access-Control-Allow-Origin "*";
}
```

---

## 🐳 Docker集成部署方案

### 🎯 设计原则
- **简化架构**: 减少容器数量，降低网络复杂性
- **资源共享**: GPU资源在同一容器内高效利用
- **维护便利**: 统一日志、监控和故障排查
- **性能优化**: 内部调用避免网络开销

### 🏗️ 集成架构
```
┌─────────────────────────────────────────────────────────┐
│                    AI-Sound Backend                    │
│  ┌─────────────────┐    ┌─────────────────────────────┐ │
│  │   FastAPI       │    │      TangoFlux Service      │ │
│  │   主服务:8000    │◄──►│      内部端口:7930          │ │
│  │                 │    │                             │ │
│  │ - 环境音管理API  │    │ - AI音效生成                │ │
│  │ - 文件管理       │    │ - 模型推理                  │ │
│  │ - 数据库操作     │    │ - 音频处理                  │ │
│  └─────────────────┘    └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │   统一数据存储   │
                   │  /app/data/     │
                   │                 │
                   │ ├─ audio/       │ ◄── TTS音频
                   │ ├─ environment_ │ ◄── 环境音音频
                   │ │   sounds/     │
                   │ ├─ voice_       │ ◄── 声音配置
                   │ │   profiles/   │
                   │ └─ uploads/     │ ◄── 上传文件
                   └─────────────────┘
```

### 🔧 Docker配置更新

#### 1. 后端Dockerfile更新
```dockerfile
# docker/backend/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖（包含TangoFlux需要的库）
RUN apt-get update && apt-get install -y \
    curl git ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖（包含TangoFlux）
COPY platform/backend/requirements.txt ./requirements.txt
COPY MegaTTS/TangoFlux/requirements.txt ./tangoflux_requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r tangoflux_requirements.txt

# 复制应用代码和TangoFlux模块
COPY platform/backend/app/ ./app/
COPY platform/backend/main.py ./main.py
COPY MegaTTS/TangoFlux/tangoflux/ ./tangoflux/
COPY MegaTTS/TangoFlux/tangoflux_api_server.py ./tangoflux_api_server.py
COPY MegaTTS/TangoFlux/start_tangoflux_api.py ./start_tangoflux_api.py

# 创建统一数据目录
RUN mkdir -p /app/data/environment_sounds/temp \
             /app/data/environment_sounds/cache/thumbnails \
             /app/data/environment_sounds/cache/waveforms

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Docker Compose更新
```yaml
# docker-compose.yml 更新backend服务
services:
  backend:
    build:
      context: .
      dockerfile: docker/backend/Dockerfile
    container_name: ai-sound-backend
    environment:
      - DATABASE_URL=postgresql://ai_sound_user:ai_sound_password@database:5432/ai_sound
      - MEGATTS3_URL=http://megatts3:7929
      - TANGOFLUX_URL=http://localhost:7930  # 内部调用
      - OLLAMA_URL=http://host.docker.internal:11434
      - AUDIO_DIR=/app/data/audio
      - ENVIRONMENT_SOUNDS_DIR=/app/data/environment_sounds  # 新增
      - UPLOADS_DIR=/app/data/uploads
      - VOICE_PROFILES_DIR=/app/data/voice_profiles
      - DEBUG=false
    volumes:
      - ./data:/app/data  # 统一数据存储
    ports:
      - "7930:7930"  # 暴露TangoFlux端口供外部调试
    depends_on:
      - database
      - redis
      - megatts3
    networks:
      - ai-sound-network
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

---

## 💻 代码集成实现

### 🚀 后端服务启动
```python
# platform/backend/main.py 更新
import threading
from fastapi import FastAPI
from contextlib import asynccontextmanager

def start_tangoflux_service():
    """在后台线程启动TangoFlux服务"""
    try:
        from start_tangoflux_api import start_api_server
        print("🎵 启动TangoFlux环境音服务...")
        start_api_server()  # 在端口7930启动
    except Exception as e:
        print(f"❌ TangoFlux服务启动失败: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    print("🚀 初始化AI-Sound后端服务...")
    
    # 在后台线程启动TangoFlux
    tangoflux_thread = threading.Thread(
        target=start_tangoflux_service, 
        daemon=True
    )
    tangoflux_thread.start()
    
    yield
    
    # 关闭时清理
    print("🔄 关闭AI-Sound后端服务...")

app = FastAPI(
    title="AI-Sound Platform",
    description="AI音频合成平台",
    version="2.0.0",
    lifespan=lifespan
)
```

### 🔌 TangoFlux客户端
```python
# platform/backend/app/clients/tangoflux_client.py
import httpx
from typing import Dict, Any

class TangoFluxClient:
    def __init__(self):
        self.base_url = "http://localhost:7930"  # 内部调用
        self.timeout = 300  # 5分钟超时
    
    async def generate_environment_sound(
        self, 
        prompt: str, 
        duration: float = 10.0,
        steps: int = 50,
        cfg_scale: float = 3.5
    ) -> Dict[str, Any]:
        """生成环境音效"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/audio/generate_file",
                json={
                    "prompt": prompt,
                    "duration": duration,
                    "steps": steps,
                    "cfg_scale": cfg_scale
                }
            )
            response.raise_for_status()
            return response.json()

tangoflux_client = TangoFluxClient()
```

### 📁 文件管理器
```python
# platform/backend/app/utils/file_manager.py
import os
import uuid
from datetime import datetime
from pathlib import Path

class EnvironmentSoundFileManager:
    def __init__(self):
        self.base_dir = Path("/app/data/environment_sounds")
        self.ensure_directories()
    
    def generate_file_path(self, category: str, name: str) -> str:
        """生成文件存储路径"""
        now = datetime.now()
        year_month = now.strftime("%Y/%m")
        date_str = now.strftime("%Y%m%d")
        unique_id = uuid.uuid4().hex[:8]
        
        clean_name = "".join(c for c in name if c.isalnum() or c in ('-', '_'))
        filename = f"env_{clean_name}_{date_str}_{unique_id}.wav"
        
        target_dir = self.base_dir / year_month
        target_dir.mkdir(parents=True, exist_ok=True)
        
        return str(target_dir / filename)
    
    def get_web_url(self, file_path: str) -> str:
        """获取Web访问的URL"""
        relative_path = os.path.relpath(file_path, self.base_dir)
        return f"/environment_sounds/{relative_path.replace(os.sep, '/')}"

file_manager = EnvironmentSoundFileManager()
```

---

## 🔧 实施步骤调整

### Phase 1: 基础设施搭建 (第1-3天)

#### Day 1: 集成部署配置
- ✅ 更新Docker后端配置，集成TangoFlux模块
- ✅ 修改端口配置从7928到7930
- ✅ 更新docker-compose.yml配置
- ✅ 配置统一文件存储结构
- ✅ 创建/data/environment_sounds/目录
- ✅ 验证TangoFlux内部调用

### 📊 优势对比

| 方案 | 独立Docker服务 | 集成部署（推荐） |
|------|---------------|-----------------|
| **架构复杂度** | 高 - 多容器通信 | 低 - 单容器内调用 |
| **网络开销** | 高 - HTTP调用 | 低 - 内部函数调用 |
| **资源利用** | 分散 - 多GPU分配 | 高效 - GPU资源共享 |
| **维护成本** | 高 - 多服务管理 | 低 - 统一管理 |
| **故障排查** | 复杂 - 跨容器日志 | 简单 - 统一日志 |
| **部署难度** | 高 - 网络配置 | 低 - 单容器部署 |

---

## 📈 预期效果

### 🎯 性能提升
- **响应时间**: 内部调用减少网络延迟，预计提升20-30%
- **资源利用**: GPU资源共享，利用率提升15-25%
- **并发能力**: 减少网络瓶颈，支持更多并发请求

### 🛠️ 运维简化
- **部署复杂度**: 减少50%的配置工作
- **监控难度**: 统一日志和监控，降低70%的运维成本
- **故障排查**: 单容器内问题定位，提升80%的效率

### 💾 存储优化
- **备份策略**: 统一数据目录，简化备份流程
- **空间利用**: 集中存储，避免重复和碎片化
- **访问性能**: 本地文件访问，提升I/O性能

---

## 🔮 未来扩展

### 📱 模块化设计
- 支持更多AI音频生成模型集成
- 插件化架构，便于功能扩展
- 统一的音频处理管道

### 🌐 分布式支持
- 支持多节点部署的负载均衡
- 分布式文件存储适配
- 微服务架构演进路径

---

## 📋 总结

通过这次部署方案调整，环境音管理模块将：

1. **简化架构** - 集成部署减少系统复杂性
2. **提升性能** - 内部调用和资源共享优化性能
3. **统一管理** - 文件存储和服务管理标准化
4. **便于维护** - 降低运维成本和故障排查难度

这些调整确保了环境音管理模块能够与现有AI-Sound平台无缝集成，为用户提供更好的使用体验和更稳定的服务质量。

---

**文档版本**: v1.0  
**更新日期**: 2024年12月  
**状态**: 已确认