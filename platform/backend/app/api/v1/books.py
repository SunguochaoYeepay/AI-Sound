"""
书籍管理API
提供书籍上传、章节检测、结构化处理等功能
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
import logging

from app.database import get_db
from app.services import ChapterService
from app.models import Book, BookChapter
from app.schemas import BookResponse, BookCreate, ChapterResponse
from app.utils.exceptions import BookNotFoundError, ChapterProcessingError

router = APIRouter(prefix="/books")

logger = logging.getLogger(__name__)


@router.post("/", response_model=BookResponse)
async def upload_book(
    file: UploadFile = File(...),
    title: str = Form(...),
    author: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    auto_detect_chapters: bool = Form(True),
    db: Session = Depends(get_db)
):
    """
    上传书籍文件并进行初步处理
    - 支持txt、docx等格式
    - 可选择自动检测章节
    """
    chapter_service = ChapterService(db)
    
    try:
        # 保存文件并创建书籍记录
        book = await chapter_service.create_book_from_upload(
            file=file,
            title=title,
            author=author,
            description=description
        )
        
        # 如果启用自动章节检测
        if auto_detect_chapters:
            # 异步处理章节检测
            asyncio.create_task(
                chapter_service.async_detect_chapters(book.id)
            )
        
        return book.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"书籍上传失败: {str(e)}")


@router.get("/", response_model=List[BookResponse])
def get_books(
    skip: int = 0,
    limit: int = 20,
    title_search: Optional[str] = None,
    author_search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取书籍列表
    - 支持分页查询
    - 支持标题和作者搜索
    """
    try:
        query = db.query(Book)
        
        if title_search:
            query = query.filter(Book.title.ilike(f"%{title_search}%"))
        
        if author_search:
            query = query.filter(Book.author.ilike(f"%{author_search}%"))
        
        books = query.offset(skip).limit(limit).all()
        return [book.to_dict() for book in books]
    except Exception as e:
        # 暂时返回空列表，避免500错误
        logger.error(f"获取书籍列表失败: {e}")
        return []


@router.get("/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    """获取书籍详情"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    return book.to_dict()


@router.post("/{book_id}/detect-chapters")
async def detect_chapters(
    book_id: int,
    force_reprocess: bool = False,
    detection_config: Optional[dict] = None,
    db: Session = Depends(get_db)
):
    """
    检测书籍章节结构
    - 支持强制重新处理
    - 支持自定义检测配置
    """
    chapter_service = ChapterService(db)
    
    try:
        # 检查书籍是否存在
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise BookNotFoundError(f"书籍 ID {book_id} 不存在")
        
        # 检查是否需要重新处理
        if not force_reprocess and book.is_structure_completed():
            return {
                "message": "章节结构已存在，使用 force_reprocess=true 强制重新处理",
                "current_chapters": book.total_chapters
            }
        
        # 异步执行章节检测
        task_id = await chapter_service.async_detect_chapters(
            book_id=book_id,
            config=detection_config or {}
        )
        
        return {
            "message": "章节检测已启动",
            "task_id": task_id,
            "book_id": book_id
        }
        
    except BookNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ChapterProcessingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"章节检测失败: {str(e)}")


@router.get("/{book_id}/chapters", response_model=List[ChapterResponse])
def get_book_chapters(
    book_id: int,
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取书籍章节列表
    - 支持分页查询
    - 支持状态筛选
    """
    # 检查书籍是否存在
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    query = db.query(BookChapter).filter(BookChapter.book_id == book_id)
    
    if status_filter:
        query = query.filter(BookChapter.analysis_status == status_filter)
    
    chapters = query.order_by(BookChapter.chapter_number).offset(skip).limit(limit).all()
    return [chapter.to_dict() for chapter in chapters]


@router.get("/{book_id}/structure-status")
def get_structure_status(book_id: int, db: Session = Depends(get_db)):
    """
    获取书籍结构化处理状态
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    # 统计章节状态
    chapter_stats = db.query(BookChapter.analysis_status, 
                           db.func.count(BookChapter.id).label('count')) \
                     .filter(BookChapter.book_id == book_id) \
                     .group_by(BookChapter.analysis_status) \
                     .all()
    
    status_counts = {stat.analysis_status: stat.count for stat in chapter_stats}
    
    return {
        "book_id": book_id,
        "structure_detected": book.structure_detected,
        "total_chapters": book.total_chapters,
        "total_words": book.total_words,
        "chapter_status_counts": status_counts,
        "detection_config": book.chapter_detection_config
    }


@router.delete("/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    """删除书籍及其所有相关数据"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    # 删除书籍（级联删除章节）
    db.delete(book)
    db.commit()
    
    return {"message": f"书籍 '{book.title}' 已删除"}


@router.patch("/{book_id}")
def update_book(
    book_id: int,
    title: Optional[str] = None,
    author: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """更新书籍信息"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    if title is not None:
        book.title = title
    if author is not None:
        book.author = author
    if description is not None:
        book.description = description
    
    db.commit()
    db.refresh(book)
    
    return book.to_dict() 