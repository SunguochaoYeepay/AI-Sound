from app.database import get_db
from app.models import AnalysisResult

def check_fix_result():
    db = next(get_db())
    
    print("=== 检查修复结果 ===")
    
    # 检查项目61相关的3个章节数据
    for chapter_id in [111, 112, 113]:
        analysis = db.query(AnalysisResult).filter(AnalysisResult.chapter_id == chapter_id).first()
        if analysis and analysis.synthesis_plan:
            segments = analysis.synthesis_plan.get('synthesis_plan', [])
            if segments:
                first_segment = segments[0]
                has_chapter_id = 'chapter_id' in first_segment
                has_chapter_number = 'chapter_number' in first_segment
                print(f"章节 {chapter_id}: {len(segments)} segments, chapter_id={has_chapter_id}, chapter_number={has_chapter_number}")
                if has_chapter_id:
                    chapter_id_value = first_segment.get('chapter_id')
                    chapter_number_value = first_segment.get('chapter_number')
                    print(f"  chapter_id值: {chapter_id_value}, chapter_number值: {chapter_number_value}")
                else:
                    print(f"  ❌ 仍然缺少章节信息")
        else:
            print(f"章节 {chapter_id}: 没有找到分析结果")

if __name__ == "__main__":
    check_fix_result() 