"""
SQLAlchemy 数据模型
定义所有数据库表结构
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class VoiceProfile(Base):
    """
    声音库表 - 对应 Characters.vue 功能
    """
    __tablename__ = "voice_profiles"
    
    # 基础字段
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    type = Column(String(20), nullable=False, index=True)  # 'male' | 'female' | 'child'
    
    # 音频文件路径
    reference_audio_path = Column(String(500), nullable=False)
    latent_file_path = Column(String(500))
    sample_audio_path = Column(String(500))
    
    # 技术参数 (JSON格式存储)
    parameters = Column(Text, nullable=False, default='{"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}')
    
    # 质量和统计
    quality_score = Column(Float, default=3.0)
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime)
    
    # 元数据
    color = Column(String(20), default='#06b6d4')
    tags = Column(Text, default='[]')  # JSON数组格式
    status = Column(String(20), default='active', index=True)  # 'active' | 'training' | 'inactive'
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    text_segments = relationship("TextSegment", back_populates="voice_profile")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "referenceAudioUrl": self.reference_audio_path,
            "latentFileUrl": self.latent_file_path,
            "sampleAudioUrl": self.sample_audio_path,
            "params": json.loads(self.parameters) if self.parameters else {},
            "quality": self.quality_score,
            "usageCount": self.usage_count,
            "lastUsed": self.last_used.isoformat() if self.last_used else None,
            "color": self.color,
            "tags": json.loads(self.tags) if self.tags else [],
            "status": self.status,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_parameters(self) -> Dict[str, Any]:
        """获取技术参数"""
        try:
            return json.loads(self.parameters) if self.parameters else {}
        except (json.JSONDecodeError, TypeError):
            return {"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}
    
    def set_parameters(self, params: Dict[str, Any]):
        """设置技术参数"""
        self.parameters = json.dumps(params)
    
    def get_tags(self) -> List[str]:
        """获取标签列表"""
        try:
            return json.loads(self.tags) if self.tags else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_tags(self, tags: List[str]):
        """设置标签列表"""
        self.tags = json.dumps(tags)

class NovelProject(Base):
    """
    朗读项目表 - 对应 NovelReader.vue 功能
    """
    __tablename__ = "novel_projects"
    
    # 基础字段
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    
    # 文本内容
    original_text = Column(Text)
    text_file_path = Column(String(500))
    
    # 处理状态
    status = Column(String(20), default='pending', index=True)  # 'pending' | 'processing' | 'paused' | 'completed' | 'failed'
    total_segments = Column(Integer, default=0)
    processed_segments = Column(Integer, default=0)
    failed_segments = Column(Text, default='[]')  # JSON数组：失败的段落ID
    current_segment = Column(Integer, default=0)
    
    # 角色映射 (JSON格式)
    character_mapping = Column(Text, default='{}')  # {"角色名": "voice_profile_id"}
    
    # 输出文件
    final_audio_path = Column(String(500))
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    estimated_completion = Column(DateTime)
    
    # 关系
    segments = relationship("TextSegment", back_populates="project", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "originalText": self.original_text,
            "textFilePath": self.text_file_path,
            "status": self.status,
            "totalSegments": self.total_segments,
            "processedSegments": self.processed_segments,
            "failedSegments": json.loads(self.failed_segments) if self.failed_segments else [],
            "currentSegment": self.current_segment,
            "characterMapping": json.loads(self.character_mapping) if self.character_mapping else {},
            "finalAudioUrl": self.final_audio_path,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "startedAt": self.started_at.isoformat() if self.started_at else None,
            "completedAt": self.completed_at.isoformat() if self.completed_at else None,
            "estimatedCompletion": self.estimated_completion.isoformat() if self.estimated_completion else None,
            "progress": round((self.processed_segments / self.total_segments * 100), 1) if self.total_segments > 0 else 0
        }
    
    def get_character_mapping(self) -> Dict[str, str]:
        """获取角色映射"""
        try:
            return json.loads(self.character_mapping) if self.character_mapping else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_character_mapping(self, mapping: Dict[str, str]):
        """设置角色映射"""
        self.character_mapping = json.dumps(mapping)

class TextSegment(Base):
    """
    文本段落表
    """
    __tablename__ = "text_segments"
    
    # 基础字段
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("novel_projects.id"), nullable=False, index=True)
    segment_order = Column(Integer, nullable=False)
    text_content = Column(Text, nullable=False)
    
    # 角色信息
    detected_speaker = Column(String(100))
    voice_profile_id = Column(Integer, ForeignKey("voice_profiles.id"), index=True)
    
    # 处理状态
    status = Column(String(20), default='pending', index=True)  # 'pending' | 'processing' | 'completed' | 'failed'
    audio_file_path = Column(String(500))
    processing_time = Column(Float)
    error_message = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    project = relationship("NovelProject", back_populates="segments")
    voice_profile = relationship("VoiceProfile", back_populates="text_segments")
    
    # 索引
    __table_args__ = (
        Index('idx_project_order', 'project_id', 'segment_order'),
        Index('idx_status_project', 'status', 'project_id'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "projectId": self.project_id,
            "segmentOrder": self.segment_order,
            "textContent": self.text_content,
            "detectedSpeaker": self.detected_speaker,
            "voiceProfileId": self.voice_profile_id,
            "status": self.status,
            "audioUrl": self.audio_file_path,
            "processingTime": self.processing_time,
            "errorMessage": self.error_message,
            "createdAt": self.created_at.isoformat() if self.created_at else None
        }

class SystemLog(Base):
    """
    系统日志表 - 对应 Settings.vue 功能
    """
    __tablename__ = "system_logs"
    
    # 基础字段
    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(10), nullable=False, index=True)  # 'info' | 'warn' | 'error'
    message = Column(Text, nullable=False)
    module = Column(String(50), index=True)  # 'voice_clone' | 'characters' | 'novel_reader' | 'system'
    details = Column(Text)  # JSON格式的详细信息
    
    # 时间戳
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "level": self.level,
            "message": self.message,
            "module": self.module,
            "details": json.loads(self.details) if self.details else None,
            "time": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else None
        }

class UsageStats(Base):
    """
    使用统计表
    """
    __tablename__ = "usage_stats"
    
    # 基础字段
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False, unique=True, index=True)  # YYYY-MM-DD格式
    
    # 统计数据
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    total_processing_time = Column(Float, default=0.0)
    audio_files_generated = Column(Integer, default=0)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        success_rate = 0
        if self.total_requests > 0:
            success_rate = round((self.successful_requests / self.total_requests) * 100, 1)
        
        avg_processing_time = 0
        if self.successful_requests > 0:
            avg_processing_time = round(self.total_processing_time / self.successful_requests, 2)
        
        return {
            "date": self.date,
            "totalRequests": self.total_requests,
            "successfulRequests": self.successful_requests,
            "failedRequests": self.failed_requests,
            "successRate": success_rate,
            "avgProcessingTime": avg_processing_time,
            "audioFilesGenerated": self.audio_files_generated
        } 