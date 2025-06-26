"""
音视频编辑器数据模型
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, ForeignKey, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func

from .base import Base


class AudioVideoProject(Base):
    """音视频编辑项目模型"""
    __tablename__ = "audio_video_projects"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    name: Mapped[str] = Column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = Column(Text, nullable=True)
    source_project_id: Mapped[Optional[int]] = Column(
        Integer, 
        ForeignKey("novel_projects.id", ondelete="SET NULL"), 
        nullable=True
    )
    project_type: Mapped[str] = Column(String(50), nullable=False, default="audio_editing")
    status: Mapped[str] = Column(String(50), nullable=False, default="draft", index=True)
    project_data: Mapped[Optional[Dict[str, Any]]] = Column(JSONB, nullable=True)
    total_duration: Mapped[float] = Column(Float, nullable=True, default=0.0)
    
    # 时间戳
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )

    # 关系
    tracks: Mapped[List["EditorTrack"]] = relationship(
        "EditorTrack", 
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="EditorTrack.track_order"
    )
    settings: Mapped[Optional["EditorSettings"]] = relationship(
        "EditorSettings", 
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan"
    )
    render_tasks: Mapped[List["RenderTask"]] = relationship(
        "RenderTask", 
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="RenderTask.created_at.desc()"
    )

    def __repr__(self):
        return f"<AudioVideoProject(id={self.id}, name='{self.name}', status='{self.status}')>"

    @property
    def track_count(self) -> int:
        """轨道数量"""
        return len(self.tracks) if self.tracks else 0

    @property
    def clip_count(self) -> int:
        """音频片段总数量"""
        if not self.tracks:
            return 0
        return sum(len(track.clips) for track in self.tracks)

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source_project_id": self.source_project_id,
            "project_type": self.project_type,
            "status": self.status,
            "project_data": self.project_data,
            "total_duration": self.total_duration,
            "track_count": self.track_count,
            "clip_count": self.clip_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class EditorTrack(Base):
    """编辑器轨道模型"""
    __tablename__ = "editor_tracks"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = Column(
        Integer, 
        ForeignKey("audio_video_projects.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    track_name: Mapped[str] = Column(String(255), nullable=False)
    track_type: Mapped[str] = Column(String(50), nullable=False)  # dialogue, environment, effects, music
    track_order: Mapped[int] = Column(Integer, nullable=False, default=0, index=True)
    is_muted: Mapped[bool] = Column(Boolean, nullable=False, default=False)
    is_solo: Mapped[bool] = Column(Boolean, nullable=False, default=False)
    volume: Mapped[float] = Column(Float, nullable=False, default=1.0)
    pan: Mapped[float] = Column(Float, nullable=False, default=0.0)  # -1.0 (左) 到 1.0 (右)
    track_color: Mapped[Optional[str]] = Column(String(7), nullable=True)  # HEX颜色值
    track_data: Mapped[Optional[Dict[str, Any]]] = Column(JSONB, nullable=True)
    
    # 时间戳
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )

    # 关系
    project: Mapped["AudioVideoProject"] = relationship("AudioVideoProject", back_populates="tracks")
    clips: Mapped[List["AudioClip"]] = relationship(
        "AudioClip", 
        back_populates="track",
        cascade="all, delete-orphan",
        order_by="AudioClip.start_time"
    )

    def __repr__(self):
        return f"<EditorTrack(id={self.id}, name='{self.track_name}', type='{self.track_type}')>"

    @property
    def duration(self) -> float:
        """轨道总时长（根据最后一个音频片段计算）"""
        if not self.clips:
            return 0.0
        return max((clip.end_time for clip in self.clips), default=0.0)

    @property
    def clip_count(self) -> int:
        """音频片段数量"""
        return len(self.clips) if self.clips else 0

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "track_name": self.track_name,
            "track_type": self.track_type,
            "track_order": self.track_order,
            "is_muted": self.is_muted,
            "is_solo": self.is_solo,
            "volume": self.volume,
            "pan": self.pan,
            "track_color": self.track_color,
            "track_data": self.track_data,
            "duration": self.duration,
            "clip_count": self.clip_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AudioClip(Base):
    """音频片段模型"""
    __tablename__ = "audio_clips"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    track_id: Mapped[int] = Column(
        Integer, 
        ForeignKey("editor_tracks.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    clip_name: Mapped[Optional[str]] = Column(String(255), nullable=True)
    file_path: Mapped[str] = Column(String(500), nullable=False)
    original_file_path: Mapped[Optional[str]] = Column(String(500), nullable=True)  # 原始文件路径
    start_time: Mapped[float] = Column(Float, nullable=False, index=True)  # 在时间轴上的开始时间
    end_time: Mapped[float] = Column(Float, nullable=False, index=True)    # 在时间轴上的结束时间
    source_start: Mapped[float] = Column(Float, nullable=False, default=0.0)  # 源文件裁剪开始点
    source_end: Mapped[Optional[float]] = Column(Float, nullable=True)   # 源文件裁剪结束点
    volume: Mapped[float] = Column(Float, nullable=False, default=1.0)
    fade_in: Mapped[float] = Column(Float, nullable=False, default=0.0)   # 淡入时长
    fade_out: Mapped[float] = Column(Float, nullable=False, default=0.0)  # 淡出时长
    effects: Mapped[Optional[Dict[str, Any]]] = Column(JSONB, nullable=True)
    clip_data: Mapped[Optional[Dict[str, Any]]] = Column(JSONB, nullable=True)
    
    # 时间戳
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )

    # 关系
    track: Mapped["EditorTrack"] = relationship("EditorTrack", back_populates="clips")

    def __repr__(self):
        return f"<AudioClip(id={self.id}, name='{self.clip_name}', start={self.start_time}, end={self.end_time})>"

    @property
    def duration(self) -> float:
        """片段时长"""
        return self.end_time - self.start_time

    @property
    def source_duration(self) -> float:
        """源文件片段时长"""
        if self.source_end is not None:
            return self.source_end - self.source_start
        return self.duration

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "track_id": self.track_id,
            "clip_name": self.clip_name,
            "file_path": self.file_path,
            "original_file_path": self.original_file_path,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "source_start": self.source_start,
            "source_end": self.source_end,
            "source_duration": self.source_duration,
            "volume": self.volume,
            "fade_in": self.fade_in,
            "fade_out": self.fade_out,
            "effects": self.effects,
            "clip_data": self.clip_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class EditorSettings(Base):
    """编辑器设置模型"""
    __tablename__ = "editor_settings"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = Column(
        Integer, 
        ForeignKey("audio_video_projects.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    zoom_level: Mapped[float] = Column(Float, nullable=False, default=1.0)
    playhead_position: Mapped[float] = Column(Float, nullable=False, default=0.0)
    visible_tracks: Mapped[Optional[List[int]]] = Column(ARRAY(Integer), nullable=True)
    timeline_settings: Mapped[Optional[Dict[str, Any]]] = Column(JSONB, nullable=True)
    ui_settings: Mapped[Optional[Dict[str, Any]]] = Column(JSONB, nullable=True)
    
    # 时间戳
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )

    # 关系
    project: Mapped["AudioVideoProject"] = relationship("AudioVideoProject", back_populates="settings")

    def __repr__(self):
        return f"<EditorSettings(id={self.id}, project_id={self.project_id}, zoom={self.zoom_level})>"

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "zoom_level": self.zoom_level,
            "playhead_position": self.playhead_position,
            "visible_tracks": self.visible_tracks,
            "timeline_settings": self.timeline_settings,
            "ui_settings": self.ui_settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class RenderTask(Base):
    """渲染任务模型"""
    __tablename__ = "render_tasks"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = Column(
        Integer, 
        ForeignKey("audio_video_projects.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    task_type: Mapped[str] = Column(String(50), nullable=False)  # preview, export, mix
    task_status: Mapped[str] = Column(String(50), nullable=False, default="pending", index=True)  # pending, processing, completed, failed
    progress: Mapped[float] = Column(Float, nullable=False, default=0.0)
    task_data: Mapped[Optional[Dict[str, Any]]] = Column(JSONB, nullable=True)
    result_file_path: Mapped[Optional[str]] = Column(String(500), nullable=True)
    error_message: Mapped[Optional[str]] = Column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = Column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = Column(DateTime(timezone=True), nullable=True)
    
    # 时间戳
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        index=True
    )

    # 关系
    project: Mapped["AudioVideoProject"] = relationship("AudioVideoProject", back_populates="render_tasks")

    def __repr__(self):
        return f"<RenderTask(id={self.id}, type='{self.task_type}', status='{self.task_status}')>"

    @property
    def duration_seconds(self) -> Optional[float]:
        """任务执行时长（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "task_type": self.task_type,
            "task_status": self.task_status,
            "progress": self.progress,
            "task_data": self.task_data,
            "result_file_path": self.result_file_path,
            "error_message": self.error_message,
            "duration_seconds": self.duration_seconds,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        } 