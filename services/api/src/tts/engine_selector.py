"""
TTS 引擎选择策略
"""

import logging
from typing import Dict, Any, Optional
from .engine import TTSEngineType

logger = logging.getLogger(__name__)

class EngineSelector:
    """TTS 引擎选择策略"""
    
    def select_engine(
        self,
        text: str,
        requirements: Optional[Dict[str, Any]] = None
    ) -> TTSEngineType:
        """
        根据文本和需求选择合适的引擎
        
        Args:
            text: 输入文本
            requirements: 额外的需求参数
            
        Returns:
            适合的引擎类型
        """
        requirements = requirements or {}
        
        # 根据文本长度选择引擎
        # 长文本倾向于使用 ESPnet（更稳定）
        if len(text) > 300:
            logger.debug(f"文本长度 {len(text)} > 300，选择 ESPnet 引擎")
            return TTSEngineType.ESPNET
        
        # 有对话的文本使用 MegaTTS3（更有表现力）
        if any(quote in text for quote in ['"', '"', '「', '」', ''', ''']):
            logger.debug("文本包含对话，选择 MegaTTS3 引擎")
            return TTSEngineType.MEGATTS3
        
        # 情感需求分析
        emotion_type = requirements.get("emotion_type")
        emotion_intensity = requirements.get("emotion_intensity", 0)
        
        # 有明确情感需求的使用 MegaTTS3
        if emotion_type and emotion_type != "neutral" and emotion_intensity > 0.3:
            logger.debug(f"情感需求 {emotion_type}（强度 {emotion_intensity}），选择 MegaTTS3 引擎")
            return TTSEngineType.MEGATTS3
        
        # 特殊场景判断
        if requirements.get("formal", False):
            logger.debug("正式场景需求，选择 ESPnet 引擎")
            return TTSEngineType.ESPNET
        
        # 用户明确指定引擎
        engine_preference = requirements.get("engine_preference")
        if engine_preference:
            try:
                logger.debug(f"用户指定引擎 {engine_preference}")
                return TTSEngineType(engine_preference)
            except ValueError:
                logger.warning(f"无效的引擎首选项: {engine_preference}，使用默认引擎")
        
        # 默认使用 MegaTTS3
        logger.debug("使用默认引擎 MegaTTS3")
        return TTSEngineType.MEGATTS3