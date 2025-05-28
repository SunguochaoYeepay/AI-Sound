from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
import logging
import time

class TTSEngineType(Enum):
    MEGATTS3 = "megatts3"
    ESPNET = "espnet"
    EDGE = "edge"
    BAIDU = "baidu"
    XUNFEI = "xunfei"

class TTSEngine(ABC):
    """Base class for all TTS engines"""
    
    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        emotion_type: Optional[str] = None,
        emotion_intensity: float = 0.5,
        speed_scale: float = 1.0,
        pitch_scale: float = 1.0,
        energy_scale: float = 1.0,
        **kwargs: Dict[str, Any]
    ) -> bytes:
        """Synthesize text to speech
        
        Args:
            text: Input text to synthesize
            voice_id: Voice ID/name to use
            emotion_type: Emotion type (happy, sad, angry, etc.)
            emotion_intensity: Emotion intensity from 0.0 to 1.0
            speed_scale: Speed scaling factor
            pitch_scale: Pitch scaling factor  
            energy_scale: Energy scaling factor
            **kwargs: Additional engine-specific parameters
            
        Returns:
            WAV audio data as bytes
        """
        pass

    @abstractmethod
    async def get_available_voices(self) -> Dict[str, Dict[str, Any]]:
        """Get available voices for this engine
            
        Returns:
            Dict mapping voice_id to voice metadata
        """
        pass
        
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the engine is healthy
        
        Returns:
            True if the engine is healthy, False otherwise
        """
        pass

class TTSEngineRouter:
    """Routes TTS requests to appropriate engine implementations"""

    def __init__(self):
        self._engines: Dict[TTSEngineType, TTSEngine] = {}
        self._logger = logging.getLogger(__name__)
        self._health_status: Dict[str, Dict[str, Any]] = {}
        self._last_health_check: float = 0

    def register_engine(self, engine_type: TTSEngineType, engine: TTSEngine):
        """Register a TTS engine implementation"""
        self._engines[engine_type] = engine
        self._logger.info(f"Registered TTS engine: {engine_type.value}")
        
    def get_engine(self, engine_type: TTSEngineType) -> Optional[TTSEngine]:
        """Get a registered engine by type"""
        return self._engines.get(engine_type)
        
    def get_registered_engines(self) -> Dict[TTSEngineType, TTSEngine]:
        """Get all registered engines"""
        return self._engines.copy()

    async def synthesize(
        self, 
        engine_type: TTSEngineType,
        text: str,
        voice_id: str,
        **kwargs: Dict[str, Any]
    ) -> bytes:
        """Route synthesis request to appropriate engine"""
        if engine_type not in self._engines:
            raise ValueError(f"TTS engine {engine_type.value} not registered")
        
        engine = self._engines[engine_type]
        return await engine.synthesize(text, voice_id, **kwargs)

    async def get_available_voices(
        self, 
        engine_type: Optional[TTSEngineType] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Get available voices, optionally filtered by engine type"""
        if engine_type:
            if engine_type not in self._engines:
                raise ValueError(f"TTS engine {engine_type.value} not registered")
            return await self._engines[engine_type].get_available_voices()
            
        # Combine voices from all engines
        all_voices = {}
        for eng_type, engine in self._engines.items():
            try:
                voices = await engine.get_available_voices()
                for voice_id, metadata in voices.items():
                    all_voices[f"{eng_type.value}:{voice_id}"] = {
                        **metadata,
                        "engine": eng_type.value
                    }
            except Exception as e:
                self._logger.error(f"获取引擎 {eng_type.value} 音色列表失败: {str(e)}")
        return all_voices
        
    async def check_engine_health(self, engine_type: TTSEngineType) -> bool:
        """Check health of a specific engine"""
        if engine_type not in self._engines:
            return False
            
        try:
            engine = self._engines[engine_type]
            is_healthy = await engine.health_check()
            
            # 更新健康状态
            self._health_status[engine_type.value] = {
                "healthy": is_healthy,
                "last_check": time.time(),
                "message": "OK" if is_healthy else "Failed health check"
            }
            
            return is_healthy
        except Exception as e:
            self._logger.error(f"引擎 {engine_type.value} 健康检查异常: {str(e)}")
            
            # 更新健康状态
            self._health_status[engine_type.value] = {
                "healthy": False,
                "last_check": time.time(),
                "message": str(e)
            }
            
            return False
            
    async def check_all_engines_health(self) -> Dict[str, bool]:
        """Check health of all registered engines"""
        results = {}
        for engine_type in self._engines.keys():
            results[engine_type.value] = await self.check_engine_health(engine_type)
            
        self._last_health_check = time.time()
        return results
        
    def get_health_status(self) -> Dict[str, Dict[str, Any]]:
        """Get cached health status of all engines"""
        return self._health_status