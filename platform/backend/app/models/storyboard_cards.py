"""
故事板卡片模型
基于6类卡片方案的小说转有声读物分析系统
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, JSON, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, Optional, List

from .base import Base


class StoryboardAnalysisSession(Base):
    """故事板分析会话模型"""
    
    __tablename__ = 'storyboard_analysis_sessions'
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
    session_name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # 分析配置
    analysis_type = Column(String(20), default='standard')  # standard, enhanced, custom
    llm_config = Column(JSON)  # LLM配置：模型、参数等
    analysis_params = Column(JSON)  # 分析参数：选项、规则等
    
    # 处理状态
    status = Column(String(20), default='pending')  # pending, analyzing, ready_for_review, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    current_step = Column(String(100))  # 当前处理步骤描述
    
    # 结果统计
    total_chapters = Column(Integer, default=0)
    analyzed_chapters = Column(Integer, default=0)
    failed_chapters = Column(Integer, default=0)
    
    # 确认状态
    book_confirmed = Column(Boolean, default=False)  # 书籍级确认
    storyboard_confirmed = Column(Boolean, default=False)  # 分镜级确认
    
    # 错误信息
    error_message = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    book = relationship("Book", back_populates="storyboard_sessions")
    cards = relationship("BaseStoryboardCard", back_populates="session", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_storyboard_sessions_book_id', 'book_id'),
        Index('idx_storyboard_sessions_status', 'status'),
        Index('idx_storyboard_sessions_analysis_type', 'analysis_type'),
        Index('idx_storyboard_sessions_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<StoryboardAnalysisSession(id={self.id}, book_id={self.book_id}, name='{self.session_name}', status='{self.status}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        book_info = None
        if self.book:
                    book_info = {
            'id': self.book.id,
            'title': self.book.title,
            'author': self.book.author,
            'description': self.book.description
        }
        
        return {
            'id': self.id,
            'book_id': self.book_id,
            'book': book_info,
            'session_name': self.session_name,
            'description': self.description,
            'analysis_type': self.analysis_type,
            'llm_config': self.llm_config,
            'analysis_params': self.analysis_params,
            'status': self.status,
            'progress': self.progress,
            'current_step': self.current_step,
            'total_chapters': self.total_chapters,
            'analyzed_chapters': self.analyzed_chapters,
            'failed_chapters': self.failed_chapters,
            'book_confirmed': self.book_confirmed,
            'storyboard_confirmed': self.storyboard_confirmed,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_progress_percentage(self) -> int:
        """获取进度百分比"""
        if self.total_chapters == 0:
            return 0
        return min(100, int((self.analyzed_chapters / self.total_chapters) * 100))
    
    def mark_started(self):
        """标记会话开始"""
        self.status = 'analyzing'
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self):
        """标记会话完成"""
        self.status = 'ready_for_review'
        self.completed_at = datetime.utcnow()
        self.progress = 100
        self.current_step = '分析完成，等待确认'
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error_message: str):
        """标记会话失败"""
        self.status = 'failed'
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
    
    def confirm_book_level(self):
        """确认书籍级分析"""
        self.book_confirmed = True
        self.updated_at = datetime.utcnow()
    
    def confirm_storyboard_level(self):
        """确认分镜级分析"""
        self.storyboard_confirmed = True
        self.status = 'completed'
        self.updated_at = datetime.utcnow()


class BaseStoryboardCard(Base):
    """故事板卡片基础模型"""
    
    __tablename__ = 'storyboard_cards'
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('storyboard_analysis_sessions.id', ondelete='CASCADE'), nullable=False)
    card_type = Column(String(20), nullable=False)  # story, character, scene, event, emotion, storyboard
    
    # 关联字段（可选）
    chapter_id = Column(Integer, ForeignKey('book_chapters.id', ondelete='CASCADE'), nullable=True)
    scene_id = Column(Integer, nullable=True)  # 场景ID（如果有场景概念）
    
    # 卡片内容
    content = Column(JSON, nullable=False)  # 卡片具体内容
    relationships = Column(JSON)  # 与其他卡片的关系
    
    # 确认状态
    confirmation_status = Column(String(20), default='pending')  # pending, confirmed, rejected
    confirmed_at = Column(DateTime)
    confirmed_by = Column(String(100))  # 确认人
    
    # 重新分析
    reanalysis_count = Column(Integer, default=0)  # 重新分析次数
    last_reanalysis_at = Column(DateTime)
    reanalysis_reason = Column(Text)  # 重新分析原因
    
    # 质量评估
    confidence_score = Column(Float, default=0.0)  # 置信度 0-1
    quality_metrics = Column(JSON)  # 质量指标
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    session = relationship("StoryboardAnalysisSession", back_populates="cards")
    chapter = relationship("BookChapter")
    
    # 索引
    __table_args__ = (
        Index('idx_storyboard_cards_session_id', 'session_id'),
        Index('idx_storyboard_cards_card_type', 'card_type'),
        Index('idx_storyboard_cards_chapter_id', 'chapter_id'),
        Index('idx_storyboard_cards_confirmation_status', 'confirmation_status'),
        Index('idx_storyboard_cards_session_type', 'session_id', 'card_type'),
    )
    
    def __repr__(self):
        return f"<BaseStoryboardCard(id={self.id}, session_id={self.session_id}, type='{self.card_type}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'card_type': self.card_type,
            'chapter_id': self.chapter_id,
            'scene_id': self.scene_id,
            'content': self.content,
            'relationships': self.relationships,
            'confirmation_status': self.confirmation_status,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'confirmed_by': self.confirmed_by,
            'reanalysis_count': self.reanalysis_count,
            'last_reanalysis_at': self.last_reanalysis_at.isoformat() if self.last_reanalysis_at else None,
            'reanalysis_reason': self.reanalysis_reason,
            'confidence_score': self.confidence_score,
            'quality_metrics': self.quality_metrics,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def confirm(self, confirmed_by: str = None):
        """确认卡片"""
        self.confirmation_status = 'confirmed'
        self.confirmed_at = datetime.utcnow()
        self.confirmed_by = confirmed_by
        self.updated_at = datetime.utcnow()
    
    def reject(self, reason: str = None):
        """拒绝卡片"""
        self.confirmation_status = 'rejected'
        self.reanalysis_reason = reason
        self.updated_at = datetime.utcnow()
    
    def request_reanalysis(self, reason: str):
        """请求重新分析"""
        self.reanalysis_count += 1
        self.last_reanalysis_at = datetime.utcnow()
        self.reanalysis_reason = reason
        self.confirmation_status = 'pending'
        self.updated_at = datetime.utcnow()


# 具体的卡片类型模型（继承BaseStoryboardCard）
class StoryCard(BaseStoryboardCard):
    """故事卡模型"""
    __tablename__ = 'story_cards'
    
    id = Column(Integer, ForeignKey('storyboard_cards.id'), primary_key=True)
    
    # 故事卡特有字段
    story_summary = Column(Text)  # 故事概要
    main_plot = Column(JSON)  # 主要情节
    themes = Column(JSON)  # 主题分析
    genre = Column(String(50))  # 类型
    target_audience = Column(String(100))  # 目标受众
    
    __mapper_args__ = {
        'polymorphic_identity': 'story',
    }


class CharacterCard(BaseStoryboardCard):
    """角色卡模型"""
    __tablename__ = 'character_cards'
    
    id = Column(Integer, ForeignKey('storyboard_cards.id'), primary_key=True)
    
    # 角色卡特有字段
    character_name = Column(String(100))  # 角色名称
    character_type = Column(String(20))  # 角色类型：主角、配角、反派等
    personality = Column(JSON)  # 性格特征
    background = Column(Text)  # 背景故事
    voice_characteristics = Column(JSON)  # 声音特征
    emotional_range = Column(JSON)  # 情感范围
    
    __mapper_args__ = {
        'polymorphic_identity': 'character',
    }


class SceneCard(BaseStoryboardCard):
    """场景卡模型"""
    __tablename__ = 'scene_cards'
    
    id = Column(Integer, ForeignKey('storyboard_cards.id'), primary_key=True)
    
    # 场景卡特有字段
    scene_name = Column(String(100))  # 场景名称
    scene_type = Column(String(50))  # 场景类型：室内、室外、特殊等
    location = Column(JSON)  # 地点描述
    atmosphere = Column(JSON)  # 氛围描述
    time_period = Column(String(50))  # 时间背景
    environmental_sounds = Column(JSON)  # 环境音效
    
    __mapper_args__ = {
        'polymorphic_identity': 'scene',
    }


class EventCard(BaseStoryboardCard):
    """事件卡模型"""
    __tablename__ = 'event_cards'
    
    id = Column(Integer, ForeignKey('storyboard_cards.id'), primary_key=True)
    
    # 事件卡特有字段
    event_name = Column(String(100))  # 事件名称
    event_type = Column(String(50))  # 事件类型：对话、动作、描述等
    participants = Column(JSON)  # 参与者
    action_description = Column(Text)  # 动作描述
    dialogue_content = Column(JSON)  # 对话内容
    emotional_context = Column(JSON)  # 情感上下文
    
    __mapper_args__ = {
        'polymorphic_identity': 'event',
    }


class EmotionCard(BaseStoryboardCard):
    """情绪卡模型"""
    __tablename__ = 'emotion_cards'
    
    id = Column(Integer, ForeignKey('storyboard_cards.id'), primary_key=True)
    
    # 情绪卡特有字段
    emotion_type = Column(String(50))  # 情绪类型
    intensity = Column(Float)  # 强度 0-1
    duration = Column(JSON)  # 持续时间
    triggers = Column(JSON)  # 触发因素
    expression = Column(JSON)  # 表达方式
    voice_impact = Column(JSON)  # 对声音的影响
    
    __mapper_args__ = {
        'polymorphic_identity': 'emotion',
    }


class AudioStoryboardCard(BaseStoryboardCard):
    """音频分镜卡模型"""
    __tablename__ = 'audio_storyboard_cards'
    
    id = Column(Integer, ForeignKey('storyboard_cards.id'), primary_key=True)
    
    # 音频分镜卡特有字段
    timeline = Column(JSON)  # 时间轴
    audio_tracks = Column(JSON)  # 音轨配置
    voice_assignments = Column(JSON)  # 声音分配
    sound_effects = Column(JSON)  # 音效配置
    background_music = Column(JSON)  # 背景音乐
    mixing_parameters = Column(JSON)  # 混音参数
    
    __mapper_args__ = {
        'polymorphic_identity': 'storyboard',
    }
