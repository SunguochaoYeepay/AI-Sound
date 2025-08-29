#!/usr/bin/env python3
"""
角色分析提示词模板
"""

CHARACTER_ANALYSIS_PROMPT = """
你是一个专业的文学分析专家，专门分析小说中的角色信息。

请分析以下小说中的角色信息：

原文内容：
{content}

请识别并分析所有重要角色，每个角色包含以下信息：

1. **角色名称**：角色的姓名
2. **角色类型**：主角/配角/反派/其他
3. **性格特征**：角色的性格特点和行为模式
4. **背景设定**：角色的身份背景和来历
5. **角色关系**：与其他角色的关系
6. **语音特征**：角色的语音特点（语调、语速、音量等）
7. **情感范围**：角色在故事中表现的情感类型
8. **角色弧线**：角色的成长和变化

分析要求：
- 识别所有重要角色
- 分析角色的深层特征
- 考虑角色对故事发展的作用
- 分析角色对音频制作的影响

请以JSON格式返回分析结果：

{{
  "characters": [
    {{
      "character_name": "角色名称",
      "character_type": "角色类型",
      "personality": {{
        "traits": ["性格特征1", "性格特征2"],
        "background": "背景设定"
      }},
      "relationships": ["与其他角色的关系"],
      "voice_characteristics": {{
        "tone": "语调特点",
        "pace": "语速特点",
        "volume": "音量特点",
        "accent": "口音特点"
      }},
      "emotional_range": ["情感类型1", "情感类型2"],
      "character_arc": "角色弧线描述"
    }}
  ]
}}

请确保返回的是有效的JSON格式，不要包含其他文字说明。
"""

CHARACTER_ANALYSIS_PROMPT_SIMPLE = """
分析以下小说中的角色：

{content}

识别所有重要角色，返回JSON格式：
{{
  "characters": [
    {{
      "character_name": "角色名称",
      "character_type": "主角/配角",
      "personality": {{"traits": ["性格特征"], "background": "背景"}},
      "voice_characteristics": {{"tone": "语调", "pace": "语速"}},
      "emotional_range": ["情感类型"]
    }}
  ]
}}
"""
