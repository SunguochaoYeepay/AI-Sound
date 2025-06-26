"""
书籍模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import json

from .base import BaseModel


class Book(BaseModel):
    """书籍模型"""
    __tablename__ = "books"
    
    title = Column(String(255), nullable=False, comment="书籍标题")
    author = Column(String(255), default="", comment="作者")
    description = Column(Text, default="", comment="描述")
    content = Column(Text, comment="书籍内容")
    chapters_data = Column(Text, comment="章节数据")
    status = Column(String(50), default="draft", comment="状态: draft, published, archived")
    tags = Column(Text, default="[]", comment="标签JSON")
    word_count = Column(Integer, default=0, comment="字数")
    chapter_count = Column(Integer, default=0, comment="章节数")
    source_file_path = Column(String(500), comment="源文件路径")
    source_file_name = Column(String(255), comment="源文件名")
    
    # 关系
    chapters = relationship("BookChapter", back_populates="book", cascade="all, delete-orphan")
    projects = relationship("NovelProject", back_populates="book", cascade="all, delete-orphan")
    
    def get_tags(self):
        """获取标签列表"""
        try:
            return json.loads(self.tags) if self.tags else []
        except json.JSONDecodeError:
            return []
    
    def set_tags(self, tags):
        """设置标签列表"""
        self.tags = json.dumps(tags, ensure_ascii=False)
    
    def get_chapters(self):
        """获取章节信息"""
        try:
            return json.loads(self.chapters_data) if self.chapters_data else []
        except json.JSONDecodeError:
            return []
    
    def set_chapters(self, chapters):
        """设置章节信息"""
        self.chapters_data = json.dumps(chapters, ensure_ascii=False)
    
    def to_dict(self):
        """转换为字典，包含特殊字段处理"""
        result = super().to_dict()
        result['tags'] = self.get_tags()
        result['chapters'] = self.get_chapters()
        return result