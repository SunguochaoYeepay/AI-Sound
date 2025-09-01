#!/usr/bin/env python3
"""
创建音频剧本表的数据库迁移脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.database_mysql import DATABASE_URL
from app.config import settings

def create_audio_script_table():
    """创建音频剧本表"""
    try:
        # 创建数据库连接
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # 创建音频剧本表
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS audio_script_cards (
                id INT PRIMARY KEY,
                script_segments JSON,
                script_metadata JSON,
                quality_score FLOAT DEFAULT 0.0,
                FOREIGN KEY (id) REFERENCES storyboard_cards(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            conn.execute(text(create_table_sql))
            conn.commit()
            
            print("✅ 音频剧本表创建成功")
            
            # 创建索引（MySQL不支持IF NOT EXISTS，需要先检查）
            try:
                create_index_sql = """
                CREATE INDEX idx_audio_script_quality_score 
                ON audio_script_cards(quality_score);
                """
                
                conn.execute(text(create_index_sql))
                conn.commit()
                
                print("✅ 音频剧本表索引创建成功")
            except Exception as e:
                if "Duplicate key name" in str(e):
                    print("✅ 音频剧本表索引已存在")
                else:
                    print(f"⚠️ 创建索引时出现问题: {str(e)}")
            
    except Exception as e:
        print(f"❌ 创建音频剧本表失败: {str(e)}")
        raise

if __name__ == "__main__":
    print("开始创建音频剧本表...")
    create_audio_script_table()
    print("音频剧本表创建完成！")
