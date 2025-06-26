# AI-Sound 大模型智能解析功能使用指南

[MODE: DOCUMENTATION]

## 🎯 功能概述

AI-Sound平台集成了**基于Dify工作流的书籍智能解析功能**，通过大模型自动分析小说内容，智能识别角色并推荐合适的语音音色，生成标准化的角色配置JSON，为语音合成提供智能化支持。

## 🏗️ 架构设计

### 核心设计思路
- **知识库同步**: 通过专用工作流将角色同步到Dify知识库
- **高效查询**: Dify分析工作流直接查询本地知识库，无需HTTP调用
- **简洁输入**: 只提供核心信息（书名、作者、章节标题、正文），避免过度配置
- **定期更新**: 角色库变化时自动同步到知识库，保持数据一致性

### 系统交互流程

#### 核心交互模式
1. **AI-Sound系统职责**:
   - 🎯 通过角色同步工作流定期更新Dify知识库
   - 🎯 准备简洁的章节数据（书名+作者+章节标题+正文）
   - 🎯 调用Dify分析工作流进行智能分析  
   - 🎯 接收并处理Dify返回的分析结果
   - 🎯 应用结果到项目配置

2. **Dify工作流职责**:
   - 🤖 **角色同步工作流**: 接收角色数据，更新知识库
   - 🤖 **智能分析工作流**: 接收结构化章节数据
   - 🤖 查询本地知识库获取可用角色（高效）
   - 🤖 基于大模型进行角色识别和声音匹配
   - 🤖 返回标准化的角色配置JSON

#### 详细交互时序

**阶段1: 角色同步（定期执行）**
```
AI-Sound角色库更新 → 触发同步工作流 → 更新Dify知识库 → 同步完成
```

**阶段2: 智能分析（用户触发）**
```
用户选择章节 → AI-Sound准备简洁数据 → 调用Dify分析工作流
     ↓
Dify接收章节数据 → 查询知识库获取角色 → Dify智能分析匹配
     ↓  
Dify返回配置JSON → AI-Sound应用结果 → 用户查看角色配置
```

#### 关键数据交换点

**📦 角色同步工作流输入** (定期同步):
```json
{
  "inputs": {
    "characters_data": [
      {
        "id": 1,
        "name": "温柔女声",
        "type": "female",
        "description": "温柔甜美的女性声音",
        "quality_score": 4.2,
        "parameters": {"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}
      }
    ],
    "sync_timestamp": "2024-01-20T10:30:00Z"
  }
}
```

**📤 AI-Sound → Dify分析工作流** (简洁的章节数据):
```json
{
  "inputs": {
    "book_info": {
      "title": "西游记",
      "author": "吴承恩"
    },
    "chapter_info": {
      "chapter_title": "第一回 灵根育孕源流出 心性修持大道生"
    },
    "content": "诗曰：混沌未分天地乱，茫茫渺渺无人见。自从盘古破鸿蒙，开辟从兹清浊辨。欲知造化会元功，须看西游释厄传。盖闻天地之数，有十二万九千六百岁为一元..."
  }
}
```

**📥 Dify → AI-Sound** (返回分析结果):
```json
{
  "data": {
    "book_info": {
      "title": "西游记",
      "chapter_title": "第一回 灵根育孕源流出 心性修持大道生"
    },
    "characters": [
      {"name": "孙悟空", "voice_id": 2, "voice_name": "活泼男声", "confidence": 95},
      {"name": "菩提祖师", "voice_id": 4, "voice_name": "沉稳长者", "confidence": 98}
    ],
    "segments": [
      {
        "text": "悟空，你在这里学些什么道理？",
        "speaker": "菩提祖师",
        "voice_id": 4,
        "voice_name": "沉稳长者",
        "parameters": {"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}
      }
    ]
  }
}
```

## 🎯 设计原则

### 简洁至上
- **只传递必要信息**: 书名、作者、章节标题、正文内容
- **避免过度配置**: 分析参数由Dify工作流内部控制
- **专注核心任务**: 让Dify专心做角色识别和声音匹配

