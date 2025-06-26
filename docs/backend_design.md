# 🚀 AI-Sound 后端服务架构设计（修正版）

## 🎯 设计目标

基于前端界面能力，设计与现有 **MegaTTS3 引擎 (localhost:7929)** 兼容的完整后端服务体系。

**⚠️ 重要修正**：遵循原始设计文档 `design.md` 的架构理念 - **简洁实用，避免过度设计**

## 🏗️ 整体架构（修正版）

```
┌─────────────────────────────────────────────────────────────┐
│                AI-Sound Platform 架构                       │
├─────────────────────────────────────────────────────────────┤
│  前端 (Vue3 + Ant Design)  →  FastAPI 后端  →  PostgreSQL  │
│                                     ↓                       │
│  MegaTTS3 引擎 (localhost:7929)  ←  TTS Client适配器        │
└─────────────────────────────────────────────────────────────┘

服务组件：
├── 🌐 FastAPI Backend (端口:8000)     # 统一后端API
├── 🎤 Voice Clone Module              # 语音克隆功能
├── 📚 Characters Module               # 角色管理功能
├── 📖 Novel Reader Module             # 多角色朗读功能
├── 📊 Monitor Module                  # 系统监控功能
├── 💾 PostgreSQL Database             # 企业级数据库
└── 🔧 MegaTTS3 Client                 # 引擎适配器
```

## 📂 Platform 目录结构（遵循原设计）

```
platform/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI应用入口
│   │   ├── database.py            # PostgreSQL数据库连接
│   │   ├── models.py              # SQLAlchemy数据模型
│   │   ├── voice_clone.py         # 语音克隆模块
│   │   ├── characters.py          # 角色管理模块
│   │   ├── novel_reader.py        # 小说朗读模块
│   │   ├── monitor.py             # 系统监控模块
│   │   └── tts_client.py          # MegaTTS3客户端
│   ├── requirements.txt
│   └── start.py
├── frontend/                      # Vue3前端 (已存在)
├── data/
│   ├── postgresql/               # PostgreSQL数据卷
│   ├── audio/                    # 生成的音频文件
│   ├── uploads/                  # 上传的音频/文本文件
│   └── voice_profiles/           # 声音库文件
└── scripts/
    ├── init_db.py               # 数据库初始化
    └── start_platform.py       # 平台启动脚本
```

## 💾 数据存储设计（PostgreSQL）

### PostgreSQL 表结构设计

```sql
-- 声音库表 (基于Characters.vue功能)
CREATE TABLE voice_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    type TEXT NOT NULL, -- 'male' | 'female' | 'child'
    
    -- 音频文件路径
    reference_audio_path TEXT NOT NULL,
    latent_file_path TEXT,
    sample_audio_path TEXT,
    
    -- 技术参数 (JSON格式)
    parameters TEXT NOT NULL, -- {"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}
    
    -- 质量和统计
    quality_score REAL DEFAULT 3.0,
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    
    -- 元数据
    color TEXT DEFAULT '#06b6d4',
    tags TEXT, -- JSON数组格式
    status TEXT DEFAULT 'active', -- 'active' | 'training' | 'inactive'
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 朗读项目表 (基于NovelReader.vue功能)
CREATE TABLE novel_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    
    -- 文本内容
    original_text TEXT NOT NULL,
    text_file_path TEXT,
    
    -- 处理状态
    status TEXT DEFAULT 'pending', -- 'pending' | 'processing' | 'paused' | 'completed' | 'failed'
    total_segments INTEGER DEFAULT 0,
    processed_segments INTEGER DEFAULT 0,
    failed_segments TEXT, -- JSON数组：失败的段落ID
    current_segment INTEGER DEFAULT 0,
    
    -- 角色映射 (JSON格式)
    character_mapping TEXT, -- {"角色名": "voice_profile_id"}
    
    -- 输出文件
    final_audio_path TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    estimated_completion TIMESTAMP
);

-- 文本段落表
CREATE TABLE text_segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    segment_order INTEGER NOT NULL,
    text_content TEXT NOT NULL,
    
    -- 角色信息
    detected_speaker TEXT,
    voice_profile_id INTEGER,
    
    -- 处理状态
    status TEXT DEFAULT 'pending', -- 'pending' | 'processing' | 'completed' | 'failed'
    audio_file_path TEXT,
    processing_time REAL,
    error_message TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES novel_projects(id),
    FOREIGN KEY (voice_profile_id) REFERENCES voice_profiles(id)
);

-- 系统日志表 (基于Settings.vue功能)
CREATE TABLE system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL, -- 'info' | 'warn' | 'error'
    message TEXT NOT NULL,
    module TEXT, -- 'voice_clone' | 'characters' | 'novel_reader' | 'system'
    details TEXT, -- JSON格式的详细信息
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 使用统计表
CREATE TABLE usage_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    total_processing_time REAL DEFAULT 0,
    audio_files_generated INTEGER DEFAULT 0,
    PRIMARY KEY (date)
);
```

