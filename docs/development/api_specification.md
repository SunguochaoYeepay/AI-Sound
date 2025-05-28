# AI-Sound API 接口规范

## 一、API 概述

AI-Sound 系统提供了一组 RESTful API，用于管理和使用语音合成功能。所有 API 采用 JSON 格式进行数据交换，并遵循一致的请求和响应模式。

### 1.1 基础 URL

```
http://{host}:{port}/api
```

### 1.2 认证方式

目前系统用于个人使用，暂不实现认证机制。如需添加认证，可考虑使用 API Key 或 JWT 方式。

### 1.3 通用响应格式

成功响应：

```json
{
  "success": true,
  "message": "操作成功",
  "data": { ... }  // 操作结果数据
}
```

错误响应：

```json
{
  "success": false,
  "message": "错误描述",
  "error_code": "ERROR_CODE"
}
```

### 1.4 错误码

| 错误码 | 说明 |
|-------|------|
| `ENGINE_NOT_FOUND` | 引擎不存在 |
| `VOICE_NOT_FOUND` | 声音不存在 |
| `CHARACTER_NOT_FOUND` | 角色不存在 |
| `NOVEL_NOT_FOUND` | 小说不存在 |
| `INVALID_PARAMS` | 参数无效 |
| `ENGINE_ERROR` | 引擎执行错误 |
| `SERVER_ERROR` | 服务器内部错误 |

## 二、TTS 合成 API

### 2.1 文本合成

**请求**:

```
POST /tts
```

**请求体**:

```json
{
  "text": "要合成的文本内容",
  "voice_id": "voice1",
  "engine_id": "megatts3",  // 可选，默认自动选择
  "params": {  // 可选
    "speed": 1.0,
    "pitch": 0,
    "volume": 1.0,
    "emotion": "neutral"
  },
  "output_format": "wav"  // 可选，默认 wav
}
```

**响应**:

```json
{
  "success": true,
  "message": "合成成功",
  "data": {
    "audio_url": "/api/audio/1234567890.wav",
    "duration": 3.5,
    "engine_used": "megatts3"
  }
}
```

### 2.2 批量合成

**请求**:

```
POST /tts/batch
```

**请求体**:

```json
{
  "items": [
    {
      "id": "item1",
      "text": "第一段文本",
      "voice_id": "voice1"
    },
    {
      "id": "item2",
      "text": "第二段文本",
      "voice_id": "voice2"
    }
  ],
  "engine_id": "megatts3",  // 可选
  "params": { ... },  // 可选
  "output_format": "mp3"  // 可选
}
```

**响应**:

```json
{
  "success": true,
  "message": "批量合成任务已创建",
  "data": {
    "task_id": "task123",
    "total_items": 2,
    "estimated_time": 10  // 预估完成时间(秒)
  }
}
```

### 2.3 获取音频文件

**请求**:

```
GET /audio/{audio_id}.{format}
```

**响应**: 二进制音频数据，带有相应的 Content-Type

## 三、引擎管理 API

### 3.1 获取所有引擎

**请求**:

```
GET /engines
```

**响应**:

```json
{
  "success": true,
  "data": {
    "engines": [
      {
        "id": "megatts3",
        "name": "MegaTTS3 引擎",
        "version": "1.0.0",
        "status": "healthy"
      },
      {
        "id": "espnet",
        "name": "ESPnet TTS",
        "version": "2.0.0",
        "status": "healthy"
      }
    ]
  }
}
```

### 3.2 获取引擎详情

**请求**:

```
GET /engines/{engine_id}
```

**响应**:

```json
{
  "success": true,
  "data": {
    "id": "megatts3",
    "name": "MegaTTS3 引擎",
    "version": "1.0.0",
    "status": "healthy",
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
      // ... 其他参数
    ]
  }
}
```

### 3.3 获取引擎配置

**请求**:

```
GET /engines/{engine_id}/config
```

**响应**:

```json
{
  "success": true,
  "data": {
    "engine_id": "megatts3",
    "config": {
      "speed": 1.0,
      "pitch": 0.0,
      "volume": 1.0,
      "emotion": "neutral"
    }
  }
}
```

