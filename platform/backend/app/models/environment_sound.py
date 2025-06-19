"""
环境音模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import BaseModel


class EnvironmentSoundCategory(BaseModel):
    """环境音分类模型"""
    __tablename__ = "environment_sound_categories"
    
    name = Column(String(100), nullable=False, unique=True, comment="分类名称")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    description = Column(Text, comment="描述")
    color = Column(String(20), default="#1890ff", comment="分类颜色")
    icon = Column(String(100), comment="图标")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # 关系
    sounds = relationship("EnvironmentSound", back_populates="category")
    tags = relationship("EnvironmentSoundTag", back_populates="category")


class EnvironmentSoundTag(BaseModel):
    """环境音标签模型"""
    __tablename__ = "environment_sound_tags"
    
    category_id = Column(Integer, ForeignKey("environment_sound_categories.id"), nullable=False)
    name = Column(String(100), nullable=False, comment="标签名称")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    description = Column(Text, comment="描述")
    color = Column(String(20), comment="标签颜色")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # 关系
    category = relationship("EnvironmentSoundCategory", back_populates="tags")


class EnvironmentSound(BaseModel):
    """环境音模型"""
    __tablename__ = "environment_sounds"
    
    name = Column(String(255), nullable=False, comment="环境音名称")
    description = Column(Text, comment="描述")
    category_id = Column(Integer, ForeignKey("environment_sound_categories.id"), nullable=False)
    
    # 生成参数
    prompt = Column(Text, nullable=False, comment="生成提示词")
    duration = Column(Float, default=10.0, comment="时长(秒)")
    steps = Column(Integer, default=20, comment="生成步数")
    guidance_scale = Column(Float, default=3.5, comment="引导强度")
    
    # 文件信息
    file_path = Column(String(500), comment="音频文件路径")
    file_size = Column(Integer, comment="文件大小(字节)")
    file_format = Column(String(20), default="wav", comment="文件格式")
    
    # 生成状态
    generation_status = Column(String(50), default="pending", comment="生成状态: pending, processing, completed, failed")
    error_message = Column(Text, comment="错误信息")
    processing_time = Column(Float, comment="处理时间(秒)")
    generated_at = Column(DateTime, comment="生成完成时间")
    
    # 使用统计
    usage_count = Column(Integer, default=0, comment="使用次数")
    last_used_at = Column(DateTime, comment="最后使用时间")
    
    # 质量评估
    quality_score = Column(Float, comment="质量评分")
    
    # 关系
    category = relationship("EnvironmentSoundCategory", back_populates="sounds")
    favorites = relationship("EnvironmentSoundFavorite", back_populates="sound", cascade="all, delete-orphan")
    
    def mark_as_used(self):
        """标记为已使用"""
        self.usage_count = (self.usage_count or 0) + 1
        self.last_used_at = datetime.utcnow()
    
    def to_dict(self):
        """转换为字典"""
        result = super().to_dict()
        if self.generated_at:
            result['generated_at'] = self.generated_at.isoformat()
        if self.last_used_at:
            result['last_used_at'] = self.last_used_at.isoformat()
        return result


class EnvironmentSoundFavorite(BaseModel):
    """环境音收藏模型"""
    __tablename__ = "environment_sound_favorites"
    
    user_id = Column(Integer, comment="用户ID")
    environment_sound_id = Column(Integer, ForeignKey("environment_sounds.id"), nullable=False)
    notes = Column(Text, comment="备注")
    
    # 关系
    sound = relationship("EnvironmentSound", back_populates="favorites")