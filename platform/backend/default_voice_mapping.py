#!/usr/bin/env python3
"""
为所有未设置角色映射的项目设置默认声音映射
"""
import sys
import os
sys.path.append('app')

def set_default_voice_mapping():
    print("🔧 === 设置默认声音映射 ===")
    
    try:
        from database import get_db
        from models import NovelProject, TextSegment, VoiceProfile
        from novel_reader import update_segments_voice_mapping_no_commit
        import asyncio
        
        db = next(get_db())
        
        # 获取第一个可用的声音档案
        voice = db.query(VoiceProfile).filter(VoiceProfile.status == 'active').first()
        if not voice:
            print("❌ 没有可用的声音档案")
            return
        
        print(f"📋 将使用默认声音档案: {voice.name} (ID: {voice.id})")
        
        # 获取所有没有角色映射的项目
        projects_without_mapping = []
        
        for project in db.query(NovelProject).all():
            char_mapping = project.get_character_mapping()
            if not char_mapping:  # 没有角色映射
                # 获取段落中的所有角色
                segments = db.query(TextSegment).filter(TextSegment.project_id == project.id).all()
                speakers = set()
                for segment in segments:
                    if segment.detected_speaker:
                        speakers.add(segment.detected_speaker)
                
                if speakers:  # 有角色需要映射
                    projects_without_mapping.append({
                        'project': project,
                        'speakers': list(speakers),
                        'segments_count': len(segments)
                    })
        
        if not projects_without_mapping:
            print("🎉 所有项目都已设置角色映射!")
            return
        
        print(f"\n📋 找到 {len(projects_without_mapping)} 个需要设置默认映射的项目:")
        for item in projects_without_mapping:
            project = item['project']
            speakers = item['speakers']
            print(f"  项目{project.id}: {project.name} - 角色: {speakers}")
        
        # 直接设置，不需要用户确认
        print(f"\n🔧 开始为 {len(projects_without_mapping)} 个项目设置默认映射...")
        
        # 批量设置默认映射
        total_fixed = 0
        
        async def set_project_mapping(project, speakers):
            try:
                # 为所有角色设置相同的声音档案
                char_mapping = {}
                for speaker in speakers:
                    char_mapping[speaker] = voice.id
                
                # 更新项目的角色映射
                project.set_character_mapping(char_mapping)
                
                # 更新段落的声音映射
                result = await update_segments_voice_mapping_no_commit(project.id, char_mapping, db)
                return result
            except Exception as e:
                return {"error": str(e), "updated_count": 0}
        
        for item in projects_without_mapping:
            project = item['project']
            speakers = item['speakers']
            
            print(f"\n🔧 设置项目{project.id}: {project.name}")
            print(f"   角色: {speakers}")
            
            # 使用异步函数设置映射
            result = asyncio.run(set_project_mapping(project, speakers))
            
            if 'error' in result:
                print(f"   ❌ 设置失败: {result['error']}")
            else:
                updated = result.get('updated_count', 0)
                total_fixed += updated
                print(f"   ✅ 设置完成: 更新了 {updated} 个段落")
        
        # 提交所有更改
        if total_fixed > 0:
            db.commit()
            print(f"\n🎉 默认映射设置完成!")
            print(f"   总共更新了 {total_fixed} 个段落")
            print(f"   涉及 {len(projects_without_mapping)} 个项目")
            print(f"   所有角色都映射到: {voice.name}")
        else:
            print("\n❌ 没有段落被更新")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 设置默认映射失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    set_default_voice_mapping()