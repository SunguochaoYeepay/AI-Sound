#!/usr/bin/env python3
"""
测试角色配音库数据
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models.character import Character
from app.models.book import Book
from app.models.book_chapter import BookChapter

def test_character_library():
    """测试角色配音库数据"""
    db = next(get_db())
    
    print("=== 角色配音库数据检查 ===")
    
    # 1. 查看所有角色
    all_characters = db.query(Character).all()
    print(f"\n📚 总共有 {len(all_characters)} 个角色配音库角色:")
    for char in all_characters:
        print(f"  - ID: {char.id}, 名称: {char.name}, 书籍ID: {char.book_id}, 语音类型: {char.voice_type}, 状态: {char.status}")
        print(f"    是否配置语音: {char.is_voice_configured}, 参考音频: {char.reference_audio_path}")
    
    # 2. 查看书籍12的角色
    book_id = 12
    book_characters = db.query(Character).filter(Character.book_id == book_id).all()
    print(f"\n📖 书籍{book_id}的角色配音库角色 ({len(book_characters)}个):")
    for char in book_characters:
        print(f"  - {char.name} (ID: {char.id}, 类型: {char.voice_type}, 状态: {char.status})")
        print(f"    是否配置语音: {char.is_voice_configured}")
    
    # 3. 查看书籍信息
    book = db.query(Book).filter(Book.id == book_id).first()
    if book:
        print(f"\n📚 书籍信息:")
        print(f"  - 书名: {book.title}")
        print(f"  - 作者: {book.author}")
        
        # 查看书籍的角色汇总
        character_summary = book.get_character_summary()
        if character_summary:
            print(f"  - 角色汇总: {len(character_summary.get('characters', []))} 个角色")
            for char in character_summary.get('characters', []):
                print(f"    * {char.get('name', 'unknown')} (出现次数: {char.get('appearances', 0)})")
    
    # 4. 检查章节110
    chapter_id = 110
    chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
    if chapter:
        print(f"\n📄 章节{chapter_id}信息:")
        print(f"  - 章节标题: {chapter.chapter_title}")
        print(f"  - 所属书籍: {chapter.book_id}")
        print(f"  - 分析状态: {chapter.analysis_status}")
        print(f"  - 合成状态: {chapter.synthesis_status}")
        
        # 查看章节的角色
        chapter_characters = db.query(Character).filter(Character.book_id == chapter.book_id).all()
        print(f"  - 该章节书籍的角色配音库角色: {[char.name for char in chapter_characters]}")
    
    # 5. 特别检查小明和小红
    xiaoming = db.query(Character).filter(Character.name == "小明").all()
    xiaohong = db.query(Character).filter(Character.name == "小红").all()
    
    print(f"\n🔍 特别检查:")
    print(f"  - 小明角色: {len(xiaoming)} 个")
    for char in xiaoming:
        print(f"    * ID: {char.id}, 书籍ID: {char.book_id}, 配置状态: {char.is_voice_configured}")
    
    print(f"  - 小红角色: {len(xiaohong)} 个")
    for char in xiaohong:
        print(f"    * ID: {char.id}, 书籍ID: {char.book_id}, 配置状态: {char.is_voice_configured}")
    
    db.close()

if __name__ == "__main__":
    test_character_library() 