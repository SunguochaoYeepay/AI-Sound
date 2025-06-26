"""
文本段落模型
管理书籍文本的段落分析
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any

from .base import Base


class TextSegment(Base):
    """文本段落模型"""
    
    __tablename__ = 'text_segments'
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('novel_projects.id', ondelete='CASCADE'), nullable=False)
    
    # 文本内容
    content = Column(Text, nullable=False)  # 文本内容（匹配数据库字段名）
    speaker = Column(String(100))       # 检测到的说话人（匹配数据库字段名）
    emotion = Column(String(50))                 # 情感状态
    voice_id = Column(String(100))              # 声音ID（匹配数据库字段名）
    
    # 段落位置
    chapter_number = Column(Integer)   # 章节号
    paragraph_index = Column(Integer)    # 段落索引（匹配数据库字段名）
    
    # 音频相关
    audio_file_path = Column(String(500))       # 生成的音频文件路径
    processing_time = Column(Integer)           # 处理耗时（秒）
    completed_at = Column(DateTime)             # 完成时间
    error_message = Column(Text)                # 错误信息
    
    # 处理状态
    status = Column(String(20), default='pending')  # pending, processing, completed, failed
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    project = relationship("NovelProject", backref="text_segments")
    
    # 索引
    __table_args__ = (
        Index('idx_text_segments_project_id', 'project_id'),
        Index('idx_text_segments_speaker', 'speaker'),
        Index('idx_text_segments_chapter', 'chapter_number'),
        Index('idx_text_segments_status', 'status'),
        Index('idx_text_segments_order', 'paragraph_index'),
    )
    
    def __repr__(self):
        return f"<TextSegment(id={self.id}, speaker='{self.speaker}', status='{self.status}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'content': self.content,
            'speaker': self.speaker,
            'emotion': self.emotion,
            'voice_id': self.voice_id,
            'chapter_number': self.chapter_number,
            'paragraph_index': self.paragraph_index,
            'audio_file_path': self.audio_file_path,
            'processing_time': self.processing_time,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }