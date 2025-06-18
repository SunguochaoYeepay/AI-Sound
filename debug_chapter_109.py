import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import BookChapter, AnalysisResult, Book
from app.database import SessionLocal

def debug_chapter_109():
    db = SessionLocal()
    try:
        # 查询章节109
        chapter = db.query(BookChapter).filter(BookChapter.id == 109).first()
        if chapter:
            print(f"章节信息:")
            print(f"  ID: {chapter.id}")
            print(f"  章节号: {chapter.chapter_number}")
            print(f"  标题: {chapter.chapter_title}")
            print(f"  分析状态: {chapter.analysis_status}")
            print(f"  书籍ID: {chapter.book_id}")
            print()
            
            # 查询分析结果
            analysis = db.query(AnalysisResult).filter(AnalysisResult.chapter_id == 109).first()
            if analysis:
                print(f"分析结果:")
                print(f"  ID: {analysis.id}")
                print(f"  状态: {analysis.status}")
                print(f"  synthesis_plan存在: {analysis.synthesis_plan is not None}")
                
                if analysis.synthesis_plan:
                    import json
                    try:
                        if isinstance(analysis.synthesis_plan, str):
                            plan = json.loads(analysis.synthesis_plan)
                        else:
                            plan = analysis.synthesis_plan
                            
                        print(f"  synthesis_plan类型: {type(plan)}")
                        
                        if isinstance(plan, dict):
                            print(f"  synthesis_plan键: {list(plan.keys())}")
                            if 'synthesis_plan' in plan:
                                segments = plan['synthesis_plan']
                                print(f"  段落数量: {len(segments) if isinstance(segments, list) else 'not list'}")
                                if isinstance(segments, list) and len(segments) > 0:
                                    print(f"  第一个段落: {segments[0]}")
                    except Exception as e:
                        print(f"  解析synthesis_plan失败: {e}")
            else:
                print("未找到分析结果")
        else:
            print("未找到章节109")
            
    except Exception as e:
        print(f"查询失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_chapter_109() 