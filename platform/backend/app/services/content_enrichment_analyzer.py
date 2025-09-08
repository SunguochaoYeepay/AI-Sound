"""
内容丰富化分析器
专门用于基于已有对话分析结果进行6卡内容丰富化
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.services.storyboard_analysis.llm_client import LLMClient
from app.utils.llm_config_loader import llm_config_loader

logger = logging.getLogger(__name__)


class ContentEnrichmentAnalyzer:
    """内容丰富化分析器 - 专门用于6卡内容丰富化"""
    
    def __init__(self):
        # 从统一配置加载器读取LLM模型设置
        self.llm_config = llm_config_loader.get_config()
        self.llm = LLMClient(
            model=self.llm_config["model"], 
            base_url=self.llm_config["base_url"]
        )
        self.llm.timeout = self.llm_config["timeout"]
        
        logger.info(f"内容丰富化分析器初始化完成，使用模型: {self.llm_config['model']}")
    
    async def enrich_content(self, 
                           paragraph_text: str, 
                           dialogue_analysis: Dict[str, Any],
                           paragraph_index: int) -> Dict[str, Any]:
        """
        基于已有对话分析结果进行内容丰富化
        
        Args:
            paragraph_text: 段落原文
            dialogue_analysis: 已有的对话分析结果
            paragraph_index: 段落索引
            
        Returns:
            6卡分析结果
        """
        try:
            logger.info(f"开始内容丰富化分析段落 {paragraph_index}")
            
            # 构建内容丰富化提示词
            prompt = self._build_enrichment_prompt(paragraph_text, dialogue_analysis)
            
            # 调用LLM进行分析
            response = await self.llm.call_json(prompt)
            
            # 验证返回结果
            if not self._validate_six_cards(response):
                logger.warning(f"段落 {paragraph_index} 6卡分析结果验证失败")
                response = self._create_fallback_cards(paragraph_text, paragraph_index)
            
            # 添加元数据
            response["_metadata"] = {
                "paragraph_index": paragraph_index,
                "paragraph_text": paragraph_text,
                "analysis_time": datetime.utcnow().isoformat(),
                "model_used": self.llm_config["model"],
                "analysis_type": "content_enrichment"
            }
            
            logger.info(f"段落 {paragraph_index} 内容丰富化分析完成")
            return response
            
        except Exception as e:
            logger.error(f"段落 {paragraph_index} 内容丰富化分析失败: {str(e)}")
            raise
    
    def _build_enrichment_prompt(self, 
                               paragraph_text: str, 
                               dialogue_analysis: Dict[str, Any]) -> str:
        """构建内容丰富化提示词"""
        
        # 提取已有的对话分析结果
        segments = dialogue_analysis.get('segments', [])
        characters = dialogue_analysis.get('characters', [])
        
        # 构建segments摘要
        segments_summary = []
        for i, segment in enumerate(segments):
            text_preview = segment.get('text', '')[:50] + ('...' if len(segment.get('text', '')) > 50 else '')
            speaker = segment.get('speaker', '未知')
            text_type = segment.get('text_type', 'dialogue')
            segments_summary.append(f"段落{i+1}: {text_preview} (说话者: {speaker}, 类型: {text_type})")
        
        # 构建角色摘要
        characters_summary = []
        for char in characters:
            name = char.get('name', '未知')
            gender = char.get('gender', '未知')
            frequency = char.get('frequency', 0)
            is_main = char.get('is_main_character', False)
            main_indicator = " [主角]" if is_main else ""
            characters_summary.append(f"- {name}: {gender} ({frequency}次){main_indicator}")
        
        prompt = f"""任务：基于已有的对话分析结果，为以下段落生成6类卡片的内容丰富化信息。

【原文段落】
{paragraph_text}

【已有对话分析结果】
已识别的段落：
{chr(10).join(segments_summary) if segments_summary else "无段落"}

已识别的角色：
{chr(10).join(characters_summary) if characters_summary else "无角色"}

【重要要求】
1. 不要重复对话分析，专注于内容丰富化
2. 基于已有角色信息，丰富角色特征和情感状态
3. 分析场景氛围、事件重要性、情绪变化
4. 提供音频制作指导
5. 确保所有已有角色都在character_card中体现

