#!/usr/bin/env python3
"""
手动添加提示词字段到图片生成任务表
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
import asyncio

# 直接使用数据库URL
DATABASE_URL = "postgresql://ai_sound_user:ai_sound_password@localhost:5432/ai_sound"

def add_prompt_fields():
    """手动添加提示词相关字段"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # 检查字段是否已存在
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'image_generation_tasks' 
                AND column_name IN ('original_prompt', 'backend_added_tags')
            """))
            existing_columns = [row[0] for row in result]
            
            # 添加 original_prompt 字段
            if 'original_prompt' not in existing_columns:
                print("添加 original_prompt 字段...")
                conn.execute(text("""
                    ALTER TABLE image_generation_tasks 
                    ADD COLUMN original_prompt TEXT
                """))
                conn.execute(text("""
                    COMMENT ON COLUMN image_generation_tasks.original_prompt 
                    IS '用户输入或基础AI生成的提示词'
                """))
                print("✓ original_prompt 字段添加成功")
            else:
                print("original_prompt 字段已存在")
            
            # 添加 backend_added_tags 字段
            if 'backend_added_tags' not in existing_columns:
                print("添加 backend_added_tags 字段...")
                conn.execute(text("""
                    ALTER TABLE image_generation_tasks 
                    ADD COLUMN backend_added_tags TEXT[]
                """))
                conn.execute(text("""
                    COMMENT ON COLUMN image_generation_tasks.backend_added_tags 
                    IS '后端自动添加的质量标签'
                """))
                print("✓ backend_added_tags 字段添加成功")
            else:
                print("backend_added_tags 字段已存在")
            
            conn.commit()
            print("\n所有字段添加完成！")
            
        except Exception as e:
            print(f"添加字段时出错: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    add_prompt_fields()