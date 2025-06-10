"""
书籍管理API
提供书籍上传、章节检测、结构化处理等功能
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, or_, and_
from typing import List, Optional
import asyncio
import logging
import json

from app.database import get_db
from app.models import Book, BookChapter

router = APIRouter(prefix="/books")

logger = logging.getLogger(__name__)


@router.post("")
async def upload_book(
    title: str = Form(...),
    author: Optional[str] = Form(""),
    description: Optional[str] = Form(""),
    content: Optional[str] = Form(""),
    tags: Optional[str] = Form("[]"),
    text_file: Optional[UploadFile] = File(None),
    auto_detect_chapters: bool = Form(True),
    db: Session = Depends(get_db)
):
    """
    创建书籍记录
    - 支持直接文本内容或文件上传
    - 支持txt、docx等格式文件
    - 可选择自动检测章节
    """
    try:
        # 解析标签
        try:
            import json
            parsed_tags = json.loads(tags) if tags else []
        except json.JSONDecodeError:
            parsed_tags = []
        
        # 获取书籍内容
        book_content = ""
        if text_file and text_file.filename:
            # 从文件读取内容
            file_content = await text_file.read()
            try:
                book_content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    book_content = file_content.decode('gbk')
                except UnicodeDecodeError:
                    raise HTTPException(status_code=400, detail="文件编码格式不支持，请使用UTF-8或GBK编码")
        elif content:
            # 使用直接传入的文本内容
            book_content = content
        else:
            raise HTTPException(status_code=400, detail="必须提供文本内容或上传文件")
        
        # 创建书籍记录
        new_book = Book(
            title=title,
            author=author or "",
            description=description or "",
            content=book_content,
            tags=json.dumps(parsed_tags, ensure_ascii=False),
            status='draft',
            word_count=len(book_content),
            chapter_count=0
        )
        
        db.add(new_book)
        db.commit()
        db.refresh(new_book)
        
        # 如果启用自动章节检测且内容不为空
        if auto_detect_chapters and book_content.strip():
            # 这里可以添加章节检测逻辑
            pass
        
        return {
            "success": True,
            "data": new_book.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建书籍失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建书籍失败: {str(e)}")


@router.get("")
async def get_books(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query("", description="搜索关键词"),
    author: str = Query("", description="作者过滤"),
    status: str = Query("", description="状态过滤"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    db: Session = Depends(get_db)
):
    """
    获取书籍列表
    - 支持分页查询
    - 支持标题和作者搜索
    """
    try:
        # 构建查询
        query = db.query(Book)
        
        # 搜索过滤
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Book.title.like(search_pattern),
                    Book.author.like(search_pattern),
                    Book.description.like(search_pattern)
                )
            )
        
        # 作者过滤
        if author:
            query = query.filter(Book.author.like(f"%{author}%"))
        
        # 状态过滤
        if status:
            query = query.filter(Book.status == status)
        
        # 排序
        sort_field = getattr(Book, sort_by, Book.created_at)
        if sort_order == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))
        
        # 统计总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        books = query.offset(offset).limit(page_size).all()
        
        # 转换为字典格式
        book_list = [book.to_dict() for book in books]
        
        # 分页信息
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "success": True,
            "data": book_list,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": total_pages,
                "hasMore": page < total_pages
            },
            "filters": {
                "search": search,
                "author": author,
                "status": status
            }
        }
        
    except Exception as e:
        logger.error(f"获取书籍列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取书籍列表失败: {str(e)}")


@router.get("/{book_id}")
def get_book(book_id: int, db: Session = Depends(get_db)):
    """获取书籍详情"""
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        return {
            "success": True,
            "data": book.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取书籍详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取书籍详情失败: {str(e)}")


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
    try:
        # 检查书籍是否存在
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail=f"书籍 ID {book_id} 不存在")
        
        # 简单的章节检测逻辑（基础实现）
        content = book.content or ""
        chapters = []
        
        # 基础的章节分割（按"第"开头的行）
        lines = content.split('\n')
        current_chapter = {"title": "序章", "content": ""}
        chapter_num = 0
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('第') and ('章' in line or '节' in line)):
                # 保存当前章节
                if current_chapter["content"].strip():
                    chapters.append(current_chapter)
                
                # 开始新章节
                chapter_num += 1
                current_chapter = {"title": line, "content": ""}
            else:
                current_chapter["content"] += line + "\n"
        
        # 保存最后一个章节
        if current_chapter["content"].strip():
            chapters.append(current_chapter)
        
        # 更新书籍信息
        book.chapter_count = len(chapters)
        book.total_chapters = len(chapters)
        db.commit()
        
        return {
            "success": True,
            "message": f"章节检测完成，发现 {len(chapters)} 个章节",
            "chapters_found": len(chapters),
            "book_id": book_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"章节检测失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"章节检测失败: {str(e)}")


@router.get("/{book_id}/chapters")
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
    
    return {
        "success": True,
        "data": [chapter.to_dict() for chapter in chapters]
    }


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