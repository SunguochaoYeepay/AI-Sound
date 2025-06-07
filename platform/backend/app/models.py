"""
SQLAlchemy 数据模型
定义所有数据库表结构
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
from urllib.parse import quote
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

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
    reference_audio_path = Column(String(500), nullable=True)
    latent_file_path = Column(String(500), nullable=True)
    sample_audio_path = Column(String(500), nullable=True)
    
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
        
        # 将文件路径转换为HTTP URL
        def path_to_url(file_path):
            if not file_path:
                return None
            
            # 智能提取纯文件名，处理各种路径格式
            # 统一替换路径分隔符，然后分割取最后一部分
            normalized_path = file_path.replace("\\", "/")
            parts = normalized_path.split("/")
            filename = parts[-1]  # 取最后一部分作为文件名
            
            # URL编码文件名以支持中文字符
            encoded_filename = quote(filename, safe='._-')
            
            # 统一返回标准的nginx路径格式
            return f"/voice_profiles/{encoded_filename}"
        
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "referenceAudioUrl": path_to_url(self.reference_audio_path),
            "latentFileUrl": path_to_url(self.latent_file_path),
            "sampleAudioUrl": path_to_url(self.sample_audio_path),
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
    朗读项目表 - 关联书籍进行语音合成
    """
    __tablename__ = "novel_projects"
    
    # 基础字段
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    
    # 关联书籍
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)
    
    # 预设角色（可选）
    initial_characters = Column(Text, default='[]')  # JSON格式的初始角色列表
    
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
    book = relationship("Book", back_populates="synthesis_projects")
    segments = relationship("TextSegment", back_populates="project", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "bookId": self.book_id,
            "book": self.book.to_dict() if self.book else None,
            "initialCharacters": json.loads(self.initial_characters) if self.initial_characters else [],
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
    
    def get_initial_characters(self) -> List[str]:
        """获取初始角色列表"""
        try:
            return json.loads(self.initial_characters) if self.initial_characters else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_initial_characters(self, characters: List[str]):
        """设置初始角色列表"""
        self.initial_characters = json.dumps(characters, ensure_ascii=False)

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

class AudioFile(Base):
    """
    音频文件表 - 统一管理所有生成的音频文件
    """
    __tablename__ = "audio_files"
    
    # 基础字段
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False, unique=True, index=True)  # 实际文件名
    original_name = Column(String(255))  # 原始显示名称
    file_path = Column(String(500), nullable=False)  # 完整文件路径
    
    # 文件信息
    file_size = Column(Integer, default=0)  # 文件大小(字节)
    duration = Column(Float, default=0.0)  # 音频时长(秒)
    sample_rate = Column(Integer, default=22050)  # 采样率
    channels = Column(Integer, default=1)  # 声道数
    
    # 关联信息
    project_id = Column(Integer, ForeignKey("novel_projects.id"), nullable=True, index=True)
    segment_id = Column(Integer, ForeignKey("text_segments.id"), nullable=True, index=True)
    voice_profile_id = Column(Integer, ForeignKey("voice_profiles.id"), nullable=True, index=True)
    
    # 文本内容
    text_content = Column(Text)  # 对应的文本内容
    
    # 音频类型
    audio_type = Column(String(20), default='segment', index=True)  # 'segment' | 'project' | 'single' | 'test'
    
    # 处理信息
    processing_time = Column(Float)  # 生成耗时
    model_used = Column(String(50))  # 使用的模型
    parameters = Column(Text)  # 生成参数(JSON格式)
    
    # 状态和标签
    status = Column(String(20), default='active', index=True)  # 'active' | 'archived' | 'deleted'
    tags = Column(Text, default='[]')  # 标签(JSON数组)
    is_favorite = Column(Boolean, default=False)  # 是否收藏
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    project = relationship("NovelProject", backref="audio_files")
    segment = relationship("TextSegment", backref="audio_files")
    voice_profile = relationship("VoiceProfile", backref="audio_files")
    
    # 索引
    __table_args__ = (
        Index('idx_audio_project_type', 'project_id', 'audio_type'),
        Index('idx_audio_created', 'created_at'),
        Index('idx_audio_status_type', 'status', 'audio_type'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "filename": self.filename,
            "originalName": self.original_name or self.filename,
            "filePath": self.file_path,
            "audioUrl": f"/audio/{self.filename}",
            "fileSize": self.file_size,
            "fileSizeMB": round(self.file_size / 1024 / 1024, 2) if self.file_size else 0,
            "duration": self.duration,
            "durationFormatted": self.format_duration(),
            "sampleRate": self.sample_rate,
            "channels": self.channels,
            "projectId": self.project_id,
            "projectName": self.project.name if self.project else None,
            "segmentId": self.segment_id,
            "segmentOrder": self.segment.segment_order if self.segment else None,
            "voiceProfileId": self.voice_profile_id,
            "voiceProfileName": self.voice_profile.name if self.voice_profile else None,
            "textContent": self.text_content,
            "audioType": self.audio_type,
            "processingTime": self.processing_time,
            "modelUsed": self.model_used,
            "parameters": json.loads(self.parameters) if self.parameters else {},
            "status": self.status,
            "tags": json.loads(self.tags) if self.tags else [],
            "isFavorite": self.is_favorite,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def format_duration(self) -> str:
        """格式化时长显示"""
        if not self.duration:
            return "00:00"
        
        total_seconds = int(self.duration)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        
        if minutes >= 60:
            hours = minutes // 60
            minutes = minutes % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def get_tags(self) -> List[str]:
        """获取标签列表"""
        try:
            return json.loads(self.tags) if self.tags else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_tags(self, tags: List[str]):
        """设置标签列表"""
        self.tags = json.dumps(tags)
    
    def get_parameters(self) -> Dict[str, Any]:
        """获取生成参数"""
        try:
            return json.loads(self.parameters) if self.parameters else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_parameters(self, params: Dict[str, Any]):
        """设置生成参数"""
        self.parameters = json.dumps(params)

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

class Book(Base):
    """
    书籍内容管理表
    """
    __tablename__ = "books"
    
    # 基础字段
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, index=True)
    author = Column(String(100), default='')
    description = Column(Text, default='')
    
    # 内容字段
    content = Column(Text, nullable=False)  # 完整文本内容
    chapters = Column(Text, default='[]')   # JSON格式的章节信息（字符串存储）
    
    # 状态管理
    status = Column(String(20), default='draft', index=True)  # 'draft' | 'published' | 'archived'
    tags = Column(Text, default='[]')  # JSON格式的标签列表（字符串存储）
    
    # 统计信息
    word_count = Column(Integer, default=0)
    chapter_count = Column(Integer, default=0)
    
    # 文件信息
    source_file_path = Column(String(500))  # 原始文件路径
    source_file_name = Column(String(200))  # 原始文件名
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    synthesis_projects = relationship("NovelProject", back_populates="book", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_book_status_created', 'status', 'created_at'),
        Index('idx_book_title_author', 'title', 'author'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        # 简单的JSON字符串处理
        try:
            chapters_data = json.loads(self.chapters) if self.chapters else []
        except:
            chapters_data = []
            
        try:
            tags_data = json.loads(self.tags) if self.tags else []
        except:
            tags_data = []
        
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "description": self.description,
            "content": self.content,
            "chapters": chapters_data,
            "status": self.status,
            "tags": tags_data,
            "wordCount": self.word_count,
            "chapterCount": self.chapter_count,
            "sourceFileName": self.source_file_name,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_chapters(self) -> List[Dict[str, Any]]:
        """获取章节信息"""
        try:
            return json.loads(self.chapters) if self.chapters else []
        except:
            return []
    
    def set_chapters(self, chapters: List[Dict[str, Any]]):
        """设置章节信息"""
        self.chapters = json.dumps(chapters, ensure_ascii=False)
        self.chapter_count = len(chapters)
    
    def get_tags(self) -> List[str]:
        """获取标签列表"""
        try:
            return json.loads(self.tags) if self.tags else []
        except:
            return []
    
    def set_tags(self, tags: List[str]):
        """设置标签列表"""
        self.tags = json.dumps(tags, ensure_ascii=False)
    
    def update_word_count(self):
        """更新字数统计"""
        if self.content:
            # 简单的中文字数统计
            self.word_count = len(self.content.replace(' ', '').replace('\n', '').replace('\r', '')) 