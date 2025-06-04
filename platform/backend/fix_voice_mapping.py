#!/usr/bin/env python3
"""
修复最新项目的声音映射问题
"""
import sys
import os
sys.path.append('app')

def fix_voice_mapping():
    print("🔧 === 修复最新项目声音映射 ===")
    
    try:
        from database import get_db
        from models import NovelProject, TextSegment, VoiceProfile
        
        db = next(get_db())
        
        # 获取最新项目
        project = db.query(NovelProject).order_by(NovelProject.id.desc()).first()
        if not project:
            print("❌ 没有项目")
            return
        
        print(f"📋 项目ID: {project.id}")
        print(f"📋 项目名: {project.name}")
        print(f"📋 当前状态: {project.status}")
        
        # 获取角色映射
        char_mapping = project.get_character_mapping()
        print(f"📋 角色映射: {char_mapping}")
        
        if not char_mapping:
            print("❌ 角色映射为空，请先在前端设置角色声音映射")
            return
        
        # 检查段落
        segments = db.query(TextSegment).filter(TextSegment.project_id == project.id).all()
        print(f"📋 段落数量: {len(segments)}")
        
        # 统计需要修复的段落
        unmapped_segments = []
        for segment in segments:
            if not segment.voice_profile_id:
                unmapped_segments.append(segment)
                print(f"  ❌ 段落{segment.segment_order}: 发言人='{segment.detected_speaker}', 声音ID=None")
            else:
                print(f"  ✅ 段落{segment.segment_order}: 发言人='{segment.detected_speaker}', 声音ID={segment.voice_profile_id}")
        
        if not unmapped_segments:
            print("🎉 所有段落都已正确映射声音档案!")
            return
        
        print(f"\n🔧 需要修复 {len(unmapped_segments)} 个段落:")
        
        # 修复映射
        fixed_count = 0
        for segment in unmapped_segments:
            speaker = segment.detected_speaker
            if speaker in char_mapping:
                voice_id = char_mapping[speaker]
                
                # 验证声音ID是否有效
                voice = db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
                if voice and voice.status == 'active':
                    segment.voice_profile_id = voice_id
                    fixed_count += 1
                    print(f"  ✅ 修复段落{segment.segment_order}: {speaker} -> 声音ID {voice_id} ({voice.name})")
                else:
                    print(f"  ❌ 段落{segment.segment_order}: 声音ID {voice_id} 无效")
            else:
                print(f"  ❌ 段落{segment.segment_order}: 角色'{speaker}'未在映射中找到")
        
        if fixed_count > 0:
            # 提交修改
            db.commit()
            print(f"\n🎉 成功修复了 {fixed_count} 个段落的声音映射!")
            
            # 如果项目状态是pending，可以提示用户重新开始生成
            if project.status == 'pending':
                print("💡 项目状态为pending，可以重新开始音频生成")
            elif project.status == 'failed':
                print("💡 项目状态为failed，建议重置状态后重新生成")
        else:
            print("❌ 没有段落能够修复")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_voice_mapping() 