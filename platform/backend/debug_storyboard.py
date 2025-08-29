#!/usr/bin/env python3
"""
直接调试故事板方法
"""

from app.database import get_db
from app.services.storyboard_analysis_service import StoryboardAnalysisService
from app.models import Book, BookChapter

def debug_storyboard():
    """调试故事板方法"""
    db = next(get_db())
    
    try:
        print("开始调试故事板方法...")
        
        # 获取会话
        service = StoryboardAnalysisService(db)
        session = service.get_session(6)  # 使用会话ID 6
        if not session:
            print("❌ 会话不存在")
            return
        
        print(f"✅ 会话找到，书籍ID: {session.book_id}")
        
        # 获取书籍
        book = db.query(Book).filter(Book.id == session.book_id).first()
        if not book:
            print("❌ 书籍不存在")
            return
        
        print(f"✅ 书籍找到: {book.title}")
        print(f"✅ 章节数: {len(book.chapters)}")
        
        # 检查每个章节
        for i, chapter in enumerate(book.chapters):
            print(f"\n章节 {i+1}:")
            print(f"  ID: {chapter.id}")
            print(f"  标题: {chapter.chapter_title}")
            print(f"  章节号: {chapter.chapter_number}")
            print(f"  内容长度: {len(chapter.content) if chapter.content else 0}")
            
            # 检查chapter_title属性
            print(f"  chapter_title属性: {chapter.chapter_title}")
            
            # 尝试获取卡片
            try:
                cards = service.get_session_cards(
                    session_id=session.id,
                    chapter_id=chapter.id
                )
                print(f"  卡片数: {len(cards)}")
            except Exception as e:
                print(f"  ❌ 获取卡片失败: {str(e)}")
        
        print("\n调试完成！")
        
    except Exception as e:
        print(f"❌ 调试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_storyboard()