### 3.4 更新引擎配置

**请求**:

```
POST /engines/{engine_id}/config
```

**请求体**:

```json
{
  "speed": 1.2,
  "pitch": 2.0
}
```

**响应**:

```json
{
  "success": true,
  "message": "配置更新成功"
}
```

### 3.5 测试引擎参数

**请求**:

```
POST /engines/{engine_id}/test
```

**请求体**:

```json
{
  "text": "测试文本",
  "voice_id": "voice1",
  "params": {
    "speed": 1.2,
    "pitch": 2.0
  }
}
```

**响应**: 二进制音频数据

### 3.6 引擎健康状态

**请求**:

```
GET /engines/health
```

**响应**:

```json
{
  "success": true,
  "data": {
    "engines": [
      {
        "id": "megatts3",
        "status": "healthy",
        "last_check": "2025-05-28T14:06:35Z",
        "details": {
          "gpu_available": true,
          "memory_usage": "1.2GB/8GB",
          "response_time": 0.05
        }
      },
      {
        "id": "espnet",
        "status": "unhealthy",
        "last_check": "2025-05-28T14:06:35Z",
        "error": "服务不可用"
      }
    ]
  }
}
```

## 四、声音管理 API

### 4.1 获取所有声音

**请求**:

```
GET /voices?engine_id=megatts3
```

**响应**:

```json
{
  "success": true,
  "data": {
    "voices": [
      {
        "id": "voice1",
        "name": "女声1",
        "engine_id": "megatts3",
        "gender": "female",
        "language": "zh-CN",
        "description": "标准女声",
        "preview_url": "/api/voices/voice1/preview"
      },
      // ... 其他声音
    ]
  }
}
```

### 4.2 获取声音详情

**请求**:

```
GET /voices/{voice_id}
```

**响应**:

```json
{
  "success": true,
  "data": {
    "id": "voice1",
    "name": "女声1",
    "engine_id": "megatts3",
    "gender": "female",
    "language": "zh-CN",
    "description": "标准女声",
    "attributes": {
      "age_group": "young",
      "style": "natural"
    },
    "preview_url": "/api/voices/voice1/preview"
  }
}
```

### 4.3 上传自定义声音

**请求**:

```
POST /voices
```

**请求体**: Form Data (multipart/form-data)

| 字段 | 类型 | 说明 |
|-----|-----|-----|
| name | string | 声音名称 |
| engine_id | string | 引擎ID |
| gender | string | 性别(male/female) |
| description | string | 描述 |
| voice_file | file | 声音文件 |
| metadata | json | 声音元数据 |

**响应**:

```json
{
  "success": true,
  "message": "声音上传成功",
  "data": {
    "voice_id": "custom_voice1",
    "name": "自定义女声",
    "engine_id": "megatts3"
  }
}
```

### 4.4 更新声音信息

**请求**:

```
PUT /voices/{voice_id}
```

**请求体**:

```json
{
  "name": "更新后的名称",
  "description": "更新后的描述",
  "attributes": {
    "age_group": "middle",
    "style": "professional"
  }
}
```

**响应**:

```json
{
  "success": true,
  "message": "声音信息更新成功"
}
```

### 4.5 删除声音

**请求**:

```
DELETE /voices/{voice_id}
```

**响应**:

```json
{
  "success": true,
  "message": "声音删除成功"
}
```

### 4.6 获取声音预览

**请求**:

```
GET /voices/{voice_id}/preview
```

**响应**: 二进制音频数据

### 4.7 生成声音预览

**请求**:

```
POST /voices/{voice_id}/preview
```

**请求体**:

```json
{
  "text": "这是一段测试文本",
  "params": {
    "speed": 1.0,
    "pitch": 0.0
  }
}
```

**响应**: 二进制音频数据

## 五、角色管理 API

### 5.1 获取所有角色

**请求**:

```
GET /characters
```

**响应**:

```json
{
  "success": true,
  "data": {
    "characters": [
      {
        "id": "char1",
        "name": "张三",
        "voice_id": "voice1",
        "attributes": {
          "gender": "male",
          "age": "middle",
          "personality": "serious"
        }
      },
      // ... 其他角色
    ]
  }
}
```

