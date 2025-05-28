# AI-Sound API 参考文档

本文档详细描述了 AI-Sound 系统提供的 API 接口，包括请求参数、响应格式和使用示例。

## 基础信息

- **基础URL**: `http://your-server-address:9930`
- **认证方式**: API Key (在请求头中添加 `Authorization: Bearer YOUR_API_KEY`)
- **响应格式**: JSON
- **音频格式**: WAV, MP3

## API 端点

### 1. 文本转语音

将文本转换为语音，支持自定义声音和情感参数。

#### 请求

```http
POST /api/v1/synthesize
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "text": "要合成的文本",
  "voice_id": "voice_001",
  "emotion": {
    "type": "happy",
    "intensity": 0.8
  },
  "style": {
    "speed": 1.0,
    "pitch": 1.0
  },
  "engine_preference": "auto"  // 可选，默认为auto
}
```

#### 参数说明

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| text | string | 是 | 要合成的文本内容 |
| voice_id | string | 是 | 声音ID |
| emotion.type | string | 否 | 情感类型 (happy, sad, angry, neutral) |
| emotion.intensity | float | 否 | 情感强度 (0.0-1.0) |
| style.speed | float | 否 | 语速倍率 (0.5-2.0) |
| style.pitch | float | 否 | 音高倍率 (0.5-2.0) |
| engine_preference | string | 否 | 引擎偏好 (auto, megatts3, espnet) |

#### 响应

```json
{
  "status": "success",
  "audio_url": "http://your-server-address:9930/api/v1/audio/abc123",
  "audio_data": "base64_encoded_audio_data",  // 可选，仅当文本较短时返回
  "duration": 3.5,
  "format": "wav",
  "task_id": "task_123"  // 如果是异步任务
}
```

### 2. 批量文本合成

批量处理多段文本，适合处理章节或对话。

#### 请求

```http
POST /api/v1/batch_synthesize
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "tasks": [
    {
      "text": "文本1",
      "voice_id": "voice_001"
    },
    {
      "text": "文本2",
      "voice_id": "voice_002"
    }
  ],
  "common_settings": {
    "emotion": {
      "type": "neutral"
    }
  }
}
```

#### 响应

```json
{
  "status": "processing",
  "task_id": "batch_task_456",
  "estimated_completion": "2023-05-28T15:30:00Z",
  "progress": {
    "total": 2,
    "completed": 0,
    "percent": 0
  }
}
```

### 3. 任务状态查询

查询异步任务的处理状态。

#### 请求

```http
GET /api/v1/tasks/{task_id}
Authorization: Bearer YOUR_API_KEY
```

#### 响应

```json
{
  "status": "completed",  // processing, completed, failed
  "progress": {
    "total": 2,
    "completed": 2,
    "percent": 100
  },
  "results": [
    {
      "audio_url": "http://your-server-address:9930/api/v1/audio/def456",
      "duration": 2.3,
      "format": "wav"
    },
    {
      "audio_url": "http://your-server-address:9930/api/v1/audio/ghi789",
      "duration": 1.8,
      "format": "wav"
    }
  ],
  "error": null  // 仅当status为failed时返回错误信息
}
```

### 4. 获取可用音色

获取系统中所有可用的音色列表。

#### 请求

```http
GET /api/v1/voices
Authorization: Bearer YOUR_API_KEY
```

#### 响应

```json
{
  "voices": [
    {
      "id": "voice_001",
      "name": "女声1",
      "gender": "female",
      "age_group": "young",
      "description": "清新自然的年轻女声",
      "engine_support": ["megatts3", "espnet"],
      "tags": ["clear", "natural", "soft"],
      "preview_url": "http://your-server-address:9930/api/v1/voice_preview/voice_001"
    },
    {
      "id": "voice_002",
      "name": "男声1",
      "gender": "male",
      "age_group": "middle",
      "description": "稳重大气的中年男声",
      "engine_support": ["megatts3", "espnet"],
      "tags": ["deep", "stable", "clear"],
      "preview_url": "http://your-server-address:9930/api/v1/voice_preview/voice_002"
    }
  ]
}
```

