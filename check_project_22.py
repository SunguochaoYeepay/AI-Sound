#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'platform', 'backend'))

from app.database import get_db
from app.models import NovelProject, TextSegment, SynthesisTask

def check_project_22():
    print("=== 检查项目22详细状态 ===")
    
    db = next(get_db())
    
    # 检查项目基本信息
    project = db.query(NovelProject).filter(NovelProject.id == 22).first()
    if not project:
        print("❌ 项目22不存在")
        return
    
    print(f"📖 项目信息:")
    print(f"   名称: {project.name}")
    print(f"   状态: {project.status}")
    print(f"   书籍ID: {project.book_id}")
    print(f"   总段落数: {project.total_segments}")
    print(f"   已处理段落数: {project.processed_segments}")
    print(f"   当前段落: {project.current_segment}")
    print(f"   开始时间: {project.started_at}")
    print(f"   完成时间: {project.completed_at}")
    
    # 检查角色映射
    char_mapping = project.get_character_mapping()
    print(f"\n🎭 角色映射:")
    if char_mapping:
        for char, voice_id in char_mapping.items():
            print(f"   {char} -> 声音ID {voice_id}")
    else:
        print("   ❌ 没有角色映射")
    
    # 检查文本段落
    segments = db.query(TextSegment).filter(TextSegment.project_id == 22).all()
    print(f"\n📝 文本段落:")
    print(f"   总数: {len(segments)}")
    
    if segments:
        # 统计段落状态
        status_count = {}
        for segment in segments:
            status = segment.status
            status_count[status] = status_count.get(status, 0) + 1
        
        print(f"   状态统计:")
        for status, count in status_count.items():
            emoji = "✅" if status == "completed" else "❌" if status == "failed" else "🔄" if status == "processing" else "⏸️"
            print(f"      {emoji} {status}: {count} 个")
        
        # 显示前几个段落的详情
        print(f"\n   前5个段落详情:")
        for i, segment in enumerate(segments[:5], 1):
            print(f"   {i}. 段落{segment.id}: {segment.status}")
            print(f"      说话人: {segment.speaker}")
            print(f"      声音ID: {segment.voice_id}")
            print(f"      内容: {segment.content[:50]}...")
            if segment.error_message:
                print(f"      错误: {segment.error_message}")
    
    # 检查合成任务
    synthesis_tasks = db.query(SynthesisTask).filter(SynthesisTask.project_id == 22).all()
    print(f"\n🎵 合成任务:")
    print(f"   总数: {len(synthesis_tasks)}")
    
    if synthesis_tasks:
        for task in synthesis_tasks:
            print(f"   任务{task.id}: {task.status}")
            print(f"      创建时间: {task.created_at}")
            print(f"      开始时间: {task.started_at}")
            print(f"      完成时间: {task.completed_at}")
            print(f"      总段落: {task.total_segments}")
            print(f"      已完成: {task.completed_segments}")
            if task.error_message:
                print(f"      错误: {task.error_message}")
    else:
        print("   ❌ 没有合成任务")

if __name__ == "__main__":
    check_project_22() 