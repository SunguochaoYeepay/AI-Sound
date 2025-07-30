#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中书籍的状态
"""

from app.database import get_db
from app.models import Book

def main():
    db = next(get_db())
    try:
        books = db.query(Book).all()
        print('书籍状态统计:')
        print(f'总共有 {len(books)} 本书籍')
        print()
        
        status_count = {}
        for book in books:
            status = book.status or 'None'
            status_count[status] = status_count.get(status, 0) + 1
            print(f'ID: {book.id}, 标题: {book.title}, 状态: {book.status}')
        
        print()
        print('状态统计:')
        for status, count in status_count.items():
            print(f'  {status}: {count} 本')
            
    except Exception as e:
        print(f'错误: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    main()