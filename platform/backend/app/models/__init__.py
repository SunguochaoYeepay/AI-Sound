"""
数据模型包
包含所有SQLAlchemy模型定义
"""

# 导入基类
from .base import Base, BaseModel, TimestampMixin

# 导入主要模型
from .book import Book
from .chapter import BookChapter
from .audio import AudioFile
from .project import NovelProject
from .voice import VoiceProfile
from .analysis import AnalysisSession, AnalysisResult
from .system import SystemLog, UsageStats, UserPreset
from .environment_sound import (
    EnvironmentSound,
    EnvironmentSoundCategory,
    EnvironmentSoundTag,
    EnvironmentSoundFavorite
)

# 导出所有模型
__all__ = [
    "Base",
    "BaseModel", 
    "TimestampMixin",
    "Book",
    "BookChapter",
    "AudioFile",
    "NovelProject",
    "VoiceProfile",
    "AnalysisSession",
    "AnalysisResult",
    "SystemLog",
    "UsageStats",
    "UserPreset",
    "EnvironmentSound",
    "EnvironmentSoundCategory",
    "EnvironmentSoundTag",
    "EnvironmentSoundFavorite"
]