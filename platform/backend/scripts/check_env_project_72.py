#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models.environment_generation import EnvironmentProject
from app.models import Book, BookChapter

def check_env_project_72():
    """检查环境音分析项目72"""
    db = next(get_db())
    
    try:
        # 查询环境音项目72
        env_project = db.query(EnvironmentProject).filter(EnvironmentProject.id == 72).first()
        if env_project:
            print(f"✅ 环境音项目72存在")
            print(f"   项目名称: {env_project.name}")
            print(f"   关联书籍ID: {env_project.book_id}")
            print(f"   书籍名称: {env_project.book_name}")
            print(f"   章节名称: {env_project.chapter_name}")
            print(f"   状态: {env_project.status}")
            print(f"   创建时间: {env_project.created_at}")
            print(f"   分析结果: {'有数据' if env_project.analysis_result else '无数据'}")
            print(f"   匹配结果: {'有数据' if env_project.matching_result else '无数据'}")
        else:
            print("❌ 环境音项目72不存在")
            return
        
        # 查询关联的书籍
        if env_project.book_id:
            book = db.query(Book).filter(Book.id == env_project.book_id).first()
            if book:
                print(f"\n📚 关联书籍信息:")
                print(f"   书籍ID: {book.id}")
                print(f"   标题: {book.title}")
                print(f"   作者: {book.author}")
                print(f"   章节数: {book.chapter_count}")
                print(f"   字数: {book.word_count}")
                
                # 查询书籍的章节
                chapters = db.query(BookChapter).filter(BookChapter.book_id == book.id).order_by(BookChapter.chapter_number).all()
                print(f"\n📖 书籍章节列表:")
                for chapter in chapters:
                    print(f"   第{chapter.chapter_number}章: {chapter.chapter_title}")
                    print(f"     字数: {chapter.word_count}")
                    print(f"     内容预览: {chapter.content[:100]}..." if chapter.content else "     无内容")
                    print()
            else:
                print("❌ 关联的书籍不存在")
        
        # 查看分析结果
        if env_project.analysis_result:
            print(f"\n🔍 分析结果预览:")
            print(f"   结果类型: {type(env_project.analysis_result)}")
            if isinstance(env_project.analysis_result, dict):
                print(f"   键数量: {len(env_project.analysis_result)}")
                for key, value in env_project.analysis_result.items():
                    if isinstance(value, dict):
                        print(f"   {key}: {len(value)} 个轨道")
                    else:
                        print(f"   {key}: {value}")
            
    except Exception as e:
        print(f"❌ 查询失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_env_project_72()
