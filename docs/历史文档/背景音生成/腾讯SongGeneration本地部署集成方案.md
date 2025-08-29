# 腾讯SongGeneration本地部署集成到AI-Sound设计方案

## 📋 项目概述

### 目标
将腾讯SongGeneration音乐生成引擎**本地化部署**并集成到AI-Sound项目，实现与TTS3、TangoFlux同样的本地化AI音频制作能力。

### 核心价值
- 🏠 **本地化部署**：无网络依赖，数据隐私保护，与现有架构一致
- 🎬 **电影级音频体验**：文本 → 语音 → 音乐 → 环境音的完整AI音频制作链路
- 🎵 **智能音乐创作**：基于情节内容自动生成契合的背景音乐
- 🎛️ **专业音频制作**：多轨混音，用户可独立调节各音轨音量

## 🔍 本地部署优势

### 为什么选择本地部署
```
AI-Sound现有架构特点：
✅ TTS3: 本地部署 (MegaTTS/espnet/)
✅ TangoFlux: 本地部署 (MegaTTS/TangoFlux/)
✅ 数据隐私: 用户文本不出本地
✅ 稳定性: 无网络依赖
✅ 可控性: 模型版本、参数完全可控

SongGeneration本地部署：
✅ GitHub开源: https://github.com/tencent-ailab/SongGeneration
✅ Docker支持: juhayna/song-generation-levo:hf0613
✅ 低显存版本: generate_lowmem.py (<30GB显存)
✅ 完整文档: 安装、推理、配置指南
```

### 技术可行性
- **硬件要求**：CUDA>=11.8，与现有环境兼容
- **显存需求**：标准版需要≥30GB，低显存版<30GB
- **部署方式**：Docker容器化，与现有微服务架构一致
- **API接口**：可封装为内部微服务，统一调用方式

## 🏗️ 本地部署架构设计

### 整体架构
```
AI-Sound本地化AI音频制作链路：

小说文本输入
    ↓
[智能分析服务] → 角色识别 + 情节分析
    ↓
[TTS3本地服务] → 对话音频生成 (端口7861)
    ↓
[SongGeneration本地服务] → 背景音乐生成 (端口7862) ← 新增
    ↓  
[TangoFlux本地服务] → 环境音效生成 (端口7930)
    ↓
[多轨混音服务] → 最终音频输出
```

### Docker部署架构
```yaml
# docker-compose.yml 新增服务
services:
  songgeneration:
    image: juhayna/song-generation-levo:hf0613
    ports:
      - "7862:7862"
    volumes:
      - ./MegaTTS/SongGeneration/ckpt:/app/ckpt
      - ./MegaTTS/SongGeneration/output:/app/output
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

## 🎵 本地音乐生成服务设计

### 模块结构
```
MegaTTS/
└── SongGeneration/                 # 新增音乐生成模块
    ├── song_generation_model.py    # 本地模型封装
    ├── music_input_generator.py    # 音乐输入生成器
    ├── audio_post_processor.py     # 音频后处理
    ├── ckpt/                       # 模型权重目录
    │   ├── songgeneration_base/    # 基础模型权重
    │   └── third_party/            # 第三方依赖
    ├── requirements.txt            # Python依赖
    ├── generate.py                 # 原版推理脚本
    ├── generate_lowmem.py          # 低显存推理脚本
    └── server.py                   # HTTP服务封装
```

### 本地模型服务封装
```python
# MegaTTS/SongGeneration/song_generation_model.py
import subprocess
import json
import asyncio
from pathlib import Path

class LocalSongGenerationModel:
    def __init__(self, model_path="./ckpt/songgeneration_base", low_memory=True):
        self.model_path = Path(model_path)
        self.low_memory = low_memory
        self.script_path = "./generate_lowmem.py" if low_memory else "./generate.py"
        
    async def generate_music(self, lyrics, descriptions=None, duration=30):
        """
        本地生成音乐
        Args:
            lyrics: 歌词结构，格式: "[intro-short] ; [verse] 歌词内容 ; [chorus] 副歌内容"
            descriptions: 音乐描述，如: "male, pop, energetic, piano and drums, the bpm is 120"
            duration: 目标时长（秒）
        Returns:
            生成的音频文件路径
        """
        # 1. 创建输入jsonl文件
        input_data = {
            "idx": f"music_{int(time.time())}",
            "gt_lyric": lyrics,
            "descriptions": descriptions
        }
        
        input_file = f"./temp_input_{input_data['idx']}.jsonl"
        output_dir = f"./output/{input_data['idx']}"
        
        # 2. 写入输入文件
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(input_data, f, ensure_ascii=False)
            f.write('\n')
        
        # 3. 调用本地生成脚本
        cmd = [
            "python", self.script_path,
            str(self.model_path), 
            input_file, 
            output_dir
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"音乐生成失败: {stderr.decode()}")
        
        # 4. 返回生成的音频文件路径
        audio_path = Path(output_dir) / "audio" / f"{input_data['idx']}.wav"
        return str(audio_path)
```

### 音乐生成HTTP服务
```python
# MegaTTS/SongGeneration/server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from song_generation_model import LocalSongGenerationModel

