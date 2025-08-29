"""
创建故事板分析表的数据库迁移脚本
"""

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, DateTime, Boolean, JSON, Float, ForeignKey, Index
from sqlalchemy.sql import text
from datetime import datetime
import os

# 数据库连接配置
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost/ai_sound")

def create_storyboard_tables():
    """创建故事板分析相关的表"""
    
    engine = create_engine(DATABASE_URL)
    metadata = MetaData()
    
    # 创建故事板分析会话表
    storyboard_analysis_sessions = Table(
        'storyboard_analysis_sessions',
        metadata,
        Column('id', Integer, primary_key=True, index=True),
        Column('book_id', Integer, ForeignKey('books.id', ondelete='CASCADE'), nullable=False),
        Column('session_name', String(200), nullable=False),
        Column('description', Text),
        Column('analysis_type', String(20), default='standard'),
        Column('llm_config', JSON),
        Column('analysis_params', JSON),
        Column('status', String(20), default='pending'),
        Column('progress', Integer, default=0),
        Column('current_step', String(100)),
        Column('total_chapters', Integer, default=0),
        Column('analyzed_chapters', Integer, default=0),
        Column('failed_chapters', Integer, default=0),
        Column('book_confirmed', Boolean, default=False),
        Column('storyboard_confirmed', Boolean, default=False),
        Column('error_message', Text),
        Column('created_at', DateTime, default=datetime.utcnow),
        Column('started_at', DateTime),
        Column('completed_at', DateTime),
        Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        
        # 索引
        Index('idx_storyboard_sessions_book_id', 'book_id'),
        Index('idx_storyboard_sessions_status', 'status'),
        Index('idx_storyboard_sessions_analysis_type', 'analysis_type'),
        Index('idx_storyboard_sessions_created_at', 'created_at'),
    )
    
    # 创建故事板卡片基础表
    storyboard_cards = Table(
        'storyboard_cards',
        metadata,
        Column('id', Integer, primary_key=True, index=True),
        Column('session_id', Integer, ForeignKey('storyboard_analysis_sessions.id', ondelete='CASCADE'), nullable=False),
        Column('card_type', String(20), nullable=False),
        Column('chapter_id', Integer, ForeignKey('book_chapters.id', ondelete='CASCADE'), nullable=True),
        Column('scene_id', Integer, nullable=True),
        Column('content', JSON, nullable=False),
        Column('relationships', JSON),
        Column('confirmation_status', String(20), default='pending'),
        Column('confirmed_at', DateTime),
        Column('confirmed_by', String(100)),
        Column('reanalysis_count', Integer, default=0),
        Column('last_reanalysis_at', DateTime),
        Column('reanalysis_reason', Text),
        Column('confidence_score', Float, default=0.0),
        Column('quality_metrics', JSON),
        Column('created_at', DateTime, default=datetime.utcnow),
        Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        
        # 索引
        Index('idx_storyboard_cards_session_id', 'session_id'),
        Index('idx_storyboard_cards_card_type', 'card_type'),
        Index('idx_storyboard_cards_chapter_id', 'chapter_id'),
        Index('idx_storyboard_cards_confirmation_status', 'confirmation_status'),
        Index('idx_storyboard_cards_session_type', 'session_id', 'card_type'),
    )
    
    # 创建故事卡表
    story_cards = Table(
        'story_cards',
        metadata,
        Column('id', Integer, ForeignKey('storyboard_cards.id'), primary_key=True),
        Column('story_summary', Text),
        Column('main_plot', JSON),
        Column('themes', JSON),
        Column('genre', String(50)),
        Column('target_audience', String(100)),
    )
    
    # 创建角色卡表
    character_cards = Table(
        'character_cards',
        metadata,
        Column('id', Integer, ForeignKey('storyboard_cards.id'), primary_key=True),
        Column('character_name', String(100)),
        Column('character_type', String(20)),
        Column('personality', JSON),
        Column('background', Text),
        Column('voice_characteristics', JSON),
        Column('emotional_range', JSON),
    )
    
    # 创建场景卡表
    scene_cards = Table(
        'scene_cards',
        metadata,
        Column('id', Integer, ForeignKey('storyboard_cards.id'), primary_key=True),
        Column('scene_name', String(100)),
        Column('scene_type', String(50)),
        Column('location', JSON),
        Column('atmosphere', JSON),
        Column('time_period', String(50)),
        Column('environmental_sounds', JSON),
    )
    
    # 创建事件卡表
    event_cards = Table(
        'event_cards',
        metadata,
        Column('id', Integer, ForeignKey('storyboard_cards.id'), primary_key=True),
        Column('event_name', String(100)),
        Column('event_type', String(50)),
        Column('participants', JSON),
        Column('action_description', Text),
        Column('dialogue_content', JSON),
        Column('emotional_context', JSON),
    )
    
    # 创建情绪卡表
    emotion_cards = Table(
        'emotion_cards',
        metadata,
        Column('id', Integer, ForeignKey('storyboard_cards.id'), primary_key=True),
        Column('emotion_type', String(50)),
        Column('intensity', Float),
        Column('duration', JSON),
        Column('triggers', JSON),
        Column('expression', JSON),
        Column('voice_impact', JSON),
    )
    
    # 创建音频分镜卡表
    audio_storyboard_cards = Table(
        'audio_storyboard_cards',
        metadata,
        Column('id', Integer, ForeignKey('storyboard_cards.id'), primary_key=True),
        Column('timeline', JSON),
        Column('audio_tracks', JSON),
        Column('voice_assignments', JSON),
        Column('sound_effects', JSON),
        Column('background_music', JSON),
        Column('mixing_parameters', JSON),
    )
    
    # 创建表
    metadata.create_all(engine)
    
    print("故事板分析表创建完成！")
    
    # 验证表是否创建成功
    with engine.connect() as conn:
        # 检查表是否存在
        result = conn.execute(text("SHOW TABLES LIKE 'storyboard_analysis_sessions'"))
        if result.fetchone():
            print("✓ storyboard_analysis_sessions 表创建成功")
        else:
            print("✗ storyboard_analysis_sessions 表创建失败")
        
        result = conn.execute(text("SHOW TABLES LIKE 'storyboard_cards'"))
        if result.fetchone():
            print("✓ storyboard_cards 表创建成功")
        else:
            print("✗ storyboard_cards 表创建失败")
        
        result = conn.execute(text("SHOW TABLES LIKE 'story_cards'"))
        if result.fetchone():
            print("✓ story_cards 表创建成功")
        else:
            print("✗ story_cards 表创建失败")
        
        result = conn.execute(text("SHOW TABLES LIKE 'character_cards'"))
        if result.fetchone():
            print("✓ character_cards 表创建成功")
        else:
            print("✗ character_cards 表创建失败")
        
        result = conn.execute(text("SHOW TABLES LIKE 'scene_cards'"))
        if result.fetchone():
            print("✓ scene_cards 表创建成功")
        else:
            print("✗ scene_cards 表创建失败")
        
        result = conn.execute(text("SHOW TABLES LIKE 'event_cards'"))
        if result.fetchone():
            print("✓ event_cards 表创建成功")
        else:
            print("✗ event_cards 表创建失败")
        
        result = conn.execute(text("SHOW TABLES LIKE 'emotion_cards'"))
        if result.fetchone():
            print("✓ emotion_cards 表创建成功")
        else:
            print("✗ emotion_cards 表创建失败")
        
        result = conn.execute(text("SHOW TABLES LIKE 'audio_storyboard_cards'"))
        if result.fetchone():
            print("✓ audio_storyboard_cards 表创建成功")
        else:
            print("✗ audio_storyboard_cards 表创建失败")

if __name__ == "__main__":
    create_storyboard_tables()
