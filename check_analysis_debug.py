import sys
import os
sys.path.append('platform/backend')

from app.database import SessionLocal
from app.models import Book, BookChapter
from app.services.chapter_analysis_service import ChapterAnalysisService
import json

def check_analysis():
    db = SessionLocal()
    try:
        # 获取西游记书籍的章节
        chapters = db.query(BookChapter).filter(BookChapter.book_id == 9).order_by(BookChapter.chapter_number).all()
        
        print(f"=== 西游记共有 {len(chapters)} 个章节 ===")
        
        service = ChapterAnalysisService(db)
        
        for chapter in chapters[:2]:  # 只检查前两章
            print(f"\n第{chapter.chapter_number}章: {chapter.chapter_title}")
            print(f"章节ID: {chapter.id}")
            
            # 获取分析结果
            analysis = service.get_existing_analysis(chapter.id)
            if analysis:
                characters = analysis.get('detected_characters', [])
                segments = analysis.get('segments', [])
                
                print(f"识别角色数: {len(characters)}")
                print("角色列表:")
                for char in characters:
                    print(f"  - {char.get('name', '未知')} (频次: {char.get('frequency', 0)})")
                
                print(f"分段数: {len(segments)}")
                print("前5个分段:")
                for i, seg in enumerate(segments[:5]):
                    speaker = seg.get('speaker', '未知')
                    text = seg.get('text', '')[:30] + '...' if len(seg.get('text', '')) > 30 else seg.get('text', '')
                    print(f"  {i+1}. [{speaker}]: {text}")
            else:
                print("  ❌ 未找到分析结果")
                
    except Exception as e:
        print(f"错误: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_analysis() 