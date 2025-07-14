#!/usr/bin/env python3
"""
检查项目61章节数据一致性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import NovelProject, BookChapter, AudioFile, AnalysisResult, Book

def main():
    db = SessionLocal()
    try:
        print("🔍 检查项目61章节数据一致性")
        print("=" * 50)
        
        # 1. 查看项目61的基本信息
        project = db.query(NovelProject).filter(NovelProject.id == 61).first()
        if not project:
            print("❌ 项目61不存在")
            return
            
        print(f"📁 项目61: {project.name}")
        print(f"   书籍ID: {project.book_id}")
        print(f"   状态: {project.status}")
        
        # 2. 查看书籍信息
        if project.book_id:
            book = db.query(Book).filter(Book.id == project.book_id).first()
            if book:
                print(f"\n📖 关联书籍: {book.title}")
                print(f"   作者: {book.author}")
        
        # 3. 查看书籍的章节列表
        chapters = db.query(BookChapter).filter(
            BookChapter.book_id == project.book_id
        ).order_by(BookChapter.chapter_number).all()
        
        print(f"\n📝 书籍章节列表 (共{len(chapters)}章):")
        for i, ch in enumerate(chapters):
            status_info = f"分析:{ch.analysis_status}, 合成:{ch.synthesis_status}"
            print(f"   第{ch.chapter_number}章 (ID={ch.id}): {ch.chapter_title[:40]}... [{status_info}]")
        
        # 4. 查看项目61的音频文件章节分布
        audio_files = db.query(AudioFile).filter(
            AudioFile.project_id == 61,
            AudioFile.audio_type == 'segment'
        ).all()
        
        print(f"\n🎵 项目61音频文件分布 (共{len(audio_files)}个):")
        chapter_stats = {}
        for af in audio_files:
            key = f"chapter_id={af.chapter_id}, chapter_number={af.chapter_number}"
            if key not in chapter_stats:
                chapter_stats[key] = []
            chapter_stats[key].append({
                'id': af.id,
                'filename': af.filename,
                'paragraph_index': af.paragraph_index
            })
        
        for key, files in sorted(chapter_stats.items()):
            print(f"   {key}: {len(files)}个文件")
            for f in files[:3]:  # 显示前3个文件
                print(f"     - ID={f['id']}, 段落={f['paragraph_index']}, 文件={f['filename']}")
            if len(files) > 3:
                print(f"     ... 还有{len(files)-3}个文件")
        
        # 5. 查看智能准备结果
        analysis_results = db.query(AnalysisResult).join(
            BookChapter, AnalysisResult.chapter_id == BookChapter.id
        ).filter(
            BookChapter.book_id == project.book_id,
            AnalysisResult.status == 'completed'
        ).all()
        
        print(f"\n🧠 智能准备结果 (共{len(analysis_results)}个):")
        for result in analysis_results:
            chapter = db.query(BookChapter).filter(BookChapter.id == result.chapter_id).first()
            if chapter:
                print(f"   分析结果ID={result.id} -> 章节ID={result.chapter_id} (第{chapter.chapter_number}章: {chapter.chapter_title[:30]}...)")
                
                # 检查合成计划
                if result.synthesis_plan and 'synthesis_plan' in result.synthesis_plan:
                    segments = result.synthesis_plan['synthesis_plan']
                    print(f"     合成段落数: {len(segments)}")
                    # 检查段落中的章节信息
                    for i, seg in enumerate(segments[:2]):  # 显示前2个段落
                        chapter_info = seg.get('chapter_id', 'N/A')
                        chapter_num = seg.get('chapter_number', 'N/A')
                        print(f"     段落{i+1}: chapter_id={chapter_info}, chapter_number={chapter_num}")
        
        # 6. 检查数据不一致问题
        print(f"\n⚠️ 数据一致性检查:")
        
        # 检查音频文件是否指向正确的章节
        for af in audio_files:
            # 查找对应的章节
            if af.chapter_id:
                chapter = db.query(BookChapter).filter(BookChapter.id == af.chapter_id).first()
                if chapter:
                    if chapter.book_id != project.book_id:
                        print(f"   ❌ 音频文件 {af.id} 的章节 {af.chapter_id} 不属于项目书籍")
                else:
                    print(f"   ❌ 音频文件 {af.id} 指向不存在的章节 {af.chapter_id}")
        
        # 找出前端可能请求的章节ID
        if chapters:
            first_chapter = chapters[0]
            print(f"\n💡 推测问题:")
            print(f"   前端可能请求第1章的ID: {first_chapter.id}")
            print(f"   但音频文件存储在章节ID: {list(chapter_stats.keys())}")
            
            # 检查是否有章节111
            chapter_111_exists = any(ch.id == 111 for ch in chapters)
            chapter_113_exists = any(ch.id == 113 for ch in chapters)
            print(f"   章节111是否存在: {chapter_111_exists}")
            print(f"   章节113是否存在: {chapter_113_exists}")
            
            if not chapter_111_exists and chapter_113_exists:
                print("   🎯 可能原因: 前端显示的章节ID与实际章节ID不匹配")
        
    except Exception as e:
        print(f"❌ 检查过程中发生错误: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        db.close()

if __name__ == "__main__":
    main() 