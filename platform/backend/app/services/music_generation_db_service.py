"""
音乐生成数据库服务
处理音乐生成相关的数据库操作和数据持久化
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func

from ..models.music_generation import (
    MusicGenerationTask, MusicSceneAnalysis, GeneratedMusicFile,
    MusicGenerationBatch, MusicStyleTemplate, MusicGenerationUsageLog,
    MusicGenerationSettings, MusicGenerationStatus, MusicSceneType, FadeMode
)

logger = logging.getLogger(__name__)


class MusicGenerationDatabaseService:
    """音乐生成数据库服务"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    # ========== 音乐生成任务相关操作 ==========
    
    def create_generation_task(self, 
                             chapter_id: str,
                             content: str,
                             user_id: Optional[int] = None,
                             novel_project_id: Optional[int] = None,
                             **kwargs) -> MusicGenerationTask:
        """创建音乐生成任务"""
        try:
            task_id = str(uuid.uuid4())
            
            task = MusicGenerationTask(
                task_id=task_id,
                chapter_id=chapter_id,
                content=content,
                user_id=user_id,
                novel_project_id=novel_project_id,
                target_duration=kwargs.get('target_duration', 30),
                custom_style=kwargs.get('custom_style'),
                volume_level=kwargs.get('volume_level', -12.0),
                fade_mode=FadeMode(kwargs.get('fade_mode', 'standard')),
                fade_in=kwargs.get('fade_in', 2.0),
                fade_out=kwargs.get('fade_out', 2.0),
                user_preferences=kwargs.get('user_preferences', {})
            )
            
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            
            logger.info(f"创建音乐生成任务成功: {task_id}")
            return task
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建音乐生成任务失败: {str(e)}")
            raise
    
    def get_generation_task(self, task_id: str) -> Optional[MusicGenerationTask]:
        """获取音乐生成任务"""
        try:
            return self.db.query(MusicGenerationTask).filter(
                MusicGenerationTask.task_id == task_id
            ).first()
        except Exception as e:
            logger.error(f"获取音乐生成任务失败: {str(e)}")
            return None
    
    def get_style_templates(self, 
                          category: Optional[str] = None,
                          is_active: bool = True,
                          is_public: bool = True) -> List[MusicStyleTemplate]:
        """获取风格模板列表"""
        try:
            query = self.db.query(MusicStyleTemplate).filter(
                MusicStyleTemplate.is_active == is_active
            )
            
            if is_public:
                query = query.filter(MusicStyleTemplate.is_public == True)
            
            if category:
                query = query.filter(MusicStyleTemplate.category == category)
            
            return query.order_by(asc(MusicStyleTemplate.name)).all()
            
        except Exception as e:
            logger.error(f"获取风格模板失败: {str(e)}")
            return []
    
    def get_setting(self, setting_key: str) -> Optional[str]:
        """获取系统设置"""
        try:
            setting = self.db.query(MusicGenerationSettings).filter(
                MusicGenerationSettings.setting_key == setting_key,
                MusicGenerationSettings.is_active == True
            ).first()
            
            return setting.setting_value if setting else None
            
        except Exception as e:
            logger.error(f"获取系统设置失败: {str(e)}")
            return None
    
    def get_generation_stats(self, 
                           user_id: Optional[int] = None,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """获取生成统计信息"""
        try:
            query = self.db.query(MusicGenerationTask)
            
            if user_id:
                query = query.filter(MusicGenerationTask.user_id == user_id)
            
            if start_date:
                query = query.filter(MusicGenerationTask.created_at >= start_date)
            
            if end_date:
                query = query.filter(MusicGenerationTask.created_at <= end_date)
            
            total_tasks = query.count()
            completed_tasks = query.filter(MusicGenerationTask.status == MusicGenerationStatus.COMPLETED).count()
            failed_tasks = query.filter(MusicGenerationTask.status == MusicGenerationStatus.FAILED).count()
            
            return {
                "total_generations": total_tasks,
                "successful_generations": completed_tasks,
                "failed_generations": failed_tasks,
                "success_rate": completed_tasks / total_tasks if total_tasks > 0 else 0.0,
                "average_generation_time": 0.0,
                "most_popular_styles": []
            }
            
        except Exception as e:
            logger.error(f"获取生成统计失败: {str(e)}")
            return {
                "total_generations": 0,
                "successful_generations": 0,
                "failed_generations": 0,
                "success_rate": 0.0,
                "average_generation_time": 0.0,
                "most_popular_styles": []
            }


def get_music_generation_db_service(db_session: Session) -> MusicGenerationDatabaseService:
    """获取音乐生成数据库服务实例"""
    return MusicGenerationDatabaseService(db_session) 