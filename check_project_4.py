#!/usr/bin/env python3
"""
检查项目4的详细状态
"""
import sys
import os
sys.path.append('app')

def check_project_4():
    print("🔍 === 检查项目4状态 ===")
    
    try:
        from database import get_db
        from models import NovelProject, TextSegment
        
        db = next(get_db())
        
        # 查询项目4
        project = db.query(NovelProject).filter(NovelProject.id == 4).first()
        
        if not project:
            print("❌ 项目4不存在")
            return
        
        print(f"📋 项目信息:")
        print(f"  ID: {project.id}")
        print(f"  名称: {project.name}")
        print(f"  状态: {project.status}")
        print(f"  原始文本: {repr(project.original_text)}")
        print(f"  原始文本长度: {len(project.original_text) if project.original_text else 0}")
        print(f"  角色映射: {project.character_mapping}")
        
        # 查询段落
        segments = db.query(TextSegment).filter(TextSegment.project_id == 4).all()
        print(f"\n📝 段落信息: 总共 {len(segments)} 个段落")
        
        for segment in segments:
            print(f"  段落 {segment.segment_order}: \"{segment.text_content}\" -> 说话人: {segment.detected_speaker}")
        
        # 分析为什么没有识别出角色
        if segments:
            print(f"\n🤔 角色识别分析:")
            speakers = set()
            for segment in segments:
                speakers.add(segment.detected_speaker)
                print(f"    段落{segment.segment_order}的说话人: '{segment.detected_speaker}'")
            
            print(f"  检测到的不重复说话人: {list(speakers)}")
            
            # 检查是否只有旁白
            non_narrator = [s for s in speakers if s not in ['旁白', 'narrator']]
            if not non_narrator:
                print(f"  ⚠️  只检测到旁白，没有其他角色")
                print(f"  💡 这可能是因为文本内容太简单，或者没有明显的对话标记")
            else:
                print(f"  ✅ 检测到非旁白角色: {non_narrator}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_project_4() 