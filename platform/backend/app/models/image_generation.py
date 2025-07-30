"""
图片生成模型
基于书籍智能准备结果生成配图
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, Optional, List

from .base import Base


class ImageGenerationTask(Base):
    """图片生成任务模型"""
    
    __tablename__ = 'image_generation_tasks'
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, ForeignKey('book_chapters.id', ondelete='CASCADE'), nullable=False)
    analysis_result_id = Column(Integer, ForeignKey('analysis_results.id', ondelete='CASCADE'), nullable=True)
    
    # 段落信息
    segment_index = Column(Integer, nullable=False, comment="段落索引")
    segment_text = Column(Text, nullable=False, comment="段落原文")
    segment_type = Column(String(50), default='narrative', comment="段落类型: dialogue, narrative, description")
    
    # 提示词生成
    scene_description = Column(Text, comment="场景描述")
    character_info = Column(JSON, comment="角色信息")
    emotional_tone = Column(String(100), comment="情感色调")
    style_keywords = Column(JSON, comment="风格关键词")
    
    # ComfyUI工作流
    comfyui_workflow = Column(JSON, comment="ComfyUI工作流配置")
    original_prompt = Column(Text, comment="原始提示词（用户输入或AI生成的基础提示词）")
    backend_added_tags = Column(JSON, comment="后端自动添加的质量标签")
    generated_prompt = Column(Text, comment="最终生成的提示词（包含质量标签）")
    negative_prompt = Column(Text, comment="负面提示词")
    
    # 生成配置
    image_width = Column(Integer, default=1024, comment="图片宽度")
    image_height = Column(Integer, default=1024, comment="图片高度")
    generation_model = Column(String(100), default='SD1.5', comment="生成模型")
    generation_params = Column(JSON, comment="生成参数")
    
    # 处理状态
    status = Column(String(20), default='pending', comment="pending, processing, completed, failed")
    progress = Column(Integer, default=0, comment="进度 0-100")
    error_message = Column(Text, comment="错误信息")
    
    # 生成结果
    generated_image_url = Column(String(500), comment="生成的图片URL")
    generated_image_path = Column(String(500), comment="生成的图片本地路径")
    generation_seed = Column(Integer, comment="生成种子")
    generation_time = Column(Integer, comment="生成耗时(秒)")
    
    # 质量评估
    quality_score = Column(Integer, comment="质量评分 0-100")
    user_rating = Column(Integer, comment="用户评分 1-5")
    is_approved = Column(Boolean, default=False, comment="是否通过审核")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, comment="开始生成时间")
    completed_at = Column(DateTime, comment="完成时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    chapter = relationship("BookChapter", back_populates="image_generation_tasks")
    analysis_result = relationship("AnalysisResult", back_populates="image_generation_tasks")
    
    # 索引
    __table_args__ = (
        Index('idx_image_generation_chapter_id', 'chapter_id'),
        Index('idx_image_generation_status', 'status'),
        Index('idx_image_generation_chapter_segment', 'chapter_id', 'segment_index'),
        Index('idx_image_generation_analysis_result', 'analysis_result_id'),
    )
    
    def __repr__(self):
        return f"<ImageGenerationTask(id={self.id}, chapter_id={self.chapter_id}, segment_index={self.segment_index}, status='{self.status}')>"


class ImageGenerationPreset(Base):
    """图片生成预设模板"""
    
    __tablename__ = 'image_generation_presets'
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="预设名称")
    description = Column(Text, comment="预设描述")
    category = Column(String(50), default='general', comment="预设分类: general, character, scene, emotion")
    
    # 预设配置
    default_workflow = Column(JSON, comment="默认ComfyUI工作流")
    prompt_template = Column(Text, comment="提示词模板")
    negative_prompt_template = Column(Text, comment="负面提示词模板")
    style_keywords = Column(JSON, comment="风格关键词")
    
    # 生成参数
    default_params = Column(JSON, comment="默认生成参数")
    recommended_models = Column(JSON, comment="推荐模型列表")
    
    # 元数据
    is_public = Column(Boolean, default=True, comment="是否公开")
    usage_count = Column(Integer, default=0, comment="使用次数")
    success_rate = Column(Integer, default=0, comment="成功率百分比")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 索引
    __table_args__ = (
        Index('idx_image_presets_category', 'category'),
        Index('idx_image_presets_public', 'is_public'),
    )
    
    def __repr__(self):
        return f"<ImageGenerationPreset(id={self.id}, name='{self.name}', category='{self.category}')>"