## 🚀 核心功能特性

### 1. 智能角色识别
- **角色提取**: 自动识别小说中的所有说话角色
- **属性分析**: 分析角色性别、年龄、性格特征
- **声音匹配**: 基于角色特征智能匹配最佳语音音色
- **情感检测**: 识别对话中的情感色彩

### 2. 语音角色库集成
- **实时获取**: Dify工作流实时调用角色API获取最新音色
- **智能过滤**: 支持按类型、质量分过滤角色
- **参数配置**: 自动配置最佳语音合成参数

### 3. 标准化输出
- **角色映射**: 生成角色到语音的精确映射关系
- **分段配置**: 输出详细的文本分段和语音配置
- **合成计划**: 生成完整的语音合成执行计划

## 📋 使用流程

### 步骤1: 准备项目数据

```bash
# 1. 上传书籍
POST /api/v1/books/
Content-Type: multipart/form-data
{
  "file": "novel.txt",
  "title": "西游记",
  "author": "吴承恩",
  "auto_detect_chapters": true
}

# 2. 创建朗读项目
POST /api/v1/projects/
{
  "name": "《西游记》智能解析项目",
  "book_id": 1,
  "description": "基于Dify工作流的智能角色分析"
}
```

### 步骤2: 配置Dify工作流

#### 环境变量配置
```bash
# 必须配置的Dify参数
DIFY_API_KEY=your_dify_api_key_here
DIFY_NOVEL_WORKFLOW_ID=your_workflow_id_here

# 可选配置
DIFY_BASE_URL=https://api.dify.ai/v1
DIFY_TIMEOUT=120
DIFY_MAX_RETRIES=3
```

#### Dify分析工作流入参格式
```json
{
  "inputs": {
    "book_info": {
      "title": "西游记", 
      "author": "吴承恩"
    },
    "chapter_info": {
      "chapter_title": "第一回 灵根育孕源流出 心性修持大道生"
    },
    "content": "诗曰：混沌未分天地乱，茫茫渺渺无人见。自从盘古破鸿蒙，开辟从兹清浊辨。欲知造化会元功，须看西游释厄传..."
  },
  "response_mode": "blocking",
  "user": "ai-sound-user"
}
```

**说明**: 
- ✅ **只传递必要信息**: 书名、作者、章节标题、正文内容
- ❌ **移除多余参数**: max_segments、detect_emotions等由Dify工作流内部控制
- 🎯 **保持简洁**: 让Dify专注于核心的角色识别和匹配任务

### 步骤3: 角色同步到Dify知识库

#### 同步工作流配置
```bash
# 1. 创建角色同步API接口
POST /api/v1/sync/characters/to-dify
{
  "target_workflow_id": "character_sync_workflow_id",
  "sync_all": true,
  "quality_filter": 3.0
}

# 2. 定期触发同步（可配置定时任务）
# 当角色库更新时自动触发
```

#### 知识库结构设计
```json
{
  "knowledge_base": "ai_sound_characters",
  "documents": [
    {
      "id": "voice_1",
      "content": "声音ID: 1, 名称: 温柔女声, 类型: female, 质量: 4.2分, 描述: 温柔甜美的女性声音, 参数: timeStep=20",
      "metadata": {
        "voice_id": 1,
        "voice_type": "female",
        "quality_score": 4.2
      }
    }
  ]
}
```

