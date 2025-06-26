# AI-Sound Platform API 文档

## 📡 概述

AI-Sound Platform 提供RESTful API接口，支持语音克隆、多角色朗读、音频管理等功能。

**Base URL**: `http://localhost/api`  
**API版本**: v1  
**认证方式**: Bearer Token (可选)  
**数据格式**: JSON  

## 🔗 交互式文档

访问 [http://localhost/docs](http://localhost/docs) 查看完整的交互式API文档（Swagger UI）。

## 🔧 核心接口

### 1. 语音克隆测试

#### POST `/voice-clone/synthesize`

使用上传的音频样本进行语音克隆合成。

**请求体**:
```json
{
  "text": "要合成的文本内容",
  "audio_file": "base64编码的音频文件",
  "settings": {
    "speed": 1.0,
    "pitch": 1.0,
    "emotion": "neutral"
  }
}
```

**响应**:
```json
{
  "success": true,
  "audio_url": "/audio/generated/output_123456.wav",
  "duration": 5.2,
  "file_size": 1024000,
  "created_at": "2024-01-01T12:00:00Z"
}
```

**示例**:
```bash
curl -X POST "http://localhost/api/voice-clone/synthesize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，这是一个语音克隆测试。",
    "audio_file": "UklGRn...(base64)",
    "settings": {
      "speed": 1.0,
      "pitch": 1.0
    }
  }'
```

### 2. 多角色朗读

#### GET `/novel-reader/projects`

获取所有朗读项目列表。

**查询参数**:
- `page`: 页码 (默认: 1)
- `limit`: 每页数量 (默认: 10)
- `status`: 项目状态 (可选: pending, processing, completed, failed)

**响应**:
```json
{
  "projects": [
    {
      "id": 1,
      "name": "三体小说朗读",
      "status": "completed",
      "total_chapters": 10,
      "completed_chapters": 10,
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T15:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 10
}
```

#### POST `/novel-reader/projects`

创建新的朗读项目。

**请求体**:
```json
{
  "name": "项目名称",
  "content": "小说全文内容",
  "settings": {
    "auto_split": true,
    "chapter_delimiter": "第.*章",
    "character_voices": {
      "叶文洁": "voice_001",
      "罗辑": "voice_002"
    }
  }
}
```

**响应**:
```json
{
  "id": 1,
  "name": "项目名称",
  "status": "pending",
  "chapters": [
    {
      "id": 1,
      "title": "第一章",
      "content": "章节内容...",
      "characters": ["叶文洁", "旁白"]
    }
  ]
}
```

#### POST `/novel-reader/projects/{project_id}/generate`

开始生成项目音频。

**路径参数**:
- `project_id`: 项目ID

**响应**:
```json
{
  "success": true,
  "message": "音频生成已开始",
  "estimated_time": 300
}
```

#### GET `/novel-reader/projects/{project_id}/progress`

获取项目生成进度。

**响应**:
```json
{
  "project_id": 1,
  "status": "processing",
  "progress": 60,
  "current_chapter": 6,
  "total_chapters": 10,
  "estimated_remaining_time": 120
}
```

### 3. 音频资源库

#### GET `/audio-library/files`

获取音频文件列表。

**查询参数**:
- `page`: 页码
- `limit`: 每页数量
- `project_id`: 项目ID筛选
- `type`: 文件类型 (voice_clone, novel_reader)
- `search`: 搜索关键词

**响应**:
```json
{
  "files": [
    {
      "id": 1,
      "filename": "chapter_1_voice_001.wav",
      "original_name": "第一章_叶文洁.wav",
      "url": "/audio/novel_reader/project_1/chapter_1_voice_001.wav",
      "size": 2048000,
      "duration": 120.5,
      "type": "novel_reader",
      "project_id": 1,
      "created_at": "2024-01-01T12:00:00Z",
      "is_favorite": false
    }
  ],
  "total": 50,
  "page": 1,
  "limit": 20
}
```

#### DELETE `/audio-library/files/{file_id}`

删除音频文件。

**响应**:
```json
{
  "success": true,
  "message": "文件已删除"
}
```

#### POST `/audio-library/files/{file_id}/favorite`

标记/取消收藏音频文件。

**请求体**:
```json
{
  "is_favorite": true
}
```

#### GET `/audio-library/stats`

获取音频库统计信息。

**响应**:
```json
{
  "total_files": 150,
  "total_size": 512000000,
  "total_duration": 7200,
  "by_type": {
    "voice_clone": 50,
    "novel_reader": 100
  },
  "by_project": {
    "1": 30,
    "2": 20
  }
}
```

### 4. 声音库管理

#### GET `/characters/`

获取声音配置列表。

**响应**:
```json
{
  "characters": [
    {
      "id": "voice_001",
      "name": "温柔女声",
      "gender": "female",
      "age_range": "young_adult",
      "tags": ["温柔", "清新"],
      "quality_score": 4.5,
      "usage_count": 25,
      "created_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

#### POST `/characters/`

创建新的声音配置。

**请求体**:
```json
{
  "name": "声音名称",
  "gender": "female",
  "age_range": "adult",
  "tags": ["标签1", "标签2"],
  "audio_sample": "base64编码的音频样本",
  "description": "声音描述"
}
```

#### GET `/characters/{character_id}`

获取特定声音配置详情。

#### PUT `/characters/{character_id}`

更新声音配置。

#### DELETE `/characters/{character_id}`

删除声音配置。

### 5. 系统接口

#### GET `/health`

健康检查接口。

**响应**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-01T12:00:00Z",
  "services": {
    "database": "healthy",
    "megatts3": "healthy",
    "redis": "healthy"
  }
}
```

#### GET `/system/stats`

系统统计信息。

**响应**:
```json
{
  "uptime": 86400,
  "memory_usage": {
    "used": 512000000,
    "total": 1073741824
  },
  "disk_usage": {
    "used": 1073741824,
    "total": 10737418240
  },
  "active_tasks": 3
}
```

## 🔐 认证授权

### Bearer Token认证

对于需要认证的接口，在请求头中包含Token：

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost/api/protected-endpoint"
```

### 获取Token

```bash
curl -X POST "http://localhost/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password"
  }'
