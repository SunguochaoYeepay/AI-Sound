"""
书籍内容管理 API
提供书籍的增删改查、内容管理等功能
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import Optional, List, Dict, Any
import os
import json
import uuid
import re
from datetime import datetime

from database import get_db
from models import Book, NovelProject
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/books", tags=["books"])

# 配置目录
BOOKS_DIR = os.path.join(os.getcwd(), "data", "books")
os.makedirs(BOOKS_DIR, exist_ok=True)

@router.get("/")
async def get_books(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query("", description="搜索关键词"),
    status: str = Query("", description="状态过滤"),
    author: str = Query("", description="作者过滤"),
    tags: str = Query("", description="标签过滤"),
    sort_by: str = Query("updated_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    db: Session = Depends(get_db)
):
    """
    获取书籍列表
    支持分页、搜索、筛选和排序
    """
    try:
        # 构建查询
        query = db.query(Book)
        
        # 搜索条件
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Book.title.ilike(search_pattern),
                    Book.author.ilike(search_pattern),
                    Book.description.ilike(search_pattern)
                )
            )
        
        # 状态过滤
        if status:
            query = query.filter(Book.status == status)
        
        # 作者过滤
        if author:
            query = query.filter(Book.author.ilike(f"%{author}%"))
        
        # 标签过滤
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            for tag in tag_list:
                query = query.filter(Book.tags.contains(f'"{tag}"'))
        
        # 排序
        if sort_order == "desc":
            query = query.order_by(desc(getattr(Book, sort_by, Book.updated_at)))
        else:
            query = query.order_by(getattr(Book, sort_by, Book.updated_at))
        
        # 分页
        total = query.count()
        offset = (page - 1) * page_size
        books = query.offset(offset).limit(page_size).all()
        
        # 安全转换为字典
        books_data = []
        for book in books:
            try:
                books_data.append(book.to_dict())
            except Exception as e:
                logger.warning(f"Book ID {book.id} to_dict失败: {str(e)}")
                # 使用简化的数据结构
                books_data.append({
                    "id": book.id,
                    "title": book.title or "未知标题",
                    "author": book.author or "",
                    "description": book.description or "",
                    "wordCount": book.word_count or 0,
                    "chapterCount": book.chapter_count or 0,
                    "status": book.status or "draft",
                    "chapters": [],
                    "tags": [],
                    "createdAt": book.created_at.isoformat() if book.created_at else None,
                    "updatedAt": book.updated_at.isoformat() if book.updated_at else None
                })
        
        return {
            "success": True,
            "data": books_data,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": (total + page_size - 1) // page_size
            },
            "filters": {
                "search": search,
                "status": status,
                "author": author,
                "tags": tags,
                "sortBy": sort_by,
                "sortOrder": sort_order
            }
        }
        
    except Exception as e:
        logger.error(f"获取书籍列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取列表失败: {str(e)}")

@router.post("/")
async def create_book(
    title: str = Form(...),
    author: str = Form(""),
    description: str = Form(""),
    content: str = Form(""),
    text_file: Optional[UploadFile] = File(None),
    tags: str = Form("[]"),
    db: Session = Depends(get_db)
):
    """
    创建新书籍
    支持直接输入内容或上传文件
    """
    try:
        # 验证书籍标题
        if not title or len(title.strip()) == 0:
            raise HTTPException(status_code=400, detail="书籍标题不能为空")
        
        # 检查标题是否已存在
        existing = db.query(Book).filter(Book.title == title).first()
        if existing:
            raise HTTPException(status_code=400, detail="书籍标题已存在")
        
        # 处理内容
        final_content = content
        source_file_path = None
        source_file_name = None
        
        if text_file:
            # 验证文件类型
            if not text_file.filename.lower().endswith(('.txt', '.md')):
                raise HTTPException(status_code=400, detail="只支持 .txt 和 .md 文件")
            
            # 读取文件内容
            file_content = await text_file.read()
            final_content = file_content.decode('utf-8', errors='ignore')
            
            # 保存文件到磁盘
            filename = f"book_{uuid.uuid4().hex}.txt"
            source_file_path = os.path.join(BOOKS_DIR, filename)
            source_file_name = text_file.filename
            
            with open(source_file_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
        
        if not final_content or len(final_content.strip()) == 0:
            raise HTTPException(status_code=400, detail="书籍内容不能为空")
        
        # 解析标签
        try:
            if isinstance(tags, list):
                tags_list = tags
            else:
                tags_list = json.loads(tags) if tags else []
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="标签格式错误")
        
        # 自动检测章节
        chapters = auto_detect_chapters(final_content)
        
        # 创建书籍记录
        book = Book(
            title=title.strip(),
            author=author.strip(),
            description=description.strip(),
            content=final_content,
            source_file_path=source_file_path,
            source_file_name=source_file_name,
            status='draft'
        )
        
        # 设置标签和章节
        book.set_tags(tags_list)
        book.set_chapters(chapters)
        book.update_word_count()
        
        db.add(book)
        db.commit()
        db.refresh(book)
        
        # 记录创建日志
        logger.info(f"书籍创建成功: {title}, ID: {book.id}, 字数: {book.word_count}, 章节: {book.chapter_count}")
        
        # 安全地获取书籍数据
        try:
            book_data = book.to_dict()
        except Exception as e:
            logger.warning(f"to_dict失败，使用简化数据: {str(e)}")
            # 使用简化的数据结构
            book_data = {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "description": book.description,
                "wordCount": book.word_count,
                "chapterCount": book.chapter_count,
                "status": book.status,
                "chapters": [],
                "tags": [],
                "createdAt": book.created_at.isoformat() if book.created_at else None,
                "updatedAt": book.updated_at.isoformat() if book.updated_at else None
            }
        
        return {
            "success": True,
            "message": "书籍创建成功",
            "data": book_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建书籍失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")

@router.get("/{book_id}")
async def get_book_detail(
    book_id: int,
    db: Session = Depends(get_db)
):
    """
    获取书籍详情
    """
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        book_data = book.to_dict()
        
        # 获取关联的合成项目
        projects = db.query(NovelProject).filter(NovelProject.book_id == book_id).all()
        book_data['synthesisProjects'] = [
            {
                "id": p.id,
                "name": p.name,
                "status": p.status,
                "createdAt": p.created_at.isoformat() if p.created_at else None
            } for p in projects
        ]
        
        return {
            "success": True,
            "data": book_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取书籍详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取详情失败: {str(e)}")

@router.put("/{book_id}")
async def update_book(
    book_id: int,
    title: str = Form(...),
    author: str = Form(""),
    description: str = Form(""),
    content: str = Form(""),
    tags: str = Form("[]"),
    status: str = Form("draft"),
    db: Session = Depends(get_db)
):
    """
    更新书籍信息
    """
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        # 检查标题重复（排除自己）
        existing = db.query(Book).filter(
            and_(
                Book.title == title,
                Book.id != book_id
            )
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="书籍标题已存在")
        
        # 验证状态
        if status not in ['draft', 'published', 'archived']:
            raise HTTPException(status_code=400, detail="无效的状态值")
        
        # 解析标签
        try:
            tags_list = json.loads(tags) if tags else []
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="标签格式错误")
        
        # 更新基本信息
        old_title = book.title
        book.title = title.strip()
        book.author = author.strip()
        book.description = description.strip()
        book.status = status
        book.updated_at = datetime.utcnow()
        
        # 如果内容发生变化，重新检测章节
        if content and content != book.content:
            book.content = content
            chapters = auto_detect_chapters(content)
            book.set_chapters(chapters)
            book.update_word_count()
        
        # 更新标签
        book.set_tags(tags_list)
        
        db.commit()
        db.refresh(book)
        
        # 记录更新日志
        logger.info(f"书籍更新成功: {old_title} -> {title}, ID: {book_id}, 状态: {status}")
        
        return {
            "success": True,
            "message": "书籍更新成功",
            "data": book.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新书籍失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

@router.delete("/{book_id}")
async def delete_book(
    book_id: int,
    force: bool = Query(False, description="是否强制删除"),
    db: Session = Depends(get_db)
):
    """
    删除书籍
    """
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        # 检查是否有关联的合成项目
        projects_count = db.query(NovelProject).filter(NovelProject.book_id == book_id).count()
        
        if projects_count > 0 and not force:
            raise HTTPException(
                status_code=400,
                detail=f"书籍有 {projects_count} 个关联的合成项目，请先删除项目或使用强制删除"
            )
        
        title = book.title
        
        # 删除关联的源文件
        if book.source_file_path and os.path.exists(book.source_file_path):
            try:
                os.remove(book.source_file_path)
            except Exception as e:
                logger.warning(f"删除源文件失败: {str(e)}")
        
        # 删除书籍记录（关联的项目会级联删除）
        db.delete(book)
        db.commit()
        
        # 记录删除日志
        logger.info(f"书籍删除成功: {title}, ID: {book_id}, 强制删除: {force}, 影响项目: {projects_count}")
        
        return {
            "success": True,
            "message": f"书籍 '{title}' 删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除书籍失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@router.get("/{book_id}/content")
async def get_book_content(
    book_id: int,
    chapter: Optional[int] = Query(None, description="章节编号"),
    start: Optional[int] = Query(None, description="开始位置"),
    length: Optional[int] = Query(None, description="内容长度"),
    db: Session = Depends(get_db)
):
    """
    获取书籍内容
    支持分章节或分段获取
    """
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        content = book.content
        
        # 如果指定章节
        if chapter is not None:
            chapters = book.get_chapters()
            if chapter < 1 or chapter > len(chapters):
                raise HTTPException(status_code=400, detail="章节编号无效")
            
            chapter_info = chapters[chapter - 1]
            start_pos = chapter_info.get('start', 0)
            end_pos = chapter_info.get('end', len(content))
            content = content[start_pos:end_pos]
        
        # 如果指定位置和长度
        elif start is not None:
            end_pos = start + length if length else len(content)
            content = content[start:end_pos]
        
        return {
            "success": True,
            "data": {
                "content": content,
                "totalLength": len(book.content),
                "chapters": book.get_chapters() if chapter is None else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取书籍内容失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取内容失败: {str(e)}")

@router.get("/{book_id}/stats")
async def get_book_stats(
    book_id: int,
    db: Session = Depends(get_db)
):
    """
    获取书籍统计信息
    """
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        # 获取合成项目统计
        projects = db.query(NovelProject).filter(NovelProject.book_id == book_id).all()
        project_stats = {
            "total": len(projects),
            "pending": len([p for p in projects if p.status == 'pending']),
            "processing": len([p for p in projects if p.status == 'processing']),
            "completed": len([p for p in projects if p.status == 'completed']),
            "failed": len([p for p in projects if p.status == 'failed'])
        }
        
        return {
            "success": True,
            "data": {
                "wordCount": book.word_count,
                "chapterCount": book.chapter_count,
                "projects": project_stats,
                "createdAt": book.created_at.isoformat() if book.created_at else None,
                "updatedAt": book.updated_at.isoformat() if book.updated_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取书籍统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")

def auto_detect_chapters(content: str) -> List[Dict[str, Any]]:
    """
    自动检测章节 - 简化版本
    """
    # 直接返回一个简单的全文章节，避免复杂的解析逻辑
    return [{
        "number": 1,
        "title": "全文",
        "start": 0,
        "end": len(content),
        "wordCount": len(content.replace(' ', '').replace('\n', ''))
    }] 