"""
章节管理API
提供书籍章节管理功能 - 重构简化版
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Form, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, or_
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.database import get_db
from app.models import BookChapter, Book, AnalysisResult
from app.utils import log_system_event
from app.services.chapter_service import ChapterService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chapters", tags=["Chapters"])

@router.post("")
async def create_chapter(
    book_id: int = Form(..., description="书籍ID"),
    title: str = Form(..., description="章节标题"),
    content: str = Form(..., description="章节内容"),
    chapter_number: Optional[int] = Form(None, description="章节序号"),
    db: Session = Depends(get_db)
):
    """创建新章节"""
    try:
        # 检查书籍是否存在
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        # 如果没有指定章节序号，自动分配
        if chapter_number is None:
            max_chapter = db.query(func.max(BookChapter.chapter_number)).filter(
                BookChapter.book_id == book_id
            ).scalar()
            chapter_number = (max_chapter or 0) + 1
        else:
            # 检查章节序号是否已存在
            existing_chapter = db.query(BookChapter).filter(
                BookChapter.book_id == book_id,
                BookChapter.chapter_number == chapter_number
            ).first()
            if existing_chapter:
                raise HTTPException(status_code=400, detail=f"章节序号 {chapter_number} 已存在")
        
        # 创建新章节
        new_chapter = BookChapter(
            book_id=book_id,
            chapter_number=chapter_number,
            chapter_title=title.strip(),
            content=content,
            word_count=len(content.strip()),
            analysis_status='pending',
            synthesis_status='pending',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_chapter)
        db.commit()
        db.refresh(new_chapter)
        
        # 更新书籍的章节数
        chapter_count = db.query(BookChapter).filter(BookChapter.book_id == book_id).count()
        book.chapter_count = chapter_count
        db.commit()
        
        # 记录创建日志
        await log_system_event(
            db=db,
            level="info",
            message=f"新章节创建: {title}",
            module="chapters",
            details={"chapter_id": new_chapter.id, "book_id": book_id}
        )
        
        return {
            "success": True,
            "message": "章节创建成功",
            "data": new_chapter.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建章节失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建章节失败: {str(e)}")

@router.post("/batch")
async def create_chapters_batch(
    book_id: int = Form(..., description="书籍ID"),
    chapters: List[Dict[str, Any]] = Body(..., description="章节列表，每个章节包含title和content"),
    start_chapter_number: Optional[int] = Form(None, description="起始章节序号"),
    batch_size: int = Form(50, description="每批处理的章节数量"),
    db: Session = Depends(get_db)
):
    """批量创建章节
    
    Args:
        book_id: 书籍ID
        chapters: 章节列表，格式为[{"title": "章节标题", "content": "章节内容"}, ...]
        start_chapter_number: 起始章节序号（可选）
        batch_size: 每批处理的章节数量，默认50
    """
    try:
        # 检查书籍是否存在
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        # 确定起始章节序号
        if start_chapter_number is None:
            max_chapter = db.query(func.max(BookChapter.chapter_number)).filter(
                BookChapter.book_id == book_id
            ).scalar()
            start_chapter_number = (max_chapter or 0) + 1
        
        created_chapters = []
        total_chapters = len(chapters)
        
        # 分批处理章节
        for i in range(0, total_chapters, batch_size):
            batch_chapters = chapters[i:i + batch_size]
            
            try:
                # 开启事务
                for idx, chapter_data in enumerate(batch_chapters):
                    chapter_number = start_chapter_number + i + idx
                    
                    # 创建新章节
                    new_chapter = BookChapter(
                        book_id=book_id,
                        chapter_number=chapter_number,
                        chapter_title=chapter_data["title"].strip(),
                        content=chapter_data["content"],
                        word_count=len(chapter_data["content"].strip()),
                        analysis_status='pending',
                        synthesis_status='pending',
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    
                    db.add(new_chapter)
                    created_chapters.append(new_chapter)
                
                # 提交当前批次
                db.commit()
                
                # 记录批量创建日志
                await log_system_event(
                    db=db,
                    level="info",
                    message=f"批量创建章节成功，批次 {i//batch_size + 1}",
                    module="chapters",
                    details={
                        "book_id": book_id,
                        "batch_start": i,
                        "batch_size": len(batch_chapters)
                    }
                )
                
            except Exception as e:
                db.rollback()
                logger.error(f"批量创建章节失败，批次 {i//batch_size + 1}: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"批量创建章节失败，批次 {i//batch_size + 1}: {str(e)}"
                )
        
        # 更新书籍的章节数
        chapter_count = db.query(BookChapter).filter(BookChapter.book_id == book_id).count()
        book.chapter_count = chapter_count
        db.commit()
        
        return {
            "success": True,
            "message": "批量创建章节成功",
            "data": {
                "total_created": len(created_chapters),
                "first_chapter_number": start_chapter_number,
                "last_chapter_number": start_chapter_number + len(created_chapters) - 1
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量创建章节失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量创建章节失败: {str(e)}")

@router.get("")
async def get_chapters(
    book_id: Optional[int] = Query(None, description="书籍ID过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query("", description="搜索关键词"),
    status: str = Query("", description="状态过滤"),
    sort_by: str = Query("chapter_number", description="排序字段"),
    sort_order: str = Query("asc", description="排序方向"),
    db: Session = Depends(get_db)
):
    """获取章节列表"""
    try:
        # 构建查询
        query = db.query(BookChapter)
        
        # 书籍过滤
        if book_id:
            query = query.filter(BookChapter.book_id == book_id)
        
        # 搜索过滤
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    BookChapter.chapter_title.like(search_pattern),
                    BookChapter.content.like(search_pattern)
                )
            )
        
        # 状态过滤
        if status:
            query = query.filter(BookChapter.analysis_status == status)
        
        # 排序
        sort_field = getattr(BookChapter, sort_by, BookChapter.chapter_number)
        if sort_order == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))
        
        # 统计总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        chapters = query.offset(offset).limit(page_size).all()
        
        # 转换为字典格式
        chapter_list = []
        for chapter in chapters:
            chapter_data = chapter.to_dict()
            
            # 添加书籍信息
            if chapter.book:
                chapter_data['book'] = {
                    "id": chapter.book.id,
                    "title": chapter.book.title,
                    "author": chapter.book.author
                }
            
            chapter_list.append(chapter_data)
        
        # 分页信息
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "success": True,
            "data": chapter_list,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": total_pages,
                "hasMore": page < total_pages
            },
            "filters": {
                "book_id": book_id,
                "search": search,
                "status": status
            }
        }
        
    except Exception as e:
        logger.error(f"获取章节列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取章节列表失败: {str(e)}")

@router.get("/{chapter_id}")
async def get_chapter(
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """获取章节详情"""
    try:
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        chapter_data = chapter.to_dict()
        
        # 添加书籍信息
        if chapter.book:
            chapter_data['book'] = {
                "id": chapter.book.id,
                "title": chapter.book.title,
                "author": chapter.book.author
            }
        
        # 添加关联的文本分段信息
        # 注意：TextSegment模型使用project_id而不是chapter_id，这里先返回空列表
        segments = []
        
        chapter_data['segments'] = [
            {
                "id": seg.id,
                "order": seg.segment_order,
                "text": seg.text_content[:100] + "..." if len(seg.text_content) > 100 else seg.text_content,
                "status": seg.status,
                "detected_speaker": getattr(seg, 'detected_speaker', None)
            }
            for seg in segments
        ]
        
        return {
            "success": True,
            "data": chapter_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取章节详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取章节详情失败: {str(e)}")

@router.patch("/{chapter_id}")
async def update_chapter(
    chapter_id: int,
    title: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    analysis_status: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """更新章节信息"""
    try:
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 更新字段
        if title is not None:
            if not title.strip():
                raise HTTPException(status_code=400, detail="章节标题不能为空")
            chapter.chapter_title = title.strip()
        
        if content is not None:
            chapter.content = content
            # 更新字数统计
            chapter.word_count = len(content.strip())
        
        if analysis_status is not None:
            if analysis_status not in ['pending', 'processing', 'completed', 'failed']:
                raise HTTPException(status_code=400, detail="无效的分析状态")
            chapter.analysis_status = analysis_status
        
        chapter.updated_at = datetime.utcnow()
        db.commit()
        
        # 记录更新日志
        await log_system_event(
            db=db,
            level="info",
            message=f"章节更新: {chapter.chapter_title}",
            module="chapters",
            details={"chapter_id": chapter_id}
        )
        
        return {
            "success": True,
            "message": "章节更新成功",
            "data": chapter.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新章节失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

@router.delete("/{chapter_id}")
async def delete_chapter(
    chapter_id: int,
    force: bool = Query(False, description="强制删除"),
    db: Session = Depends(get_db)
):
    """删除章节"""
    try:
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 注意：TextSegment模型使用project_id而不是chapter_id，这里跳过分段检查
        chapter_title = chapter.chapter_title
        
        # 删除章节
        db.delete(chapter)
        db.commit()
        
        # 记录删除日志
        await log_system_event(
            db=db,
            level="info",
            message=f"章节删除: {chapter_title}",
            module="chapters",
            details={"chapter_id": chapter_id, "force": force}
        )
        
        return {
            "success": True,
            "message": "章节删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除章节失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@router.post("/{chapter_id}/split")
async def split_chapter(
    chapter_id: int,
    split_position: int = Form(..., description="分割位置"),
    new_title: str = Form(..., description="新章节标题"),
    db: Session = Depends(get_db)
):
    """分割章节"""
    try:
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        if not chapter.content:
            raise HTTPException(status_code=400, detail="章节内容为空，无法分割")
        
        content_length = len(chapter.content)
        if split_position <= 0 or split_position >= content_length:
            raise HTTPException(status_code=400, detail="分割位置无效")
        
        if not new_title.strip():
            raise HTTPException(status_code=400, detail="新章节标题不能为空")
        
        # 分割内容
        original_content = chapter.content[:split_position]
        new_content = chapter.content[split_position:]
        
        # 更新原章节
        chapter.content = original_content
        chapter.word_count = len(original_content.strip())
        chapter.updated_at = datetime.utcnow()
        
        # 创建新章节
        new_chapter = BookChapter(
            book_id=chapter.book_id,
            chapter_number=chapter.chapter_number + 1,
            chapter_title=new_title.strip(),
            content=new_content,
            word_count=len(new_content.strip()),
            analysis_status='pending',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # 更新后续章节的编号
        db.query(BookChapter).filter(
            BookChapter.book_id == chapter.book_id,
            BookChapter.chapter_number > chapter.chapter_number
        ).update({
            BookChapter.chapter_number: BookChapter.chapter_number + 1
        })
        
        db.add(new_chapter)
        db.commit()
        db.refresh(new_chapter)
        
        # 记录分割日志
        await log_system_event(
            db=db,
            level="info",
            message=f"章节分割: {chapter.chapter_title} -> {new_title}",
            module="chapters",
            details={
                "original_chapter_id": chapter_id,
                "new_chapter_id": new_chapter.id,
                "split_position": split_position
            }
        )
        
        return {
            "success": True,
            "message": "章节分割成功",
            "data": {
                "original_chapter": chapter.to_dict(),
                "new_chapter": new_chapter.to_dict()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分割章节失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分割失败: {str(e)}")

@router.post("/{chapter_id}/merge")
async def merge_chapters(
    chapter_id: int,
    target_chapter_id: int = Form(..., description="目标章节ID"),
    merge_direction: str = Form("after", description="合并方向: before/after"),
    db: Session = Depends(get_db)
):
    """合并章节"""
    try:
        if chapter_id == target_chapter_id:
            raise HTTPException(status_code=400, detail="不能与自己合并")
        
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        target_chapter = db.query(BookChapter).filter(BookChapter.id == target_chapter_id).first()
        
        if not chapter:
            raise HTTPException(status_code=404, detail="源章节不存在")
        if not target_chapter:
            raise HTTPException(status_code=404, detail="目标章节不存在")
        
        if chapter.book_id != target_chapter.book_id:
            raise HTTPException(status_code=400, detail="只能合并同一本书的章节")
        
        if merge_direction not in ["before", "after"]:
            raise HTTPException(status_code=400, detail="合并方向必须是 before 或 after")
        
        # 合并内容
        if merge_direction == "after":
            # 将目标章节内容合并到当前章节后面
            merged_content = chapter.content + "\n\n" + target_chapter.content
            merged_title = chapter.chapter_title
            keep_chapter = chapter
            delete_chapter = target_chapter
        else:
            # 将当前章节内容合并到目标章节前面
            merged_content = chapter.content + "\n\n" + target_chapter.content
            merged_title = target_chapter.chapter_title
            keep_chapter = target_chapter
            delete_chapter = chapter
        
        # 更新保留的章节
        keep_chapter.content = merged_content
        keep_chapter.word_count = len(merged_content.strip())
        keep_chapter.updated_at = datetime.utcnow()
        
        # 删除合并的章节
        delete_chapter_number = delete_chapter.chapter_number
        db.delete(delete_chapter)
        
        # 更新后续章节编号
        db.query(BookChapter).filter(
            BookChapter.book_id == chapter.book_id,
            BookChapter.chapter_number > delete_chapter_number
        ).update({
            BookChapter.chapter_number: BookChapter.chapter_number - 1
        })
        
        db.commit()
        
        # 记录合并日志
        await log_system_event(
            db=db,
            level="info",
            message=f"章节合并: {chapter.chapter_title} + {target_chapter.chapter_title}",
            module="chapters",
            details={
                "chapter_id": chapter_id,
                "target_chapter_id": target_chapter_id,
                "merge_direction": merge_direction,
                "kept_chapter_id": keep_chapter.id
            }
        )
        
        return {
            "success": True,
            "message": "章节合并成功",
            "data": keep_chapter.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"合并章节失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"合并失败: {str(e)}")

@router.get("/{chapter_id}/statistics")
async def get_chapter_statistics(
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """获取章节统计信息"""
    try:
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 🚀 新架构：不再使用TextSegment分段统计
        # 因为新架构直接基于智能准备结果合成，章节不依赖TextSegment
        status_counts = {}
        total_segments = 0
        
        return {
            "success": True,
            "data": {
                "chapter_id": chapter_id,
                "title": chapter.chapter_title,
                "word_count": chapter.word_count,
                "total_segments": total_segments,
                "segment_status_counts": status_counts,
                "analysis_status": chapter.analysis_status,
                "created_at": chapter.created_at.isoformat() if chapter.created_at else None,
                "updated_at": chapter.updated_at.isoformat() if chapter.updated_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取章节统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")