### 5. 声纹特征提取

上传音频文件并提取声纹特征。

#### 请求

```http
POST /api/v1/voices/extract
Content-Type: multipart/form-data
Authorization: Bearer YOUR_API_KEY

audio_file: [音频文件二进制数据]
name: "新音色名称"
description: "音色描述"
tags: ["male", "young", "clear"]
```

#### 响应

```json
{
  "status": "success",
  "voice_id": "voice_003",
  "feature_quality": 0.92,
  "message": "声纹特征提取成功"
}
```

### 6. 健康检查

检查系统和引擎的健康状态。

#### 请求

```http
GET /api/v1/health
Authorization: Bearer YOUR_API_KEY
```

#### 响应

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "engines": {
    "megatts3": {
      "status": "healthy",
      "last_check": "2023-05-28T14:20:15Z"
    },
    "espnet": {
      "status": "healthy",
      "last_check": "2023-05-28T14:20:10Z"
    }
  },
  "system": {
    "cpu_usage": 23.5,
    "memory_usage": 45.2,
    "gpu_usage": 12.3
  }
}
```

## 错误处理

API 使用标准的 HTTP 状态码表示请求结果：

- **200 OK**: 请求成功
- **202 Accepted**: 请求已接受，正在异步处理
- **400 Bad Request**: 请求参数错误
- **401 Unauthorized**: 认证失败
- **404 Not Found**: 资源不存在
- **500 Internal Server Error**: 服务器内部错误

错误响应格式：

```json
{
  "status": "error",
  "code": "ERROR_CODE",
  "message": "错误描述信息",
  "details": {  // 可选
    "param": "参数名",
    "value": "无效的值"
  }
}
```

## 使用示例

### Python 示例

```python
import requests
import json
import base64

# 配置
api_key = "YOUR_API_KEY"
base_url = "http://your-server-address:9930"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# 文本转语音
def synthesize_text(text, voice_id="voice_001", emotion_type="neutral", emotion_intensity=0.5):
    url = f"{base_url}/api/v1/synthesize"
    payload = {
        "text": text,
        "voice_id": voice_id,
        "emotion": {
            "type": emotion_type,
            "intensity": emotion_intensity
        },
        "style": {
            "speed": 1.0,
            "pitch": 1.0
        }
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        result = response.json()
        # 保存音频文件
        if "audio_data" in result:
            audio_data = base64.b64decode(result["audio_data"])
            with open("output.wav", "wb") as f:
                f.write(audio_data)
            print(f"音频已保存到 output.wav，时长: {result['duration']}秒")
        else:
            print(f"音频URL: {result['audio_url']}")
        return result
    else:
        print(f"错误: {response.status_code}")
        print(response.text)
        return None

# 使用示例
synthesize_text("欢迎使用AI-Sound语音合成服务。", voice_id="voice_001", emotion_type="happy", emotion_intensity=0.8)
```

### cURL 示例

```bash
# 文本转语音
curl -X POST "http://your-server-address:9930/api/v1/synthesize" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "欢迎使用AI-Sound语音合成服务。",
       "voice_id": "voice_001",
       "emotion": {
         "type": "happy",
         "intensity": 0.8
       }
     }' \
     --output output.wav

# 获取可用音色
curl -X GET "http://your-server-address:9930/api/v1/voices" \
     -H "Authorization: Bearer YOUR_API_KEY"
```

## 限制说明

- 单次请求文本长度限制: 5000字符
- 批量请求最大任务数: 100
- 免费用户API调用频率限制: 100次/天
- 音频文件保存时间: 24小时后自动删除

## 更多资源

- [开发者指南](../development/developer_guide.md)
- [系统架构](../architecture/system_architecture.md)
- [技术细节](../architecture/technical_details.md)