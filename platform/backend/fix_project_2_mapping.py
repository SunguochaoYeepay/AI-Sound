#!/usr/bin/env python3
"""
修复项目2的角色映射配置
"""
import sys
import os
sys.path.append('app')

def fix_project_2():
    print("🔧 === 修复项目2角色映射 ===")
    
    try:
        from database import get_db
        from models import NovelProject, TextSegment, VoiceProfile
        
        db = next(get_db())
        
        # 1. 检查可用声音档案
        voices = db.query(VoiceProfile).filter(VoiceProfile.status == 'active').all()
        print(f"📋 可用声音档案: {len(voices)}个")
        
        if not voices:
            print("❌ 没有可用的声音档案，无法设置映射")
            return
        
        # 使用第一个声音档案
        voice = voices[0]
        print(f"✅ 将使用声音档案: ID={voice.id}, 名称={voice.name}")
        
        # 2. 获取项目2
        project = db.query(NovelProject).filter(NovelProject.id == 2).first()
        if not project:
            print("❌ 项目2不存在")
            return
        
        print(f"📋 项目: {project.name}")
        
        # 3. 设置角色映射：旁白 -> voice.id
        char_mapping = {"旁白": voice.id}
        project.set_character_mapping(char_mapping)
        
        # 4. 更新所有段落的voice_profile_id
        segments = db.query(TextSegment).filter(TextSegment.project_id == 2).all()
        print(f"📋 更新 {len(segments)} 个段落的声音映射...")
        
        for segment in segments:
            if segment.detected_speaker == "旁白":
                segment.voice_profile_id = voice.id
                print(f"  ✅ 段落{segment.segment_order}: 旁白 -> 声音ID {voice.id}")
        
        # 5. 提交更改
        db.commit()
        
        print("🎉 角色映射修复完成！")
        print(f"   旁白 -> {voice.name} (ID: {voice.id})")
        
        # 6. 验证修复结果
        db.refresh(project)
        print(f"📋 验证 - 角色映射: {project.get_character_mapping()}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_project_2() 