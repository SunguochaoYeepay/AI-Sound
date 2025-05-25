from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum
import logging

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

class TTSEngineRouter:
    """Routes TTS requests to appropriate engine implementations"""

    def __init__(self):
        self._engines: Dict[TTSEngineType, TTSEngine] = {}
        self._logger = logging.getLogger(__name__)

    def register_engine(self, engine_type: TTSEngineType, engine: TTSEngine):
        """Register a TTS engine implementation"""
        self._engines[engine_type] = engine
        self._logger.info(f"Registered TTS engine: {engine_type.value}")

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
        
        # 预留ESPnet-TTS分支
        if engine_type.value == "espnet":
            from .espnet_adapter import synthesize as espnet_synthesize
            return await espnet_synthesize(text, **kwargs)
        
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
            voices = await engine.get_available_voices()
            for voice_id, metadata in voices.items():
                all_voices[f"{eng_type.value}:{voice_id}"] = {
                    **metadata,
                    "engine": eng_type.value
                }
        return all_voices