#!/usr/bin/env python3
"""
调试Project 61章节进度数据
"""
import sys
sys.path.append('.')

from app.database import get_db
from app.models import NovelProject, AudioFile, AnalysisResult, BookChapter

def debug_project_61():
    db = next(get_db())
    try:
        print("=" * 60)
        print("🔍 调试Project 61章节进度数据")
        print("=" * 60)
        
        # 1. 获取Project 61基本信息
        project = db.query(NovelProject).filter(NovelProject.id == 61).first()
        if not project:
            print("❌ 未找到Project 61")
            return
            
        print(f"📋 项目信息:")
        print(f"   ID: {project.id}")
        print(f"   名称: {project.name}")
        print(f"   书籍ID: {project.book_id}")
        print(f"   状态: {project.status}")
        
        # 2. 获取书籍的章节列表
        if project.book_id:
            chapters = db.query(BookChapter).filter(
                BookChapter.book_id == project.book_id
            ).order_by(BookChapter.chapter_number).all()
            
            print(f"\n📚 书籍章节列表:")
            for chapter in chapters:
                print(f"   章节ID: {chapter.id}, 章节号: {chapter.chapter_number}, 标题: {chapter.chapter_title}")
        
        # 3. 获取每个章节的智能准备结果
        print(f"\n🧠 智能准备结果:")
        for chapter in chapters:
            analysis_result = db.query(AnalysisResult).filter(
                AnalysisResult.chapter_id == chapter.id,
                AnalysisResult.status == 'completed',
                AnalysisResult.synthesis_plan.isnot(None)
            ).first()
            
            if analysis_result:
                segments_count = 0
                if analysis_result.synthesis_plan and 'synthesis_plan' in analysis_result.synthesis_plan:
                    segments = analysis_result.synthesis_plan['synthesis_plan']
                    segments_count = len(segments)
                    
                print(f"   章节{chapter.chapter_number} (ID:{chapter.id}): {segments_count} 个段落")
                
                # 查询该章节的AudioFile数量
                audio_files = db.query(AudioFile).filter(
                    AudioFile.project_id == 61,
                    AudioFile.audio_type == 'segment',
                    AudioFile.chapter_id == chapter.id
                ).all()
                
                # 去重统计
                completed_segment_ids = list(set([af.paragraph_index for af in audio_files if af.paragraph_index is not None]))
                audio_count = len(completed_segment_ids)
                
                progress = round((audio_count / segments_count) * 100, 1) if segments_count > 0 else 0
                
                print(f"   章节{chapter.chapter_number} AudioFile: {audio_count} 个段落已完成 ({progress}%)")
                
                if audio_files:
                    print(f"   章节{chapter.chapter_number} 段落ID: {sorted(completed_segment_ids)}")
            else:
                print(f"   章节{chapter.chapter_number} (ID:{chapter.id}): 无智能准备结果")
        
        # 4. 检查总的项目AudioFile数据
        print(f"\n💾 项目总AudioFile数据:")
        all_audio_files = db.query(AudioFile).filter(
            AudioFile.project_id == 61,
            AudioFile.audio_type == 'segment'
        ).all()
        
        print(f"   总AudioFile数量: {len(all_audio_files)}")
        
        # 按章节分组
        by_chapter = {}
        no_chapter = []
        for af in all_audio_files:
            if af.chapter_id:
                if af.chapter_id not in by_chapter:
                    by_chapter[af.chapter_id] = []
                by_chapter[af.chapter_id].append(af)
            else:
                no_chapter.append(af)
        
        for chapter_id, files in by_chapter.items():
            chapter = next((c for c in chapters if c.id == chapter_id), None)
            chapter_name = f"第{chapter.chapter_number}章" if chapter else f"未知章节{chapter_id}"
            segment_ids = [af.paragraph_index for af in files if af.paragraph_index is not None]
            print(f"   {chapter_name} (ID:{chapter_id}): {len(files)} 个文件, 段落ID: {sorted(set(segment_ids))}")
        
        if no_chapter:
            segment_ids = [af.paragraph_index for af in no_chapter if af.paragraph_index is not None]
            print(f"   无章节关联: {len(no_chapter)} 个文件, 段落ID: {sorted(set(segment_ids))}")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_project_61() 