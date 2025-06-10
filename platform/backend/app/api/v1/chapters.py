"""
章节管理API
提供书籍章节管理功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Form
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, or_, and_
from typing import List, Optional, Dict, Any
import json
import logging
from datetime import datetime

from app.database import get_db
from app.models import BookChapter, Book, TextSegment
from app.utils import log_system_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chapters", tags=["Chapters"])

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
                    BookChapter.title.like(search_pattern),
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
        segments = db.query(TextSegment).filter(
            TextSegment.book_chapter_id == chapter_id
        ).order_by(TextSegment.segment_order).all()
        
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
    summary: Optional[str] = Form(None),
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
            chapter.title = title.strip()
        
        if content is not None:
            chapter.content = content
            # 更新字数统计
            chapter.word_count = len(content.strip())
        
        if analysis_status is not None:
            if analysis_status not in ['pending', 'processing', 'completed', 'failed']:
                raise HTTPException(status_code=400, detail="无效的分析状态")
            chapter.analysis_status = analysis_status
        
        if summary is not None:
            chapter.summary = summary
        
        chapter.updated_at = datetime.utcnow()
        db.commit()
        
        # 记录更新日志
        await log_system_event(
            db=db,
            level="info",
            message=f"章节更新: {chapter.title}",
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
        
        # 检查是否有关联的文本分段
        segment_count = db.query(func.count(TextSegment.id)).filter(
            TextSegment.book_chapter_id == chapter_id
        ).scalar()
        
        if not force and segment_count > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"章节关联了 {segment_count} 个文本分段，请使用强制删除"
            )
        
        chapter_title = chapter.title
        
        # 删除关联的文本分段
        db.query(TextSegment).filter(TextSegment.book_chapter_id == chapter_id).delete()
        
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
            title=new_title.strip(),
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
            message=f"章节分割: {chapter.title} -> {new_title}",
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
            merged_title = chapter.title
            keep_chapter = chapter
            delete_chapter = target_chapter
        else:
            # 将当前章节内容合并到目标章节前面
            merged_content = chapter.content + "\n\n" + target_chapter.content
            merged_title = target_chapter.title
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
            message=f"章节合并: {chapter.title} + {target_chapter.title}",
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
        
        # 获取分段统计
        segment_stats = db.query(
            TextSegment.status,
            func.count(TextSegment.id).label('count')
        ).filter(TextSegment.book_chapter_id == chapter_id).group_by(TextSegment.status).all()
        
        status_counts = {stat.status: stat.count for stat in segment_stats}
        
        # 计算基础统计
        total_segments = sum(status_counts.values())
        
        return {
            "success": True,
            "data": {
                "chapter_id": chapter_id,
                "title": chapter.title,
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