```

**响应**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## 📊 错误处理

### 标准错误格式

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": {
      "field": "text",
      "issue": "文本内容不能为空"
    }
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "path": "/api/voice-clone/synthesize"
}
```

### 错误代码

| HTTP状态码 | 错误代码 | 描述 |
|------------|----------|------|
| 400 | VALIDATION_ERROR | 请求参数验证失败 |
| 401 | UNAUTHORIZED | 未授权访问 |
| 403 | FORBIDDEN | 权限不足 |
| 404 | NOT_FOUND | 资源不存在 |
| 409 | CONFLICT | 资源冲突 |
| 422 | UNPROCESSABLE_ENTITY | 业务逻辑错误 |
| 429 | RATE_LIMIT_EXCEEDED | 请求频率超限 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |
| 503 | SERVICE_UNAVAILABLE | 服务不可用 |

## 🚀 使用示例

### Python示例

```python
import requests
import base64

# 1. 语音克隆
def voice_clone(text, audio_file_path):
    with open(audio_file_path, 'rb') as f:
        audio_data = base64.b64encode(f.read()).decode()
    
    response = requests.post(
        'http://localhost/api/voice-clone/synthesize',
        json={
            'text': text,
            'audio_file': audio_data,
            'settings': {
                'speed': 1.0,
                'pitch': 1.0
            }
        }
    )
    
    return response.json()

# 2. 创建朗读项目
def create_project(name, content):
    response = requests.post(
        'http://localhost/api/novel-reader/projects',
        json={
            'name': name,
            'content': content,
            'settings': {
                'auto_split': True,
                'chapter_delimiter': '第.*章'
            }
        }
    )
    
    return response.json()

# 3. 获取音频文件列表
def get_audio_files(page=1, limit=20):
    response = requests.get(
        f'http://localhost/api/audio-library/files?page={page}&limit={limit}'
    )
    
    return response.json()
```

### JavaScript示例

```javascript
// 1. 语音克隆
async function voiceClone(text, audioFile) {
  const formData = new FormData();
  formData.append('text', text);
  formData.append('audio_file', audioFile);
  
  const response = await fetch('/api/voice-clone/synthesize', {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
}

// 2. 获取项目进度
async function getProjectProgress(projectId) {
  const response = await fetch(`/api/novel-reader/projects/${projectId}/progress`);
  return await response.json();
}

// 3. WebSocket实时进度监听
const ws = new WebSocket('ws://localhost/api/ws/progress');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('进度更新:', data);
};
```

## 📈 性能优化

### 缓存策略

- 音频文件列表缓存5分钟
- 项目信息缓存10分钟
- 声音配置缓存30分钟

### 请求限制

- 单个IP每分钟最多100次请求
- 语音合成接口每分钟最多10次
- 文件上传最大100MB

### 分页建议

- 默认分页大小：20
- 最大分页大小：100
- 建议使用游标分页处理大量数据

## 🔄 版本变更

### v1.1.0 (计划中)
- 新增批量操作接口
- 支持WebSocket实时通信
- 增强错误处理机制

### v1.0.0 (当前版本)
- 基础功能完整实现
- RESTful API设计
- 完整的文档支持

---

**💡 提示**: 
- 所有时间戳使用ISO 8601格式
- 文件大小以字节为单位
- 音频时长以秒为单位
- 建议使用HTTPS访问生产环境API 