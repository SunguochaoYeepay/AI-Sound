"""
音视频编辑器服务
与现有模块深度集成，提供完整的编辑功能
"""
import os
import shutil
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

logger = logging.getLogger(__name__)

from app.models.audio_editor import (
    AudioVideoProject, EditorTrack, AudioClip, 
    EditorSettings, RenderTask
)
from app.models.novel_project import NovelProject
from app.models.synthesis_task import SynthesisTask
from app.models.environment_sound import EnvironmentSound
from app.schemas.audio_editor import (
    AudioVideoProjectCreate, AudioVideoProjectUpdate,
    EditorTrackCreate, AudioClipCreate,
    ProjectImportRequest, TrackType
)
from app.services.moviepy_service import MoviePyService
# from .base_service import BaseService


class AudioEditorService:
    """音视频编辑器主服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.moviepy_service = MoviePyService()
        
        # 配置目录路径
        self.projects_dir = Path("data/editor_projects")
        self.uploads_dir = Path("data/editor_uploads")
        self.exports_dir = Path("data/editor_exports")
        
        # 确保目录存在
        for directory in [self.projects_dir, self.uploads_dir, self.exports_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    # =========================== 项目管理 ===========================
    
    async def create_project(
        self, 
        project_data: AudioVideoProjectCreate
    ) -> AudioVideoProject:
        """创建新的音视频编辑项目"""
        
        # 创建项目目录
        project_dir = self.projects_dir / f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        project_dir.mkdir(exist_ok=True)
        
        # 创建项目记录
        db_project = AudioVideoProject(
            name=project_data.name,
            description=project_data.description,
            project_type=project_data.project_type,
            project_data={
                "project_dir": str(project_dir),
                "audio_format": "wav",
                "sample_rate": 44100,
                "channels": 2
            }
        )
        
        self.db.add(db_project)
        self.db.commit()
        self.db.refresh(db_project)
        
        # 创建默认编辑器设置
        await self._create_default_settings(db_project.id)
        
        return db_project

    async def import_from_synthesis(
        self, 
        import_request: ProjectImportRequest
    ) -> AudioVideoProject:
        """从合成中心导入项目"""
        
        # 获取源项目数据
        source_project = self.db.query(NovelProject).filter(
            NovelProject.id == import_request.source_project_id
        ).first()
        
        if not source_project:
            raise ValueError(f"源项目 {import_request.source_project_id} 不存在")
        
        # 检查项目状态
        if source_project.status != "completed":
            raise ValueError(f"源项目状态为 {source_project.status}，只能导入已完成的项目")
        
        # 检查是否有最终音频文件
        if not source_project.final_audio_path:
            raise ValueError("源项目没有生成最终音频文件")
        
        # 创建编辑项目
        project_data = AudioVideoProjectCreate(
            name=import_request.project_name or f"{source_project.name} - 编辑版",
            description=import_request.description or f"从《{source_project.name}》导入的编辑项目",
            project_type="synthesis_import"
        )
        
        db_project = await self.create_project(project_data)
        
        # 关联源项目
        db_project.source_project_id = import_request.source_project_id
        
        # 导入音频轨道
        await self._import_synthesis_audio(db_project, source_project)
        
        self.db.commit()
        self.db.refresh(db_project)
        
        return db_project

    async def _import_synthesis_audio(
        self, 
        project: AudioVideoProject, 
        source_project: NovelProject
    ):
        """导入合成项目的音频"""
        
        # 创建主音频轨道
        main_track = EditorTrack(
            project_id=project.id,
            track_name="主音频轨道",
            track_type=TrackType.DIALOGUE.value,
            track_order=0,
            track_color="#4CAF50"
        )
        self.db.add(main_track)
        self.db.flush()
        
        # 检查音频文件是否存在
        audio_file_path = source_project.final_audio_path
        
        # 处理相对路径，转换为绝对路径
        if not os.path.isabs(audio_file_path):
            # 假设音频文件在项目根目录下
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            audio_file_path = os.path.join(base_dir, audio_file_path)
        
        if not os.path.exists(audio_file_path):
            raise ValueError(f"音频文件不存在: {audio_file_path}")
        
        # 获取音频文件信息
        try:
            duration = await self._get_audio_duration(audio_file_path)
        except Exception as e:
            # 如果无法获取音频时长，使用默认值
            duration = 300.0  # 5分钟默认时长
            logger.warning(f"无法获取音频时长，使用默认值: {e}")
        
        # 创建音频片段
        audio_clip = AudioClip(
            track_id=main_track.id,
            clip_name=f"{source_project.name} - 完整音频",
            file_path=source_project.final_audio_path,  # 保持原始路径
            start_time=0.0,
            end_time=duration,
            clip_data={
                "source_project_id": source_project.id,
                "source_project_name": source_project.name,
                "import_type": "synthesis_complete"
            }
        )
        self.db.add(audio_clip)
        
        # 更新项目统计信息
        project.total_duration = duration

    async def get_projects(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None,
        project_type: Optional[str] = None
    ) -> Tuple[List[AudioVideoProject], int]:
        """获取项目列表"""
        
        query = self.db.query(AudioVideoProject)
        
        # 搜索过滤
        if search:
            query = query.filter(
                or_(
                    AudioVideoProject.name.ilike(f"%{search}%"),
                    AudioVideoProject.description.ilike(f"%{search}%")
                )
            )
        
        # 状态过滤
        if status:
            query = query.filter(AudioVideoProject.status == status)
        
        # 类型过滤
        if project_type:
            query = query.filter(AudioVideoProject.project_type == project_type)
        
        # 统计总数
        total_count = query.count()
        
        # 分页查询
        projects = query.order_by(AudioVideoProject.updated_at.desc()).offset(skip).limit(limit).all()
        
        return projects, total_count

    async def get_project_with_details(self, project_id: int) -> Optional[AudioVideoProject]:
        """获取项目详细信息（包含轨道和片段）"""
        return self.db.query(AudioVideoProject).filter(
            AudioVideoProject.id == project_id
        ).first()

    # =========================== 轨道管理 ===========================
    
    async def create_track(
        self, 
        project_id: int, 
        track_data: EditorTrackCreate
    ) -> EditorTrack:
        """创建新轨道"""
        
        # 检查项目是否存在
        project = await self.get_project_with_details(project_id)
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")
        
        # 获取下一个轨道顺序
        max_order = self.db.query(EditorTrack.track_order.label('max_order')).filter(
            EditorTrack.project_id == project_id
        ).scalar() or 0
        
        # 创建轨道
        db_track = EditorTrack(
            project_id=project_id,
            track_name=track_data.track_name,
            track_type=track_data.track_type,
            track_order=max_order + 1,
            track_color=track_data.track_color,
            volume=track_data.volume or 1.0,
            pan=track_data.pan or 0.0
        )
        
        self.db.add(db_track)
        self.db.commit()
        self.db.refresh(db_track)
        
        return db_track

    async def get_project_tracks(self, project_id: int) -> List[EditorTrack]:
        """获取项目的所有轨道"""
        return self.db.query(EditorTrack).filter(
            EditorTrack.project_id == project_id
        ).order_by(EditorTrack.track_order).all()

    # =========================== 音频片段管理 ===========================
    
    async def add_audio_clip(
        self, 
        track_id: int, 
        clip_data: AudioClipCreate
    ) -> AudioClip:
        """添加音频片段"""
        
        # 检查轨道是否存在
        track = self.db.query(EditorTrack).filter(EditorTrack.id == track_id).first()
        if not track:
            raise ValueError(f"轨道 {track_id} 不存在")
        
        # 获取音频文件信息
        duration = await self._get_audio_duration(clip_data.file_path)
        
        # 创建音频片段
        db_clip = AudioClip(
            track_id=track_id,
            clip_name=clip_data.clip_name,
            file_path=clip_data.file_path,
            start_time=clip_data.start_time,
            end_time=clip_data.start_time + duration,
            volume=clip_data.volume or 1.0,
            fade_in=clip_data.fade_in or 0.0,
            fade_out=clip_data.fade_out or 0.0
        )
        
        self.db.add(db_clip)
        self.db.commit()
        self.db.refresh(db_clip)
        
        return db_clip

    # =========================== 音频处理 ===========================
    
    async def mix_project_audio(
        self, 
        project_id: int,
        export_path: Optional[str] = None
    ) -> str:
        """混合项目音频"""
        
        project = await self.get_project_with_details(project_id)
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")
        
        # 创建渲染任务
        render_task = RenderTask(
            project_id=project_id,
            task_type="mix",
            task_status="processing",
            started_at=datetime.utcnow()
        )
        self.db.add(render_task)
        self.db.commit()
        
        try:
            # 准备音频轨道数据
            track_data = []
            for track in project.tracks:
                if track.is_muted:
                    continue
                    
                for clip in track.clips:
                    track_data.append({
                        "file_path": clip.file_path,
                        "start_time": clip.start_time,
                        "end_time": clip.end_time,
                        "volume": clip.volume * track.volume,
                        "fade_in": clip.fade_in,
                        "fade_out": clip.fade_out
                    })
            
            # 使用MoviePy服务混合音频
            if not export_path:
                export_path = str(self.exports_dir / f"project_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav")
            
            result_path = await self.moviepy_service.mix_multiple_audio_tracks(
                track_data, export_path
            )
            
            # 更新渲染任务状态
            render_task.task_status = "completed"
            render_task.completed_at = datetime.utcnow()
            render_task.result_file_path = result_path
            render_task.progress = 100.0
            
            self.db.commit()
            
            return result_path
            
        except Exception as e:
            # 更新渲染任务错误状态
            render_task.task_status = "failed"
            render_task.error_message = str(e)
            render_task.completed_at = datetime.utcnow()
            
            self.db.commit()
            raise

    # =========================== 辅助方法 ===========================
    
    async def _create_default_settings(self, project_id: int):
        """创建默认编辑器设置"""
        settings = EditorSettings(
            project_id=project_id,
            zoom_level=1.0,
            playhead_position=0.0,
            timeline_settings={
                "grid_size": 1.0,
                "snap_enabled": True,
                "auto_scroll": True
            },
            ui_settings={
                "track_height": 80,
                "timeline_height": 400,
                "properties_panel_width": 300
            }
        )
        
        self.db.add(settings)
        self.db.commit()

    async def _get_audio_duration(self, file_path: str) -> float:
        """获取音频文件时长"""
        try:
            audio_info = await self.moviepy_service.get_audio_info(file_path)
            # 如果返回的是字典，提取duration字段
            if isinstance(audio_info, dict):
                return audio_info.get('duration', 0.0)
            # 如果返回的是数字，直接返回
            return float(audio_info)
        except Exception:
            return 0.0

    async def save_project_settings(
        self, 
        project_id: int, 
        settings_data: dict
    ) -> EditorSettings:
        """保存项目设置"""
        settings = self.db.query(EditorSettings).filter(
            EditorSettings.project_id == project_id
        ).first()
        
        if not settings:
            settings = EditorSettings(project_id=project_id)
            self.db.add(settings)
        
        # 更新设置数据
        for key, value in settings_data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        self.db.commit()
        self.db.refresh(settings)
        
        return settings

    async def delete_project(self, project_id: int) -> bool:
        """删除项目及相关数据"""
        project = self.db.query(AudioVideoProject).filter(
            AudioVideoProject.id == project_id
        ).first()
        
        if not project:
            return False
        
        # 删除项目目录
        if project.project_data and "project_dir" in project.project_data:
            project_dir = Path(project.project_data["project_dir"])
            if project_dir.exists():
                shutil.rmtree(project_dir, ignore_errors=True)
        
        # 删除数据库记录（级联删除轨道、片段等）
        self.db.delete(project)
        self.db.commit()
        
        return True 