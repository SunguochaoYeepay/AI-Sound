#!/usr/bin/env python3
"""
批量修复所有项目的声音映射问题
"""
import sys
import os
sys.path.append('app')

def batch_fix_voice_mapping():
    print("🔧 === 批量修复所有项目声音映射 ===")
    
    try:
        from database import get_db
        from models import NovelProject, TextSegment, VoiceProfile
        from novel_reader import update_segments_voice_mapping_no_commit
        import asyncio
        
        db = next(get_db())
        
        # 获取所有有角色映射但存在未映射段落的项目
        projects = db.query(NovelProject).all()
        problem_projects = []
        
        for project in projects:
            char_mapping = project.get_character_mapping()
            if not char_mapping:
                continue  # 跳过没有角色映射的项目
            
            # 检查是否有未映射的段落
            segments = db.query(TextSegment).filter(TextSegment.project_id == project.id).all()
            unmapped_count = len([s for s in segments if not s.voice_profile_id])
            
            if unmapped_count > 0:
                problem_projects.append({
                    'project': project,
                    'char_mapping': char_mapping,
                    'unmapped_count': unmapped_count,
                    'total_count': len(segments)
                })
        
        if not problem_projects:
            print("🎉 所有项目的声音映射都正常!")
            return
        
        print(f"📋 找到 {len(problem_projects)} 个需要修复的项目:")
        for item in problem_projects:
            project = item['project']
            print(f"  项目{project.id}: {project.name} - {item['unmapped_count']}/{item['total_count']} 段落未映射")
        
        # 确认是否继续
        confirm = input(f"\n是否继续修复这 {len(problem_projects)} 个项目? (y/n): ")
        if confirm.lower() != 'y':
            print("❌ 用户取消操作")
            return
        
        # 批量修复
        total_fixed = 0
        
        async def fix_project(project, char_mapping):
            try:
                result = await update_segments_voice_mapping_no_commit(project.id, char_mapping, db)
                return result
            except Exception as e:
                return {"error": str(e), "updated_count": 0}
        
        for item in problem_projects:
            project = item['project']
            char_mapping = item['char_mapping']
            
            print(f"\n🔧 修复项目{project.id}: {project.name}")
            print(f"   角色映射: {char_mapping}")
            
            # 使用异步函数修复
            result = asyncio.run(fix_project(project, char_mapping))
            
            if 'error' in result:
                print(f"   ❌ 修复失败: {result['error']}")
            else:
                updated = result.get('updated_count', 0)
                unmapped = result.get('unmapped_speakers', [])
                total_fixed += updated
                
                print(f"   ✅ 修复完成: 更新了 {updated} 个段落")
                if unmapped:
                    print(f"   ⚠️  仍有未映射角色: {unmapped}")
        
        # 提交所有更改
        if total_fixed > 0:
            db.commit()
            print(f"\n🎉 批量修复完成!")
            print(f"   总共修复了 {total_fixed} 个段落")
            print(f"   涉及 {len(problem_projects)} 个项目")
        else:
            print("\n❌ 没有段落被修复")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 批量修复失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    batch_fix_voice_mapping() 