#!/usr/bin/env python3
"""
测试角色匹配功能
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.services.character_service import CharacterService
from app.models.character import Character
from app.models.book import Book
from app.models.book_chapter import BookChapter

def test_character_matching():
    """测试角色匹配功能"""
    db = next(get_db())
    character_service = CharacterService(db)
    
    try:
        # 创建测试数据
        print("创建测试数据...")
        
        # 模拟匹配功能
        print("测试角色匹配...")
        result = character_service.match_characters_by_chapter(1, 1)
        print(f"匹配结果: {result}")
        
        # 测试同步功能
        print("测试角色同步...")
        sync_result = character_service.sync_characters_with_analysis(1, 1)
        print(f"同步结果: {sync_result}")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_character_matching()