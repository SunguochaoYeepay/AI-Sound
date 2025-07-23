#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试书籍ID为12的章节检测问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import get_db
from app.models.book import Book
from app.models.book_chapter import BookChapter
from app.api.v1.books import detect_chapters_from_content

def main():
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 获取书籍信息
        book = db.query(Book).filter(Book.id == 12).first()
        if not book:
            print("❌ 未找到书籍ID为12的记录")
            return
        
        print(f"📚 书籍信息:")
        print(f"   标题: {book.title}")
        print(f"   作者: {book.author}")
        print(f"   字数: {book.word_count}")
        print(f"   章节数: {book.chapter_count}")
        print(f"   状态: {book.status}")
        print()
        
        # 预览书籍内容
        if book.content:
            content_preview = book.content[:500] + "..." if len(book.content) > 500 else book.content
            print(f"📖 书籍内容预览 (前500字符):")
            print(content_preview)
            print()
            
            # 显示内容中的换行符和特殊字符
            lines = book.content.split('\n')[:20]  # 前20行
            print(f"📝 内容结构分析 (前20行):")
            for i, line in enumerate(lines, 1):
                line_preview = line[:100] + "..." if len(line) > 100 else line
                print(f"   第{i:2d}行: {repr(line_preview)}")
            print()
            
            # 测试章节检测
            print(f"🔍 测试章节检测:")
            chapters_data = detect_chapters_from_content(book.content)
            print(f"   检测到 {len(chapters_data)} 个章节:")
            
            for i, chapter in enumerate(chapters_data, 1):
                content_preview = chapter['content'][:100] + "..." if len(chapter['content']) > 100 else chapter['content']
                print(f"   章节 {i}: {chapter['title']}")
                print(f"      字数: {chapter['word_count']}")
                print(f"      内容预览: {content_preview}")
                print()
        else:
            print("❌ 书籍内容为空")
        
        # 查询数据库中已有的章节
        existing_chapters = db.query(BookChapter).filter(BookChapter.book_id == 12).all()
        print(f"💾 数据库中已有 {len(existing_chapters)} 个章节:")
        for chapter in existing_chapters:
            print(f"   章节 {chapter.chapter_number}: {chapter.chapter_title}")
            print(f"      字数: {chapter.word_count}")
            print(f"      分析状态: {chapter.analysis_status}")
            print(f"      合成状态: {chapter.synthesis_status}")
            print()
        
        # 比较结果
        print(f"🔄 比较结果:")
        print(f"   检测到的章节数: {len(chapters_data) if book.content else 0}")
        print(f"   数据库中的章节数: {len(existing_chapters)}")
        print(f"   书籍记录的章节数: {book.chapter_count}")
        
        if book.content and len(chapters_data) != len(existing_chapters):
            print("⚠️  检测结果与数据库不一致！")
        else:
            print("✅ 检测结果与数据库一致")
            
    except Exception as e:
        print(f"❌ 调试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()