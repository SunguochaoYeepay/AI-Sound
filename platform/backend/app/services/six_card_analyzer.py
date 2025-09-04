"""
基于段落的6卡分析服务
根据AI-Sound-Plus设计方案实现
"""

import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.storyboard_analysis.llm_client import LLMClient

logger = logging.getLogger(__name__)


class SixCardAnalyzer:
    """6卡分析器 - 基于段落生成6类卡片"""
    
    def __init__(self):
        # 使用qwen3:8b进行分析
        self.llm = LLMClient(model="qwen3:8b", base_url="http://localhost:11434")
        self.llm.timeout = 300  # 增加超时时间到5分钟
        
        # 6卡分析提示词
        self.analysis_prompt = self._build_analysis_prompt()
    
    def _build_analysis_prompt(self) -> str:
        """构建6卡分析提示词"""
        return """你是一个专业的小说分析师，专门负责将小说段落转换为6类结构化卡片。

任务：分析以下小说段落，生成6类卡片的JSON结构。

【6类卡片说明】
1. 故事卡(story_card): 该段落的核心情节和主题
2. 角色卡(character_card): 该段落中角色的具体表现和对话
3. 场景卡(scene_card): 该段落的场景描述和环境元素
4. 事件卡(event_card): 该段落的具体事件和动作
5. 情绪卡(emotion_card): 该段落的情感变化和氛围
6. 音频剧本卡(audio_script_card): 该段落的音频制作指导

【返回格式】
请返回严格的JSON格式，包含以下结构：

```json
{
  "story_card": {
    "theme": "该段落的主题",
    "plot_point": "核心情节点",
    "narrative_purpose": "叙事目的"
  },
  "character_card": {
    "characters": [
      {
        "name": "角色名",
        "actions": "角色行为",
        "dialogue": "角色对话",
        "emotions": "角色情感"
      }
    ]
  },
  "scene_card": {
    "location": "地点",
    "time": "时间",
    "atmosphere": "氛围",
    "environment_sounds": ["环境音效1", "环境音效2"]
  },
  "event_card": {
    "main_event": "主要事件",
    "sub_events": ["子事件1", "子事件2"],
    "significance": "事件重要性"
  },
  "emotion_card": {
    "overall_tone": "整体情感基调",
    "emotion_changes": [
      {
        "from": "起始情感",
        "to": "结束情感",
        "trigger": "触发因素"
      }
    ]
  },
  "audio_script_card": {
    "voice_direction": "语音指导",
    "pacing": "节奏控制",
    "background_music": "背景音乐建议",
    "sound_effects": ["音效1", "音效2"]
  }
}
```

请分析以下段落："""

    async def analyze_segment(self, segment_text: str, segment_index: int) -> Dict[str, Any]:
        """分析单个段落，生成6卡数据"""
        try:
            logger.info(f"开始分析段落 {segment_index}，长度: {len(segment_text)} 字符")
            
            # 调用LLM进行分析
            prompt = self.analysis_prompt + "\n\n" + segment_text
            response = await self.llm.call_json(prompt)
            
            # 验证返回结果
            if not self._validate_six_cards(response):
                logger.warning(f"段落 {segment_index} 6卡分析结果验证失败")
                return self._create_fallback_cards(segment_text, segment_index)
            
            # 添加元数据
            response["_metadata"] = {
                "segment_index": segment_index,
                "segment_text": segment_text,
                "analysis_time": datetime.utcnow().isoformat(),
                "model_used": "qwen3:8b"
            }
            
            logger.info(f"段落 {segment_index} 6卡分析完成")
            return response
            
        except Exception as e:
            logger.error(f"段落 {segment_index} 6卡分析失败: {str(e)}")
            return self._create_fallback_cards(segment_text, segment_index)

    async def analyze_segments(self, segments: List[str]) -> List[Dict[str, Any]]:
        """分析所有段落，生成6卡数据列表"""
        logger.info(f"开始分析 {len(segments)} 个段落")
        
        results = []
        for i, segment in enumerate(segments):
            result = await self.analyze_segment(segment, i + 1)
            results.append(result)
        
        logger.info(f"完成所有段落6卡分析，共 {len(results)} 个结果")
        return results

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

    def _create_fallback_cards(self, segment_text: str, segment_index: int) -> Dict[str, Any]:
        """创建失败时的回退6卡数据"""
        return {
            "story_card": {
                "theme": "未知主题",
                "plot_point": "段落内容分析",
                "narrative_purpose": "推进故事发展"
            },
            "character_card": {
                "characters": [{
                    "name": "未识别角色",
                    "actions": "基本行为",
                    "dialogue": "",
                    "emotions": "中性"
                }]
            },
            "scene_card": {
                "location": "未指定",
                "time": "未知时间",
                "atmosphere": "中性",
                "environment_sounds": []
            },
            "event_card": {
                "main_event": "段落事件",
                "sub_events": [],
                "significance": "中等"
            },
            "emotion_card": {
                "overall_tone": "中性",
                "emotion_changes": []
            },
            "audio_script_card": {
                "voice_direction": "正常语调",
                "pacing": "标准节奏",
                "background_music": "轻音乐",
                "sound_effects": []
            },
            "_metadata": {
                "segment_index": segment_index,
                "segment_text": segment_text,
                "analysis_time": datetime.utcnow().isoformat(),
                "model_used": "fallback",
                "is_fallback": True
            }
        }
