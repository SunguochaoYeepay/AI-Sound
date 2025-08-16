#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models import NovelProject, Book

def list_projects():
    """列出所有项目"""
    db = next(get_db())
    
    try:
        # 查询所有项目
        projects = db.query(NovelProject).order_by(NovelProject.id).all()
        print(f"📋 总共有 {len(projects)} 个项目:")
        print("=" * 60)
        
        for project in projects:
            book_title = "无关联书籍"
            if project.book_id:
                book = db.query(Book).filter(Book.id == project.book_id).first()
                if book:
                    book_title = book.title
            
            print(f"项目ID: {project.id}")
            print(f"  名称: {project.name}")
            print(f"  书籍: {book_title} (ID: {project.book_id})")
            print(f"  状态: {project.status}")
            print(f"  创建时间: {project.created_at}")
            print("-" * 40)
        
        # 查询所有书籍
        books = db.query(Book).order_by(Book.id).all()
        print(f"\n📚 总共有 {len(books)} 本书:")
        print("=" * 60)
        
        for book in books:
            print(f"书籍ID: {book.id}")
            print(f"  标题: {book.title}")
            print(f"  作者: {book.author}")
            print(f"  章节数: {book.chapter_count}")
            print(f"  字数: {book.word_count}")
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ 查询失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_projects()
