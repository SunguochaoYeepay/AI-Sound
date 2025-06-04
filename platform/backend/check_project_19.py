#!/usr/bin/env python3
"""
检查项目19的详细状态
"""
import sys
sys.path.append('app')

from database import get_db
from models import NovelProject, TextSegment

def check_project_19():
    print("🔍 === 检查项目19状态 ===")
    
    db = next(get_db())
    
    # 查询项目19
    project = db.query(NovelProject).filter(NovelProject.id == 19).first()
    
    if not project:
        print("❌ 项目19不存在")
        return
    
    print(f"📋 项目信息:")
    print(f"  ID: {project.id}")
    print(f"  名称: {project.name}")
    print(f"  状态: {project.status}")
    print(f"  角色映射: {project.character_mapping}")
    print(f"  角色映射类型: {type(project.character_mapping)}")
    
    # 解析角色映射
    try:
        mapping_dict = project.get_character_mapping()
        print(f"  解析后映射: {mapping_dict}")
        print(f"  映射是否为空: {len(mapping_dict) == 0}")
    except Exception as e:
        print(f"  解析映射失败: {e}")
    
    # 查询段落
    segments = db.query(TextSegment).filter(TextSegment.project_id == 19).all()
    print(f"\n📝 段落信息: 总共 {len(segments)} 个段落")
    
    for segment in segments:
        print(f"  段落 {segment.segment_order}: {segment.detected_speaker} -> VoiceID {segment.voice_profile_id}")
    
    # 检查有多少段落没有分配声音
    unassigned = [s for s in segments if not s.voice_profile_id]
    print(f"\n⚠️  未分配声音的段落数: {len(unassigned)}")

if __name__ == "__main__":
    check_project_19() 