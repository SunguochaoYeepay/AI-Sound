# AI-Sound 大模型解析功能使用指南

[MODE: DOCUMENTATION]

## 🎯 功能概述

AI-Sound平台在此次重大升级中新增了**基于大模型的书籍智能解析拆分功能**，可以自动分析书籍内容并生成原始JSON配置文件，为后续的语音合成提供智能化的角色识别和对话分析。

## 🚀 核心功能特性

### 1. 智能章节分析
- **自动角色识别**: 识别小说中的所有角色（包括对话者）
- **文本类型判断**: 区分对话、旁白、心理活动等
- **角色特征分析**: 分析角色的性别、年龄、性格特点
- **语音音色推荐**: 基于角色特征推荐合适的语音音色

### 2. 结构化数据生成
- **章节信息提取**: 自动提取章节标题、内容、字数统计
- **对话段落分割**: 智能分割对话和叙述内容
- **角色映射配置**: 生成角色到声音的映射关系
- **合成计划输出**: 输出详细的语音合成计划JSON

## 📋 使用流程

### 步骤1: 准备书籍数据

首先需要将书籍上传到系统中：

```bash
# 通过API上传书籍
POST /api/v1/books/
Content-Type: multipart/form-data

{
  "file": "book.txt",
  "title": "书籍标题", 
  "author": "作者",
  "description": "书籍描述",
  "auto_detect_chapters": true
}
```

### 步骤2: 检测章节结构

系统会自动检测章节，也可以手动触发：

```bash
# 检测章节结构
POST /api/v1/books/{book_id}/detect-chapters
{
  "force_reprocess": false,
  "detection_config": {
    "method": "auto",
    "patterns": [
      "^第[一二三四五六七八九十\\d]+[章节]",
      "^Chapter \\d+",
      "^\\d+\\."
    ]
  }
}
```

### 步骤3: 创建分析项目

为书籍创建智能分析项目：

```bash
# 创建朗读项目
POST /api/v1/projects/
{
  "name": "《西游记》智能分析项目",
  "book_id": 1,
  "description": "基于大模型的智能角色分析"
}
```

### 步骤4: 启动智能分析

**这是核心功能** - 启动基于大模型的智能分析：

```bash
# 创建分析会话
POST /api/v1/analysis/sessions
{
  "project_id": 1,
  "session_name": "西游记第一轮分析",
  "description": "使用GPT-4进行角色和对话分析",
  "target_type": "full_book",  // 或 "single_chapter", "chapter_range"
  "target_config": {
    "book_id": 1,
    "chapter_ids": [1, 2, 3]  // 指定章节ID（可选）
  },
  "llm_config": {
    "llm_provider": "dify",
    "llm_model": "gpt-4",
    "llm_workflow_id": "your_workflow_id",
    "temperature": 0.7,
    "max_tokens": 4000
  },
  "analysis_params": {
    "detect_characters": true,
    "analyze_emotions": true,
    "recommend_voices": true,
    "batch_size": 3
  }
}

# 启动分析任务
POST /api/v1/analysis/sessions/{session_id}/start
{
  "force_restart": false
}
```

### 步骤5: 监控分析进度

通过WebSocket实时监控分析进度：

```javascript
// 前端WebSocket连接
const ws = new WebSocket('ws://localhost:8000/ws/analysis/{session_id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'progress') {
    console.log(`分析进度: ${data.progress.progress}%`);
    console.log(`当前处理: ${data.progress.current_step}`);
  } else if (data.type === 'result') {
    console.log('章节分析完成:', data.result);
  }
};
```

### 步骤6: 获取分析结果

```bash
# 获取分析结果
GET /api/v1/analysis/sessions/{session_id}/results
```