app = FastAPI(title="SongGeneration Local Service")
model = LocalSongGenerationModel()

class MusicGenerationRequest(BaseModel):
    lyrics: str
    descriptions: str = None
    duration: int = 30

class MusicGenerationResponse(BaseModel):
    audio_path: str
    generation_time: float

@app.post("/generate", response_model=MusicGenerationResponse)
async def generate_music(request: MusicGenerationRequest):
    try:
        start_time = time.time()
        
        audio_path = await model.generate_music(
            lyrics=request.lyrics,
            descriptions=request.descriptions,
            duration=request.duration
        )
        
        generation_time = time.time() - start_time
        
        return MusicGenerationResponse(
            audio_path=audio_path,
            generation_time=generation_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7862)
```

## 🎵 智能音乐生成策略

### 情节-音乐映射规则
| 情节类型 | 歌词结构 | 音乐描述 | 音量设置 |
|---------|---------|---------|---------|
| 战斗场景 | `[intro-short] ; [verse] 激昂战斗 ; [chorus] 英雄凯旋` | `male, rock, energetic, guitar and drums, the bpm is 140` | -10dB到-8dB |
| 爱情场景 | `[intro-medium] ; [verse] 温柔爱意 ; [bridge] 深情告白` | `female, pop, romantic, piano and strings, the bpm is 80` | -15dB到-12dB |
| 悬疑场景 | `[inst-short] ; [verse] 神秘气氛 ; [inst-medium]` | `dark, mysterious, synthesizer, the bpm is 100` | -12dB到-10dB |
| 平静日常 | `[intro-short] ; [verse] 平静生活 ; [outro-short]` | `acoustic, folk, peaceful, guitar, the bpm is 90` | -18dB到-15dB |

### 音乐输入生成器
```python
# MegaTTS/SongGeneration/music_input_generator.py
class MusicInputGenerator:
    def __init__(self):
        self.scene_templates = {
            "battle": {
                "lyrics": "[intro-short] ; [verse] Epic battle unfolds with courage and might. Heroes stand tall against the darkness of night ; [chorus] Victory calls through the storm and the fight. Honor and glory shine bright in the light ; [outro-short]",
                "descriptions": "male, rock, energetic, guitar and drums, the bpm is 140"
            },
            "romance": {
                "lyrics": "[intro-medium] ; [verse] Gentle whispers in the moonlight glow. Sweet emotions only we can know ; [bridge] Heart to heart our love will grow. In this moment time moves slow ; [outro-medium]",
                "descriptions": "female, pop, romantic, piano and strings, the bpm is 80"
            },
            "mystery": {
                "lyrics": "[inst-short] ; [verse] Shadows dance in corridors unknown. Secrets hide where light has never shone ; [inst-medium]",
                "descriptions": "dark, mysterious, synthesizer, the bpm is 100"
            },
            "peaceful": {
                "lyrics": "[intro-short] ; [verse] Morning dew on fields of green. Peaceful moments calm and serene ; [outro-short]",
                "descriptions": "acoustic, folk, peaceful, guitar, the bpm is 90"
            }
        }
    
    def generate_for_scene(self, scene_type, duration=30):
        """根据场景类型生成音乐输入"""
        template = self.scene_templates.get(scene_type, self.scene_templates["peaceful"])
        
        # 根据时长调整歌词结构
        if duration > 60:
            # 长时间：添加更多段落
            lyrics = template["lyrics"].replace("[outro-short]", "[verse] Extended melody continues the theme ; [outro-medium]")
        elif duration < 20:
            # 短时间：简化结构
            lyrics = template["lyrics"].replace("[intro-medium]", "[intro-short]").replace("[outro-medium]", "[outro-short]")
        else:
            lyrics = template["lyrics"]
        
        return {
            "lyrics": lyrics,
            "descriptions": template["descriptions"],
            "duration": duration
        }
```

## 🔧 AI-Sound后端集成

### 音乐生成服务
```python
# platform/backend/app/services/song_generation_service.py
import httpx
from typing import Optional
from ..models.synthesis_project import SynthesisProject
from .music_input_generator import MusicInputGenerator

class SongGenerationService:
    def __init__(self):
        self.base_url = "http://localhost:7862"  # 本地SongGeneration服务
        self.input_generator = MusicInputGenerator()
        
    async def generate_background_music(
        self, 
        project: SynthesisProject, 
        scene_analysis: dict,
        duration: int
    ) -> str:
        """
        为合成项目生成背景音乐
        
        Args:
            project: 合成项目对象
            scene_analysis: 场景分析结果
            duration: 音乐时长（秒）
            
        Returns:
            生成的音频文件路径
        """
        try:
            # 1. 根据场景分析生成音乐输入
            scene_type = scene_analysis.get('scene_type', 'peaceful')
            music_input = self.input_generator.generate_for_scene(scene_type, duration)
            
            # 2. 调用本地SongGeneration服务
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/generate",
                    json=music_input,
                    timeout=300  # 5分钟超时
                )
                response.raise_for_status()
                
                result = response.json()
                
            # 3. 将生成的音乐文件移动到项目目录
            source_path = result["audio_path"]
            target_path = f"data/projects/{project.id}/background_music.wav"
            
            import shutil
            shutil.move(source_path, target_path)
            
            # 4. 记录生成信息
            logger.info(f"背景音乐生成成功: {target_path}, 耗时: {result['generation_time']:.2f}s")
            
            return target_path
            
        except Exception as e:
            logger.error(f"背景音乐生成失败: {str(e)}")
            # 返回默认静音文件或处理错误
            return None