【6类卡片说明】
1. 故事卡：段落主题和叙事目的
2. 角色卡：基于已有角色，丰富情感状态和行为描述
3. 场景卡：环境氛围和感官元素
4. 事件卡：事件重要性和因果关系
5. 情绪卡：情感变化和强度
6. 音频剧本卡：语音指导和音效建议

【返回格式】
请返回严格的JSON格式：

```json
{{
  "story_card": {{
    "theme": "段落主题",
    "plot_point": "核心情节点",
    "narrative_purpose": "叙事目的"
  }},
  "character_card": {{
    "characters": [
      {{
        "name": "角色名（必须基于已有角色）",
        "role_type": "主角/重要配角/一般配角/背景角色",
        "actions": "角色行为描述",
        "dialogue": ["该角色的具体对话内容（从segments中提取）"],
        "emotions": ["情感状态"],
        "description": "角色特征描述"
      }}
    ],
    "narrator": {{
      "type": "旁白/叙述者",
      "content": "旁白叙述内容（从segments中提取）",
      "tone": "叙述语调"
    }}
  }},
  "scene_card": {{
    "location": "具体地点",
    "time": "时间描述",
    "atmosphere": "整体氛围",
    "environment_sounds": ["环境音效"],
    "visual_elements": ["视觉元素"],
    "sensory_details": ["感官细节"]
  }},
  "event_card": {{
    "main_event": "主要事件",
    "sub_events": ["子事件"],
    "significance": "关键转折/日常对话/战斗场景",
    "causality": "因果关系"
  }},
  "emotion_card": {{
    "overall_tone": "整体情感基调",
    "emotion_changes": [
      {{
        "from": "起始情感",
        "to": "结束情感",
        "trigger": "触发因素"
      }}
    ],
    "emotional_intensity": 8,
    "primary_emotion": "主要情感"
  }},
  "audio_script_card": {{
    "voice_direction": "语音指导",
    "pacing": "节奏控制",
    "background_music": "背景音乐建议",
    "sound_effects": ["音效建议"],
    "voice_characteristics": "声音特征要求"
  }}
}}
```

【特别注意事项】
1. character_card.characters中的每个角色都必须对应已有的角色
2. 每个角色的dialogue字段必须从segments中提取该角色的实际对话
3. narrator.content必须从segments中提取旁白的实际内容
4. 不要编造不存在的角色或对话

请分析以下段落："""
        
        return prompt
    
    def _validate_six_cards(self, cards: Dict[str, Any]) -> bool:
        """验证6卡结果是否完整"""
        required_cards = [
            "story_card", "character_card", "scene_card", 
            "event_card", "emotion_card", "audio_script_card"
        ]
        
        for card_type in required_cards:
            if card_type not in cards:
                return False
        
        return True
    
    def _create_fallback_cards(self, paragraph_text: str, paragraph_index: int) -> Dict[str, Any]:
        """创建失败时的回退6卡数据"""
        return {
            "story_card": {
                "theme": "段落内容",
                "plot_point": "基本情节",
                "narrative_purpose": "推进故事"
            },
            "character_card": {
                "characters": [],
                "narrator": {
                    "type": "旁白",
                    "content": paragraph_text,
                    "tone": "中性"
                }
            },
            "scene_card": {
                "location": "未指定",
                "time": "未知",
                "atmosphere": "中性",
                "environment_sounds": [],
                "visual_elements": [],
                "sensory_details": []
            },
            "event_card": {
                "main_event": "段落事件",
                "sub_events": [],
                "significance": "日常对话",
                "causality": "因果关系不明"
            },
            "emotion_card": {
                "overall_tone": "中性",
                "emotion_changes": [],
                "emotional_intensity": 5,
                "primary_emotion": "平静"
            },
            "audio_script_card": {
                "voice_direction": "标准语音",
                "pacing": "正常节奏",
                "background_music": "无",
                "sound_effects": [],
                "voice_characteristics": "标准音色"
            }
        }
