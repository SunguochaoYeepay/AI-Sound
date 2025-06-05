#!/usr/bin/env python3
"""
检查AudioFile表中的数据
"""

import sys
import os
sys.path.append('app')

from database import SessionLocal
from models import AudioFile, NovelProject

def check_audio_data():
    """检查音频数据"""
    db = SessionLocal()
    try:
        # 检查总数
        total_count = db.query(AudioFile).count()
        print(f"AudioFile表总记录数: {total_count}")
        
        # 检查活跃状态的文件
        active_count = db.query(AudioFile).filter(AudioFile.status == 'active').count()
        print(f"活跃状态文件数: {active_count}")
        
        # 显示前5个文件
        files = db.query(AudioFile).limit(5).all()
        print(f"\n前5个文件:")
        for f in files:
            print(f"  {f.id}: {f.filename} (状态: {f.status}, 类型: {f.audio_type})")
        
        # 按类型统计
        print(f"\n按类型统计:")
        from sqlalchemy import func
        type_stats = db.query(
            AudioFile.audio_type,
            func.count(AudioFile.id).label('count')
        ).group_by(AudioFile.audio_type).all()
        
        for stat in type_stats:
            print(f"  {stat.audio_type}: {stat.count}个")
        
        # 检查项目关联
        project_files = db.query(AudioFile).filter(AudioFile.project_id.isnot(None)).count()
        print(f"\n关联项目的文件数: {project_files}")
        
    except Exception as e:
        print(f"检查失败: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    check_audio_data() 