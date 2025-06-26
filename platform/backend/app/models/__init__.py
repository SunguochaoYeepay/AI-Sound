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
from .novel_project import NovelProject
from .voice import VoiceProfile

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
from .audio_editor import (
    AudioVideoProject, EditorTrack, AudioClip, EditorSettings, RenderTask
)
from .synthesis_task import SynthesisTask
from .text_segment import TextSegment
from .environment_generation import (
    EnvironmentGenerationSession, EnvironmentTrackConfig, 
    EnvironmentAudioMixingJob, EnvironmentGenerationLog
)
from .background_music import BackgroundMusic, MusicCategory

# 🎵 音乐生成相关模型
from .music_generation import (
    MusicGenerationTask, MusicSceneAnalysis, GeneratedMusicFile,
    MusicGenerationBatch, MusicStyleTemplate, MusicGenerationUsageLog,
    MusicGenerationSettings, MusicGenerationStatus, MusicSceneType, FadeMode
)

__all__ = [
    'Base',
    'BaseModel', 
    'Book',
    'BookChapter',
    'AudioFile',
    'NovelProject',
    'VoiceProfile',
    'AnalysisSession',
    'AnalysisResult',
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
    # 音频编辑器模型
    'AudioVideoProject',
    'EditorTrack', 
    'AudioClip',
    'EditorSettings',
    'RenderTask',
    # 其他模型
    'SynthesisTask',
    'TextSegment',
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
    'FadeMode'
]