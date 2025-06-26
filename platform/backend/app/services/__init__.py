"""
智能分析系统 - 服务层
提供业务逻辑处理的核心服务类
"""

from .chapter_service import ChapterService
from .analysis_service import AnalysisService
# from .synthesis_service import SynthesisService  # 🚀 已删除
from .preset_service import PresetService
# from .dify_client import DifyClient, DifyClientFactory  # 🚀 已删除 - 文件不存在

# 🎵 新增：SongGeneration音乐生成相关服务
from .song_generation_service import get_song_generation_service
from .music_scene_analyzer import get_music_scene_analyzer
from .background_music_generation_service import get_background_music_generation_service

__all__ = [
    'ChapterService',
    'AnalysisService', 
    # 'SynthesisService',  # 🚀 已删除
    'PresetService',
    # 'DifyClient',  # 🚀 已删除
    # 'DifyClientFactory'  # 🚀 已删除
    
    # 🎵 音乐生成服务
    'get_song_generation_service',
    'get_music_scene_analyzer', 
    'get_background_music_generation_service',
] 