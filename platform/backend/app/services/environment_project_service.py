"""
环境音项目服务
封装环境音项目的CRUD操作
"""

import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.environment_generation import EnvironmentProject
from app.models.novel_project import NovelProject

logger = logging.getLogger(__name__)


class EnvironmentProjectService:
    """环境音项目服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_novel_project_id(self, novel_project_id: int) -> Optional[EnvironmentProject]:
        """根据合成项目ID获取环境音项目"""
        return self.db.query(EnvironmentProject).filter(
            EnvironmentProject.novel_project_id == novel_project_id
        ).first()
    
    def create_or_update(
        self, 
        novel_project_id: int, 
        analysis_result: Dict[str, Any],
        analysis_stats: Dict[str, Any],
        analysis_options: Dict[str, Any] = None
    ) -> EnvironmentProject:
        """创建或更新环境音项目"""
        
        # 查找现有项目
        env_project = self.get_by_novel_project_id(novel_project_id)
        
        if env_project:
            # 更新现有项目
            env_project.analysis_result = analysis_result
            env_project.matching_result = {
                'analysis_stats': analysis_stats,
                'session_stage': 'analyzed'
            }
            env_project.analysis_options = analysis_options or {}
            env_project.updated_at = datetime.utcnow()
            
            logger.info(f"更新环境音项目: {env_project.id}")
        else:
            # 获取合成项目信息
            novel_project = self.db.query(NovelProject).filter(
                NovelProject.id == novel_project_id
            ).first()
            
            if not novel_project:
                raise ValueError(f"合成项目 {novel_project_id} 不存在")
            
            # 创建新项目
            env_project = EnvironmentProject(
                novel_project_id=novel_project_id,
                name=f"环境音分析_{novel_project.name}",
                description=f"基于项目 '{novel_project.name}' 的环境音分析",
                status="analyzed",
                analysis_result=analysis_result,
                matching_result={
                    'analysis_stats': analysis_stats,
                    'session_stage': 'analyzed'
                },
                analysis_options=analysis_options or {},
                book_name=novel_project.name,
                chapter_name="第1章"
            )
            
            self.db.add(env_project)
            logger.info(f"创建环境音项目: {novel_project_id}")
        
        self.db.commit()
        self.db.refresh(env_project)
        return env_project
    
    def update_track_config(
        self, 
        novel_project_id: int, 
        track_index: int, 
        track_config: Dict[str, Any]
    ) -> bool:
        """更新轨道配置"""
        
        env_project = self.get_by_novel_project_id(novel_project_id)
        if not env_project or not env_project.analysis_result:
            return False
        
        environment_tracks = env_project.analysis_result.get('environment_tracks', [])
        if track_index >= len(environment_tracks):
            return False
        
        # 更新轨道配置
        track = environment_tracks[track_index]
        track.update(track_config)
        track['user_confirmed'] = True
        
        # 更新项目
        env_project.analysis_result['environment_tracks'] = environment_tracks
        env_project.updated_at = datetime.utcnow()
        
        self.db.commit()
        logger.info(f"更新轨道配置: 项目{novel_project_id}, 轨道{track_index}")
        return True
    
    def finalize_project(self, novel_project_id: int) -> bool:
        """完成环境音项目"""
        
        env_project = self.get_by_novel_project_id(novel_project_id)
        if not env_project:
            return False
        
        env_project.status = "completed"
        env_project.matching_result['session_stage'] = 'completed'
        env_project.updated_at = datetime.utcnow()
        
        self.db.commit()
        logger.info(f"完成环境音项目: {novel_project_id}")
        return True
    
    def delete_by_novel_project_id(self, novel_project_id: int) -> bool:
        """删除环境音项目"""
        
        env_project = self.get_by_novel_project_id(novel_project_id)
        if not env_project:
            return False
        
        self.db.delete(env_project)
        self.db.commit()
        logger.info(f"删除环境音项目: {novel_project_id}")
        return True
