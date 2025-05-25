from typing import Dict, Any, Optional
import logging
import os
import sys
from pathlib import Path

from .engine import TTSEngine

# Add MegaTTS3 to Python path
MEGATTS3_PATH = Path(__file__).parent.parent.parent.parent.parent / "MegaTTS3"
sys.path.append(str(MEGATTS3_PATH))

try:
    from inference import TTSInference
except ImportError as e:
    logging.error(f"Failed to import MegaTTS3: {e}")
    raise

class MegaTTS3Adapter(TTSEngine):
    """Adapter for MegaTTS3 engine"""

    def __init__(self, model_path: str):
        self._logger = logging.getLogger(__name__)
        self._model_path = model_path
        self._tts = TTSInference(model_path)
        self._available_voices = self._load_available_voices()

    def _load_available_voices(self) -> Dict[str, Dict[str, Any]]:
        """Load available voice metadata from MegaTTS3"""
        voices = {}
        try:
            # TODO: Implement actual voice loading from MegaTTS3
            # This is a placeholder
            voices = {
                "female_1": {
                    "name": "Female Voice 1",
                    "gender": "female",
                    "description": "Young female voice"
                },
                "male_1": {
                    "name": "Male Voice 1", 
                    "gender": "male",
                    "description": "Adult male voice"
                }
            }
        except Exception as e:
            self._logger.error(f"Failed to load voices: {e}")
        return voices

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
        """Synthesize text using MegaTTS3"""
        try:
            # Convert parameters to MegaTTS3 format
            params = {
                "text": text,
                "voice_id": voice_id,
                "emotion": emotion_type,
                "emotion_intensity": emotion_intensity,
                "speed": speed_scale,
                "pitch": pitch_scale,
                "energy": energy_scale,
                **kwargs
            }
            
            # Call MegaTTS3 inference
            wav_data = self._tts.synthesize(**params)
            return wav_data

        except Exception as e:
            self._logger.error(f"MegaTTS3 synthesis failed: {e}")
            raise

    async def get_available_voices(self) -> Dict[str, Dict[str, Any]]:
        """Get available MegaTTS3 voices"""
        return self._available_voices.copy()