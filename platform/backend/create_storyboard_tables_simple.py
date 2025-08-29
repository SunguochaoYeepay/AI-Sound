#!/usr/bin/env python3
"""
简单的故事板表创建脚本
使用应用程序的数据库连接
"""

from app.database import engine
from app.models.storyboard_cards import (
    StoryboardAnalysisSession, BaseStoryboardCard, StoryCard, CharacterCard,
    SceneCard, EventCard, EmotionCard, AudioStoryboardCard
)
from sqlalchemy import text

def create_storyboard_tables():
    """创建故事板相关的数据库表"""
    try:
        print("开始创建故事板分析表...")
        
        # 创建所有表
        StoryboardAnalysisSession.__table__.create(engine, checkfirst=True)
        BaseStoryboardCard.__table__.create(engine, checkfirst=True)
        StoryCard.__table__.create(engine, checkfirst=True)
        CharacterCard.__table__.create(engine, checkfirst=True)
        SceneCard.__table__.create(engine, checkfirst=True)
        EventCard.__table__.create(engine, checkfirst=True)
        EmotionCard.__table__.create(engine, checkfirst=True)
        AudioStoryboardCard.__table__.create(engine, checkfirst=True)
        
        print("✅ 故事板分析表创建成功！")
        
        # 验证表是否创建成功
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES LIKE 'storyboard%'"))
            tables = [row[0] for row in result]
            print(f"创建的表: {tables}")
            
    except Exception as e:
        print(f"❌ 创建表失败: {str(e)}")
        raise

if __name__ == "__main__":
    create_storyboard_tables()
