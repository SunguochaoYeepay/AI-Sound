"""
环境音项目数据服务
提取重复的项目查找和轨道处理逻辑
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.services.environment_project_service import EnvironmentProjectService
from app.models.environment_generation import EnvironmentProject

logger = logging.getLogger(__name__)


class EnvironmentProjectDataService:
    """环境音项目数据服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.env_service = EnvironmentProjectService(db)
    
    def get_project_with_validation(self, project_id: int) -> EnvironmentProject:
        """获取项目并进行基础验证"""
        env_project = self.env_service.get_by_project_id(project_id)
        
        if not env_project:
            raise ValueError(f"未找到环境音项目: {project_id}")
        
        if not env_project.analysis_result:
            raise ValueError(f"环境音项目没有分析结果: {project_id}")
        
        return env_project
    
    def extract_environment_tracks(self, env_project: EnvironmentProject, chapter_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """提取环境音轨道数据"""
        analysis_result = env_project.analysis_result
        environment_tracks = []
        
        logger.info(f"[PROJECT_DATA] 分析结果类型: {type(analysis_result)}")
        
        # 检查是否是多章节格式（键是章节ID）
        if isinstance(analysis_result, dict) and not analysis_result.get('environment_tracks'):
            # 多章节格式
            if chapter_id:
                # 只处理指定章节的轨道
                if str(chapter_id) in analysis_result:
                    chapter_analysis = analysis_result[str(chapter_id)]
                    if isinstance(chapter_analysis, dict) and chapter_analysis.get('environment_tracks'):
                        environment_tracks = chapter_analysis['environment_tracks']
                        logger.info(f"[PROJECT_DATA] 章节 {chapter_id} 轨道数量: {len(environment_tracks)}")
                else:
                    logger.warning(f"[PROJECT_DATA] 未找到章节 {chapter_id}")
            else:
                # 收集所有章节的环境轨道
                sorted_chapter_ids = sorted(analysis_result.keys(), key=lambda x: int(x))
                logger.info(f"[PROJECT_DATA] 多章节格式，收集所有章节: {sorted_chapter_ids}")
                
                for chapter_id_str in sorted_chapter_ids:
                    chapter_analysis = analysis_result[chapter_id_str]
                    if isinstance(chapter_analysis, dict) and chapter_analysis.get('environment_tracks'):
                        environment_tracks.extend(chapter_analysis['environment_tracks'])
        else:
            # 单章节格式，直接获取environment_tracks
            environment_tracks = analysis_result.get('environment_tracks', [])
            logger.info(f"[PROJECT_DATA] 单章节格式，轨道数量: {len(environment_tracks)}")
        
        return environment_tracks
    
    def get_track_by_index(self, project_id: int, track_index: int) -> Tuple[EnvironmentProject, Dict[str, Any]]:
        """根据索引获取轨道数据"""
        env_project = self.get_project_with_validation(project_id)
        environment_tracks = self.extract_environment_tracks(env_project)
        
        if track_index >= len(environment_tracks):
            raise ValueError("轨道索引超出范围")
        
        return env_project, environment_tracks[track_index]
    
    def filter_tracks_for_generation(self, tracks: List[Dict[str, Any]], track_indices: Optional[List[int]] = None) -> List[Tuple[int, Dict[str, Any]]]:
        """筛选需要生成的轨道"""
        tracks_to_generate = []
        
        if track_indices:
            # 生成指定轨道
            for index in track_indices:
                if 0 <= index < len(tracks):
                    track = tracks[index]
                    keywords = track.get('environment_keywords') or []
                    if keywords:
                        tracks_to_generate.append((index, track))
                    else:
                        logger.warning(f"轨道 {index} 无环境关键词，跳过生成")
                else:
                    logger.warning(f"轨道索引 {index} 超出范围，跳过")
        else:
            # 仅生成有关键词的轨道
            for i, track in enumerate(tracks):
                keywords = track.get('environment_keywords') or []
                if keywords:
                    tracks_to_generate.append((i, track))
        
        return tracks_to_generate
    
    def filter_tracks_for_mixing(self, tracks: List[Dict[str, Any]], track_indices: Optional[List[int]] = None) -> List[Tuple[int, Dict[str, Any]]]:
        """筛选需要混音的轨道"""
        import os
        tracks_to_mix = []
        
        if track_indices:
            # 混音指定轨道
            for index in track_indices:
                if 0 <= index < len(tracks):
                    track = tracks[index]
                    if track.get('generated_file_path') and os.path.exists(track['generated_file_path']):
                        tracks_to_mix.append((index, track))
                    else:
                        logger.warning(f"轨道 {index} 文件不存在，跳过")
                else:
                    logger.warning(f"轨道索引 {index} 超出范围，跳过")
        else:
            # 混音所有已生成的轨道
            for i, track in enumerate(tracks):
                if track.get('generated_file_path') and os.path.exists(track['generated_file_path']):
                    tracks_to_mix.append((i, track))
                else:
                    logger.warning(f"轨道 {i} 文件不存在或无生成路径")
        
        return tracks_to_mix
