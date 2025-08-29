#!/usr/bin/env python3
"""
场景分析提示词模板
"""

SCENE_ANALYSIS_PROMPT = """
你是一个专业的文学分析专家，专门分析小说中的场景信息。

请分析以下小说章节中的场景信息：

原文内容：
{content}

请识别并分析所有场景，每个场景包含以下信息：

1. **场景名称**：简洁描述场景的核心内容
2. **场景类型**：室内/室外/特殊/虚拟等
3. **地点描述**：具体的地点信息和环境描述
4. **氛围描述**：情绪氛围、光线、天气、温度等
5. **时间背景**：具体的时间段或时代背景
6. **环境音效**：该场景中可能出现的环境声音

分析要求：
- 准确识别场景转换点
- 详细描述环境细节
- 注意场景对情节的推动作用
- 考虑场景对音频制作的影响

请以JSON格式返回分析结果：

{{
  "scenes": [
    {{
      "scene_name": "场景名称",
      "scene_type": "场景类型",
      "location": {{
        "type": "地点类型",
        "description": "详细的地点描述"
      }},
      "atmosphere": {{
        "mood": "情绪氛围",
        "lighting": "光线条件",
        "weather": "天气状况",
        "temperature": "温度感受"
      }},
      "time_period": "时间背景",
      "environmental_sounds": ["音效1", "音效2", "音效3"]
    }}
  ]
}}

请确保返回的是有效的JSON格式，不要包含其他文字说明。
"""

SCENE_ANALYSIS_PROMPT_SIMPLE = """
分析以下小说章节中的场景：

{content}

识别所有场景，返回JSON格式：
{{
  "scenes": [
    {{
      "scene_name": "场景名称",
      "scene_type": "室内/室外/特殊",
      "location": {{"type": "地点类型", "description": "地点描述"}},
      "atmosphere": {{"mood": "情绪", "lighting": "光线"}},
      "time_period": "时间背景",
      "environmental_sounds": ["音效列表"]
    }}
  ]
}}
"""
