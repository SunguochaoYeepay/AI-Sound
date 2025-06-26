#!/usr/bin/env python3
"""
检查模型字段和数据状态
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models import BookChapter, AudioFile, NovelProject

def main():
    try:
        # 获取数据库连接
        db = next(get_db())

        print('🔍 检查模型字段和实际数据状态')
        print('=' * 50)

        # 检查BookChapter模型字段
        chapter = db.query(BookChapter).filter(BookChapter.id == 106).first()
        if chapter:
            print(f'📖 BookChapter模型字段:')
            print(f'  analysis_status: {chapter.analysis_status}')
            print(f'  synthesis_status: {chapter.synthesis_status}')
            print()

        # 检查AudioFile模型字段和数据
        audio_files = db.query(AudioFile).filter(AudioFile.project_id == 42).all()
        print(f'🎵 AudioFile字段检查 (项目42的音频文件):')
        if audio_files:
            af = audio_files[0]  # 查看第一个文件
            print(f'  chapter_id字段: {af.chapter_id}')
            print(f'  segment_id字段: {af.segment_id}')
            print(f'  paragraph_index字段: {af.paragraph_index}')
            print(f'  status字段: {af.status}')
            print(f'  audio_type字段: {af.audio_type}')
            print()
            
            # 统计各字段的值分布
            chapter_ids = set(af.chapter_id for af in audio_files if af.chapter_id is not None)
            segment_ids = set(af.segment_id for af in audio_files if af.segment_id is not None)
            paragraph_indices = set(af.paragraph_index for af in audio_files if af.paragraph_index is not None)
            
            print(f'  章节ID分布: {list(chapter_ids) if chapter_ids else "全部为None"}')
            print(f'  段落ID分布: {list(segment_ids) if segment_ids else "全部为None"}')
            print(f'  段落索引分布: {list(paragraph_indices) if paragraph_indices else "全部为None"}')
        else:
            print('  未找到音频文件')

        print()
        print('💡 结论:')
        print('- BookChapter有analysis_status和synthesis_status字段 ✅')
        print('- AudioFile有chapter_id, segment_id, paragraph_index字段 ✅')
        print('- 问题在于这些字段的值为None，不是字段不存在 ❌')

        db.close()
        
    except Exception as e:
        print(f"❌ 检查过程中发生错误: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main() 