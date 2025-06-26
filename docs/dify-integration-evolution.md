# 🤖 AI-Sound Dify集成演进计划

## 🎯 核心理念

**简单明确的职责分工**：
- **AI-Sound后端**：书籍管理、音频合成、文件存储
- **Dify大模型**：文本分析、角色识别、合成规划

## 📋 系统架构

```
用户操作 → AI-Sound前端 → AI-Sound后端 → Dify工作流 → 返回JSON → 执行合成 → 存储音频
```

### 🔄 核心流程

1. **用户创建项目** → 关联书籍内容
2. **点击"执行自动匹配"** → 调用Dify分析
3. **Dify返回JSON** → 包含完整合成计划
4. **用户确认配置** → 开始音频合成
5. **TTS批量生成** → 存储音频文件

## 🤖 Dify大模型职责

### 📖 输入内容
- **书籍文本内容**（完整或分章节）
- **现有声音库信息**（可选）
- **用户偏好设置**（可选）

### 🎯 核心任务

#### 1. **角色识别与分析**
```json
{
  "characters": [
    {
      "name": "孙悟空",
      "type": "main",           // main/supporting/narrator
      "gender": "male",
      "age_group": "adult",
      "personality_traits": ["活泼", "机智", "勇敢"],
      "description": "主角，活泼好动的猴王"
    }
  ]
}
```

#### 2. **文本分段与说话人标注**
```json
{
  "synthesis_plan": [
    {
      "segment_id": 1,
      "text": "悟空，你在这里学些什么道理？",
      "speaker": "菩提祖师",
      "type": "dialogue",       // dialogue/narration/thought
      "context": "师父询问悟空学习情况"
    }
  ]
}
```

#### 3. **声音匹配推荐**
```json
{
  "voice_recommendations": [
    {
      "character": "孙悟空",
      "recommended_voice_id": 2,
      "recommended_voice_name": "活泼男声",
      "matching_reason": "性格活泼，适合年轻男性声音",
      "confidence": 0.95
    }
  ]
}
```

#### 4. **TTS参数优化**
```json
{
  "tts_parameters": [
    {
      "character": "孙悟空",
      "timeStep": 20,
      "pWeight": 1.2,
      "tWeight": 1.0,
      "speed": 1.1,
      "emotion": "活泼"
    }
  ]
}
```

### 📤 标准输出格式
```json
{
  "analysis_result": {
    "project_info": {
      "novel_type": "古典小说",
      "total_segments": 150,
      "estimated_duration_minutes": 45,
      "analysis_confidence": 0.92
    },
    "characters": [...],
    "synthesis_plan": [...],
    "voice_recommendations": [...],
    "tts_parameters": [...]
  }
}
```

## 🔧 AI-Sound后端职责

### 📥 接收处理
- 接收用户请求（项目ID）
- 提取书籍内容
- 调用Dify工作流
- 解析返回的JSON

### 🎙️ 音频合成
- 按照Dify的synthesis_plan执行TTS
- 使用推荐的voice_id和参数
- 批量生成音频片段
- 合并为完整音频文件

### 💾 数据存储
- 保存分析结果到数据库
- 存储音频文件到文件系统
- 维护项目状态和进度

## 🚀 演进实施计划

### 阶段1：基础接口实现（Week 1）

**目标**：让前端按钮能工作

```python
# app/api/v1/intelligent_analysis.py
@router.post("/analyze/{project_id}")
async def analyze_project(project_id: int, db: Session = Depends(get_db)):
    """调用Dify分析项目"""
    # 1. 获取项目和关联书籍
    project = get_project_by_id(db, project_id)
    book_content = get_book_content(db, project.book_id)
    
    # 2. 调用Dify工作流
    dify_client = await get_dify_client()
    analysis_result = await dify_client.analyze_text(
        text=book_content,
        workflow_id=settings.DIFY_NOVEL_WORKFLOW_ID
    )
    
    # 3. 返回标准格式
    return {
        "success": True,
        "data": analysis_result.data
    }

@router.post("/apply/{project_id}")  
async def apply_analysis(project_id: int, analysis_data: dict, db: Session = Depends(get_db)):
    """应用分析结果到项目"""
    # 保存角色映射到project.character_mapping
    # 更新项目状态为ready_for_synthesis
```