## 📋 核心模块设计

### 1. 🎤 Voice Clone Module

**对应前端**：`BasicTTS.vue` - 声音克隆测试台

```python
# app/voice_clone.py
from fastapi import APIRouter, UploadFile, File, Form
from sqlalchemy.orm import Session
import os
import uuid
from .database import get_db
from .tts_client import MegaTTS3Client
from .models import VoiceProfile

router = APIRouter(prefix="/api/voice", tags=["voice-clone"])

@router.post("/upload-reference")
async def upload_reference_audio(
    audio_file: UploadFile = File(...),
    latent_file: UploadFile = File(None),
    name: str = Form(...),
    description: str = Form(""),
    voice_type: str = Form(...),
    db: Session = Depends(get_db)
):
    """上传参考音频文件"""
    # 1. 保存音频文件到本地
    file_id = str(uuid.uuid4())
    audio_path = f"data/uploads/{file_id}_{audio_file.filename}"
    
    with open(audio_path, "wb") as f:
        content = await audio_file.read()
        f.write(content)
    
    # 2. 处理latent文件（如果有）
    latent_path = None
    if latent_file:
        latent_path = f"data/uploads/{file_id}_latent.npy"
        with open(latent_path, "wb") as f:
            latent_content = await latent_file.read()
            f.write(latent_content)
    
    # 3. 音频分析（获取时长、采样率等）
    duration, sample_rate = analyze_audio(audio_path)
    
    return {
        "fileId": file_id,
        "fileUrl": audio_path,
        "duration": duration,
        "sampleRate": sample_rate,
        "status": "uploaded"
    }

@router.post("/clone-synthesis")
async def clone_synthesis(
    reference_file_id: str,
    latent_file_id: str = None,
    text: str = "",
    time_step: int = 20,
    p_weight: float = 1.0,
    t_weight: float = 1.0
):
    """实时语音克隆合成"""
    # 1. 获取文件路径
    reference_path = f"data/uploads/{reference_file_id}_*.wav"
    latent_path = f"data/uploads/{latent_file_id}_latent.npy" if latent_file_id else None
    
    # 2. 调用MegaTTS3
    tts_client = MegaTTS3Client()
    result = await tts_client.synthesize_with_clone(
        reference_audio_path=reference_path,
        latent_file_path=latent_path,
        text=text,
        parameters={
            "time_step": time_step,
            "p_w": p_weight,
            "t_w": t_weight
        }
    )
    
    # 3. 保存生成的音频
    task_id = str(uuid.uuid4())
    output_path = f"data/audio/{task_id}.wav"
    with open(output_path, "wb") as f:
        f.write(result.audio_data)
    
    # 4. 质量评估
    quality_score = evaluate_audio_quality(output_path)
    
    return {
        "taskId": task_id,
        "audioUrl": f"/audio/{task_id}.wav",
        "processingTime": result.processing_time,
        "qualityScore": quality_score,
        "status": "completed"
    }
```

### 2. 📚 Characters Module

**对应前端**：`Characters.vue` - 声音库管理