### 5.2 获取角色详情

**请求**:

```
GET /characters/{character_id}
```

**响应**:

```json
{
  "success": true,
  "data": {
    "id": "char1",
    "name": "张三",
    "voice_id": "voice1",
    "attributes": {
      "gender": "male",
      "age": "middle",
      "personality": "serious"
    },
    "created_at": "2025-05-28T14:06:35Z",
    "voice": {
      "id": "voice1",
      "name": "男声1",
      "engine_id": "megatts3"
    }
  }
}
```

### 5.3 创建角色

**请求**:

```
POST /characters
```

**请求体**:

```json
{
  "name": "李四",
  "voice_id": "voice2",
  "attributes": {
    "gender": "male",
    "age": "young",
    "personality": "cheerful"
  }
}
```

**响应**:

```json
{
  "success": true,
  "message": "角色创建成功",
  "data": {
    "character_id": "char2",
    "name": "李四"
  }
}
```

### 5.4 更新角色

**请求**:

```
PUT /characters/{character_id}
```

**请求体**:

```json
{
  "name": "李四(更新)",
  "voice_id": "voice3",
  "attributes": {
    "personality": "calm"
  }
}
```

**响应**:

```json
{
  "success": true,
  "message": "角色更新成功"
}
```

### 5.5 删除角色

**请求**:

```
DELETE /characters/{character_id}
```

**响应**:

```json
{
  "success": true,
  "message": "角色删除成功"
}
```

### 5.6 角色语音测试

**请求**:

```
POST /characters/{character_id}/speak
```

**请求体**:

```json
{
  "text": "这是角色测试文本",
  "params": {  // 可选
    "speed": 1.1
  }
}
```

**响应**: 二进制音频数据

## 六、小说管理 API

### 6.1 获取小说列表

**请求**:

```
GET /novels
```

**响应**:

```json
{
  "success": true,
  "data": {
    "novels": [
      {
        "id": "novel1",
        "title": "小说标题",
        "author": "作者",
        "word_count": 5000,
        "status": "imported",
        "created_at": "2025-05-28T14:06:35Z"
      },
      // ... 其他小说
    ]
  }
}
```

### 6.2 获取小说详情

**请求**:

```
GET /novels/{novel_id}
```

**响应**:

```json
{
  "success": true,
  "data": {
    "id": "novel1",
    "title": "小说标题",
    "author": "作者",
    "word_count": 5000,
    "chapter_count": 10,
    "status": "imported",
    "created_at": "2025-05-28T14:06:35Z",
    "updated_at": "2025-05-28T14:06:35Z",
    "chapters": [
      {
        "id": "chapter1",
        "title": "第一章",
        "word_count": 500,
        "status": "pending"
      },
      // ... 其他章节
    ]
  }
}
```

### 6.3 上传小说

**请求**:

```
POST /novels
```

**请求体**: Form Data (multipart/form-data)

| 字段 | 类型 | 说明 |
|-----|-----|-----|
| title | string | 小说标题 |
| author | string | 作者 |
| novel_file | file | 小说文件(txt) |
| metadata | json | 小说元数据 |

**响应**:

```json
{
  "success": true,
  "message": "小说上传成功",
  "data": {
    "novel_id": "novel2",
    "title": "上传的小说",
    "word_count": 8000,
    "chapter_count": 15
  }
}
```

### 6.4 删除小说

**请求**:

```
DELETE /novels/{novel_id}
```

**响应**:

```json
{
  "success": true,
  "message": "小说删除成功"
}
```

### 6.5 开始处理小说

**请求**:

```
POST /novels/{novel_id}/process
```

**请求体**:

```json
{
  "voice_mappings": {
    "narrator": "voice1",
    "character:张三": "voice2",
    "character:李四": "voice3"
  },
  "engine_id": "megatts3",  // 可选
  "engine_params": {  // 可选
    "speed": 1.0,
    "pitch": 0.0
  },
  "output_format": "mp3",
  "split_by": "chapter",  // chapter 或 paragraph
  "processing_mode": "sequential"  // sequential 或 parallel
}
```

