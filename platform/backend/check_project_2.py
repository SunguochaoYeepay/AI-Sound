#!/usr/bin/env python3
"""
检查项目2的角色映射配置
"""
import sys
import os
sys.path.append('app')

def check_project_2():
    print("🔍 === 检查项目2角色映射 ===")
    
    try:
        from database import get_db
        from models import NovelProject, TextSegment, VoiceProfile
        
        db = next(get_db())
        
        # 检查项目
        project = db.query(NovelProject).filter(NovelProject.id == 2).first()
        if not project:
            print("❌ 项目2不存在")
            return
        
        print(f"📋 项目名: {project.name}")
        print(f"📋 状态: {project.status}")
        print(f"📋 角色映射原始字段: {repr(project.character_mapping)}")
        print(f"📋 角色映射类型: {type(project.character_mapping)}")
        print(f"📋 解析后角色映射: {project.get_character_mapping()}")
        
        # 检查段落
        segments = db.query(TextSegment).filter(TextSegment.project_id == 2).all()
        print(f"📋 段落数量: {len(segments)}")
        
        for segment in segments:
            print(f"  段落{segment.segment_order}: 发言人='{segment.detected_speaker}', 声音ID={segment.voice_profile_id}")
        
        # 检查可用声音档案
        voices = db.query(VoiceProfile).filter(VoiceProfile.status == 'active').all()
        print(f"📋 可用声音档案: {len(voices)}个")
        for voice in voices:
            print(f"  ID={voice.id}: {voice.name}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_project_2() 