"""
背景音乐库数据模型
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class MusicCategory(Base):
    """音乐分类模型"""
    __tablename__ = "music_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="分类名称")
    description = Column(Text, comment="分类描述")
    icon = Column(String(50), comment="分类图标")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    music_files = relationship("BackgroundMusic", back_populates="category")

class BackgroundMusic(Base):
    """背景音乐模型"""
    __tablename__ = "background_music"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="音乐名称")
    description = Column(Text, comment="音乐描述")
    
    # 文件信息
    filename = Column(String(255), nullable=False, comment="文件名")
    file_path = Column(String(500), nullable=False, comment="文件路径")
    file_size = Column(Integer, comment="文件大小(字节)")
    duration = Column(Float, comment="时长(秒)")
    
    # 分类和标签
    category_id = Column(Integer, ForeignKey("music_categories.id"), comment="分类ID")
    emotion_tags = Column(JSON, comment="情感标签JSON数组")
    style_tags = Column(JSON, comment="风格标签JSON数组")
    
    # 质量和统计
    quality_rating = Column(Float, default=3.0, comment="质量评分(1-5)")
    usage_count = Column(Integer, default=0, comment="使用次数")
    last_used_at = Column(DateTime, comment="最后使用时间")
    
    # 状态管理
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    category = relationship("MusicCategory", back_populates="music_files")