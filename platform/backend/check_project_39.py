#!/usr/bin/env python3
import os
import sys
sys.path.append('.')

from app.database import get_db
from app.models import NovelProject

def check_project():
    db_gen = get_db()
    db = next(db_gen)
    
    project = db.query(NovelProject).filter(NovelProject.id == 39).first()
    if not project:
        print("项目39不存在")
        return
    
    print(f"=== 项目39数据检查 ===")
    print(f"项目ID: {project.id}")
    print(f"项目名称: {project.name}")
    print(f"项目状态: {project.status}")
    print(f"最终音频路径: {project.final_audio_path}")
    print(f"总段落: {project.total_segments}")
    print(f"已完成段落: {project.processed_segments}")
    
    # 检查是否有failed_segments字段
    try:
        print(f"失败段落: {project.failed_segments}")
    except AttributeError:
        print("失败段落: 字段不存在")
    
    # 检查音频文件
    if project.final_audio_path:
        exists = os.path.exists(project.final_audio_path)
        print(f"音频文件存在: {exists}")
        if exists:
            size = os.path.getsize(project.final_audio_path)
            print(f"文件大小: {size} bytes ({size/1024/1024:.2f} MB)")
        else:
            print(f"音频文件路径错误: {project.final_audio_path}")
    else:
        print("最终音频路径为空")
    
    # 检查error_message
    if hasattr(project, 'error_message') and project.error_message:
        print(f"错误信息: {project.error_message}")
    
    db.close()

if __name__ == "__main__":
    check_project() 