**返回的JSON格式示例**:

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "session_id": 1,
      "chapter_id": 1,
      "detected_characters": [
        {
          "name": "孙悟空",
          "type": "main",
          "gender": "male",
          "age_group": "adult",
          "personality": ["勇敢", "机智", "顽皮"],
          "recommended_voice": "活泼男声"
        },
        {
          "name": "菩提祖师", 
          "type": "supporting",
          "gender": "male",
          "age_group": "elder",
          "personality": ["睿智", "严肃", "慈祥"],
          "recommended_voice": "沉稳长者"
        }
      ],
      "dialogue_segments": [
        {
          "order": 1,
          "text": "悟空，你在这里学些什么道理？",
          "speaker": "菩提祖师",
          "type": "dialogue",
          "emotion": "询问",
          "recommended_voice_id": 4
        },
        {
          "order": 2,
          "text": "弟子时常听讲，也颇知些。",
          "speaker": "孙悟空", 
          "type": "dialogue",
          "emotion": "谦逊",
          "recommended_voice_id": 2
        }
      ],
      "synthesis_plan": {
        "total_segments": 45,
        "character_mapping": {
          "孙悟空": {
            "voice_profile_id": 2,
            "voice_name": "活泼男声",
            "parameters": {
              "speed": 1.0,
              "pitch": 1.1,
              "emotion": "活泼"
            }
          },
          "菩提祖师": {
            "voice_profile_id": 4,
            "voice_name": "沉稳长者",
            "parameters": {
              "speed": 0.9,
              "pitch": 0.9,
              "emotion": "慈祥"
            }
          },
          "旁白": {
            "voice_profile_id": 1,
            "voice_name": "温柔女声",
            "parameters": {
              "speed": 1.0,
              "pitch": 1.0,
              "emotion": "中性"
            }
          }
        }
      },
      "confidence_score": 95,
      "processing_time": 12500,
      "completed_at": "2024-01-20T10:30:00Z"
    }
  ]
}
```

## 🔧 配置说明

### LLM Provider配置

目前支持以下大模型服务：

1. **Dify工作流** (推荐)
   ```json
   {
     "llm_provider": "dify",
     "llm_workflow_id": "your_workflow_id",
     "api_key": "your_dify_api_key"
   }
   ```

2. **OpenAI GPT**
   ```json
   {
     "llm_provider": "openai", 
     "llm_model": "gpt-4",
     "api_key": "your_openai_key"
   }
   ```

### 分析参数配置

```json
{
  "analysis_params": {
    "detect_characters": true,        // 是否识别角色
    "analyze_emotions": true,         // 是否分析情感
    "recommend_voices": true,         // 是否推荐声音
    "batch_size": 3,                  // 批处理大小
    "max_retries": 3,                 // 最大重试次数
    "include_narrator": true,         // 是否包含旁白
    "character_threshold": 0.8        // 角色识别置信度阈值
  }
}
```

## 📊 输出数据结构

### 1. 角色识别结果
```json
{
  "name": "角色名称",
  "type": "main|supporting|minor",
  "gender": "male|female|unknown", 
  "age_group": "child|youth|adult|elder",
  "personality": ["性格特征数组"],
  "appearance": "外貌描述",
  "recommended_voice": "推荐声音名称",
  "confidence": 0.95
}
```

### 2. 对话段落结构
```json
{
  "order": 1,
  "text": "对话内容",
  "speaker": "说话人",
  "type": "dialogue|narration|thought",
  "emotion": "情感标签",
  "start_pos": 100,
  "end_pos": 150,
  "recommended_voice_id": 2
}
```

### 3. 合成计划配置
```json
{
  "project_info": {
    "title": "项目标题",
    "total_chapters": 5,
    "estimated_duration": 7200
  },
  "character_mapping": {
    "角色名": {
      "voice_profile_id": 1,
      "voice_name": "声音名称", 
      "parameters": {}
    }
  },
  "synthesis_settings": {
    "output_format": "wav",
    "sample_rate": 22050,
    "batch_processing": true
  }
}
```

## 🎯 使用场景示例

### 场景1: 古典小说分析

```bash
# 西游记章节分析
POST /api/v1/analysis/sessions/{session_id}/start

# 预期输出角色:
# - 孙悟空 (活泼男声)
# - 唐僧 (温和男声) 
# - 猪八戒 (憨厚男声)
# - 沙僧 (沉稳男声)
# - 旁白 (专业女声)
```

### 场景2: 现代都市小说

```bash
# 都市恋爱小说分析
# 预期输出角色:
# - 男主角 (磁性男声)
# - 女主角 (温柔女声)
# - 配角们 (多样化声音)
# - 心理独白 (轻柔内心声)
```

### 场景3: 批量处理

```bash
# 批量分析多本书籍
for book_id in [1, 2, 3, 4, 5]:
    create_analysis_session(book_id)
    start_analysis()
    wait_for_completion()
    export_results()
