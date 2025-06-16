#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'platform', 'backend'))

from app.database import get_db
from app.models import TextSegment

def check_failed_segments():
    print("=== 检查失败的段落详情 ===")
    
    db = next(get_db())
    
    # 查询项目22中失败的段落
    failed_segments = db.query(TextSegment).filter(
        TextSegment.project_id == 22,
        TextSegment.status == 'failed'
    ).order_by(TextSegment.paragraph_index).all()
    
    if not failed_segments:
        print("✅ 没有失败的段落")
        return
    
    print(f"❌ 发现 {len(failed_segments)} 个失败的段落:")
    
    for i, segment in enumerate(failed_segments, 1):
        print(f"\n📋 失败段落 {i}:")
        print(f"   ID: {segment.id}")
        print(f"   段落索引: {segment.paragraph_index}")
        print(f"   说话人: {segment.speaker}")
        print(f"   声音ID: {segment.voice_id}")
        print(f"   状态: {segment.status}")
        print(f"   错误信息: {segment.error_message}")
        print(f"   处理时间: {segment.processing_time}")
        print(f"   创建时间: {segment.created_at}")
        print(f"   更新时间: {segment.updated_at}")
        print(f"   内容预览: {segment.content[:100]}...")
        
        # 检查音频文件路径
        if hasattr(segment, 'audio_file_path') and segment.audio_file_path:
            print(f"   音频文件: {segment.audio_file_path}")
        else:
            print(f"   音频文件: 无")

if __name__ == "__main__":
    check_failed_segments() 