# 智能分析API规范

## 📋 **设计理念**

智能分析功能采用**一步到位**的设计，大模型直接输出可执行的合成计划，无需复杂的二次转换。

## 🔄 **工作流程**

```
小说文本 → 智能分析检测 → 大模型推荐 → 最终可用JSON → 直接合成
```

## 📤 **API接口**

### **POST `/api/intelligent-analysis/analyze/{project_id}`**

**功能**: 对小说项目进行智能分析，返回直接可用的合成计划

**响应格式**:
```json
{
  "success": true,
  "message": "智能分析完成",
  "data": {
    "project_info": {
      "novel_type": "科幻",
      "analysis_time": "2025-06-09T05:30:07.528560",
      "total_segments": 5,
      "ai_model": "dify-intelligent-analysis"
    },
    
    "synthesis_plan": [
      {
        "segment_id": 1,
        "text": "在数字化时代的浪潮中，数据如同蚕茧般包裹着我们的生活。",
        "speaker": "系统旁白",
        "voice_id": 3,
        "voice_name": "中性旁白",
        "parameters": {
          "timeStep": 20,
          "pWeight": 1.0,
          "tWeight": 1.0
        }
      },
      {
        "segment_id": 2,
        "text": "数据的流动模式确实很有趣。",
        "speaker": "李维",
        "voice_id": 2,
        "voice_name": "磁性男声",
        "parameters": {
          "timeStep": 15,
          "pWeight": 1.2,
          "tWeight": 0.8
        }
      }
    ],
    
    "characters": [
      {
        "name": "李维",
        "voice_id": 2,
        "voice_name": "磁性男声"
      },
      {
        "name": "艾莉",
        "voice_id": 1,
        "voice_name": "温柔女声"
      }
    ]
  }
}
```

## 📋 **数据字段说明**

### **project_info**
- `novel_type`: 小说类型
- `analysis_time`: 分析时间戳
- `total_segments`: 总分段数
- `ai_model`: 使用的AI模型

### **synthesis_plan**
每个分段包含：
- `segment_id`: 分段ID
- `text`: 要合成的文本
- `speaker`: 说话人
- `voice_id`: 使用的声音ID
- `voice_name`: 声音名称（便于显示）
- `parameters`: TTS参数
  - `timeStep`: 时间步长
  - `pWeight`: P权重
  - `tWeight`: T权重

### **characters**
角色列表，包含：
- `name`: 角色名称
- `voice_id`: 分配的声音ID
- `voice_name`: 声音名称

## 🎯 **前端使用方式**

1. **调用分析接口**获取合成计划
2. **显示角色配置**供用户确认/调整
3. **直接执行合成**，按synthesis_plan循环调用TTS API

### **示例代码**:
```javascript
// 1. 获取分析结果
const analysisResult = await api.post(`/intelligent-analysis/analyze/${projectId}`)
const synthesisPlan = analysisResult.data.synthesis_plan

// 2. 执行合成
for (const segment of synthesisPlan) {
  if (segment.voice_id) {
    await ttsApi.synthesize({
      text: segment.text,
      voice_id: segment.voice_id,
      ...segment.parameters
    })
  }
}
```

## 🔧 **参数调整**

用户可以在前端调整：
- 角色的声音分配（修改voice_id）
- TTS参数（timeStep, pWeight, tWeight）
- 分段的说话人

调整后直接按新的计划执行合成。

## ✅ **优势**

1. **简洁高效**: 一个JSON包含所有执行信息
2. **直接可用**: 无需二次转换，直接调用TTS
3. **易于调试**: 参数清晰，便于测试和调优
4. **灵活可编辑**: 用户可以随时调整任何参数

## 🚀 **未来扩展**

- 支持更多TTS参数
- 支持情感标签
- 支持语速调节
- 支持音效插入