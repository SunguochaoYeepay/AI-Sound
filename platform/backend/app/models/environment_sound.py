"""
环境音模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float
from sqlalchemy.orm import relationship
import json
from datetime import datetime

from .base import Base


class EnvironmentSound(Base):
    """环境音模型"""
    __tablename__ = "environment_sounds"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="环境音名称")
    prompt = Column(Text, nullable=False, comment="生成提示词")
    description = Column(Text, comment="描述")
    duration = Column(Float, nullable=False, comment="时长(秒)")
    
    # TangoFlux生成参数
    steps = Column(Integer, comment="生成步数")
    cfg_scale = Column(Float, comment="CFG scale参数")
    
    # 文件信息
    file_path = Column(String(500), comment="文件路径")
    file_size = Column(Integer, comment="文件大小(字节)")
    sample_rate = Column(Integer, comment="采样率")
    channels = Column(Integer, comment="声道数")
    
    # 生成信息
    generation_time = Column(Float, comment="生成耗时(秒)")
    generation_model = Column(String(100), comment="生成模型")
    generation_status = Column(String(50), comment="生成状态")
    error_message = Column(Text, comment="错误信息")
    
    # 分类和标签
    category_id = Column(Integer, comment="分类ID")
    tags = Column(JSON, comment="标签列表")  # 存储标签名称列表
    
    # 统计信息
    play_count = Column(Integer, default=0, comment="播放次数")
    download_count = Column(Integer, default=0, comment="下载次数")
    favorite_count = Column(Integer, default=0, comment="收藏次数")
    
    # 评分信息
    quality_score = Column(Float, comment="质量评分")
    user_rating = Column(Float, comment="用户评分")
    rating_count = Column(Integer, default=0, comment="评分人数")
    
    # 状态标志
    is_public = Column(Boolean, default=True, comment="是否公开")
    is_featured = Column(Boolean, default=False, comment="是否精选")
    is_active = Column(Boolean, default=True, comment="是否激活")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    color = Column(String(7), default="#1890ff", comment="显示颜色")
    
    # 创建者和时间戳
    created_by = Column(String(100), comment="创建者")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_generation_params(self):
        """获取生成参数字典"""
        return {
            "steps": self.steps,
            "cfg_scale": self.cfg_scale,
            "generation_model": self.generation_model
        }
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'prompt': self.prompt,
            'description': self.description,
            'duration': self.duration,
            'steps': self.steps,
            'cfg_scale': self.cfg_scale,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'generation_time': self.generation_time,
            'generation_model': self.generation_model,
            'generation_status': self.generation_status,
            'error_message': self.error_message,
            'category_id': self.category_id,
            'tags': self.tags or [],
            'play_count': self.play_count or 0,
            'download_count': self.download_count or 0,
            'favorite_count': self.favorite_count or 0,
            'quality_score': self.quality_score,
            'user_rating': self.user_rating,
            'rating_count': self.rating_count or 0,
            'is_public': self.is_public,
            'is_featured': self.is_featured,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'color': self.color,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'generation_params': self.get_generation_params()
        }


class EnvironmentSoundCategory(Base):
    """环境音分类模型"""
    __tablename__ = "environment_sound_categories"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String(100), nullable=False, unique=True, comment="分类名称")
    description = Column(Text, comment="分类描述")
    icon = Column(String(100), comment="图标")
    sort_order = Column(Integer, comment="排序顺序")
    is_active = Column(Boolean, default=True, comment="是否激活")
    color = Column(String(20), default="#1890ff", comment="分类颜色")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EnvironmentSoundTag(Base):
    """环境音标签模型"""
    __tablename__ = "environment_sound_tags"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String(100), nullable=False, unique=True, comment="标签名称")
    description = Column(Text, default="", comment="标签描述")
    color = Column(String(20), default="#007bff", comment="标签颜色")
    usage_count = Column(Integer, default=0, comment="使用次数")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)


class EnvironmentSoundFavorite(Base):
    """环境音收藏模型"""
    __tablename__ = "environment_sound_favorites"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(String(100), nullable=False, comment="用户ID")
    sound_id = Column(Integer, nullable=False, comment="环境音ID")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 组合唯一约束
    __table_args__ = (
        {'extend_existing': True}
    )


class EnvironmentSoundUsageLog(Base):
    """环境音使用日志模型"""
    __tablename__ = "environment_sound_usage_logs"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    
    sound_id = Column(Integer, nullable=False, comment="环境音ID")
    action = Column(String(50), nullable=False, comment="操作类型")
    user_id = Column(String(100), comment="用户ID")
    ip_address = Column(String(45), comment="IP地址")
    user_agent = Column(Text, comment="User Agent")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EnvironmentSoundPreset(Base):
    """环境音预设模型"""
    __tablename__ = "environment_sound_presets"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String(255), nullable=False, comment="预设名称")
    description = Column(Text, default="", comment="预设描述")
    category_id = Column(Integer, comment="分类ID")
    
    # 预设参数
    default_duration = Column(Float, default=10.0, comment="默认时长")
    default_steps = Column(Integer, default=100, comment="默认步数")
    default_cfg_scale = Column(Float, default=7.5, comment="默认CFG scale")
    
    # 提示词模板
    prompt_templates = Column(JSON, comment="提示词模板")
    example_prompts = Column(JSON, comment="示例提示词")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    sort_order = Column(Integer, default=0, comment="排序")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)