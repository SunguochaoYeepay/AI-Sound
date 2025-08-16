#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models import NovelProject, Book, BookChapter

def check_project_72():
    """检查项目72和书籍58的关系"""
    db = next(get_db())
    
    try:
        # 查询项目72
        project = db.query(NovelProject).filter(NovelProject.id == 72).first()
        if project:
            print(f"✅ 项目72存在")
            print(f"   项目名称: {project.name}")
            print(f"   关联书籍ID: {project.book_id}")
            print(f"   创建时间: {project.created_at}")
        else:
            print("❌ 项目72不存在")
            return
        
        # 查询书籍58
        book = db.query(Book).filter(Book.id == 58).first()
        if book:
            print(f"✅ 书籍58存在")
            print(f"   书籍标题: {book.title}")
            print(f"   作者: {book.author}")
            print(f"   章节数: {book.chapter_count}")
            print(f"   字数: {book.word_count}")
        else:
            print("❌ 书籍58不存在")
            return
        
        # 查询书籍58的章节
        chapters = db.query(BookChapter).filter(BookChapter.book_id == 58).order_by(BookChapter.chapter_number).all()
        print(f"📚 书籍58的章节列表:")
        for chapter in chapters:
            print(f"   第{chapter.chapter_number}章: {chapter.chapter_title}")
            print(f"     字数: {chapter.word_count}")
            print(f"     内容预览: {chapter.content[:50]}..." if chapter.content else "     无内容")
        
        # 检查项目72是否真的关联书籍58
        if project.book_id == 58:
            print("✅ 项目72确实关联书籍58")
        else:
            print(f"❌ 项目72关联的书籍ID是{project.book_id}，不是58")
            
    except Exception as e:
        print(f"❌ 查询失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_project_72()
