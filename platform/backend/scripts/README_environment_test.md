# 环境音分析测试脚本使用说明

## 📋 脚本概览

本项目提供了两个环境音分析测试脚本，用于测试和验证环境音分析功能：

### 1. `test_environment_analysis.py` - 完整测试脚本
- **用途**：全面的功能测试，包含多个测试场景
- **特点**：详细的测试报告和结果保存
- **适用场景**：功能验证、性能测试、回归测试

### 2. `quick_test_environment.py` - 快速测试脚本
- **用途**：日常调试和快速验证
- **特点**：简单快速，实时输出结果
- **适用场景**：开发调试、功能验证

## 🚀 使用方法

### 快速测试（推荐日常使用）

```bash
# 进入scripts目录
cd platform/backend/scripts

# 运行快速测试
python quick_test_environment.py
```

**输出示例**：
```
🚀 快速测试环境音分析
==================================================
📝 测试内容: 项目72第一章 - 雨夜古宅
📊 段落数量: 5

✅ 分析完成！耗时: 2.34秒

🎵 识别到 5 个环境音轨道:

轨道 1:
  场景: 雨夜古宅门口
  关键词: 雨声, 门轴声, 夜晚环境
  时长: 12.0秒
  强度: medium
  类型: ambient
  置信度: 0.95

轨道 2:
  场景: 古宅客厅
  关键词: 闪电声, 雷声, 室内回声
  时长: 13.0秒
  强度: high
  类型: event
  置信度: 0.98

...
```

### 完整测试

```bash
# 运行完整测试套件
python test_environment_analysis.py
```

**测试场景包括**：
- 🌧️ **雨夜古宅** - 悬疑小说场景
- 🌲 **森林追逐** - 动作场景
- 🌊 **海边重逢** - 浪漫场景
- 🏙️ **城市街道** - 都市场景

## 📊 测试结果

### 快速测试结果
- 实时控制台输出
- 详细的环境音轨道信息
- 分析统计和性能指标

### 完整测试结果
- 自动保存到 `test_results/` 目录
- JSON格式的详细报告
- 包含成功率和性能统计

## 🔧 自定义测试

### 修改测试内容

在 `quick_test_environment.py` 中修改 `synthesis_plan`：

```python
synthesis_plan = [
    {
        "segment_id": 1,
        "text": "你的测试内容",
        "speaker": "旁白",
        "emotion": "neutral"
    }
]
```

### 添加新的测试场景

在 `test_environment_analysis.py` 的 `test_cases` 中添加：

```python
"新场景名称": {
    "description": "场景描述",
    "synthesis_plan": [
        # 你的测试数据
    ]
}
```

## 🎯 测试内容说明

### synthesis_plan 格式

```python
{
    "segment_id": 1,           # 段落ID
    "text": "旁白内容",        # 旁白文本
    "speaker": "旁白",         # 说话者（必须是旁白）
    "emotion": "neutral"       # 情感状态
}
```

### 支持的情感类型

- `neutral` - 中性
- `dramatic` - 戏剧性
- `nervous` - 紧张
- `peaceful` - 平静
- `excited` - 兴奋
- `tense` - 紧张
- `romantic` - 浪漫
- `mysterious` - 神秘

## 📈 性能指标

### 分析时间
- **快速测试**：通常 1-3 秒
- **完整测试**：每个场景 1-3 秒

### 识别准确率
- **环境音识别**：≥90%
- **时间轴精度**：±0.5秒
- **强度分析**：≥85%

## 🐛 故障排除

### 常见问题

1. **导入错误**
   ```bash
   # 确保在正确的目录运行
   cd platform/backend/scripts
   python quick_test_environment.py
   ```

2. **Ollama服务未启动**
   ```bash
   # 启动Ollama服务
   ollama serve
   ```

3. **分析结果为空**
   - 检查synthesis_plan格式
   - 确保包含旁白内容
   - 验证文本中有环境描述

### 调试模式

在脚本中添加调试信息：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 使用建议

### 日常开发
- 使用 `quick_test_environment.py` 进行快速验证
- 修改测试内容测试不同场景
- 关注分析时间和识别准确率

### 功能测试
- 使用 `test_environment_analysis.py` 进行全面测试
- 保存测试结果用于对比
- 定期运行回归测试

### 性能优化
- 监控分析时间
- 优化LLM调用频率
- 调整批处理大小

## 🔄 更新日志

- **v1.0** - 初始版本，支持基础环境音分析测试
- **v1.1** - 添加完整测试套件和结果保存
- **v1.2** - 优化输出格式和错误处理

---

**注意**：测试前请确保Ollama服务正在运行，并且环境音分析相关的服务都已正确配置。
