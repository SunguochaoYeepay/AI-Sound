#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'platform', 'backend'))

from app.database import get_db
from app.models import TextSegment, NovelProject

def retry_failed_segments():
    print("=== 重试失败的段落 ===")
    
    db = next(get_db())
    
    # 查询项目22中失败的段落
    failed_segments = db.query(TextSegment).filter(
        TextSegment.project_id == 22,
        TextSegment.status == 'failed'
    ).all()
    
    if not failed_segments:
        print("✅ 没有失败的段落需要重试")
        return
    
    print(f"🔄 找到 {len(failed_segments)} 个失败的段落，准备重试")
    
    # 重置失败段落的状态
    for segment in failed_segments:
        print(f"   重置段落 {segment.id}: {segment.speaker}")
        segment.status = 'pending'
        segment.error_message = None
        segment.processing_time = None
    
    # 更新项目状态
    project = db.query(NovelProject).filter(NovelProject.id == 22).first()
    if project:
        print(f"🔄 重置项目状态: {project.status} -> processing")
        project.status = 'processing'
        # 重新计算已处理段落数
        completed_count = db.query(TextSegment).filter(
            TextSegment.project_id == 22,
            TextSegment.status == 'completed'
        ).count()
        project.processed_segments = completed_count
    
    # 提交更改
    try:
        db.commit()
        print(f"✅ 成功重置 {len(failed_segments)} 个失败段落的状态")
        print(f"✅ 项目状态已重置为 processing")
        print(f"📝 现在可以重新启动合成任务")
    except Exception as e:
        db.rollback()
        print(f"❌ 重置失败: {e}")

if __name__ == "__main__":
    retry_failed_segments() 