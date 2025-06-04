#!/usr/bin/env python3
"""
检查最新项目的段落数据和角色映射问题
"""
import sys
import os
sys.path.append('app')

def check_project_segments():
    print("🔍 === 检查最新项目段落数据 ===")
    
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
        print(f"📋 状态: {project.status}")
        print(f"📋 角色映射原始字段: {repr(project.character_mapping)}")
        print(f"📋 解析后角色映射: {project.get_character_mapping()}")
        
        # 检查段落
        segments = db.query(TextSegment).filter(TextSegment.project_id == project.id).all()
        print(f"📋 段落数量: {len(segments)}")
        
        # 统计说话人
        speakers = {}
        voice_assigned = {}
        
        for segment in segments:
            speaker = segment.detected_speaker or "未识别"
            speakers[speaker] = speakers.get(speaker, 0) + 1
            
            if segment.voice_profile_id:
                voice_assigned[speaker] = voice_assigned.get(speaker, 0) + 1
            
            # 显示前几个段落的详细信息
            if segment.segment_order <= 10:
                print(f"  段落{segment.segment_order}: 发言人='{segment.detected_speaker}', 声音ID={segment.voice_profile_id}, 文本='{segment.text_content[:30]}...'")
        
        print(f"\n🎭 说话人统计:")
        for speaker, count in speakers.items():
            assigned_count = voice_assigned.get(speaker, 0)
            print(f"  {speaker}: {count}个段落, {assigned_count}个已分配声音")
        
        # 检查可用声音档案
        voices = db.query(VoiceProfile).filter(VoiceProfile.status == 'active').all()
        print(f"\n🎵 可用声音档案: {len(voices)}个")
        for voice in voices:
            print(f"  ID={voice.id}: {voice.name}")
        
        # 分析问题
        print(f"\n🔍 问题分析:")
        char_mapping = project.get_character_mapping()
        
        for speaker in speakers.keys():
            if speaker in char_mapping:
                voice_id = char_mapping[speaker]
                # 检查声音ID是否有效
                voice = db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
                if voice and voice.status == 'active':
                    print(f"  ✅ {speaker} -> 声音ID {voice_id} ({voice.name}) - 正常")
                else:
                    print(f"  ❌ {speaker} -> 声音ID {voice_id} - 声音档案无效或不存在")
            else:
                print(f"  ❌ {speaker} - 未在角色映射中找到")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_project_segments() 