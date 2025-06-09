"""
外部服务客户端包
包含与外部TTS服务和API的客户端实现
"""

from .tts_client import TTSClient, TTSProvider, tts_client, init_tts_client
from .audio_processor import AudioProcessor, audio_processor
from .file_manager import FileManager, file_manager

__all__ = [
    'TTSClient',
    'TTSProvider', 
    'tts_client',
    'init_tts_client',
    'AudioProcessor',
    'audio_processor',
    'FileManager',
    'file_manager'
] 