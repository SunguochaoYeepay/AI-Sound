"""
小说项目模型  
管理TTS转换项目
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any
import logging

from .base import Base


class NovelProject(Base):
    """小说项目模型"""
    
    __tablename__ = 'novel_projects'
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey('books.id', ondelete='SET NULL'))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # 朗读项目状态
    status = Column(String(20), default='pending')  # pending, processing, paused, completed, failed
    
    # 朗读进度
    total_segments = Column(Integer, default=0)
    processed_segments = Column(Integer, default=0)
    current_segment = Column(Integer, default=0)
    
    # 朗读时间
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # 项目配置
    config = Column(JSON)  # 项目配置信息，包含角色映射等
    
    # 最终音频文件路径
    final_audio_path = Column(String(500))
    
    # 错误信息
    error_message = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    book = relationship("Book", back_populates="projects")
    analysis_sessions = relationship("AnalysisSession", back_populates="project", cascade="all, delete-orphan")
    synthesis_tasks = relationship("SynthesisTask", back_populates="project")
    audio_files = relationship("AudioFile", back_populates="project", cascade="all, delete-orphan")
    
    # 🎵 音乐生成相关关系
    music_generation_tasks = relationship("MusicGenerationTask", back_populates="novel_project", cascade="all, delete-orphan")
    music_generation_batches = relationship("MusicGenerationBatch", back_populates="novel_project", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_novel_projects_book_id', 'book_id'),
        Index('idx_novel_projects_name', 'name'),
        Index('idx_novel_projects_status', 'status'),
        Index('idx_novel_projects_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<NovelProject(id={self.id}, name='{self.name}', book_id={self.book_id})>"
    
    def get_character_mapping(self) -> Dict[str, str]:
        """获取角色声音映射"""
        if self.config and isinstance(self.config, dict):
            return self.config.get('character_mapping', {})
        return {}
    
    def set_character_mapping(self, mapping: Dict[str, str]):
        """设置角色声音映射"""
        logger = logging.getLogger(__name__)
        
        logger.info(f"[MODEL DEBUG] set_character_mapping called with: {mapping}")
        logger.info(f"[MODEL DEBUG] Current config before update: {self.config}")
        
        if not self.config:
            self.config = {}
        elif not isinstance(self.config, dict):
            self.config = {}
        self.config['character_mapping'] = mapping
        
        # 重要：标记JSON字段为已修改，强制SQLAlchemy更新
        from sqlalchemy.orm import attributes
        attributes.flag_modified(self, 'config')
        
        logger.info(f"[MODEL DEBUG] Config after update: {self.config}")
        logger.info(f"[MODEL DEBUG] character_mapping in config: {self.config.get('character_mapping')}")
        logger.info(f"[MODEL DEBUG] JSON field marked as modified")
    
    def get_settings(self) -> Dict[str, Any]:
        """获取项目设置"""
        if self.config and isinstance(self.config, dict):
            return {k: v for k, v in self.config.items() if k != 'character_mapping'}
        return {}
    
    def set_settings(self, settings: Dict[str, Any]):
        """设置项目设置"""
        if not self.config:
            self.config = {}
        elif not isinstance(self.config, dict):
            self.config = {}
        # 保留角色映射，更新其他设置
        char_mapping = self.config.get('character_mapping', {})
        self.config.update(settings)
        if char_mapping:
            self.config['character_mapping'] = char_mapping

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'book_id': self.book_id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'total_segments': self.total_segments,
            'processed_segments': self.processed_segments,
            'current_segment': self.current_segment,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'config': self.config,
            'final_audio_path': self.final_audio_path,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 