```python
# app/characters.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from .database import get_db
from .models import VoiceProfile
from pydantic import BaseModel

router = APIRouter(prefix="/api/library", tags=["voice-library"])

class VoiceProfileCreate(BaseModel):
    name: str
    description: str = ""
    type: str  # 'male' | 'female' | 'child'
    reference_audio_path: str
    latent_file_path: Optional[str] = None
    parameters: dict = {"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}
    color: str = "#06b6d4"
    tags: List[str] = []

@router.get("/voices")
async def get_voice_profiles(
    search: Optional[str] = None,
    voice_type: Optional[str] = None,
    quality_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取声音库列表"""
    query = db.query(VoiceProfile)
    
    # 搜索过滤
    if search:
        query = query.filter(VoiceProfile.name.contains(search))
    
    # 类型过滤
    if voice_type:
        query = query.filter(VoiceProfile.type == voice_type)
    
    # 质量过滤
    if quality_filter == "high":
        query = query.filter(VoiceProfile.quality_score >= 4.0)
    elif quality_filter == "medium":
        query = query.filter(VoiceProfile.quality_score >= 3.0, VoiceProfile.quality_score < 4.0)
    elif quality_filter == "low":
        query = query.filter(VoiceProfile.quality_score < 3.0)
    
    voices = query.all()
    return [voice.to_dict() for voice in voices]

@router.post("/voices")
async def create_voice_profile(
    voice_data: VoiceProfileCreate,
    db: Session = Depends(get_db)
):
    """创建新声音库"""
    # 检查名称是否已存在
    existing = db.query(VoiceProfile).filter(VoiceProfile.name == voice_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="声音名称已存在")
    
    # 创建新声音库
    voice_profile = VoiceProfile(
        name=voice_data.name,
        description=voice_data.description,
        type=voice_data.type,
        reference_audio_path=voice_data.reference_audio_path,
        latent_file_path=voice_data.latent_file_path,
        parameters=json.dumps(voice_data.parameters),
        color=voice_data.color,
        tags=json.dumps(voice_data.tags)
    )
    
    db.add(voice_profile)
    db.commit()
    db.refresh(voice_profile)
    
    return voice_profile.to_dict()

@router.post("/voices/{voice_id}/test")
async def test_voice_quality(
    voice_id: int,
    test_text: str = "你好，这是语音质量测试。",
    db: Session = Depends(get_db)
):
    """测试声音质量"""
    voice = db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
    if not voice:
        raise HTTPException(status_code=404, detail="声音库不存在")
    
    # 使用声音库参数进行合成
    tts_client = MegaTTS3Client()
    parameters = json.loads(voice.parameters)
    
    result = await tts_client.synthesize_with_clone(
        reference_audio_path=voice.reference_audio_path,
        latent_file_path=voice.latent_file_path,
        text=test_text,
        parameters=parameters
    )
    
    # 更新使用统计
    voice.usage_count += 1
    voice.last_used = datetime.utcnow()
    db.commit()
    
    return {
        "audioUrl": result.audio_url,
        "qualityScore": result.quality_score,
        "processingTime": result.processing_time
    }
```

### 3. 📖 Novel Reader Module

**对应前端**：`NovelReader.vue` - 智能多角色朗读

```python
# app/novel_reader.py
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
import re
import json
from typing import List, Dict
from .database import get_db
from .models import NovelProject, TextSegment, VoiceProfile

router = APIRouter(prefix="/api/reader", tags=["novel-reader"])

@router.post("/projects")
async def create_novel_project(
    name: str,
    description: str = "",
    db: Session = Depends(get_db)
):
    """创建朗读项目"""
    project = NovelProject(
        name=name,
        description=description
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return project.to_dict()

@router.post("/projects/{project_id}/upload-text")
async def upload_text_file(
    project_id: int,
    text_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传文本文件"""
    project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 读取文本内容
    content = await text_file.read()
    text_content = content.decode('utf-8')
    
    # 保存文件
    file_path = f"data/uploads/{project_id}_{text_file.filename}"
    with open(file_path, "w", encoding='utf-8') as f:
        f.write(text_content)
    
    # 更新项目
    project.original_text = text_content
    project.text_file_path = file_path
    db.commit()
    
    return {"message": "文本上传成功", "projectId": project_id}

@router.post("/projects/{project_id}/parse-segments")
async def parse_text_segments(
    project_id: int,
    db: Session = Depends(get_db)
):
    """解析文本分段"""
    project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 分段处理
    segments = split_text_into_segments(project.original_text)
    
    # 保存分段到数据库
    for i, segment_text in enumerate(segments):
        segment = TextSegment(
            project_id=project_id,
            segment_order=i + 1,
            text_content=segment_text,
            detected_speaker=detect_speaker(segment_text)  # 简单的说话人检测
        )
        db.add(segment)
    
    project.total_segments = len(segments)
    db.commit()
    
    return {
        "message": "文本分段完成",
        "totalSegments": len(segments),
        "segments": [seg.to_dict() for seg in project.segments]
    }

def split_text_into_segments(text: str) -> List[str]:
    """将文本分割成段落"""
    # 按段落分割
    paragraphs = text.split('\n\n')
    segments = []
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if paragraph:
            # 如果段落太长，按句子进一步分割
            if len(paragraph) > 200:
                sentences = re.split(r'[。！？]', paragraph)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if sentence:
                        segments.append(sentence + '。')
            else:
                segments.append(paragraph)
    
    return segments

def detect_speaker(text: str) -> str:
    """简单的说话人检测"""
    # 检测对话标记
    if '"' in text or '"' in text or '"' in text:
        return "dialogue"
    elif text.startswith(('他说', '她说', '我说')):
        return "narrative"
    else:
        return "narrator"

@router.post("/projects/{project_id}/start")
async def start_project_generation(
    project_id: int,
    db: Session = Depends(get_db)
):
    """开始生成音频"""
    project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 更新项目状态
    project.status = "processing"
    project.started_at = datetime.utcnow()
    db.commit()
    
    # 启动后台任务处理
    background_tasks.add_task(process_project_segments, project_id)
    
    return {"message": "项目开始生成", "status": "processing"}

async def process_project_segments(project_id: int):
    """后台处理项目分段"""
    # 这里实现具体的分段处理逻辑
    # 包括调用MegaTTS3生成音频、保存文件、更新状态等
    pass
```

