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
            logger.info("开始情绪分析...")
            
            # 强制使用AI分析，不进行健康检查
            chunks = self._chunk_content(content)
            logger.info(f"内容分块数量: {len(chunks)}")
            all_emotions = []
            
            for i, chunk in enumerate(chunks):
                logger.info(f"分析情绪块 {i+1}/{len(chunks)}")
                logger.info(f"块内容长度: {len(chunk)}")
                
                # 构建提示词
                prompt = self._build_prompt(chunk, chunk_index=i, total_chunks=len(chunks))
                
                # 强制调用AI分析
                logger.info("调用AI分析...")
                result = await self._call_llm_json(prompt, temperature=0.3)
                
                if result and "emotions" in result:
                    emotions = result["emotions"]
                    logger.info(f"AI识别到 {len(emotions)} 个情绪")
                    # 为每个情绪添加块索引信息
                    for emotion in emotions:
                        emotion["chunk_index"] = i
                        emotion["chunk_total"] = len(chunks)
                    all_emotions.extend(emotions)
                else:
                    logger.error(f"AI分析失败，返回结果: {result}")
                    raise Exception(f"AI分析失败，无法获取情绪数据")
            
            # 合并和去重情绪
            merged_emotions = self._merge_emotions(all_emotions)
            
            logger.info(f"情绪分析完成，识别到 {len(merged_emotions)} 个情绪")
            for i, emotion in enumerate(merged_emotions):
                logger.info(f"情绪 {i+1}: {emotion.get('emotion_type', 'Unknown')}")
            
            return merged_emotions
            
        except Exception as e:
            logger.error(f"情绪分析失败: {str(e)}")
            raise Exception(f"情绪分析失败: {str(e)}")
    
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
