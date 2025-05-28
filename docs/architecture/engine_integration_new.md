# AI-Sound 引擎集成设计 (重构版)

## 一、引擎架构概述

### 1.1 引擎集成模型

AI-Sound 重构后的引擎集成架构采用独立服务模式，每个TTS引擎作为独立的微服务部署，通过统一的适配层与API服务通信。

```
┌─────────────────────────────────────────────────┐
│                API 服务层                        │
└───────────────────────┬─────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│                引擎适配层                        │
└──────┬─────────────┬────────────────┬───────────┘
       │             │                │
       ▼             ▼                ▼
┌──────────┐  ┌────────────┐  ┌────────────────┐
│MegaTTS3  │  │ESPnet      │  │Bert-VITS2      │
│服务容器   │  │服务容器    │  │服务容器        │
└──────────┘  └────────────┘  └────────────────┘
```

### 1.2 架构优势

1. **松耦合**：引擎与API服务解耦，可独立升级和扩展
2. **统一接口**：通过适配层提供统一的接口，简化集成
3. **扩展性**：轻松添加新引擎，无需修改核心代码
4. **资源隔离**：每个引擎在独立容器中运行，避免资源冲突
5. **按需部署**：可以根据需求选择性部署引擎

## 二、引擎适配器设计

### 2.1 统一适配器接口

所有引擎适配器必须实现以下统一接口：

```python
class TTSEngineAdapter:
    """TTS引擎统一适配器接口"""
    
    async def get_capabilities(self) -> dict:
        """
        获取引擎能力和参数规范
        
        返回:
            dict: 包含引擎ID、名称、版本、能力和参数定义
        """
        pass
    
    async def get_voices(self) -> list:
        """
        获取引擎支持的所有声音
        
        返回:
            list: 声音列表，每个声音包含id、名称、性别等信息
        """
        pass
    
    async def synthesize(
        self, 
        text: str, 
        voice_id: str, 
        params: dict = None
    ) -> bytes:
        """
        合成语音
        
        参数:
            text: 要合成的文本
            voice_id: 声音ID
            params: 合成参数
            
        返回:
            bytes: 音频数据
        """
        pass
    
    async def health_check(self) -> dict:
        """
        健康检查
        
        返回:
            dict: 健康状态信息
        """
        pass
    
    async def test_params(
        self, 
        text: str, 
        voice_id: str, 
        params: dict
    ) -> bytes:
        """
        测试参数效果
        
        参数:
            text: 测试文本
            voice_id: 声音ID
            params: 测试参数
            
        返回:
            bytes: 测试音频数据
        """
        pass
```

### 2.2 能力发现机制

引擎通过能力发现机制向API服务暴露其功能和参数规范：

```json
{
  "engine_id": "megatts3",
  "name": "MegaTTS3 引擎",
  "version": "1.0.0",
  "capabilities": {
    "supports_emotion": true,
    "supports_speed": true,
    "supports_pitch": true,
    "supports_volume": true,
    "max_text_length": 5000,
    "supported_languages": ["zh-CN"],
    "supported_audio_formats": ["wav", "mp3"]
  },
  "params": [
    {
      "name": "speed",
      "type": "float",
      "default": 1.0,
      "min": 0.5,
      "max": 2.0,
      "step": 0.1,
      "label": "语速",
      "description": "语音播放速度"
    },
    {
      "name": "pitch",
      "type": "float",
      "default": 0.0,
      "min": -12.0,
      "max": 12.0,
      "step": 1.0,
      "label": "音调",
      "description": "语音音调调整"
    },
    {
      "name": "volume",
      "type": "float",
      "default": 1.0,
      "min": 0.1,
      "max": 2.0,
      "step": 0.1,
      "label": "音量",
      "description": "语音音量调整"
    },
    {
      "name": "emotion",
      "type": "select",
      "default": "neutral",
      "options": [
        {"value": "neutral", "label": "平静"},
        {"value": "happy", "label": "开心"},
        {"value": "sad", "label": "悲伤"},
        {"value": "angry", "label": "生气"}
      ],
      "label": "情感",
      "description": "语音情感风格"
    }
  ]
}
```

### 2.3 参数映射机制

