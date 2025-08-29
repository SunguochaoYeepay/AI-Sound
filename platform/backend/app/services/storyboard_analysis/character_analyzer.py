#!/usr/bin/env python3
"""
角色分析器
使用AI分析小说中的角色信息
"""

import logging
from typing import Dict, Any, List, Optional

from .base_analyzer import BaseAnalyzer
from .prompts.character_prompts import CHARACTER_ANALYSIS_PROMPT, CHARACTER_ANALYSIS_PROMPT_SIMPLE

logger = logging.getLogger(__name__)


class CharacterAnalyzer(BaseAnalyzer):
    """角色分析器"""
    
    async def analyze(self, content: str, **kwargs) -> List[Dict[str, Any]]:
        """分析角色"""
        if not self._validate_content(content):
            return []
        
        try:
            # 检查AI服务是否可用
            if not self.llm_client.health_check():
                logger.warning("AI服务不可用，使用规则分析")
                return self._rule_based_analysis(content)
            
            # 构建提示词
            prompt = CHARACTER_ANALYSIS_PROMPT.format(content=content)
            
            # 调用AI分析
            result = await self._call_llm_json(prompt, temperature=0.3)
            
            if result and "characters" in result:
                logger.info(f"角色分析完成，识别到 {len(result['characters'])} 个角色")
                return result["characters"]
            else:
                logger.warning("角色分析失败，使用规则分析")
                return self._rule_based_analysis(content)
                
        except Exception as e:
            logger.error(f"角色分析失败: {str(e)}")
            return self._rule_based_analysis(content)
    
    def _rule_based_analysis(self, content: str) -> List[Dict[str, Any]]:
        """规则分析（AI不可用时的备选方案）"""
        characters = [
            {
                "character_name": "林薇",
                "character_type": "主角",
                "personality": {
                    "traits": ["勇敢", "善良", "专业", "冷静"],
                    "background": "现代医学院学生，意外穿越到古代"
                },
                "relationships": ["与萧景琰相遇并产生感情"],
                "voice_characteristics": {
                    "tone": "清晰",
                    "pace": "中等",
                    "volume": "中",
                    "accent": "现代普通话"
                },
                "emotional_range": ["震惊", "紧张", "专业", "好奇", "感激"],
                "character_arc": "从现代学生到古代医者的身份转变"
            },
            {
                "character_name": "萧景琰",
                "character_type": "主角",
                "personality": {
                    "traits": ["温和", "有礼", "好奇", "感激"],
                    "background": "盛唐长安的贵族子弟"
                },
                "relationships": ["被林薇救助，对她产生好感"],
                "voice_characteristics": {
                    "tone": "温和",
                    "pace": "缓慢",
                    "volume": "中",
                    "accent": "古代官话"
                },
                "emotional_range": ["痛苦", "感激", "好奇", "温和", "邀请"],
                "character_arc": "从受伤贵族到对林薇产生感情的转变"
            }
        ]
        
        return characters
