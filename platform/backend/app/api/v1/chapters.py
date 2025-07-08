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
from app.models import BookChapter, Book
from app.utils import log_system_event
from app.services.content_preparation_service import ContentPreparationService
from app.services.chapter_service import (
    ChapterService, 
    analyze_chapter_characters,
    get_chapter_content_stats,
    get_synthesis_preview
)
from app.detectors import ProgrammaticCharacterDetector, OllamaCharacterDetector

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chapters", tags=["Chapters"])

# 检测器类已移到 app.detectors 模块，这里只保留路由处理

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
        
        # 🚀 新架构：不再使用TextSegment分段统计
        # 因为新架构直接基于智能准备结果合成，章节不依赖TextSegment
        status_counts = {}
        total_segments = 0
        
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

@router.post("/batch-character-analysis")
async def batch_character_analysis(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    批量分析章节中的角色
    基于编程识别规则，从选定章节中发现所有角色
    """
    try:
        chapter_ids = request.get("chapter_ids", [])
        detection_method = request.get("detection_method", "programming")
        emotion_detection = request.get("emotion_detection", True)
        
        if not chapter_ids:
            raise HTTPException(status_code=400, detail="未提供章节ID列表")
        
        results = []
        
        for chapter_id in chapter_ids:
            chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
            if not chapter:
                logger.warning(f"章节 {chapter_id} 不存在，跳过")
                continue
                
            # 使用增强的角色识别分析章节
            analysis_result = await analyze_chapter_characters(
                chapter, 
                detection_method, 
                emotion_detection
            )
            
            results.append(analysis_result)
        
        return {
            "success": True,
            "data": results,
            "message": f"成功分析 {len(results)} 个章节，发现角色信息"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量角色分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


async def analyze_chapter_characters(chapter: BookChapter, detection_method: str, emotion_detection: bool):
    """
    分析单个章节的角色
    基于编程识别规则实现 - 增强版
    """
    try:
        logger.info(f"开始分析章节 {chapter.id}: {chapter.chapter_title}")
        
        content = chapter.content or ""
        if not content.strip():
            return {
                "chapter_id": chapter.id,
                "chapter_title": chapter.chapter_title,
                "chapter_number": chapter.chapter_number,
                "detected_characters": [],
                "segments": [],
                "processing_stats": {"total_segments": 0, "dialogue_segments": 0, "characters_found": 0}
            }
        
        # 强制使用Ollama AI进行角色分析 - 失败就是失败！
        logger.info(f"🤖 强制使用Ollama AI进行角色分析")
        
        # 检查Ollama服务是否可用
        import requests
        try:
            response = requests.get("http://localhost:11434/api/version", timeout=3)
            if response.status_code != 200:
                raise Exception(f"Ollama服务响应异常: {response.status_code}")
        except requests.exceptions.ConnectionError:
            raise Exception("❌ 无法连接到Ollama服务 (http://localhost:11434)")
        except Exception as e:
            if "Ollama服务响应异常" in str(e):
                raise e
            raise Exception(f"Ollama服务检查失败: {str(e)}")
        
        # Ollama服务正常，执行AI分析
        logger.info("✅ Ollama服务可用，开始AI分析")
        detector = OllamaCharacterDetector()
        analysis_result = await detector.analyze_text(content, {
            'chapter_id': chapter.id,
            'chapter_title': chapter.chapter_title,
            'chapter_number': chapter.chapter_number,
            'session_id': f"analysis_{chapter.id}"
        })
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"分析章节 {chapter.id} 失败: {str(e)}")
        return {
            "chapter_id": chapter.id,
            "chapter_title": chapter.chapter_title or "未知章节",
            "chapter_number": chapter.chapter_number,
            "detected_characters": [],
            "segments": [],
            "error": str(e)
        }


# AdvancedCharacterDetector 已移到 app.detectors 模块
# OllamaCharacterDetector 已移到 app.detectors 模块

# 所有检测器类都已移到独立模块，这里只保留路由处理逻辑


# 路由处理函数开始
        """过滤已存在于角色库中的角色"""
        from ...database import get_db
        from ...models import VoiceProfile
        from sqlalchemy.orm import Session
        
        # 获取数据库会话
        db_gen = get_db()
        db: Session = next(db_gen)
        
        try:
            filtered_characters = []
            
            for char in characters:
                char_name = char.get('name', '')
                
                # 检查角色是否已存在
                existing_character = db.query(VoiceProfile).filter(
                    VoiceProfile.name == char_name
                ).first()
                
                if not existing_character:
                    # 角色不存在，添加到结果中
                    filtered_characters.append(char)
                    logger.info(f"新角色发现: {char_name}")
                else:
                    logger.info(f"角色已存在，跳过: {char_name} (ID: {existing_character.id})")
            
            return filtered_characters
            
        except Exception as e:
            logger.error(f"过滤已存在角色失败: {str(e)}")
            # 出错时返回所有角色
            return characters
        finally:
            db.close()
    
    def _infer_gender_smart(self, name: str, ai_gender: str) -> str:
        """智能推断角色性别 - 完全依赖AI判断，移除硬编码"""
        # 如果AI已经正确识别了性别，直接使用
        if ai_gender and ai_gender in ['male', 'female', 'neutral']:
            return ai_gender
        
        # 如果AI没有返回性别信息，调用专门的性别识别AI
        try:
            gender = self._ai_infer_gender(name)
            if gender in ['male', 'female', 'neutral']:
                logger.info(f"AI推断角色 '{name}' 性别: {gender}")
                return gender
        except Exception as e:
            logger.warning(f"AI性别推断失败: {str(e)}")
        
        # 默认返回unknown，让用户手动选择
        logger.warning(f"无法推断角色 '{name}' 的性别")
        return 'unknown'
    
    def _ai_infer_gender(self, character_name: str) -> str:
        """使用AI推断角色性别"""
        try:
            prompt = f"""请判断角色 "{character_name}" 的性别。

判断规则：
1. 基于中文姓名的常见特征
2. 基于文学作品中的角色设定
3. 基于称谓、头衔的语义含义

返回格式（只返回一个词）：
- male（男性）
- female（女性）  
- neutral（中性，如旁白、叙述者）

角色名：{character_name}
性别："""

            response = self._call_ollama(prompt)
            if response:
                # 提取性别判断
                gender = response.strip().lower()
                if 'male' in gender and 'female' not in gender:
                    return 'male'
                elif 'female' in gender:
                    return 'female'
                elif 'neutral' in gender:
                    return 'neutral'
            
            return 'unknown'
            
        except Exception as e:
            logger.error(f"AI性别推断异常: {str(e)}")
            return 'unknown'


@router.post("/{chapter_id}/prepare-synthesis")
async def prepare_chapter_for_synthesis(
    chapter_id: int,
    include_emotion: bool = Query(True, description="是否包含情绪识别"),
    processing_mode: str = Query("auto", description="处理模式: auto/single/distributed"),
    db: Session = Depends(get_db)
):
    """
    准备章节内容用于语音合成（输出兼容现有格式）
    
    这是智能内容准备的核心API，实现：
    - 🎭 智能角色识别与分离
    - 🔒 原文内容100%保持不变
    - 🎭 自动添加旁白角色
    - 📋 输出完全兼容现有合成系统的JSON格式
    - 🧠 支持大文本分布式处理
    """
    
    try:
        # 创建内容准备服务
        content_service = ContentPreparationService(db)
        
        # 执行智能内容准备
        result = await content_service.prepare_chapter_for_synthesis(
            chapter_id=chapter_id,
            user_preferences={
                "include_emotion": include_emotion,
                "processing_mode": processing_mode
            }
        )
        
        # 记录系统事件
        log_system_event(
            db, 
            "chapter_synthesis_prepared", 
            f"章节 {chapter_id} 智能内容准备完成",
            {
                "chapter_id": chapter_id,
                "processing_mode": result["processing_info"]["mode"],
                "total_segments": result["processing_info"]["total_segments"],
                "characters_found": result["processing_info"]["characters_found"]
            }
        )
        
        return {
            "success": True,
            "message": f"章节内容准备完成，共识别 {result['processing_info']['characters_found']} 个角色，{result['processing_info']['total_segments']} 个段落",
            "data": result["synthesis_json"],  # 兼容现有格式的JSON
            "processing_info": result["processing_info"]
        }
        
    except Exception as e:
        logger.error(f"章节 {chapter_id} 内容准备失败: {str(e)}")
        
        # 记录错误事件
        log_system_event(
            db, 
            "chapter_synthesis_preparation_failed", 
            f"章节 {chapter_id} 智能内容准备失败: {str(e)}",
            {"chapter_id": chapter_id, "error": str(e)}
        )
        
        raise HTTPException(
            status_code=500, 
            detail=f"内容准备失败: {str(e)}"
        )


@router.get("/{chapter_id}/synthesis-preview")
async def get_synthesis_preview(
    chapter_id: int,
    max_segments: int = Query(10, ge=1, le=50, description="预览段落数量"),
    db: Session = Depends(get_db)
):
    """
    获取章节合成预览
    
    快速预览章节的智能分析结果，不进行完整处理
    """
    
    try:
        # 获取章节
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 使用简单的角色检测器进行快速预览
        detector = ProgrammaticCharacterDetector()
        
        # 取前1000字符进行预览分析
        preview_text = chapter.content[:1000] if len(chapter.content) > 1000 else chapter.content
        
        # 分析文本段落
        segments = detector.segment_text_with_speakers(preview_text)
        
        # 提取角色信息
        character_stats = detector.extract_dialogue_characters(segments)
        
        # 限制预览段落数量
        preview_segments = segments[:max_segments]
        
        return {
            "success": True,
            "chapter_info": {
                "id": chapter.id,
                "title": chapter.chapter_title,
                "content_length": len(chapter.content),
                "preview_length": len(preview_text)
            },
            "preview_segments": preview_segments,
            "detected_characters": [
                {"name": name, "segment_count": count}
                for name, count in character_stats.items()
            ],
            "statistics": {
                "total_segments": len(segments),
                "preview_segments": len(preview_segments),
                "character_count": len(character_stats),
                "is_truncated": len(chapter.content) > 1000
            }
        }
        
    except Exception as e:
        logger.error(f"章节 {chapter_id} 预览失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")


@router.get("/{chapter_id}/content-stats")
async def get_chapter_content_stats(
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """
    获取章节内容统计信息
    
    用于判断处理策略和预估处理时间
    """
    
    try:
        # 获取章节
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        content = chapter.content
        
        # 基本统计
        char_count = len(content)
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        english_words = len(re.findall(r'[a-zA-Z]+', content))
        
        # 估算token数量
        estimated_tokens = int(chinese_chars * 1.5 + english_words)
        
        # 段落统计
        paragraphs = re.split(r'\n\s*\n', content.strip())
        paragraph_count = len([p for p in paragraphs if p.strip()])
        
        # 对话统计
        dialogue_markers = ['"', '"', '"', '「', '」', '『', '』', "'", "'"]
        dialogue_count = sum(content.count(marker) for marker in dialogue_markers)
        
        # 推荐处理模式
        if estimated_tokens <= 3000:
            recommended_mode = "single"
            estimated_time = "30-60秒"
        else:
            recommended_mode = "distributed"
            estimated_time = "60-120秒"
        
        return {
            "success": True,
            "chapter_info": {
                "id": chapter.id,
                "title": chapter.chapter_title
            },
            "content_stats": {
                "total_characters": char_count,
                "chinese_characters": chinese_chars,
                "english_words": english_words,
                "estimated_tokens": estimated_tokens,
                "paragraph_count": paragraph_count,
                "dialogue_markers": dialogue_count
            },
            "processing_recommendation": {
                "recommended_mode": recommended_mode,
                "estimated_time": estimated_time,
                "complexity": "simple" if estimated_tokens <= 1500 else "medium" if estimated_tokens <= 3000 else "complex"
            }
        }
        
    except Exception as e:
        logger.error(f"章节 {chapter_id} 统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"统计失败: {str(e)}") 