### 4. 🔧 MegaTTS3 Client

```python
# app/tts_client.py
import aiohttp
import os
import time
from typing import Optional, Dict, Any

class MegaTTS3Client:
    """MegaTTS3引擎客户端"""
    
    def __init__(self, base_url: str = "http://localhost:7929"):
        self.base_url = base_url
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"status": "error", "message": f"HTTP {resp.status}"}
        except Exception as e:
            return {"status": "offline", "error": str(e)}
    
    async def synthesize_with_clone(
        self,
        reference_audio_path: str,
        text: str,
        parameters: Dict[str, Any],
        latent_file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """语音克隆合成"""
        try:
            async with aiohttp.ClientSession() as session:
                # 准备表单数据
                form_data = aiohttp.FormData()
                
                # 添加音频文件
                with open(reference_audio_path, 'rb') as f:
                    form_data.add_field('reference_audio', f, filename='reference.wav')
                
                # 添加latent文件（如果有）
                if latent_file_path and os.path.exists(latent_file_path):
                    with open(latent_file_path, 'rb') as f:
                        form_data.add_field('latent_file', f, filename='latent.npy')
                
                # 添加参数
                form_data.add_field('text', text)
                form_data.add_field('time_step', str(parameters.get('time_step', 20)))
                form_data.add_field('p_w', str(parameters.get('p_w', 1.0)))
                form_data.add_field('t_w', str(parameters.get('t_w', 1.0)))
                
                start_time = time.time()
                async with session.post(f"{self.base_url}/synthesize", data=form_data) as resp:
                    if resp.status == 200:
                        audio_data = await resp.read()
                        processing_time = time.time() - start_time
                        
                        return {
                            "audio_data": audio_data,
                            "processing_time": processing_time,
                            "status": "success"
                        }
                    else:
                        error_text = await resp.text()
                        return {
                            "status": "error",
                            "message": f"MegaTTS3 error: {error_text}"
                        }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Client error: {str(e)}"
            }
```

## 🚀 修正后的部署方案

### 简化的启动方式
```bash
# 1. 确保MegaTTS3运行
curl http://localhost:7929/health

# 2. 启动Platform
cd platform
python scripts/start_platform.py

# 访问界面
# 前端: http://localhost:3000
# 后端API: http://localhost:8000
# API文档: http://localhost:8000/docs
```

### Docker部署（简化版）
```yaml
# platform/docker/docker-compose.yml
version: '3.8'
services:
  platform-backend:
    build: ../backend
    ports:
      - "8000:8000"
    volumes:
      - ../data:/app/data
    environment:
      - DATABASE_URL=postgresql://ai_sound_user:ai_sound_password@ai-sound-db:5432/ai_sound
      - MEGATTS3_URL=http://host.docker.internal:7929
    
  platform-frontend:
    build: ../frontend
    ports:
      - "3000:3000"
    depends_on:
      - platform-backend
```

## 🎯 核心优势（修正版）

### ✅ **遵循原设计理念**
- **PostgreSQL** 企业级关系型数据库 - 高性能，事务安全，扩展性强
- **单体FastAPI** 替代微服务架构 - 简单部署，易于调试
- **本地文件存储** 替代分布式存储 - 直接、可靠、无依赖

### ✅ **完全兼容现有系统**
- 100%兼容MegaTTS3引擎 (localhost:7929)
- 不影响现有services目录
- 可以并行开发和部署

### ✅ **前后端功能对应**
- BasicTTS.vue ↔ Voice Clone Module
- Characters.vue ↔ Characters Module  
- NovelReader.vue ↔ Novel Reader Module
- Settings.vue ↔ Monitor Module

---

**🙏 感谢指正！** 修正后的设计完全遵循原始 `design.md` 的架构理念：
- ✅ **PostgreSQL** 企业级数据库
- ✅ **FastAPI** 单体后端服务
- ✅ **本地文件存储** 
- ✅ **简洁实用** 的设计原则

这样的架构更适合当前项目的规模和需求！接下来要实现哪个模块？ 