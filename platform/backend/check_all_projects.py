#!/usr/bin/env python3
"""
检查所有项目中的声音映射问题
"""
import sys
import os
sys.path.append('app')

def check_all_projects():
    print("🔍 === 检查所有项目的声音映射 ===")
    
    try:
        from database import get_db
        from models import NovelProject, TextSegment, VoiceProfile
        
        db = next(get_db())
        
        # 获取所有项目
        projects = db.query(NovelProject).order_by(NovelProject.id.desc()).all()
        if not projects:
            print("❌ 没有项目")
            return
        
        print(f"📋 共找到 {len(projects)} 个项目")
        
        problem_projects = []
        
        for project in projects:
            print(f"\n📋 检查项目 {project.id}: {project.name} ({project.status})")
            
            # 获取段落
            segments = db.query(TextSegment).filter(TextSegment.project_id == project.id).all()
            
            # 统计未映射的段落
            unmapped_count = 0
            mapped_count = 0
            
            for segment in segments:
                if not segment.voice_profile_id:
                    unmapped_count += 1
                    print(f"  ❌ 段落{segment.segment_order}: 发言人='{segment.detected_speaker}', 声音ID=None")
                else:
                    mapped_count += 1
            
            if unmapped_count > 0:
                problem_projects.append({
                    'id': project.id,
                    'name': project.name,
                    'status': project.status,
                    'unmapped': unmapped_count,
                    'total': len(segments)
                })
                print(f"  ⚠️  问题: {unmapped_count}/{len(segments)} 个段落未映射声音")
            else:
                print(f"  ✅ 所有 {mapped_count} 个段落都已映射声音")
        
        # 汇总
        if problem_projects:
            print(f"\n🚨 发现 {len(problem_projects)} 个有问题的项目:")
            for proj in problem_projects:
                print(f"  项目{proj['id']}: {proj['name']} - {proj['unmapped']}/{proj['total']} 段落未映射")
        else:
            print(f"\n🎉 所有项目的声音映射都正常!")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_all_projects() 