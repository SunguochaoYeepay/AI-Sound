#!/usr/bin/env python3
"""
检查所有环境音项目
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def check_all_env_projects():
    """检查所有环境音项目"""
    
    # 数据库连接
    DATABASE_URL = "postgresql://ai_sound_user:ai_sound_password@localhost:5432/ai_sound"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 查询所有环境音项目
        result = db.execute(text("""
            SELECT id, name, description, book_id, book_name, status, 
                   created_at, updated_at
            FROM environment_projects 
            ORDER BY id DESC
        """))
        
        projects = result.fetchall()
        
        print(f"环境音项目总数: {len(projects)}")
        
        if projects:
            print(f"\n项目列表:")
            for project in projects:
                print(f"  ID: {project[0]}, 名称: {project[1]}, 状态: {project[5]}, 创建时间: {project[6]}")
        else:
            print("❌ 没有找到任何环境音项目")
            
    except Exception as e:
        print(f"❌ 查询失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_all_env_projects()