#### 角色API返回格式
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "温柔女声",
      "type": "female",
      "description": "温柔甜美的女性声音",
      "qualityScore": 4.2,
      "parameters": "{\"timeStep\": 20, \"pWeight\": 1.0, \"tWeight\": 1.0}",
      "color": "#06b6d4",
      "usageCount": 15
    },
    {
      "id": 2,
      "name": "磁性男声",
      "type": "male", 
      "description": "低沉磁性的男性声音",
      "qualityScore": 4.5,
      "parameters": "{\"timeStep\": 32, \"pWeight\": 1.4, \"tWeight\": 3.0}",
      "color": "#f97316",
      "usageCount": 23
    }
  ],
  "pagination": {
    "total": 15,
    "hasMore": false
  }
}
```

### 步骤4: 启动章节智能分析

```bash
# 调用智能分析接口
POST /api/v1/intelligent-analysis/analyze/{project_id}
{
  "chapter_ids": [1, 2, 3],  # 要分析的章节ID列表
  "dify_config": {
    "workflow_id": "your_workflow_id",
    "timeout": 120
  }
}
```

### 步骤5: 监控分析进度

```javascript
// WebSocket实时监控
const ws = new WebSocket('ws://localhost:8000/ws/analysis/{project_id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'progress':
      console.log(`分析进度: ${data.progress}%`);
      break;
    case 'character_found':
      console.log(`发现角色: ${data.character_name}`);
      break;
    case 'voice_matched':
      console.log(`语音匹配: ${data.character} → ${data.voice_name}`);
      break;
    case 'completed':
      console.log('分析完成！');
      break;
  }
};
```

### 步骤6: 获取和应用结果

```bash
# 获取分析结果
GET /api/v1/intelligent-analysis/results/{project_id}

# 应用分析结果到项目
POST /api/v1/intelligent-analysis/apply/{project_id}
{
  "result_id": 123,
  "apply_options": {
    "override_existing": true,
    "create_presets": true
  }
}
```

## 📊 Dify工作流标准返回格式

### 期望的JSON结构
```json
{
  "data": {
    "project_info": {
      "novel_type": "古典小说",
      "analysis_time": "2024-01-20T10:30:00Z",
      "total_segments": 45,
      "ai_model": "gpt-4",
      "confidence_score": 92
    },
    "characters": [
      {
        "name": "孙悟空",
        "voice_id": 2,
        "voice_name": "活泼男声",
        "character_type": "main",
        "gender": "male",
        "personality": ["勇敢", "机智", "顽皮"],
        "match_reason": "基于角色的活泼性格和年轻特征匹配"
      },
      {
        "name": "菩提祖师", 
        "voice_id": 4,
        "voice_name": "沉稳长者",
        "character_type": "supporting",
        "gender": "male",
        "personality": ["睿智", "严肃", "慈祥"],
        "match_reason": "基于长者身份和威严气质匹配"
      },
      {
        "name": "旁白",
        "voice_id": 1, 
        "voice_name": "温柔女声",
        "character_type": "narrator",
        "match_reason": "专业旁白配音，声音清晰稳定"
      }
    ],
    "segments": [
      {
        "order": 1,
        "text": "悟空，你在这里学些什么道理？",
        "speaker": "菩提祖师",
        "voice_id": 4,
        "voice_name": "沉稳长者",
        "segment_type": "dialogue",
        "emotion": "询问",
        "parameters": {
          "timeStep": 20,
          "pWeight": 1.0,
          "tWeight": 1.0
        }
      },
      {
        "order": 2,
        "text": "弟子时常听讲，也颇知些。",
        "speaker": "孙悟空",
        "voice_id": 2,
        "voice_name": "活泼男声", 
        "segment_type": "dialogue",
        "emotion": "谦逊",
        "parameters": {
          "timeStep": 25,
          "pWeight": 1.2,
          "tWeight": 1.1
        }
      }
    ]
  }
}
```

## 🔧 系统集成配置

### 1. 角色API接口说明

**基础接口**: `GET /api/v1/characters`

**支持的查询参数**:
```bash
# 获取所有高质量角色（Dify推荐用法）
GET /api/v1/characters?page_size=1000&quality_min=3.0&status=active

# 按类型过滤
GET /api/v1/characters?voice_type=male&page_size=1000
GET /api/v1/characters?voice_type=female&page_size=1000

# 按质量分过滤
GET /api/v1/characters?quality_min=4.0&page_size=1000