```

### 增强混音服务
```python
# platform/backend/app/services/enhanced_audio_mixer.py
class EnhancedAudioMixer:
    def __init__(self):
        self.track_configs = {
            "dialogue": {"default_volume": -3, "priority": 1},
            "background_music": {"default_volume": -12, "priority": 3},  # 新增
            "environment": {"default_volume": -15, "priority": 4},
            "effects": {"default_volume": -8, "priority": 2}
        }
    
    def mix_all_tracks(self, tracks: dict, output_path: str):
        """
        混合所有音轨（包括新的背景音乐轨道）
        
        Args:
            tracks: {
                "dialogue": "path/to/dialogue.wav",
                "background_music": "path/to/music.wav",  # 新增
                "environment": "path/to/environment.wav",
                "effects": "path/to/effects.wav"
            }
        """
        audio_segments = []
        
        for track_type, file_path in tracks.items():
            if file_path and os.path.exists(file_path):
                # 加载音频
                audio = AudioSegment.from_file(file_path)
                
                # 应用默认音量
                config = self.track_configs.get(track_type, {"default_volume": -10})
                audio = audio + config["default_volume"]
                
                # 特殊处理背景音乐：添加淡入淡出
                if track_type == "background_music":
                    audio = audio.fade_in(3000).fade_out(2000)  # 3秒淡入，2秒淡出
                
                audio_segments.append(audio)
        
        # 混合所有音轨
        if audio_segments:
            mixed = audio_segments[0]
            for audio in audio_segments[1:]:
                mixed = mixed.overlay(audio)
            
            # 导出最终音频
            mixed.export(output_path, format="wav")
            return output_path
        
        return None
```

## 🚀 部署步骤

### 1. 环境准备
```bash
# 1. 下载SongGeneration模型权重
cd AI-Sound/MegaTTS/
git clone https://github.com/tencent-ailab/SongGeneration.git
cd SongGeneration

# 2. 下载模型文件（从HuggingFace）
huggingface-cli download tencent/SongGeneration --cache-dir ./ckpt

# 3. 安装依赖
pip install -r requirements.txt
pip install https://github.com/Dao-AILab/flash-attention/releases/download/v2.6.3/flash_attn-2.6.3+cu118torch2.2cxx11abiFALSE-cp310-cp310-linux_x86_64.whl
```

### 2. Docker部署（推荐）
```bash
# 1. 拉取预构建镜像
docker pull juhayna/song-generation-levo:hf0613

# 2. 更新docker-compose.yml
vim docker-compose.yml  # 添加songgeneration服务

# 3. 启动所有服务
docker-compose up -d
```

### 3. 测试部署
```bash
# 测试SongGeneration服务
curl -X POST http://localhost:7862/generate \
  -H "Content-Type: application/json" \
  -d '{
    "lyrics": "[intro-short] ; [verse] Test music generation ; [outro-short]",
    "descriptions": "acoustic, peaceful, guitar, the bpm is 90",
    "duration": 30
  }'
```

## 📊 性能优化

### 显存管理策略
```python
# 显存优化配置
MEMORY_CONFIG = {
    "use_low_memory_mode": True,  # 启用低显存模式
    "max_concurrent_generation": 1,  # 限制并发生成数
    "gpu_memory_fraction": 0.8,  # 限制GPU显存使用比例
    "enable_mixed_precision": True  # 启用混合精度
}
```

### 缓存策略
```python
# 音乐生成缓存
class MusicCache:
    def __init__(self):
        self.cache = {}
        
    def get_cache_key(self, scene_type, duration):
        return f"{scene_type}_{duration}"
        
    def get_cached_music(self, scene_type, duration):
        key = self.get_cache_key(scene_type, duration)
        return self.cache.get(key)
        
    def cache_music(self, scene_type, duration, audio_path):
        key = self.get_cache_key(scene_type, duration)
        self.cache[key] = audio_path
```

## ⚠️ 注意事项

### 硬件要求
- **GPU**：NVIDIA GPU with CUDA>=11.8
- **显存**：推荐≥30GB（低显存模式可运行在<30GB）
- **内存**：推荐≥32GB RAM
- **存储**：模型权重约10-15GB，建议预留50GB存储空间

### 兼容性
- 与现有TTS3、TangoFlux服务完全兼容
- 支持现有的Docker部署环境
- 可独立启停，不影响其他服务

### 监控指标
- GPU显存使用率
- 音乐生成成功率
- 平均生成时间
- 服务健康状态

---

**设计完成时间**：2024年1月  
**文档版本**：v2.0 (本地部署版)  
**负责团队**：AI-Sound开发团队
