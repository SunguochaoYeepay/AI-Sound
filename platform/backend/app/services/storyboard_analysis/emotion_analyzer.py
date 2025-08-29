#!/usr/bin/env python3
"""
情绪分析器
使用AI分析小说中的情绪信息
"""

import logging
from typing import Dict, Any, List, Optional

from .base_analyzer import BaseAnalyzer
from .prompts.emotion_prompts import EMOTION_ANALYSIS_PROMPT, EMOTION_ANALYSIS_PROMPT_SIMPLE

logger = logging.getLogger(__name__)


class EmotionAnalyzer(BaseAnalyzer):
    """情绪分析器"""
    
    async def analyze(self, content: str, **kwargs) -> List[Dict[str, Any]]:
        """分析情绪"""
        if not self._validate_content(content):
            return []
        
        try:
            # 检查AI服务是否可用
            if not self.llm_client.health_check():
                logger.warning("AI服务不可用，使用规则分析")
                return self._rule_based_analysis(content)
            
            # 分块处理长内容
            chunks = self._chunk_content(content)
            all_emotions = []
            
            for i, chunk in enumerate(chunks):
                logger.info(f"分析情绪块 {i+1}/{len(chunks)}")
                
                # 构建提示词
                prompt = self._build_prompt(chunk, chunk_index=i, total_chunks=len(chunks))
                
                # 调用AI分析
                result = await self._call_llm_json(prompt, temperature=0.3)
                
                if result and "emotions" in result:
                    emotions = result["emotions"]
                    # 为每个情绪添加块索引信息
                    for emotion in emotions:
                        emotion["chunk_index"] = i
                        emotion["chunk_total"] = len(chunks)
                    all_emotions.extend(emotions)
                else:
                    logger.warning(f"情绪块 {i+1} 分析失败，使用规则分析")
                    rule_emotions = self._rule_based_analysis(chunk)
                    for emotion in rule_emotions:
                        emotion["chunk_index"] = i
                        emotion["chunk_total"] = len(chunks)
                    all_emotions.extend(rule_emotions)
            
            # 合并和去重情绪
            merged_emotions = self._merge_emotions(all_emotions)
            
            logger.info(f"情绪分析完成，识别到 {len(merged_emotions)} 个情绪")
            return merged_emotions
            
        except Exception as e:
            logger.error(f"情绪分析失败: {str(e)}")
            return self._rule_based_analysis(content)
    
    def _build_prompt(self, content: str, **kwargs) -> str:
        """构建提示词"""
        chunk_index = kwargs.get("chunk_index", 0)
        total_chunks = kwargs.get("total_chunks", 1)
        
        if total_chunks > 1:
            # 多块处理时的提示词
            prompt = f"""
这是第 {chunk_index + 1}/{total_chunks} 块内容，请分析其中的情绪：

{content}

注意：这是章节的一部分，请专注于当前块中的情绪，不要重复前面块的内容。
"""
            return prompt + EMOTION_ANALYSIS_PROMPT_SIMPLE.format(content=content)
        else:
            # 单块处理
            return EMOTION_ANALYSIS_PROMPT.format(content=content)
    
    def _rule_based_analysis(self, content: str) -> List[Dict[str, Any]]:
        """规则分析（AI不可用时的备选方案）"""
        emotions = []
        
        # 分析穿越时的震惊情绪
        if "穿越" in content or "震惊" in content:
            emotions.append({
                "emotion_type": "震惊",
                "intensity": 0.9,
                "duration": {"start": "穿越瞬间", "end": "适应环境"},
                "triggers": ["意外穿越到古代"],
                "expression": ["心跳加速", "瞳孔放大", "呼吸急促"],
                "voice_impact": {"tone": "颤抖", "pace": "快速", "volume": "高"}
            })
        
        # 分析救助时的紧张情绪
        if "救助" in content or "紧张" in content:
            emotions.append({
                "emotion_type": "紧张",
                "intensity": 0.8,
                "duration": {"start": "发现伤者", "end": "救助完成"},
                "triggers": ["看到受伤的人", "需要紧急救助"],
                "expression": ["专注", "动作迅速", "表情严肃"],
                "voice_impact": {"tone": "坚定", "pace": "中等", "volume": "中"}
            })
        
        # 分析感激情绪
        if "感谢" in content or "感激" in content:
            emotions.append({
                "emotion_type": "感激",
                "intensity": 0.7,
                "duration": {"start": "被救助后", "end": "表达感谢"},
                "triggers": ["被他人救助"],
                "expression": ["眼神温和", "表情柔和", "身体放松"],
                "voice_impact": {"tone": "温和", "pace": "缓慢", "volume": "中"}
            })
        
        return emotions
    
    def _merge_emotions(self, emotions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并和去重情绪"""
        if not emotions:
            return []
        
        # 简单的去重逻辑：基于情绪类型
        seen_types = set()
        merged = []
        
        for emotion in emotions:
            emotion_type = emotion.get("emotion_type", "")
            if emotion_type and emotion_type not in seen_types:
                seen_types.add(emotion_type)
                merged.append(emotion)
        
        return merged