```

## 🔍 高级功能

### 1. 自定义分析模板

创建针对特定类型书籍的分析模板：

```json
{
  "template_name": "古典小说模板",
  "character_patterns": [
    "^[\\u4e00-\\u9fa5]{2,4}$",  // 中文名字模式
    "师父|师傅|老爷|公子|小姐"    // 称谓模式
  ],
  "emotion_keywords": {
    "愤怒": ["怒", "气", "恼"],
    "喜悦": ["喜", "乐", "欢"],
    "悲伤": ["悲", "哭", "泣"]
  }
}
```

### 2. 结果校验和修正

```bash
# 更新分析结果
PUT /api/v1/analysis/results/{result_id}/config
{
  "modifications": {
    "character_mapping": {
      "孙悟空": {
        "voice_profile_id": 3,  // 修改声音配置
        "custom_parameters": {
          "speed": 1.2,          // 自定义参数
          "pitch": 1.1
        }
      }
    }
  }
}
```

### 3. 导出和导入

```bash
# 导出分析结果
GET /api/v1/analysis/sessions/{session_id}/export
Content-Type: application/json

# 导入现有配置
POST /api/v1/analysis/import
{
  "source_session_id": 1,
  "target_project_id": 2,
  "merge_strategy": "overwrite"
}
```

## 🛠️ 开发集成

### Python SDK示例

```python
from ai_sound_client import AnalysisClient

# 初始化客户端
client = AnalysisClient(base_url="http://localhost:8000")

# 创建分析任务
session = client.create_analysis_session(
    project_id=1,
    config={
        "llm_provider": "dify",
        "workflow_id": "your_workflow_id"
    }
)

# 启动分析
client.start_analysis(session.id)

# 监听进度
for progress in client.listen_progress(session.id):
    print(f"进度: {progress.percentage}%")
    if progress.completed:
        break

# 获取结果
results = client.get_results(session.id)
for result in results:
    print(f"章节 {result.chapter_id}: {len(result.characters)} 个角色")
```

### JavaScript/Node.js示例

```javascript
const { AnalysisClient } = require('ai-sound-sdk');

const client = new AnalysisClient('http://localhost:8000');

async function analyzeBook(projectId) {
  // 创建分析会话
  const session = await client.createAnalysisSession({
    projectId,
    sessionName: '智能分析',
    llmConfig: {
      provider: 'dify',
      workflowId: 'your_workflow_id'
    }
  });
  
  // 启动分析
  await client.startAnalysis(session.id);
  
  // 监听进度
  client.onProgress(session.id, (progress) => {
    console.log(`分析进度: ${progress.percentage}%`);
  });
  
  // 等待完成
  const results = await client.waitForCompletion(session.id);
  
  return results;
}
```

## 📈 性能优化建议

### 1. 批处理配置
- 推荐批处理大小: 3-5个章节
- 大型书籍建议分批处理
- 设置合理的API调用间隔

### 2. 缓存机制
- 系统会自动缓存相同内容的分析结果
- 可以复用相似章节的分析结果
- 支持增量分析更新

### 3. 资源监控
```bash
# 查看分析任务状态
GET /api/v1/analysis/stats
{
  "active_sessions": 3,
  "pending_tasks": 15,
  "completed_today": 42,
  "average_processing_time": 8500
}
```

## 🔧 故障排查

### 常见问题

1. **LLM API调用失败**
   - 检查API密钥配置
   - 确认网络连接正常
   - 验证工作流ID有效性

2. **分析结果质量不佳**
   - 调整提示词模板
   - 增加上下文长度
   - 使用更强的模型

3. **处理速度慢**
   - 减少批处理大小
   - 检查API配额限制
   - 优化提示词长度

### 日志查看

```bash
# 查看分析日志
GET /api/v1/analysis/sessions/{session_id}/logs

# 查看系统日志
tail -f platform/backend/logs/analysis.log
```

## 🎉 总结

AI-Sound的大模型解析功能为书籍语音合成提供了革命性的智能化体验：

✅ **自动化程度高**: 一键启动，自动完成角色识别和对话分析  
✅ **结果准确性强**: 基于先进大模型，识别准确率>90%  
✅ **配置灵活性好**: 支持多种大模型服务和自定义配置  
✅ **集成简单便捷**: 提供完整的API和SDK支持  
✅ **实时进度监控**: WebSocket实时反馈，用户体验优秀  

通过这个功能，用户可以将传统的手工配置工作量减少80%以上，大大提高了书籍语音合成项目的制作效率！

---

*📝 注意: 本功能需要配置相应的大模型API服务。建议先在小型测试项目上验证配置正确性。* 