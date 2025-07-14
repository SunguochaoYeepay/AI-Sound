from app.database import get_db
from app.models import AnalysisResult, BookChapter
import json

def diagnose_chapters():
    db = next(get_db())
    
    print("=== 诊断章节数据结构 ===")
    
    # 检查这三个章节的详细信息
    for chapter_id in [111, 112, 113]:
        print(f"\n--- 章节 {chapter_id} ---")
        
        # 1. 检查章节是否存在
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if chapter:
            print(f"✅ 章节存在: ID={chapter.id}, 编号={chapter.chapter_number}, 标题={chapter.chapter_title}")
        else:
            print(f"❌ 章节不存在")
            continue
        
        # 2. 检查分析结果
        analysis = db.query(AnalysisResult).filter(AnalysisResult.chapter_id == chapter_id).first()
        if analysis:
            print(f"✅ 分析结果存在: ID={analysis.id}")
            
            # 3. 检查synthesis_plan结构
            if analysis.synthesis_plan:
                plan = analysis.synthesis_plan
                print(f"synthesis_plan类型: {type(plan)}")
                print(f"synthesis_plan键: {list(plan.keys()) if isinstance(plan, dict) else 'Not a dict'}")
                
                if 'synthesis_plan' in plan:
                    segments = plan['synthesis_plan']
                    print(f"segments数量: {len(segments)}")
                    
                    if segments:
                        first = segments[0]
                        print(f"第一个segment的键: {list(first.keys())}")
                        print(f"是否有chapter_id: {'chapter_id' in first}")
                        print(f"是否有chapter_number: {'chapter_number' in first}")
                        
                        # 检查前3个segments的详细信息
                        for i, seg in enumerate(segments[:3]):
                            print(f"  Segment {i+1}:")
                            print(f"    segment_id: {seg.get('segment_id', 'None')}")
                            print(f"    chapter_id: {seg.get('chapter_id', 'None')}")  
                            print(f"    chapter_number: {seg.get('chapter_number', 'None')}")
                            print(f"    speaker: {seg.get('speaker', 'None')}")
                else:
                    print("❌ synthesis_plan中没有'synthesis_plan'键")
            else:
                print("❌ 没有synthesis_plan数据")
        else:
            print(f"❌ 没有找到分析结果")

def fix_specific_chapters():
    """专门修复这三个章节"""
    db = next(get_db())
    
    print("\n=== 专门修复这三个章节 ===")
    
    for chapter_id in [111, 112, 113]:
        print(f"\n🔄 修复章节 {chapter_id}...")
        
        # 获取章节信息
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            print(f"❌ 章节 {chapter_id} 不存在")
            continue
        
        # 获取分析结果
        analysis = db.query(AnalysisResult).filter(AnalysisResult.chapter_id == chapter_id).first()
        if not analysis or not analysis.synthesis_plan:
            print(f"❌ 章节 {chapter_id} 没有分析结果")
            continue
        
        # 修复数据
        synthesis_plan = analysis.synthesis_plan
        if 'synthesis_plan' in synthesis_plan:
            segments = synthesis_plan['synthesis_plan']
            
            print(f"   修复 {len(segments)} 个segments...")
            
            for segment in segments:
                segment['chapter_id'] = chapter.id
                segment['chapter_number'] = chapter.chapter_number
            
            # 保存修改
            analysis.synthesis_plan = synthesis_plan
            print(f"   ✅ 章节 {chapter.id} (第{chapter.chapter_number}章) 修复完成")
        else:
            print(f"❌ 章节 {chapter_id} 数据格式异常")
    
    # 提交所有修改
    try:
        db.commit()
        print("\n🎉 所有修改已提交到数据库")
    except Exception as e:
        print(f"❌ 提交失败: {str(e)}")
        db.rollback()

if __name__ == "__main__":
    # 先诊断
    diagnose_chapters()
    
    # 再修复
    fix_specific_chapters()
    
    # 最后验证
    print("\n=== 修复后验证 ===")
    diagnose_chapters() 