### 阶段2：Dify工作流调试（Week 2）

**目标**：确保Dify返回正确格式

1. **配置Dify工作流**
   - 输入：书籍文本内容
   - 输出：标准JSON格式
   - 测试不同类型书籍

2. **错误处理**
   ```python
   try:
       result = await dify_client.analyze_text(...)
   except DifyAPIException as e:
       return {"success": False, "error": f"AI分析失败: {str(e)}"}
   ```

3. **结果验证**
   ```python
   def validate_dify_result(result: dict) -> bool:
       """简单验证Dify返回格式"""
       required_fields = ["characters", "synthesis_plan"]
       return all(field in result for field in required_fields)
   ```

### 阶段3：合成集成（Week 3）

**目标**：基于Dify结果执行音频合成

```python
# app/services/synthesis_service.py
class SynthesisService:
    async def execute_synthesis_plan(self, project_id: int, synthesis_plan: list):
        """按照Dify的计划执行合成"""
        for segment in synthesis_plan:
            audio_result = await self.tts_client.synthesize(
                text=segment["text"],
                voice_id=segment.get("recommended_voice_id"),
                parameters=segment.get("tts_parameters", {})
            )
            # 保存音频片段
            save_audio_segment(project_id, segment["segment_id"], audio_result)
        
        # 合并所有片段
        merge_audio_segments(project_id)
```

### 阶段4：优化完善（Week 4）

**目标**：用户体验优化

1. **进度监控**
   ```python
   # WebSocket实时进度推送
   async def notify_analysis_progress(project_id: int, progress: dict):
       await websocket_manager.broadcast(f"analysis_{project_id}", progress)
   ```

2. **错误恢复**
   ```python
   # 支持分析失败后重试
   @router.post("/analyze/{project_id}/retry")
   async def retry_analysis(project_id: int):
       """重新分析项目"""
   ```

## ⚡ 简化原则

### ❌ 不做的功能
- ❌ 本地AI算法实现
- ❌ 复杂的学习机制  
- ❌ 多模型对比分析
- ❌ 自定义分析模板
- ❌ 智能参数优化

### ✅ 专注核心
- ✅ 稳定的Dify API调用
- ✅ 标准化数据格式处理
- ✅ 可靠的音频合成执行
- ✅ 简洁的用户界面
- ✅ 完整的错误处理

## 🎯 成功标准

1. **功能完整性**
   - 前端"执行自动匹配"按钮正常工作
   - Dify返回的JSON能正确解析和显示
   - 用户能基于AI推荐成功合成音频

2. **系统稳定性**  
   - Dify API调用成功率 > 95%
   - 音频合成成功率 > 98%
   - 系统响应时间 < 30秒

3. **用户体验**
   - 操作流程简单直观
   - 错误信息清晰明确
   - 进度反馈及时准确

## 📝 Dify工作流要求

### 输入格式
```json
{
  "text": "完整的书籍文本内容",
  "available_voices": [
    {"id": 1, "name": "温柔女声", "type": "female"},
    {"id": 2, "name": "磁性男声", "type": "male"}
  ],
  "analysis_config": {
    "max_segments": 500,
    "include_narration": true,
    "detect_emotions": false
  }
}
```

### 必需输出格式
```json
{
  "success": true,
  "data": {
    "project_info": {
      "novel_type": "类型",
      "total_segments": 数量,
      "ai_model": "使用的模型"
    },
    "characters": [角色列表],
    "synthesis_plan": [分段计划],
    "voice_recommendations": [声音推荐]
  }
}
```

---

## 🎉 总结

这个演进计划遵循**"大道至简"**的原则：
- **AI-Sound专注**：书籍管理、音频合成、存储服务  
- **Dify专注**：文本分析、角色识别、智能推荐
- **清晰边界**：接口标准化，职责单一化
- **快速迭代**：4周完成核心功能，后续增量优化

让AI做AI擅长的事，让我们做工程擅长的事！ 