#!/usr/bin/env python3
"""
清除章节的旧分析结果
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models import AnalysisResult, BookChapter

def clear_analysis_result(chapter_id):
    """清除章节的分析结果"""
    db = next(get_db())
    
    try:
        # 删除分析结果
        deleted_count = db.query(AnalysisResult).filter(
            AnalysisResult.chapter_id == chapter_id
        ).delete()
        
        # 重置章节状态
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if chapter:
            chapter.analysis_status = 'pending'
            chapter.synthesis_status = 'pending'
            
        db.commit()
        
        print(f"✅ 章节{chapter_id}的分析结果已清除")
        print(f"   - 删除了{deleted_count}个分析结果记录")
        print(f"   - 章节状态已重置为pending")
        
    except Exception as e:
        print(f"❌ 清除失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    chapter_id = 110
    clear_analysis_result(chapter_id) 