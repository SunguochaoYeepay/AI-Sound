#!/usr/bin/env python3
"""
修复项目19的角色映射
"""
import sys
import json
sys.path.append('app')

from database import get_db
from models import NovelProject, TextSegment

def fix_project_19():
    print("🔧 === 修复项目19角色映射 ===")
    
    db = next(get_db())
    
    # 获取项目19
    project = db.query(NovelProject).filter(NovelProject.id == 19).first()
    
    if not project:
        print("❌ 项目19不存在")
        return
    
    print(f"📋 项目信息: {project.name}")
    print(f"📋 当前映射: {project.character_mapping}")
    
    # 获取段落和检测到的说话人
    segments = db.query(TextSegment).filter(TextSegment.project_id == 19).all()
    print(f"📝 段落数: {len(segments)}")
    
    speakers = set()
    for segment in segments:
        if segment.detected_speaker:
            speakers.add(segment.detected_speaker)
            print(f"  段落 {segment.segment_order}: {segment.detected_speaker}")
    
    print(f"🎭 检测到的角色: {list(speakers)}")
    
    # 设置角色映射（都映射到声音ID 1）
    character_mapping = {}
    for speaker in speakers:
        character_mapping[speaker] = 1
    
    print(f"🎯 设置新映射: {character_mapping}")
    
    # 更新项目
    project.character_mapping = json.dumps(character_mapping, ensure_ascii=False)
    
    # 更新段落的voice_profile_id
    for segment in segments:
        if segment.detected_speaker in character_mapping:
            segment.voice_profile_id = character_mapping[segment.detected_speaker]
    
    # 提交更改
    db.commit()
    
    print("✅ 修复完成")
    
    # 验证
    db.refresh(project)
    print(f"🔍 验证映射: {project.character_mapping}")

if __name__ == "__main__":
    fix_project_19() 