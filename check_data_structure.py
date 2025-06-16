import sys
sys.path.append('platform/backend')

from app.database import SessionLocal
from app.models import Book, NovelProject, BookChapter

def check_data():
    db = SessionLocal()
    try:
        books = db.query(Book).all()
        projects = db.query(NovelProject).all()
        chapters = db.query(BookChapter).filter(BookChapter.book_id == 9).all()
        
        print(f'📚 书籍数量: {len(books)}')
        for book in books:
            print(f'  ID{book.id}: {book.title}')
        
        print(f'\n📋 项目数量: {len(projects)}')
        for project in projects:
            print(f'  ID{project.id}: {project.title}')
        
        print(f'\n📖 西游记章节数量: {len(chapters)}')
        for chapter in chapters:
            print(f'  第{chapter.chapter_number}章: {chapter.chapter_title}')
        
        # 检查智能分析如何工作
        print('\n=== 智能分析逻辑 ===')
        print('🤔 问题：智能分析需要项目ID，但西游记只是书籍，没有项目！')
        print('💡 解决：')
        print('   1. 为西游记创建项目')
        print('   2. 或者修改智能分析直接基于书籍ID')
        
    except Exception as e:
        print(f'错误: {e}')
    finally:
        db.close()

if __name__ == "__main__":
    check_data() 