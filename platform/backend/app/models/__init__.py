"""
数据模型模块
导出所有数据模型
"""

from .base import Base, BaseModel
from .book import Book
from .book_chapter import BookChapter  
from .audio import AudioFile
from .analysis_result import AnalysisResult
from .analysis_session import AnalysisSession
from .storyboard_cards import (
    StoryboardAnalysisSession, BaseStoryboardCard, StoryCard, CharacterCard,
    SceneCard, EventCard, EmotionCard, AudioStoryboardCard
)
from .novel_project import NovelProject
from .voice import VoiceProfile
from .character import Character

from .system import SystemLog, UsageStats, UserPreset
from .environment_sound import (
    EnvironmentSound, EnvironmentSoundCategory, EnvironmentSoundTag,
    EnvironmentSoundFavorite, EnvironmentSoundUsageLog, EnvironmentSoundPreset
)
from .backup import (
    BackupTask, BackupConfig, RestoreTask, BackupSchedule, BackupStats,
    TaskStatus, BackupType, StorageLocation, RestoreType
)
from .auth import (
    User, Role, Permission, UserSession, LoginLog, UserStatus,
    user_roles, role_permissions
)

from .synthesis_task import SynthesisTask
from .text_segment import TextSegment
from .environment_generation import (
    EnvironmentProject, EnvironmentGenerationSession, EnvironmentTrackConfig, 
    EnvironmentAudioMixingJob, EnvironmentGenerationLog
)
from .background_music import BackgroundMusic, MusicCategory

# 🎵 音乐生成相关模型
from .music_generation import (
    MusicGenerationTask, MusicSceneAnalysis, GeneratedMusicFile,
    MusicGenerationBatch, MusicStyleTemplate, MusicGenerationUsageLog,
    MusicGenerationSettings, MusicGenerationStatus, MusicSceneType, FadeMode
)

# 🖼️ 图片生成相关模型
from .image_generation import ImageGenerationTask, ImageGenerationPreset

__all__ = [
    'Base',
    'BaseModel', 
    'Book',
    'BookChapter',
    'AudioFile',
    'NovelProject',
    'VoiceProfile',
    'Character',
    'AnalysisSession',
    'AnalysisResult',
    'StoryboardAnalysisSession',
    'BaseStoryboardCard',
    'StoryCard',
    'CharacterCard',
    'SceneCard',
    'EventCard',
    'EmotionCard',
    'AudioStoryboardCard',
    'SystemLog',
    'UsageStats',
    'UserPreset',
    'EnvironmentSound',
    'EnvironmentSoundCategory',
    'EnvironmentSoundTag',
    'EnvironmentSoundFavorite',
    'EnvironmentSoundUsageLog',
    'EnvironmentSoundPreset',
    'BackupTask',
    'BackupConfig',
    'RestoreTask',
    'BackupSchedule',
    'BackupStats',
    'TaskStatus',
    'BackupType',
    'StorageLocation',
    'RestoreType',
    'User',
    'Role',
    'Permission',
    'UserSession',
    'LoginLog',
    'UserStatus',
    'user_roles',
    'role_permissions',

    # 其他模型
    'SynthesisTask',
    'TextSegment',
    'EnvironmentProject',
    'EnvironmentGenerationSession',
    'EnvironmentTrackConfig',
    'EnvironmentAudioMixingJob', 
    'EnvironmentGenerationLog',
    # 背景音乐模型
    'BackgroundMusic',
    'MusicCategory',
    # 🎵 音乐生成模型
    'MusicGenerationTask',
    'MusicSceneAnalysis',
    'GeneratedMusicFile',
    'MusicGenerationBatch',
    'MusicStyleTemplate',
    'MusicGenerationUsageLog',
    'MusicGenerationSettings',
    'MusicGenerationStatus',
    'MusicSceneType',
    'FadeMode',
    # 🖼️ 图片生成模型
    'ImageGenerationTask',
    'ImageGenerationPreset',
]