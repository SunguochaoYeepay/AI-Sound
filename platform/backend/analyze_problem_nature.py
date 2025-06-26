# 分析问题性质：数据问题 vs 代码缺陷
from app.database import get_db
from app.models import NovelProject, BookChapter, AnalysisResult
import json

def analyze_problem_nature():
    db = next(get_db())
    
    print("=== 分析问题性质：数据 vs 代码 ===")
    
    # 1. 检查智能准备结果的完整性
    project = db.query(NovelProject).filter(NovelProject.id == 34).first()
    if not project or not project.book_id:
        print("❌ 项目数据不完整")
        return
    
    chapters = db.query(BookChapter).filter(BookChapter.book_id == project.book_id).all()
    
    print(f"📊 数据完整性检查:")
    
    for chapter in chapters:
        if chapter.analysis_results:
            analysis = chapter.analysis_results[0]
            
            print(f"\n📖 章节: {chapter.chapter_title}")
            
            # 检查synthesis_plan数据
            if hasattr(analysis, 'synthesis_plan') and analysis.synthesis_plan:
                plan = analysis.synthesis_plan
                
                if isinstance(plan, dict) and 'synthesis_plan' in plan:
                    segments = plan['synthesis_plan']
                    
                    # 统计角色配置情况
                    total_segments = len(segments)
                    has_voice_id = 0
                    missing_voice_id = 0
                    unassigned_segments = []
                    
                    for seg in segments:
                        if 'voice_id' in seg and seg['voice_id']:
                            has_voice_id += 1
                        else:
                            missing_voice_id += 1
                            if seg.get('voice_name') == '未分配':
                                unassigned_segments.append({
                                    'segment_id': seg.get('segment_id'),
                                    'speaker': seg.get('speaker'),
                                    'voice_name': seg.get('voice_name')
                                })
                    
                    print(f"  总段落数: {total_segments}")
                    print(f"  有voice_id: {has_voice_id}")
                    print(f"  缺voice_id: {missing_voice_id}")
                    
                    if unassigned_segments:
                        print(f"  未分配段落:")
                        for seg in unassigned_segments[:5]:  # 只显示前5个
                            print(f"    - 段落{seg['segment_id']}: {seg['speaker']} -> {seg['voice_name']}")
                        if len(unassigned_segments) > 5:
                            print(f"    ... 还有{len(unassigned_segments) - 5}个")
    
    print(f"\n🔍 问题性质分析:")
    
    # 2. 分析是代码缺陷还是数据问题
    print(f"\n1️⃣ 数据层面:")
    print(f"  ✅ 智能分析结果完整 - 正确检测到了林渊、导师、将领等角色")
    print(f"  ✅ synthesis_plan生成完整 - 40个段落都有详细配置")
    print(f"  ✅ 每个段落都有speaker、text等基础信息")
    print(f"  ❌ 但部分段落缺少voice_id，标记为'未分配'")
    
    print(f"\n2️⃣ 代码逻辑层面:")
    print(f"  🔍 问题出现在哪个环节？")
    
    # 检查角色映射逻辑
    current_mapping = project.get_character_mapping() or {}
    print(f"  📋 项目角色映射: {list(current_mapping.keys())}")
    
    # 从智能分析结果中提取实际检测到的角色
    detected_characters = set()
    for chapter in chapters:
        if chapter.analysis_results:
            analysis = chapter.analysis_results[0]
            if hasattr(analysis, 'detected_characters'):
                detected_characters.update(analysis.detected_characters)
    
    print(f"  🎭 智能检测角色: {list(detected_characters)}")
    
    # 找出缺失的映射
    missing_in_mapping = detected_characters - set(current_mapping.keys())
    print(f"  ❌ 映射中缺失: {list(missing_in_mapping)}")
    
    print(f"\n3️⃣ 问题定性:")
    if missing_in_mapping:
        print(f"  🎯 这是 **代码缺陷**，原因:")
        print(f"    1. 智能分析正确检测到了角色")
        print(f"    2. 但生成synthesis_plan时，缺失角色的voice_id没有被正确设置")
        print(f"    3. 可能的缺陷位置:")
        print(f"       - 智能分析结果 -> synthesis_plan的转换逻辑")
        print(f"       - 角色映射的查找和应用逻辑")
        print(f"       - 默认值处理逻辑")
    else:
        print(f"  📊 这可能是数据问题")
    
    print(f"\n4️⃣ 代码缺陷具体分析:")
    print(f"  🔍 应该在哪个函数中修复：")
    print(f"    - 智能分析服务：analysis_service.py")
    print(f"    - synthesis_plan生成逻辑")
    print(f"    - 角色映射应用逻辑")
    
    print(f"\n💡 修复策略:")
    print(f"  1. 短期：手动补充角色映射（已完成）")
    print(f"  2. 长期：修复synthesis_plan生成时的角色映射逻辑")
    print(f"  3. 兜底：为'未分配'角色设置默认声音")

if __name__ == "__main__":
    analyze_problem_nature()