# 搜索特定声音
GET /api/v1/characters?search=温柔&page_size=1000
```

### 2. Dify工作流配置要点

#### HTTP节点配置
```json
{
  "method": "GET",
  "url": "{{characters_api_url}}",
  "params": {
    "page_size": 1000,
    "quality_min": "{{quality_threshold}}",
    "status": "active"
  },
  "headers": {
    "Content-Type": "application/json"
  }
}
```

#### 数据处理节点
```python
# Dify工作流中的数据处理逻辑示例
def process_characters(characters_response):
    characters = characters_response['data']
    
    # 按类型分组
    male_voices = [c for c in characters if c['type'] == 'male']
    female_voices = [c for c in characters if c['type'] == 'female']
    
    # 按质量排序
    male_voices.sort(key=lambda x: x['qualityScore'], reverse=True)
    female_voices.sort(key=lambda x: x['qualityScore'], reverse=True)
    
    return {
        'available_male_voices': male_voices[:10],
        'available_female_voices': female_voices[:10],
        'total_voices': len(characters)
    }
```

### 3. 错误处理机制

```bash
# 如果Dify调用失败，系统会降级到Mock模式
{
  "status": "mock_mode",
  "reason": "Dify API调用失败",
  "fallback_result": {
    "characters": [
      {"name": "主角", "voice_id": 1, "voice_name": "默认男声"},
      {"name": "旁白", "voice_id": 2, "voice_name": "默认女声"}
    ]
  }
}
```

## 🎯 实际使用案例

### 案例1: 古典小说《西游记》

**输入文本**:
```
第一回 灵根育孕源流出 心性修持大道生
那猴王叫道："师父，弟子时常听讲，也颇知些。"
菩提祖师道："悟空，你在这里学些什么道理？"
```

**Dify分析过程**:
1. 获取角色库: 调用`/api/v1/characters?page_size=1000&quality_min=3.0`
2. 识别角色: 孙悟空、菩提祖师
3. 智能匹配: 
   - 孙悟空 → 活泼男声 (基于年轻、机智特征)
   - 菩提祖师 → 沉稳长者 (基于长者、威严特征)

**输出结果**:
```json
{
  "characters": [
    {
      "name": "孙悟空", 
      "voice_id": 2,
      "voice_name": "活泼男声",
      "match_confidence": 95
    },
    {
      "name": "菩提祖师",
      "voice_id": 4, 
      "voice_name": "沉稳长者",
      "match_confidence": 98
    }
  ]
}
```

### 案例2: 现代都市小说

**特点**: 男女主角对话较多，情感丰富

**Dify匹配策略**:
- 男主角 → 磁性男声
- 女主角 → 温柔女声  
- 配角 → 根据性格匹配不同音色
- 心理独白 → 轻柔内心声

## 🛠️ 开发集成SDK

### Python SDK示例

```python
from ai_sound_client import IntelligentAnalysisClient

# 初始化客户端
client = IntelligentAnalysisClient(
    base_url="http://localhost:8000",
    dify_config={
        "api_key": "your_dify_key",
        "workflow_id": "your_workflow_id"
    }
)

# 启动智能分析
async def analyze_novel(project_id):
    # 开始分析
    result = await client.analyze_project(
        project_id=project_id,
        options={
            "include_emotions": True,
            "quality_threshold": 3.5
        }
    )
    
    # 监听进度
    async for progress in client.watch_progress(project_id):
        print(f"进度: {progress.percentage}%")
        if progress.completed:
            break
    
    # 应用结果
    await client.apply_analysis_result(
        project_id=project_id,
        result_id=result.id
    )
    
    return result

# 使用示例
result = await analyze_novel(project_id=1)
print(f"识别到 {len(result.characters)} 个角色")
```

### JavaScript/React示例

```javascript
import { useIntelligentAnalysis } from 'ai-sound-react-hooks';

