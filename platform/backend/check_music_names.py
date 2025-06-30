#!/usr/bin/env python3
"""
检查音乐生成任务的名称显示问题
"""

import os
import sys
sys.path.append('.')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.music_generation import MusicGenerationTask

# 数据库连接 - 使用环境配置
DATABASE_URL = "postgresql://ai_sound_user:ai_sound_password@localhost:5432/ai_sound"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_music_names():
    """检查音乐生成任务的名称"""
    session = SessionLocal()
    try:
        # 获取最近的音乐生成任务
        tasks = session.query(MusicGenerationTask).order_by(
            MusicGenerationTask.created_at.desc()
        ).limit(10).all()
        
        print("📋 数据库中的音乐生成任务:")
        print("-" * 80)
        for task in tasks:
            print(f"ID: {task.id}")
            print(f"名称: {task.name}")
            print(f"风格: {task.custom_style}")
            print(f"状态: {task.status}")
            print(f"内容: {task.content[:50]}..." if task.content else "无内容")
            print(f"创建时间: {task.created_at}")
            print("-" * 40)
            
        if not tasks:
            print("❌ 没有找到音乐生成任务")
            
    except Exception as e:
        print(f"❌ 数据库查询失败: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_music_names() 