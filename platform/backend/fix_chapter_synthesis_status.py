#!/usr/bin/env python3
"""
修复章节合成状态脚本
为现有项目更新章节的synthesis_status字段
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import get_db
from app.models import NovelProject, BookChapter, AudioFile
import logging

logger = logging.getLogger(__name__)

def fix_chapter_synthesis_status():
    """修复章节合成状态"""
    print("🔧 开始修复章节合成状态...")
    
    db = next(get_db())
    
    try:
        # 获取所有已完成的项目
        completed_projects = db.query(NovelProject).filter(
            NovelProject.status.in_(['completed', 'partial_completed'])
        ).all()
        
        print(f"📊 找到 {len(completed_projects)} 个已完成的项目")
        
        fixed_chapters = 0
        
        for project in completed_projects:
            print(f"\n🎯 处理项目: {project.name} (ID: {project.id})")
            
            if not project.book_id:
                print(f"  ⚠️  项目未关联书籍，跳过")
                continue
            
            # 获取项目相关的音频文件
            audio_files = db.query(AudioFile).filter(
                AudioFile.project_id == project.id,
                AudioFile.audio_type == 'segment'
            ).all()
            
            print(f"  📁 项目有 {len(audio_files)} 个音频文件")
            
            if not audio_files:
                continue
            
            # 获取书籍的所有章节
            chapters = db.query(BookChapter).filter(
                BookChapter.book_id == project.book_id
            ).all()
            
            print(f"  📖 书籍有 {len(chapters)} 个章节")
            
            # 按章节更新状态
            for chapter in chapters:
                # 方法1：通过chapter_id匹配
                chapter_audio_count_by_id = db.query(AudioFile).filter(
                    AudioFile.project_id == project.id,
                    AudioFile.chapter_id == chapter.id,
                    AudioFile.audio_type == 'segment'
                ).count()
                
                # 方法2：通过chapter_number匹配
                chapter_audio_count_by_number = db.query(AudioFile).filter(
                    AudioFile.project_id == project.id,
                    AudioFile.chapter_number == chapter.chapter_number,
                    AudioFile.audio_type == 'segment'
                ).count()
                
                total_audio_count = max(chapter_audio_count_by_id, chapter_audio_count_by_number)
                
                old_status = chapter.synthesis_status
                
                if total_audio_count > 0:
                    chapter.synthesis_status = 'completed'
                    status_text = f"completed (发现 {total_audio_count} 个音频文件)"
                else:
                    chapter.synthesis_status = 'pending'
                    status_text = "pending (无音频文件)"
                
                if old_status != chapter.synthesis_status:
                    print(f"    📝 章节 {chapter.chapter_number}: {old_status} → {status_text}")
                    fixed_chapters += 1
        
        # 提交更改
        db.commit()
        print(f"\n✅ 修复完成！共更新了 {fixed_chapters} 个章节的状态")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 修复失败: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    fix_chapter_synthesis_status() 