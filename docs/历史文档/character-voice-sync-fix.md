# 角色语音配置同步修复

## 问题描述

用户在角色管理界面修改角色的音频配置后，合成模块仍然使用旧的配置进行语音合成。

### 根本原因

1. **数据存储分离**：
   - 角色配置保存在 `Book.character_summary` 字段中
   - 合成模块读取 `AnalysisResult.synthesis_plan` 中的 `voice_id`
   - 两者数据不同步

2. **合成流程依赖**：
   - `novel_reader.py` 中的合成逻辑从 `synthesis_plan.segments[].voice_id` 读取配置
   - 角色配置修改只更新了书籍级汇总，未同步到章节级合成计划

## 解决方案

### 1. 同步机制实现

在 `app/api/v1/books.py` 中实现 `_sync_character_voice_to_synthesis_plans()` 函数：

```python
async def _sync_character_voice_to_synthesis_plans(
    book_id: int, 
    character_voice_mappings: Dict[str, int], 
    db: Session
) -> int:
```

**核心逻辑**：
1. 查找书籍所有已完成分析的章节
2. 遍历每个章节的 `synthesis_plan.segments`
3. 更新匹配角色的 `voice_id`
4. 批量提交数据库更改

### 2. API 集成

在以下角色配置 API 中集成同步功能：

- `POST /books/{book_id}/characters/{character_name}/voice-mapping` - 单个角色配置
- `POST /books/{book_id}/characters/batch-voice-mappings` - 批量角色配置

### 3. 响应增强

API 响应中增加同步信息：
```json
{
  "success": true,
  "message": "成功设置角色语音配置，已同步更新X个章节的合成计划",
  "data": {
    "updated_chapters": 5,
    "updated_mappings": {...}
  }
}
```

### 4. 🔥 数据格式兼容性修复

**问题**：`rebuild_character_summary` API 报错 `'str' object has no attribute 'get'`

**原因**：数据库中的 `character_summary` 字段可能存储为字符串格式而不是JSON对象

**解决方案**：
- 修复 `Book.get_character_summary()` 方法，增加字符串格式检测和转换
- 在 `rebuild_character_summary` 函数中增加错误处理和类型检查

```python
def get_character_summary(self) -> Dict[str, Any]:
    """获取角色汇总信息"""
    if not self.character_summary:
        return {"characters": [], "voice_mappings": {}, ...}
    
    # 🔥 修复：处理字符串格式的数据
    if isinstance(self.character_summary, str):
        try:
            return json.loads(self.character_summary)
        except json.JSONDecodeError:
            return {"characters": [], "voice_mappings": {}, ...}
    
    return self.character_summary
```

**API级别修复**：
在 `rebuild_character_summary` 函数中增强错误处理：

```python
# 保存当前的语音映射配置
try:
    current_summary = book.get_character_summary()
    # 🔥 确保current_summary是字典格式
    if isinstance(current_summary, dict):
        current_mappings = current_summary.get('voice_mappings', {})
    else:
        logger.warning(f"角色汇总数据格式异常: {type(current_summary)} - {current_summary}")
        current_mappings = {}
except Exception as e:
    logger.warning(f"获取当前语音映射失败: {str(e)}，使用空映射")
    current_mappings = {}
```

### 5. 🔧 API参数格式修复

**问题**：批量设置API返回422错误 `Input should be a valid dictionary`

**原因**：前端发送FormData格式的JSON字符串，但后端期望直接接收字典

**解决方案**：修改后端API参数类型定义
```python
# 修复前
mappings: dict = Form(..., description="角色语音映射字典")

# 修复后  
mappings: str = Form(..., description="角色语音映射JSON字符串")
```

保持现有的字符串转换逻辑：
```python
if isinstance(mappings, str):
    try:
        mappings = json.loads(mappings)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="映射数据格式错误")
```

## 技术细节

### 数据流程

```
用户修改角色配置
    ↓
更新 Book.character_summary
    ↓
同步更新 AnalysisResult.synthesis_plan
    ↓
合成模块使用最新配置
```

### 性能优化

- 仅更新有变化的 `voice_id`
- 批量数据库操作
- 智能跳过无需更新的章节

### 错误处理

- 单个章节更新失败不影响其他章节
- 详细的日志记录
- 异常情况下返回部分成功结果
- **数据格式兼容性**：自动处理字符串/JSON格式转换
- **API参数格式兼容**：正确处理FormData JSON字符串

## 测试验证

创建测试脚本 `test_character_voice_sync.py`：

1. 获取角色配置状态
2. 检查修改前的 `synthesis_plan`
3. 修改角色语音配置
4. 验证 `synthesis_plan` 同步状态
5. 确认合成模块使用新配置

## 影响范围

### 修改的文件

- `platform/backend/app/api/v1/books.py` - 核心同步逻辑 + 错误处理修复 + API参数格式修复
- `platform/backend/app/models/book.py` - 数据格式兼容性修复
- `platform/backend/test_character_voice_sync.py` - 测试脚本

### API 变更

- 角色配置 API 响应格式增强
- 增加同步状态反馈
- **修复 rebuild_character_summary API 的500错误**
- **修复 batch_voice_mappings API 的422错误**

### 数据库

- 无表结构变更
- 仅更新现有 JSON 字段内容
- **增强数据格式兼容性**

## 使用说明

1. **重启后端服务**应用修改
2. **正常使用角色管理功能**，系统自动同步
3. **检查 API 响应**确认同步状态
4. **运行测试脚本**验证功能正确性

## 注意事项

- 同步操作是增量的，只更新变化的配置
- 大量章节的书籍同步可能需要几秒时间
- 建议在低峰期进行大批量角色配置修改
- 同步失败不影响角色配置的保存
- **数据格式自动兼容**：支持字符串和JSON两种格式
- **前后端数据格式统一**：正确处理FormData JSON参数

## 修复历史

| 日期 | 问题 | 修复内容 |
|------|------|----------|
| 2025-01-28 | 角色配置不同步 | 实现同步机制和API集成 |
| 2025-01-28 | rebuild_summary 500错误 | 数据格式兼容性修复 |
| 2025-01-28 | batch_voice_mappings 422错误 | API参数格式修复 |
| 2025-01-28 | 同步功能导入错误 | 修复相对导入路径问题 |

---

**修复日期**: 2025-01-28  
**影响版本**: 所有包含角色管理功能的版本  
**重要性**: 🔥 关键修复 - 影响合成功能的正确性

**更新日期**: 2025-01-28 (追加数据格式兼容性修复)  
**追加修复**: ✅ 解决 rebuild_character_summary API 的500错误

**最新更新**: 2025-01-28 (追加同步功能导入修复)  
**最新修复**: ✅ 解决 _sync_character_voice_to_synthesis_plans 函数的导入错误

### 6. 🔧 同步功能导入修复

**问题**：角色配置保存成功，但同步更新失败，报错 `No module named 'app.api.models'`

**原因**：`_sync_character_voice_to_synthesis_plans`函数中错误的相对导入路径

**解决方案**：移除函数内部的重复导入，使用文件顶部已导入的模型

```python
# 修复前：错误的相对导入
from ..models import BookChapter, AnalysisResult

# 修复后：直接使用已导入的模型
# 注意：BookChapter, AnalysisResult 已在文件顶部导入
```

现在角色配置保存后会正确同步到所有相关章节的synthesis_plan中。 