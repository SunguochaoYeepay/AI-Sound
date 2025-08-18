#!/usr/bin/env python3
"""
检查项目91在数据库中的实际数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

def check_project_91_db():
    """检查项目91在数据库中的实际数据"""
    
    # 数据库连接
    DATABASE_URL = "postgresql://ai_sound_user:ai_sound_password@localhost:5432/ai_sound"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 查询项目91
        result = db.execute(text("""
            SELECT id, name, description, book_id, book_name, chapter_ids, 
                   chapter_name, status, analysis_result, matching_result, 
                   created_at, updated_at
            FROM environment_projects 
            WHERE id = 91
        """))
        
        project = result.fetchone()
        
        if project:
            print(f"项目91数据库记录:")
            print(f"  ID: {project[0]}")
            print(f"  名称: {project[1]}")
            print(f"  描述: {project[2]}")
            print(f"  书籍ID: {project[3]}")
            print(f"  书籍名称: {project[4]}")
            print(f"  章节IDs: {project[5]}")
            print(f"  章节名称: {project[6]}")
            print(f"  状态: {project[7]}")
            print(f"  创建时间: {project[10]}")
            print(f"  更新时间: {project[11]}")
            
            # 检查analysis_result字段
            analysis_result = project[8]
            print(f"\nanalysis_result字段:")
            print(f"  类型: {type(analysis_result)}")
            print(f"  内容: {analysis_result}")
            
            if analysis_result:
                try:
                    if isinstance(analysis_result, str):
                        parsed = json.loads(analysis_result)
                    else:
                        parsed = analysis_result
                    
                    print(f"  解析成功: {type(parsed)}")
                    if isinstance(parsed, dict):
                        print(f"  键: {list(parsed.keys())}")
                        
                        # 检查嵌套结构
                        if 'success' in parsed and 'analysis_result' in parsed:
                            tracks = parsed['analysis_result'].get('environment_tracks', [])
                            print(f"  轨道数: {len(tracks)}")
                        else:
                            tracks = parsed.get('environment_tracks', [])
                            print(f"  轨道数: {len(tracks)}")
                except Exception as e:
                    print(f"  解析失败: {e}")
            
            # 检查matching_result字段
            matching_result = project[9]
            print(f"\nmatching_result字段:")
            print(f"  类型: {type(matching_result)}")
            print(f"  内容: {matching_result}")
            
        else:
            print("❌ 项目91不存在")
            
    except Exception as e:
        print(f"❌ 查询失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_project_91_db()