由于不同引擎的参数名称和取值范围可能不同，适配器负责进行参数映射：

```python
class MegaTTS3Adapter(TTSEngineAdapter):
    def __init__(self, service_url: str):
        self.service_url = service_url
        self.client = httpx.AsyncClient(base_url=service_url, timeout=30.0)
    
    async def synthesize(self, text: str, voice_id: str, params: dict = None) -> bytes:
        if params is None:
            params = {}
        
        # 参数映射
        mapped_params = {
            "text": text,
            "voice_id": voice_id,
            "speed_scale": params.get("speed", 1.0),
            "pitch_scale": params.get("pitch", 0.0) / 12.0 + 1.0,  # 转换为MegaTTS3的pitch scale
            "volume_scale": params.get("volume", 1.0),
            "emotion_type": params.get("emotion", "neutral")
        }
        
        try:
            response = await self.client.post("/api/synthesize", json=mapped_params)
            response.raise_for_status()
            return response.content
        except Exception as e:
            raise TTSEngineError(f"MegaTTS3合成失败: {str(e)}")
```

## 三、引擎服务设计

### 3.1 MegaTTS3引擎服务

MegaTTS3作为一个高性能TTS引擎，将被封装为独立服务：

```
┌─────────────────────────────────────────────────┐
│                MegaTTS3 服务                     │
│                                                 │
│  ┌─────────────┐       ┌──────────────────┐     │
│  │ FastAPI API │◄─────►│ MegaTTS3核心引擎 │     │
│  └─────────────┘       └──────────────────┘     │
│         │                       │               │
│         │                       │               │
│  ┌─────────────┐       ┌──────────────────┐     │
│  │ 声音资源    │◄─────►│ 音频处理模块     │     │
│  └─────────────┘       └──────────────────┘     │
│                                                 │
└─────────────────────────────────────────────────┘
```

#### 3.1.1 MegaTTS3 API规范

```
# 健康检查
GET /api/health
响应:
{
  "status": "ok",
  "version": "1.0.0",
  "gpu_available": true
}

# 获取能力
GET /api/capabilities
响应: {引擎能力JSON}

# 获取可用声音
GET /api/voices
响应:
{
  "voices": [
    {
      "id": "voice1",
      "name": "女声1",
      "gender": "female",
      "description": "标准女声",
      "preview_url": "/api/preview/voice1"
    },
    ...
  ]
}

# 合成语音
POST /api/synthesize
请求体:
{
  "text": "要合成的文本",
  "voice_id": "voice1",
  "speed_scale": 1.0,
  "pitch_scale": 1.0,
  "volume_scale": 1.0,
  "emotion_type": "neutral"
}
响应: 音频数据 (二进制)
```

### 3.2 ESPnet引擎服务

ESPnet服务封装了ESPnet TTS引擎，提供高质量语音合成：

```
┌─────────────────────────────────────────────────┐
│                ESPnet 服务                       │
│                                                 │
│  ┌─────────────┐       ┌──────────────────┐     │
│  │ FastAPI API │◄─────►│ ESPnet核心引擎   │     │
│  └─────────────┘       └──────────────────┘     │
│         │                       │               │
│         │                       │               │
│  ┌─────────────┐       ┌──────────────────┐     │
│  │ 模型资源    │◄─────►│ 声码器模块       │     │
│  └─────────────┘       └──────────────────┘     │
│                                                 │
└─────────────────────────────────────────────────┘
```

#### 3.2.1 ESPnet API规范

```
# 健康检查
GET /api/health
响应:
{
  "status": "ok",
  "version": "2.0.0",
  "gpu_available": true
}

# 获取能力
GET /api/capabilities
响应: {引擎能力JSON}

# 获取可用声音(说话人)
GET /api/speakers
响应:
{
  "speakers": [
    {
      "id": 0,
      "name": "说话人1",
      "gender": "female",
      "language": "zh-CN"
    },
    ...
  ]
}

# 合成语音
POST /api/tts
请求体:
{
  "text": "要合成的文本",
  "speaker_id": 0,
  "speed_factor": 1.0,
  "pitch_factor": 0.0,
  "energy_factor": 1.0
}
响应: 音频数据 (二进制)
```