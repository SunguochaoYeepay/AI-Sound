"""
应用配置管理
统一管理环境变量和配置选项
"""

import os
from typing import Optional, List
from dataclasses import dataclass, field

@dataclass
class Settings:
    """应用设置配置类"""
    
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://ai_sound_user:ai_sound_password@localhost:5432/ai_sound")
    
    # TTS服务配置
    TTS_SERVER_URL: str = os.getenv("MEGATTS3_URL", "http://localhost:7929")
    TTS_TIMEOUT: int = int(os.getenv("TTS_TIMEOUT", "300"))
    
    # 🎵 SongGeneration音乐生成服务配置
    SONGGENERATION_URL: str = os.getenv("SONGGENERATION_URL", "http://localhost:7863")
    SONGGENERATION_TIMEOUT: int = int(os.getenv("SONGGENERATION_TIMEOUT", "300"))
    SONGGENERATION_MAX_RETRIES: int = int(os.getenv("SONGGENERATION_MAX_RETRIES", "3"))
    SONGGENERATION_MAX_CONCURRENT: int = int(os.getenv("SONGGENERATION_MAX_CONCURRENT", "2"))
    
    # 🎵 音乐生成默认配置
    MUSIC_DEFAULT_DURATION: int = int(os.getenv("MUSIC_DEFAULT_DURATION", "30"))
    MUSIC_MAX_DURATION: int = int(os.getenv("MUSIC_MAX_DURATION", "300"))
    MUSIC_DEFAULT_VOLUME: float = float(os.getenv("MUSIC_DEFAULT_VOLUME", "-12.0"))
    MUSIC_CLEANUP_HOURS: int = int(os.getenv("MUSIC_CLEANUP_HOURS", "24"))
    
    # Dify配置
    DIFY_API_KEY: str = os.getenv("DIFY_API_KEY", "")
    DIFY_BASE_URL: str = os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1")
    DIFY_NOVEL_WORKFLOW_ID: Optional[str] = os.getenv("DIFY_NOVEL_WORKFLOW_ID")
    DIFY_TIMEOUT: int = int(os.getenv("DIFY_TIMEOUT", "120"))
    DIFY_MAX_RETRIES: int = int(os.getenv("DIFY_MAX_RETRIES", "3"))
    
    # 应用配置
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "ai-sound-secret-key-change-in-production")
    
    # 文件存储配置
    STORAGE_PATH: str = os.getenv("STORAGE_PATH", "storage")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "104857600"))  # 100MB
    ALLOWED_AUDIO_EXTENSIONS: List[str] = field(default_factory=lambda: [".wav", ".mp3", ".flac", ".m4a", ".ogg"])
    ALLOWED_TEXT_EXTENSIONS: List[str] = field(default_factory=lambda: [".txt", ".docx", ".pdf"])
    
    # WebSocket配置
    WS_HEARTBEAT_INTERVAL: int = int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))
    WS_MAX_CONNECTIONS: int = int(os.getenv("WS_MAX_CONNECTIONS", "100"))
    
    # 性能配置
    MAX_CONCURRENT_SYNTHESIS: int = int(os.getenv("MAX_CONCURRENT_SYNTHESIS", "3"))
    ANALYSIS_CACHE_TTL: int = int(os.getenv("ANALYSIS_CACHE_TTL", "3600"))  # 1小时
    
    def __post_init__(self):
        """配置验证和后处理"""
        # 创建必要的目录
        os.makedirs(self.STORAGE_PATH, exist_ok=True)
        os.makedirs(f"{self.STORAGE_PATH}/audio", exist_ok=True)
        os.makedirs(f"{self.STORAGE_PATH}/uploads", exist_ok=True)
        os.makedirs(f"{self.STORAGE_PATH}/temp", exist_ok=True)
        
        # 🎵 创建音乐生成相关目录
        os.makedirs(f"{self.STORAGE_PATH}/generated_music", exist_ok=True)
        os.makedirs("data/audio/generated_music", exist_ok=True)
        
        # Dify配置验证
        if not self.DIFY_API_KEY and not self.DEBUG:
            import warnings
            warnings.warn("DIFY_API_KEY未配置，智能分析功能将使用Mock模式")
        
        # 🎵 SongGeneration配置验证
        if not self.DEBUG:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"SongGeneration服务配置: {self.SONGGENERATION_URL}")

# 全局配置实例
settings = Settings()

def get_settings() -> Settings:
    """获取配置实例"""
    return settings 