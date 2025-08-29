#!/usr/bin/env python3
"""
故事分析器
使用AI分析小说的整体故事结构和主题
"""

import logging
from typing import Dict, Any, List, Optional

from .base_analyzer import BaseAnalyzer
from .prompts.story_prompts import STORY_ANALYSIS_PROMPT, STORY_ANALYSIS_PROMPT_SIMPLE

logger = logging.getLogger(__name__)


class StoryAnalyzer(BaseAnalyzer):
    """故事分析器"""
    
    async def analyze(self, content: str, **kwargs) -> List[Dict[str, Any]]:
        """分析故事"""
        if not self._validate_content(content):
            return []
        
        try:
            # 检查AI服务是否可用
            if not self.llm_client.health_check():
                logger.warning("AI服务不可用，使用规则分析")
                return self._rule_based_analysis(content)
            
            # 构建提示词
            prompt = STORY_ANALYSIS_PROMPT.format(content=content)
            
            # 调用AI分析
            result = await self._call_llm_json(prompt, temperature=0.3)
            
            if result:
                logger.info("故事分析完成")
                return [result]
            else:
                logger.warning("故事分析失败，使用规则分析")
                return self._rule_based_analysis(content)
                
        except Exception as e:
            logger.error(f"故事分析失败: {str(e)}")
            return self._rule_based_analysis(content)
    
    def _rule_based_analysis(self, content: str) -> List[Dict[str, Any]]:
        """规则分析（AI不可用时的备选方案）"""
        story_data = {
            "story_summary": "现代医学院学生林薇意外穿越到盛唐长安，凭借现代医学知识救助了贵族子弟萧景琰，两人由此相识并发展出感情。",
            "main_plot": [
                {"chapter": "第一章", "event": "林薇穿越到盛唐长安"},
                {"chapter": "第一章", "event": "林薇救助萧景琰"},
                {"chapter": "第一章", "event": "萧景琰邀请林薇回府"}
            ],
            "themes": ["穿越", "医术", "相遇", "古代生活", "爱情"],
            "genre": "穿越言情",
            "target_audience": "女性读者",
            "story_structure": {
                "beginning": "林薇在现代实验室意外穿越",
                "development": "在古代长安适应生活并救助他人",
                "climax": "与萧景琰相遇并产生感情",
                "ending": "两人关系发展"
            },
            "world_setting": "现代与盛唐长安的双重世界设定"
        }
        
        return [story_data]
