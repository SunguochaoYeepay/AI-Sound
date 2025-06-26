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
import re
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models import Book, BookChapter, AnalysisResult

# 注意：PUT端点现在使用Form参数而不是JSON请求

router = APIRouter(prefix="/books")

logger = logging.getLogger(__name__)


def detect_chapters_from_content(content: str) -> List[dict]:
    """
    从书籍内容中检测章节
    返回章节列表，每个章节包含：title, content, word_count
    """
    if not content or not content.strip():
        return []
    
    chapters = []
    lines = content.split('\n')
    current_chapter = None
    chapter_content = []
    chapter_number = 0
    
    # 章节标题检测模式
    chapter_patterns = [
        r'^#{1,6}\s+',  # Markdown标题 # ## ### 等
        r'^第[一二三四五六七八九十\d]+[章节回]',  # 第一章、第1章、第一节等
        r'^Chapter\s+\d+',  # Chapter 1
        r'^\d+\.',  # 1.
        r'^[一二三四五六七八九十]+、',  # 一、二、三、
        r'^【.*?】',  # 【章节标题】
        r'^（第.*?）',  # （第一章）
    ]
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 检测是否为章节标题
        is_chapter_title = False
        for pattern in chapter_patterns:
            if re.match(pattern, line):
                is_chapter_title = True
                break
        
        if is_chapter_title:
            # 保存上一章节
            if current_chapter and chapter_content:
                chapter_text = '\n'.join(chapter_content)
                if chapter_text.strip():  # 确保章节内容不为空
                    chapters.append({
                        'number': chapter_number,
                        'title': current_chapter,
                        'content': chapter_text,
                        'word_count': len(chapter_text.replace(' ', '').replace('\n', ''))
                    })
            
            # 开始新章节
            chapter_number += 1
            current_chapter = line
            chapter_content = []
        else:
            chapter_content.append(line)
    
    # 保存最后一章
    if current_chapter and chapter_content:
        chapter_text = '\n'.join(chapter_content)
        if chapter_text.strip():
            chapters.append({
                'number': chapter_number,
                'title': current_chapter,
                'content': chapter_text,
                'word_count': len(chapter_text.replace(' ', '').replace('\n', ''))
            })
    
    # 如果没有检测到章节，将整个内容作为一个章节
    if not chapters and content.strip():
        chapters.append({
            'number': 1,
            'title': '全文',
            'content': content.strip(),
            'word_count': len(content.replace(' ', '').replace('\n', ''))
        })
    
    return chapters


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
            try:
                # 检测章节
                chapters_data = detect_chapters_from_content(book_content)
                
                # 保存章节到数据库
                for chapter_data in chapters_data:
                    chapter = BookChapter(
                        book_id=new_book.id,
                        chapter_number=chapter_data['number'],
                        chapter_title=chapter_data['title'],
                        content=chapter_data['content'],
                        word_count=chapter_data['word_count'],
                        analysis_status='pending',
                        synthesis_status='pending',
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(chapter)
                
                # 更新书籍的章节数
                new_book.chapter_count = len(chapters_data)
                db.commit()
                
                logger.info(f"书籍 '{title}' 自动检测到 {len(chapters_data)} 个章节")
                
            except Exception as e:
                logger.error(f"章节检测失败: {str(e)}")
                # 章节检测失败不影响书籍创建
        
        return {
            "success": True,
            "data": new_book.to_dict(),
            "message": f"书籍创建成功，检测到 {new_book.chapter_count} 个章节"
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
async def get_book(book_id: int, db: Session = Depends(get_db)):
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
        
        # 检查是否已有章节数据
        existing_chapters = db.query(BookChapter).filter(BookChapter.book_id == book_id).count()
        if existing_chapters > 0 and not force_reprocess:
            raise HTTPException(
                status_code=400, 
                detail=f"书籍已有 {existing_chapters} 个章节，使用 force_reprocess=true 强制重新处理"
            )
        
        # 如果强制重新处理，删除现有章节
        if force_reprocess and existing_chapters > 0:
            db.query(BookChapter).filter(BookChapter.book_id == book_id).delete()
            db.commit()
        
        # 检测章节
        chapters_data = detect_chapters_from_content(book.content or "")
        
        if not chapters_data:
            raise HTTPException(status_code=400, detail="未检测到有效章节")
        
        # 保存章节到数据库
        for chapter_data in chapters_data:
            chapter = BookChapter(
                book_id=book_id,
                chapter_number=chapter_data['number'],
                chapter_title=chapter_data['title'],
                content=chapter_data['content'],
                word_count=chapter_data['word_count'],
                analysis_status='pending',
                synthesis_status='pending',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(chapter)
        
        # 更新书籍信息
        book.chapter_count = len(chapters_data)
        db.commit()
        
        return {
            "success": True,
            "message": f"章节检测完成，发现 {len(chapters_data)} 个章节",
            "chapters_found": len(chapters_data),
            "book_id": book_id,
            "chapters": [
                {
                    "number": ch['number'],
                    "title": ch['title'],
                    "word_count": ch['word_count']
                }
                for ch in chapters_data
            ]
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


@router.put("/{book_id}")
async def update_book_put(
    book_id: int,
    title: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """完整更新书籍信息 (PUT方法) - 支持Form格式"""
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        # 更新提供的字段
        if title is not None:
            if not title.strip():
                raise HTTPException(status_code=400, detail="书籍标题不能为空")
            book.title = title.strip()
        
        if author is not None:
            book.author = author.strip()
        
        if description is not None:
            book.description = description.strip()
        
        if content is not None:
            book.content = content
            book.word_count = len(content)
        
        if tags is not None:
            try:
                parsed_tags = json.loads(tags) if tags else []
                book.tags = json.dumps(parsed_tags, ensure_ascii=False)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="标签格式错误")
        
        if status is not None:
            if status not in ['draft', 'published', 'archived']:
                raise HTTPException(status_code=400, detail="无效的状态值")
            book.status = status
        
        db.commit()
        db.refresh(book)
        
        return {
            "success": True,
            "data": book.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新书籍失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新书籍失败: {str(e)}")


@router.patch("/{book_id}")
def update_book_patch(
    book_id: int,
    title: Optional[str] = None,
    author: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """部分更新书籍信息 (PATCH方法)"""
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
    
    return {
        "success": True,
        "data": book.to_dict()
    } 


@router.get("/{book_id}/analysis-results")
async def get_book_analysis_results(
    book_id: int,
    chapter_ids: Optional[str] = Query(None, description="逗号分隔的章节ID列表"),
    db: Session = Depends(get_db)
):
    """
    获取书籍的所有智能准备结果
    用于合成中心加载已完成的分析数据
    """
    try:
        # 检查书籍是否存在
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        # 构建查询条件
        query = db.query(BookChapter, AnalysisResult).join(
            AnalysisResult, BookChapter.id == AnalysisResult.chapter_id, isouter=True
        ).filter(
            BookChapter.book_id == book_id
        )
        
        # 如果指定了章节ID，则只查询这些章节
        if chapter_ids:
            try:
                chapter_id_list = [int(id.strip()) for id in chapter_ids.split(',') if id.strip()]
                if chapter_id_list:
                    query = query.filter(BookChapter.id.in_(chapter_id_list))
                    logger.info(f"过滤章节ID: {chapter_id_list}")
            except ValueError:
                raise HTTPException(status_code=400, detail="章节ID格式错误")
        
        chapters_with_analysis = query.order_by(BookChapter.chapter_number).all()
        
        analysis_results = []
        
        for chapter, analysis in chapters_with_analysis:
            if analysis and analysis.synthesis_plan:
                # 构建分析结果数据
                result_data = {
                    "chapter_id": chapter.id,
                    "chapter_number": chapter.chapter_number,
                    "chapter_title": chapter.chapter_title,
                    "word_count": chapter.word_count,
                    "analysis_id": analysis.id,
                    "synthesis_json": analysis.synthesis_plan,
                    "confidence_score": analysis.confidence_score,
                    "processing_time": analysis.processing_time,
                    "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
                    "updated_at": analysis.updated_at.isoformat() if analysis.updated_at else None
                }
                analysis_results.append(result_data)
        
        logger.info(f"获取书籍 {book_id} 的分析结果: 找到 {len(analysis_results)} 个已分析章节")
        
        return {
            "success": True,
            "data": analysis_results,
            "book_info": {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "total_chapters": len(chapters_with_analysis),
                "analyzed_chapters": len(analysis_results)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取书籍分析结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取分析结果失败: {str(e)}") 