"""
书籍章节模型
管理书籍的章节分割和结构化数据
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any

from .base import Base


class BookChapter(Base):
    """书籍章节模型"""
    
    __tablename__ = 'book_chapters'
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    chapter_title = Column(String(200))
    content = Column(Text, nullable=False)
    word_count = Column(Integer, default=0)
    character_count = Column(Integer, default=0, comment="字符数")
    
    # 处理状态
    analysis_status = Column(String(20), default='pending')  # pending, analyzing, completed, failed
    synthesis_status = Column(String(20), default='pending')  # pending, synthesizing, completed, failed
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    book = relationship("Book", back_populates="chapters")
    analysis_results = relationship("AnalysisResult", back_populates="chapter", cascade="all, delete-orphan")
    synthesis_tasks = relationship("SynthesisTask", back_populates="chapter")
    characters = relationship("Character", back_populates="chapter")  # 添加与 Character 的反向关系
    
    # 索引
    __table_args__ = (
        Index('idx_book_chapters_book_id', 'book_id'),
        Index('idx_book_chapters_chapter_number', 'chapter_number'),
        Index('idx_book_chapters_analysis_status', 'analysis_status'),
        Index('idx_book_chapters_synthesis_status', 'synthesis_status'),
        Index('idx_book_chapters_book_chapter', 'book_id', 'chapter_number'),
    )
    
    def __repr__(self):
        return f"<BookChapter(id={self.id}, book_id={self.book_id}, chapter={self.chapter_number}, title='{self.chapter_title}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'book_id': self.book_id,
            'chapter_number': self.chapter_number,
            'chapter_title': self.chapter_title,
            'content': self.content,
            'word_count': self.word_count,
            'character_count': self.character_count,
            'analysis_status': self.analysis_status,
            'synthesis_status': self.synthesis_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_content_preview(self, max_length: int = 200) -> str:
        """获取内容预览"""
        if not self.content:
            return ""
        
        if len(self.content) <= max_length:
            return self.content
        
        return self.content[:max_length] + "..."
    
    def update_word_count(self):
        """更新字数统计"""
        if self.content:
            # 简单的中文字数统计
            self.word_count = len(self.content.replace(' ', '').replace('\n', '').replace('\r', ''))
            # 字符数包括所有字符
            self.character_count = len(self.content)
        else:
            self.word_count = 0
            self.character_count = 0 