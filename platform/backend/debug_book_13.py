#!/usr/bin/env python3
"""
调试书籍ID为13的章节检测问题
"""
import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models import Book, BookChapter
from app.api.v1.books import detect_chapters_from_content

def debug_book_13():
    """调试书籍13的章节检测问题"""
    db = next(get_db())
    
    print("=== 调试书籍 ID=13 的章节检测问题 ===")
    
    try:
        # 1. 获取书籍信息
        book = db.query(Book).filter(Book.id == 13).first()
        if not book:
            print("❌ 书籍 ID=13 不存在")
            return
        
        print(f"📖 书籍信息:")
        print(f"   ID: {book.id}")
        print(f"   标题: {book.title}")
        print(f"   作者: {book.author}")
        print(f"   状态: {book.status}")
        print(f"   章节数: {book.chapter_count}")
        print(f"   字数: {book.word_count}")
        
        # 2. 检查书籍内容
        if not book.content:
            print("❌ 书籍没有内容")
            return
        
        content_preview = book.content[:500] + "..." if len(book.content) > 500 else book.content
        print(f"\n📄 书籍内容预览 (前500字符):")
        print(content_preview)
        
        # 3. 测试章节检测
        print("\n🔍 开始测试章节检测...")
        detected_chapters = detect_chapters_from_content(book.content)
        
        print(f"\n✅ 检测到 {len(detected_chapters)} 个章节:")
        for i, chapter in enumerate(detected_chapters[:5]):  # 只显示前5个章节
            print(f"   章节 {chapter.get('number', i+1)}: {chapter.get('title', '无标题')}")
            print(f"      字数: {chapter.get('word_count', 0)}")
            content_preview = chapter.get('content', '')[:100] + "..." if len(chapter.get('content', '')) > 100 else chapter.get('content', '')
            print(f"      内容预览: {content_preview}")
            print()
        
        if len(detected_chapters) > 5:
            print(f"   ... 还有 {len(detected_chapters) - 5} 个章节")
        
        # 4. 检查数据库中的章节
        existing_chapters = db.query(BookChapter).filter(BookChapter.book_id == 13).all()
        print(f"\n💾 数据库中已有 {len(existing_chapters)} 个章节:")
        for chapter in existing_chapters[:5]:  # 只显示前5个章节
            print(f"   章节 {chapter.chapter_number}: {chapter.chapter_title}")
            print(f"      字数: {chapter.word_count}")
            print(f"      分析状态: {chapter.analysis_status}")
            print(f"      合成状态: {chapter.synthesis_status}")
            print()
        
        if len(existing_chapters) > 5:
            print(f"   ... 还有 {len(existing_chapters) - 5} 个章节")
        
        # 5. 比较检测结果和数据库数据
        print(f"\n🔄 比较结果:")
        print(f"   检测到的章节数: {len(detected_chapters)}")
        print(f"   数据库中的章节数: {len(existing_chapters)}")
        print(f"   书籍记录的章节数: {book.chapter_count}")
        
        if len(detected_chapters) != len(existing_chapters):
            print("⚠️  检测结果与数据库不一致！")
        else:
            print("✅ 检测结果与数据库一致")
        
    except Exception as e:
        print(f"❌ 调试过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_book_13()