**响应**:

```json
{
  "success": true,
  "message": "小说处理任务已创建",
  "data": {
    "task_id": "task123",
    "novel_id": "novel1",
    "estimated_time": 600  // 预估完成时间(秒)
  }
}
```

### 6.6 获取章节内容

**请求**:

```
GET /novels/{novel_id}/chapters/{chapter_id}
```

**响应**:

```json
{
  "success": true,
  "data": {
    "id": "chapter1",
    "title": "第一章",
    "novel_id": "novel1",
    "content": "章节内容...",
    "word_count": 500,
    "status": "pending"
  }
}
```

### 6.7 获取章节音频

**请求**:

```
GET /novels/{novel_id}/chapters/{chapter_id}/audio
```

**响应**: 二进制音频数据，或音频文件下载链接

## 七、任务管理 API

### 7.1 获取任务列表

**请求**:

```
GET /tasks?status=processing&type=novel_processing
```

**响应**:

```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "id": "task123",
        "type": "novel_processing",
        "status": "processing",
        "progress": 0.45,
        "created_at": "2025-05-28T14:06:35Z",
        "updated_at": "2025-05-28T14:10:35Z",
        "resource_id": "novel1",
        "resource_type": "novel"
      },
      // ... 其他任务
    ]
  }
}
```

### 7.2 获取任务详情

**请求**:

```
GET /tasks/{task_id}
```

**响应**:

```json
{
  "success": true,
  "data": {
    "id": "task123",
    "type": "novel_processing",
    "status": "processing",
    "progress": 0.45,
    "created_at": "2025-05-28T14:06:35Z",
    "updated_at": "2025-05-28T14:10:35Z",
    "resource_id": "novel1",
    "resource_type": "novel",
    "details": {
      "total_chapters": 10,
      "completed_chapters": 4,
      "current_chapter": "第五章",
      "estimated_completion": "2025-05-28T15:06:35Z"
    }
  }
}
```

### 7.3 取消任务

**请求**:

```
POST /tasks/{task_id}/cancel
```

**响应**:

```json
{
  "success": true,
  "message": "任务已取消"
}
```

### 7.4 删除任务

**请求**:

```
DELETE /tasks/{task_id}
```

**响应**:

```json
{
  "success": true,
  "message": "任务已删除"
}
```

## 八、系统设置 API

### 8.1 获取系统设置

**请求**:

```
GET /settings
```

**响应**:

```json
{
  "success": true,
  "data": {
    "output_directory": "/data/outputs",
    "default_engine": "megatts3",
    "default_voice": "voice1",
    "default_format": "mp3",
    "log_level": "info",
    "auto_clean_temp": true,
    "temp_files_max_age": 7,
    "max_concurrent_tasks": 2
  }
}
```

### 8.2 更新系统设置

**请求**:

```
POST /settings
```

**请求体**:

```json
{
  "default_engine": "espnet",
  "default_format": "wav",
  "max_concurrent_tasks": 3
}
```

**响应**:

```json
{
  "success": true,
  "message": "系统设置已更新"
}
```

## 九、状态码说明

| 状态码 | 说明 |
|-------|------|
| 200 | 请求成功 |
| 201 | 资源创建成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 422 | 参数验证失败 |
| 500 | 服务器内部错误 |

## 十、WebSocket API

除了RESTful API外，系统还提供WebSocket接口用于实时通知和任务进度监控。

### 10.1 连接WebSocket

```
ws://{host}:{port}/api/ws
```

### 10.2 事件类型

| 事件类型 | 说明 |
|---------|------|
| `task_progress` | 任务进度更新 |
| `task_complete` | 任务完成 |
| `task_error` | 任务出错 |
| `engine_status` | 引擎状态变化 |
| `system_notification` | 系统通知 |

### 10.3 消息格式

```json
{
  "event": "task_progress",
  "data": {
    "task_id": "task123",
    "progress": 0.75,
    "details": {
      "current_chapter": "第八章",
      "speed": "2.5x"
    }
  }
}
```