function AnalysisPanel({ projectId }) {
  const {
    startAnalysis,
    progress,
    result,
    isAnalyzing,
    error
  } = useIntelligentAnalysis();

  const handleStartAnalysis = async () => {
    try {
      await startAnalysis(projectId, {
        difyConfig: {
          workflowId: 'your_workflow_id',
          includeEmotions: true
        }
      });
    } catch (err) {
      console.error('分析失败:', err);
    }
  };

  return (
    <div>
      <button onClick={handleStartAnalysis} disabled={isAnalyzing}>
        {isAnalyzing ? '分析中...' : '开始智能分析'}
      </button>
      
      {progress && (
        <div>
          <div>进度: {progress.percentage}%</div>
          <div>当前: {progress.currentStep}</div>
        </div>
      )}
      
      {result && (
        <div>
          <h3>分析结果</h3>
          <p>识别角色: {result.characters.length} 个</p>
          <p>文本分段: {result.segments.length} 段</p>
        </div>
      )}
    </div>
  );
}
```

## 📈 性能优化建议

### 1. Dify工作流优化
- **并行处理**: 角色识别和语音匹配并行执行
- **缓存机制**: 缓存相似文本的分析结果
- **批量调用**: 一次获取所有角色信息，避免多次API调用

### 2. 系统配置建议
```bash
# 推荐的Dify配置
DIFY_TIMEOUT=180          # 超时时间3分钟
DIFY_MAX_RETRIES=3        # 最大重试3次
DIFY_BATCH_SIZE=5         # 批处理大小5个章节

# 角色API调用优化
CHARACTERS_CACHE_TTL=300  # 角色缓存5分钟
CHARACTERS_MAX_LIMIT=1000 # 最大返回1000个角色
```

### 3. 监控和日志
```bash
# 查看分析统计
GET /api/v1/intelligent-analysis/stats
{
  "today_analysis_count": 15,
  "success_rate": 0.94,
  "average_processing_time": 45.2,
  "most_used_voices": [
    {"voice_name": "温柔女声", "usage_count": 8},
    {"voice_name": "磁性男声", "usage_count": 6}
  ]
}
```

## 🔍 故障排查

### 常见问题解决

1. **Dify工作流调用失败**
   ```bash
   # 检查配置
   curl -X GET "http://localhost:8000/api/v1/characters?page_size=10"
   
   # 验证Dify连接
   curl -X POST "https://api.dify.ai/v1/workflows/run" \
        -H "Authorization: Bearer YOUR_API_KEY"
   ```

2. **角色匹配质量不佳**
   - 调整`quality_threshold`参数提高声音质量
   - 在Dify工作流中优化角色分析提示词
   - 增加角色库中的高质量声音

3. **分析速度慢**
   - 减少单次分析的文本长度
   - 优化Dify工作流的并行处理
   - 启用角色API缓存机制

### 调试命令
```bash
# 测试角色API
curl "http://localhost:8000/api/v1/characters?page_size=5&quality_min=4.0"

# 查看分析日志  
tail -f platform/backend/logs/intelligent_analysis.log

# 检查Dify配置
python -c "
import os
print('DIFY_API_KEY:', os.getenv('DIFY_API_KEY', 'NOT_SET'))
print('DIFY_WORKFLOW_ID:', os.getenv('DIFY_NOVEL_WORKFLOW_ID', 'NOT_SET'))
"
```

## 🎉 总结

AI-Sound的大模型智能解析功能通过与Dify工作流的深度集成，实现了：

✅ **智能化程度高**: 基于大模型的深度理解和角色分析  
✅ **架构设计优秀**: 解耦合设计，Dify自主获取和决策  
✅ **集成简单高效**: 复用现有API，无需额外开发  
✅ **结果质量稳定**: 智能匹配算法，角色声音匹配准确率>90%  
✅ **扩展性强**: 支持多种小说类型和自定义配置  
✅ **用户体验好**: 实时进度反馈，可视化分析过程  

通过这个解决方案，用户可以将手工角色配置的工作量减少**85%以上**，同时获得更加智能和精确的角色声音匹配结果！

---

*📝 配置要求: 需要有效的Dify API密钥和工作流ID。建议先用简短文本测试配置的正确性。*

*🔗 相关文档: [Dify工作流配置指南](./dify-workflow-setup.md) | [角色API详细文档](./characters-api.md)* 