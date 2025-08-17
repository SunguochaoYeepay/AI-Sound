#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models.book_chapter import BookChapter

def query_chapter():
    """查询第一章的真实内容"""
    
    print("🔍 查询第一章真实内容")
    print("=" * 50)
    
    try:
        db = next(get_db())
        
        # 查询章节836
        chapter = db.query(BookChapter).filter(BookChapter.id == 836).first()
        
        if chapter:
            print(f"📖 章节ID: {chapter.id}")
            print(f"📖 章节标题: {chapter.title}")
            print(f"📖 章节编号: {chapter.chapter_number}")
            print(f"📖 书籍ID: {chapter.book_id}")
            print()
            print("📝 章节内容:")
            print("-" * 30)
            print(chapter.content)
            print("-" * 30)
            
            # 按句号分割，看看有多少个段落
            sentences = [s.strip() for s in chapter.content.split('。') if s.strip()]
            print(f"\n📊 按句号分割后的段落数: {len(sentences)}")
            for i, sentence in enumerate(sentences, 1):
                print(f"段落{i}: {sentence}。")
                
        else:
            print("❌ 未找到章节836")
            
    except Exception as e:
        print(f"❌ 查询失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    query_chapter()
