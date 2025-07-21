"""
书籍管理API
提供书籍上传、章节检测、结构化处理等功能
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import desc, asc, func, or_, and_
from typing import List, Optional, Dict, Any
import asyncio
import logging
import json
import re
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models import Book, BookChapter, AnalysisResult

# 配置文件上传大小限制
from fastapi import File
from typing import BinaryIO

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
    text_file: Optional[UploadFile] = File(None, description="上传的文本文件"),
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
async def get_chapters(
    book_id: int,
    skip: int = Query(0, description="跳过的记录数"),
    limit: int = Query(100, description="返回的记录数"),
    status_filter: str = Query("", description="状态过滤"),
    fields: str = Query("", description="指定返回字段，逗号分隔，如'id,chapter_number,chapter_title,word_count'"),
    exclude_content: bool = Query(True, description="是否排除内容字段以优化性能"),
    db: Session = Depends(get_db)
):
    """获取书籍的章节列表
    
    性能优化：
    - 支持字段选择，避免返回大字段
    - 默认排除content字段以减少数据传输
    - 支持分页查询
    """
    try:
        # 检查书籍是否存在
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        # 构建查询
        query = db.query(BookChapter).filter(BookChapter.book_id == book_id)
        
        # 应用状态过滤
        if status_filter:
            query = query.filter(BookChapter.analysis_status == status_filter)
        
        # 获取总数
        total = query.count()
        
        # 应用分页
        chapters = query.order_by(BookChapter.chapter_number).offset(skip).limit(limit).all()
        
        # 处理字段选择
        if fields:
            requested_fields = [f.strip() for f in fields.split(',') if f.strip()]
        else:
            # 默认字段，排除大内容字段
            requested_fields = [
                'id', 'book_id', 'chapter_number', 'chapter_title', 
                'word_count', 'character_count', 'analysis_status', 
                'synthesis_status', 'created_at', 'updated_at'
            ]
            if not exclude_content:
                requested_fields.append('content')
        
        # 转换为精简字典
        chapters_data = []
        for chapter in chapters:
            chapter_dict = chapter.to_dict()
            
            # 根据字段选择过滤
            if fields or exclude_content:
                filtered_dict = {}
                for field in requested_fields:
                    if field in chapter_dict:
                        filtered_dict[field] = chapter_dict[field]
                chapters_data.append(filtered_dict)
            else:
                chapters_data.append(chapter_dict)
        
        return {
            "success": True,
            "data": chapters_data,
            "total": total,
            "skip": skip,
            "limit": limit,
            "pagination": {
                "page": (skip // limit) + 1 if limit > 0 else 1,
                "page_size": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
                "has_next": skip + limit < total,
                "has_prev": skip > 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取章节列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取章节列表失败: {str(e)}")


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


# ============= 角色管理相关API =============

@router.get("/{book_id}/characters")
async def get_book_characters(
    book_id: int,
    db: Session = Depends(get_db)
):
    """
    获取书籍角色汇总信息
    高性能：不遍历所有章节，直接从book.character_summary读取
    """
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        character_summary = book.get_character_summary()
        voice_mappings = character_summary.get('voice_mappings', {})
        
        # 🔧 添加调试信息
        logger.info(f"[调试] 获取书籍{book_id}角色汇总:")
        logger.info(f"  voice_mappings: {voice_mappings}")
        
        # 🔥 关键修复：将配音信息合并到角色对象中
        enhanced_characters = []
        raw_characters = character_summary.get('characters', [])
        
        # 加载角色配音库数据
        character_library = {}
        try:
            from ..models import Character
            library_chars = db.query(Character).filter(Character.book_id == book_id).all()
            character_library = {char.name: char for char in library_chars}
            logger.info(f"📚 [角色配音库] 加载了 {len(character_library)} 个角色")
        except Exception as e:
            logger.warning(f"加载角色配音库失败: {e}")
        
        # 加载VoiceProfile数据
        voice_profiles = {}
        try:
            from ..models import VoiceProfile
            profiles = db.query(VoiceProfile).filter(VoiceProfile.status == 'active').all()
            voice_profiles = {profile.id: profile for profile in profiles}
            logger.info(f"📋 [语音档案] 加载了 {len(voice_profiles)} 个语音档案")
        except Exception as e:
            logger.warning(f"加载语音档案失败: {e}")
        
        for character in raw_characters:
            enhanced_char = dict(character)  # 复制原始角色数据
            char_name = character.get('name', '')
            
            # 🔥 重要：从voice_mappings获取配音ID
            voice_id_str = voice_mappings.get(char_name)
            character_id = None
            voice_id = None
            voice_name = "未分配"
            in_character_library = False
            is_voice_configured = False
            
            if voice_id_str:
                try:
                    voice_id_int = int(voice_id_str)
                    
                    # 🔥 智能判断ID类型：优先检查角色配音库
                    if char_name in character_library:
                        library_char = character_library[char_name]
                        if library_char.id == voice_id_int:
                            # 匹配角色配音库
                            character_id = library_char.id
                            voice_name = library_char.name
                            in_character_library = True
                            # 🔥 修复：检查是否有音频文件配置，而不是简单检查status
                            is_voice_configured = bool(library_char.reference_audio_path)
                            logger.info(f"🎭 [配音信息] {char_name} -> 角色配音库 ID:{character_id} (配音状态: {is_voice_configured})")
                        else:
                            logger.warning(f"⚠️ [配音信息] {char_name} 在配音库中但ID不匹配: 库中ID={library_char.id}, 映射ID={voice_id_int}")
                    
                    # 如果不是角色配音库，检查VoiceProfile
                    if not character_id and voice_id_int in voice_profiles:
                        voice_profile = voice_profiles[voice_id_int]
                        voice_id = voice_profile.id
                        voice_name = voice_profile.name
                        is_voice_configured = True
                        logger.info(f"🎤 [配音信息] {char_name} -> VoiceProfile ID:{voice_id}")
                    
                    if not character_id and not voice_id:
                        logger.warning(f"⚠️ [配音信息] {char_name} 的配音ID {voice_id_int} 无法找到对应配置")
                        
                except ValueError:
                    logger.warning(f"⚠️ [配音信息] {char_name} 的配音ID格式错误: {voice_id_str}")
            else:
                # 检查是否在角色配音库中但未配音
                if char_name in character_library:
                    library_char = character_library[char_name]
                    character_id = library_char.id
                    voice_name = library_char.name
                    in_character_library = True
                    # 🔥 修复：检查是否有音频文件配置，而不是简单检查status
                    is_voice_configured = bool(library_char.reference_audio_path)
                    logger.info(f"🎭 [配音信息] {char_name} -> 角色配音库 ID:{character_id} (未配置voice_mappings, 配音状态: {is_voice_configured})")
            
            # 🔥 关键：添加配音相关字段到角色对象
            enhanced_char.update({
                'character_id': character_id,
                'voice_id': voice_id,
                'voice_name': voice_name,
                'in_character_library': in_character_library,
                'is_voice_configured': is_voice_configured
            })
            
            enhanced_characters.append(enhanced_char)
        
        logger.info(f"✅ [数据增强] 成功增强 {len(enhanced_characters)} 个角色的配音信息")
        
        return {
            "success": True,
            "data": {
                "book_id": book_id,
                "book_title": book.title,
                "characters": enhanced_characters,  # 🔥 使用增强后的角色数据
                "voice_mappings": voice_mappings,
                "last_updated": character_summary.get('last_updated'),
                "total_chapters_analyzed": character_summary.get('total_chapters_analyzed', 0),
                "character_count": len(enhanced_characters),
                "configured_count": len([c for c in enhanced_characters if c.get('is_voice_configured')])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取书籍角色汇总失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取角色汇总失败: {str(e)}")


@router.post("/{book_id}/characters/{character_name}/voice-mapping")
async def set_character_voice_mapping(
    book_id: int,
    character_name: str,
    voice_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    设置单个角色的语音映射
    """
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        # 检查角色是否存在
        character_names = book.get_all_character_names()
        if character_name not in character_names:
            raise HTTPException(status_code=404, detail=f"角色 '{character_name}' 不存在")
        
        # 设置语音映射
        book.set_character_voice_mapping(character_name, voice_id)
        db.commit()
        
        # 🔥 关键修复：同步更新相关章节的synthesis_plan
        # 获取完整的角色语音映射（而不是只传递单个角色映射）
        db.refresh(book)  # 确保获取最新数据
        complete_voice_mappings = book.get_character_summary().get('voice_mappings', {})
        
        if complete_voice_mappings:
            updated_chapters = await _sync_character_voice_to_synthesis_plans(
                book_id, complete_voice_mappings, db
            )
        else:
            updated_chapters = 0
        
        logger.info(f"设置角色语音映射: 书籍{book_id} - {character_name} -> {voice_id}，同步更新了 {updated_chapters} 个章节")
        
        return {
            "success": True,
            "message": f"已设置角色 '{character_name}' 的语音配置，同步更新了 {updated_chapters} 个章节的合成计划",
            "data": {
                "character_name": character_name,
                "voice_id": voice_id,
                "updated_chapters": updated_chapters,
                "updated_at": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置角色语音映射失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"设置语音映射失败: {str(e)}")


@router.post("/{book_id}/characters/batch-voice-mappings")
async def batch_set_character_voice_mappings(
    book_id: int,
    mappings: str = Form(..., description="角色语音映射JSON字符串，格式: {角色名: voice_id}"),
    db: Session = Depends(get_db)
):
    """
    批量设置角色语音映射
    """
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        # 解析映射数据
        if isinstance(mappings, str):
            try:
                mappings = json.loads(mappings)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="映射数据格式错误")
        
        if not isinstance(mappings, dict):
            raise HTTPException(status_code=400, detail="映射数据必须是字典格式")
        
        # 检查所有角色是否存在
        character_names = book.get_all_character_names()
        invalid_characters = [char for char in mappings.keys() if char not in character_names]
        if invalid_characters:
            raise HTTPException(
                status_code=400, 
                detail=f"以下角色不存在: {', '.join(invalid_characters)}"
            )
        
        # 批量设置语音映射
        success_count = 0
        updated_mappings = {}
        for character_name, voice_id in mappings.items():
            if voice_id:  # 只设置非空的voice_id
                logger.info(f"[调试] 设置角色语音映射: {character_name} -> {voice_id}")
                book.set_character_voice_mapping(character_name, voice_id)
                updated_mappings[character_name] = voice_id
                success_count += 1
        
        # 🔥 调试：提交前检查数据
        logger.info(f"[调试] 提交前检查 character_summary: {book.character_summary}")
        db.commit()
        
        # 🔥 调试：提交后重新查询验证
        db.refresh(book)
        post_commit_summary = book.get_character_summary()
        # 🔥 安全类型检查
        if isinstance(post_commit_summary, dict):
            logger.info(f"[调试] 提交后重新查询 voice_mappings: {post_commit_summary.get('voice_mappings', {})}")
        else:
            logger.warning(f"[调试] 提交后数据格式异常: {type(post_commit_summary)} - {post_commit_summary}")
        
        # 🔥 关键修复：同步更新所有相关章节的synthesis_plan
        # 获取完整的角色语音映射（而不是只传递本次更新的部分映射）
        db.refresh(book)  # 确保获取最新数据
        complete_voice_mappings = book.get_character_summary().get('voice_mappings', {})
        
        if complete_voice_mappings:
            # 🔥 修复：传递完整的角色映射，确保所有角色都能被正确同步
            updated_chapters = await _sync_character_voice_to_synthesis_plans(
                book_id, complete_voice_mappings, db
            )
            logger.info(f"同步更新了 {updated_chapters} 个章节的synthesis_plan，完整映射: {complete_voice_mappings}")
        else:
            updated_chapters = 0
            logger.warning(f"书籍 {book_id} 没有任何角色语音映射，跳过同步")
        
        logger.info(f"批量设置角色语音映射: 书籍{book_id} - 成功设置 {success_count} 个角色")
        
        return {
            "success": True,
            "message": f"成功设置 {success_count} 个角色的语音配置，已同步更新 {updated_chapters} 个章节的合成计划",
            "data": {
                "book_id": book_id,
                "updated_mappings": updated_mappings,
                "success_count": success_count,
                "updated_chapters": updated_chapters,
                "updated_at": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量设置角色语音映射失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量设置失败: {str(e)}")


@router.post("/{book_id}/chapters/batch-status")
async def get_chapters_batch_status(
    book_id: int,
    chapter_ids: List[int] = Query(None, description="章节ID列表，不传则返回所有章节"),
    include_analysis: bool = Query(False, description="是否包含分析结果摘要"),
    include_synthesis: bool = Query(False, description="是否包含合成状态"),
    db: Session = Depends(get_db)
):
    """
    批量获取章节状态信息
    
    性能优化：
    - 单次请求获取多个章节的状态，避免8000+次单独请求
    - 支持选择性包含分析结果和合成状态
    - 返回轻量级状态数据
    """
    try:
        # 检查书籍是否存在
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        # 构建查询
        query = db.query(BookChapter).filter(BookChapter.book_id == book_id)
        
        # 如果指定了章节ID，则只查询这些章节
        if chapter_ids:
            query = query.filter(BookChapter.id.in_(chapter_ids))
        
        chapters = query.order_by(BookChapter.chapter_number).all()
        
        if not chapters:
            return {
                "success": True,
                "data": [],
                "total": 0,
                "message": "未找到章节"
            }
        
        # 准备结果
        results = []
        
        # 如果需要分析结果，批量查询
        analysis_map = {}
        if include_analysis:
            chapter_ids_list = [c.id for c in chapters]
            analysis_results = db.query(AnalysisResult).filter(
                AnalysisResult.chapter_id.in_(chapter_ids_list)
            ).all()
            analysis_map = {a.chapter_id: a for a in analysis_results}
        
        # 合成任务状态查询（如果需要）
        synthesis_map = {}
        if include_synthesis:
            from ..models import SynthesisTask
            chapter_ids_list = [c.id for c in chapters]
            synthesis_tasks = db.query(SynthesisTask).filter(
                SynthesisTask.chapter_id.in_(chapter_ids_list)
            ).all()
            synthesis_map = {t.chapter_id: t for t in synthesis_tasks}
        
        # 构建响应数据
        for chapter in chapters:
            chapter_data = {
                "id": chapter.id,
                "chapter_number": chapter.chapter_number,
                "chapter_title": chapter.chapter_title,
                "word_count": chapter.word_count,
                "analysis_status": chapter.analysis_status,
                "synthesis_status": chapter.synthesis_status,
                "updated_at": chapter.updated_at.isoformat() if chapter.updated_at else None
            }
            
            # 添加分析结果摘要
            if include_analysis and chapter.id in analysis_map:
                analysis = analysis_map[chapter.id]
                chapter_data["analysis_summary"] = {
                    "id": analysis.id,
                    "status": analysis.status,
                    "confidence_score": analysis.confidence_score,
                    "character_count": len(analysis.detected_characters or []),
                    "segment_count": len(analysis.synthesis_plan.get('segments', [])) if analysis.synthesis_plan else 0,
                    "created_at": analysis.created_at.isoformat() if analysis.created_at else None
                }
            
            # 添加合成状态
            if include_synthesis and chapter.id in synthesis_map:
                synthesis = synthesis_map[chapter.id]
                chapter_data["synthesis_summary"] = {
                    "task_id": synthesis.id,
                    "status": synthesis.status,
                    "progress": synthesis.progress,
                    "duration": synthesis.duration,
                    "created_at": synthesis.created_at.isoformat() if synthesis.created_at else None
                }
            
            results.append(chapter_data)
        
        return {
            "success": True,
            "data": results,
            "total": len(results),
            "book_info": {
                "id": book.id,
                "title": book.title,
                "total_chapters": book.chapter_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量获取章节状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量获取章节状态失败: {str(e)}")


@router.post("/{book_id}/characters/rebuild-summary")
async def rebuild_character_summary(
    book_id: int,
    db: Session = Depends(get_db)
):
    """
    重建书籍角色汇总（从所有章节分析结果重新汇总）
    用于修复或更新汇总数据
    """
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        # 获取所有已分析的章节
        chapters_with_analysis = db.query(BookChapter, AnalysisResult).join(
            AnalysisResult, BookChapter.id == AnalysisResult.chapter_id
        ).filter(
            BookChapter.book_id == book_id,
            AnalysisResult.detected_characters.isnot(None)
        ).all()
        
        if not chapters_with_analysis:
            return {
                "success": True,
                "message": "暂无章节分析数据，角色汇总为空",
                "data": book.get_character_summary()
            }
        
        # 保存当前的语音映射配置
        try:
            current_summary = book.get_character_summary()
            # 🔥 确保current_summary是字典格式
            if isinstance(current_summary, dict):
                current_mappings = current_summary.get('voice_mappings', {})
            else:
                logger.warning(f"角色汇总数据格式异常: {type(current_summary)} - {current_summary}")
                current_mappings = {}
        except Exception as e:
            logger.warning(f"获取当前语音映射失败: {str(e)}，使用空映射")
            current_mappings = {}
        
        # 清空角色汇总，重新构建
        book.character_summary = None
        
        # 逐章节更新角色汇总
        total_rebuilt = 0
        for chapter, analysis in chapters_with_analysis:
            detected_characters = analysis.detected_characters or []
            if detected_characters:
                book.update_character_summary(detected_characters, chapter.id)
                total_rebuilt += 1
        
        # 恢复之前的语音映射配置
        try:
            current_summary = book.get_character_summary()
            # 🔥 增强安全检查
            if isinstance(current_summary, dict):
                current_summary['voice_mappings'] = current_mappings
                book.character_summary = current_summary
                flag_modified(book, 'character_summary')  # 确保SQLAlchemy检测到修改
            else:
                logger.warning(f"角色汇总数据格式异常: {type(current_summary)}, 跳过语音映射恢复")
        except Exception as e:
            logger.warning(f"恢复语音映射失败: {str(e)}")
        
        db.commit()
        
        logger.info(f"重建书籍角色汇总: 书籍{book_id} - 处理了 {total_rebuilt} 个章节")
        
        return {
            "success": True,
            "message": f"成功重建角色汇总，处理了 {total_rebuilt} 个章节",
            "data": book.get_character_summary()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重建角色汇总失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重建汇总失败: {str(e)}")


@router.get("/{book_id}/chapters/search")
async def search_chapters(
    book_id: int,
    query: str = Query("", description="搜索关键词，支持章节标题模糊搜索"),
    chapter_number: int = Query(None, description="按章节号精确搜索"),
    status_filter: str = Query("", description="状态过滤"),
    skip: int = Query(0, description="跳过的记录数"),
    limit: int = Query(50, description="返回的记录数"),
    db: Session = Depends(get_db)
):
    """
    搜索章节
    
    支持：
    - 按章节标题模糊搜索
    - 按章节号精确搜索
    - 状态过滤
    - 分页返回
    """
    try:
        # 检查书籍是否存在
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        # 构建查询
        query_obj = db.query(BookChapter).filter(BookChapter.book_id == book_id)
        
        # 应用搜索条件
        if query:
            search_pattern = f"%{query}%"
            query_obj = query_obj.filter(BookChapter.chapter_title.like(search_pattern))
        
        if chapter_number:
            query_obj = query_obj.filter(BookChapter.chapter_number == chapter_number)
        
        if status_filter:
            query_obj = query_obj.filter(BookChapter.analysis_status == status_filter)
        
        # 获取总数
        total = query_obj.count()
        
        # 应用分页
        chapters = query_obj.order_by(BookChapter.chapter_number).offset(skip).limit(limit).all()
        
        # 返回精简数据
        chapters_data = []
        for chapter in chapters:
            chapters_data.append({
                "id": chapter.id,
                "chapter_number": chapter.chapter_number,
                "chapter_title": chapter.chapter_title,
                "word_count": chapter.word_count,
                "analysis_status": chapter.analysis_status,
                "synthesis_status": chapter.synthesis_status,
                "created_at": chapter.created_at.isoformat() if chapter.created_at else None,
                "updated_at": chapter.updated_at.isoformat() if chapter.updated_at else None
            })
        
        return {
            "success": True,
            "data": chapters_data,
            "total": total,
            "skip": skip,
            "limit": limit,
            "query": query,
            "pagination": {
                "page": (skip // limit) + 1 if limit > 0 else 1,
                "page_size": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
                "has_next": skip + limit < total,
                "has_prev": skip > 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索章节失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索章节失败: {str(e)}")


# ========== 内部辅助函数 ==========

async def _sync_character_voice_to_synthesis_plans(
    book_id: int, 
    character_voice_mappings: Dict[str, Any], 
    db: Session
) -> int:
    """
    同步角色语音配置到所有相关章节的synthesis_plan
    
    🚀 新架构说明：
    在新架构中，synthesis_plan存储character_id而不是voice_id，
    合成时会动态查找Character表获取最新配音，因此不再需要手动同步。
    
    🔄 向后兼容：
    此函数保留用于处理使用旧架构的历史数据，
    新的智能准备将直接生成使用character_id的synthesis_plan。
    
    Args:
        book_id: 书籍ID
        character_voice_mappings: 角色语音映射 {角色名: id_value}
        db: 数据库会话
    
    Returns:
        更新的章节数量
    """
    try:
        # 🔥 增强调试：记录传入的映射信息
        logger.info(f"🚀 [开始同步] 书籍 {book_id}, 传入映射: {character_voice_mappings}")
        
        # 🔥 CRITICAL FIX: 根据传入ID的实际类型建立正确映射
        # Step 1: 分析传入的ID，区分Character ID和VoiceProfile ID
        character_mappings = {}  # {角色名: Character对象}
        voice_profile_mappings = {}  # {角色名: VoiceProfile对象}
        id_to_name_mapping = {}  # 用于日志显示
        
        # 加载角色配音库数据
        try:
            from ...models import Character
            characters = db.query(Character).filter(
                Character.book_id == book_id
            ).all()
            character_id_map = {char.id: char for char in characters}
            logger.info(f"📚 [角色配音库] 加载了 {len(character_id_map)} 个角色配音库记录")
        except Exception as e:
            logger.warning(f"获取角色配音库失败: {str(e)}")
            character_id_map = {}

        # 加载VoiceProfile数据  
        try:
            from ...models import VoiceProfile
            voices = db.query(VoiceProfile).filter(VoiceProfile.status == 'active').all()
            voice_profile_id_map = {voice.id: voice for voice in voices}
            logger.info(f"📋 [语音档案] 加载了 {len(voice_profile_id_map)} 个语音档案记录")
        except Exception as e:
            logger.warning(f"获取语音档案失败: {str(e)}")
            voice_profile_id_map = {}

        # Step 2: 分析传入映射，判断每个ID的真实类型
        for character_name, id_value in character_voice_mappings.items():
            try:
                id_int = int(id_value)
                
                # 优先检查是否为Character ID
                if id_int in character_id_map:
                    character_mappings[character_name] = character_id_map[id_int]
                    id_to_name_mapping[str(id_int)] = f"{character_id_map[id_int].name}(角色配音库)"
                    logger.info(f"🎭 [ID类型识别] 角色'{character_name}' -> Character ID {id_int} ({character_id_map[id_int].name})")
                
                # 如果不是Character ID，检查是否为VoiceProfile ID
                elif id_int in voice_profile_id_map:
                    voice_profile_mappings[character_name] = voice_profile_id_map[id_int]
                    id_to_name_mapping[str(id_int)] = f"{voice_profile_id_map[id_int].name}(语音档案)"
                    logger.info(f"🎤 [ID类型识别] 角色'{character_name}' -> VoiceProfile ID {id_int} ({voice_profile_id_map[id_int].name})")
                
                else:
                    logger.warning(f"⚠️ [ID类型识别] 角色'{character_name}' -> ID {id_int} 在两个表中都不存在")
                    id_to_name_mapping[str(id_int)] = f"ID_{id_int}(未知)"
                    
            except (ValueError, TypeError):
                logger.warning(f"⚠️ [ID类型识别] 角色'{character_name}' -> 无效ID格式: {id_value}")

        logger.info(f"🎯 [映射汇总] Character映射: {len(character_mappings)}, VoiceProfile映射: {len(voice_profile_mappings)}")
        
        # 获取这本书所有已完成分析的章节
        chapters_with_analysis = db.query(BookChapter, AnalysisResult).join(
            AnalysisResult, BookChapter.id == AnalysisResult.chapter_id
        ).filter(
            BookChapter.book_id == book_id,
            AnalysisResult.status == 'completed',
            AnalysisResult.synthesis_plan.isnot(None)
        ).all()
        
        if not chapters_with_analysis:
            logger.info(f"书籍 {book_id} 暂无需要同步的章节分析结果")
            return 0
        
        updated_count = 0
        
        for chapter, analysis in chapters_with_analysis:
            try:
                synthesis_plan = analysis.synthesis_plan
                if not synthesis_plan:
                    continue
                
                # 🔥 修复：支持两种数据结构
                # 结构1: {'segments': [...]}  (旧版本)
                # 结构2: {'synthesis_plan': [...], 'project_info': {...}, 'characters': [...]}  (新版本)
                segments = None
                if 'segments' in synthesis_plan:
                    segments = synthesis_plan.get('segments', [])
                elif 'synthesis_plan' in synthesis_plan:
                    segments = synthesis_plan.get('synthesis_plan', [])
                
                if not segments or not isinstance(segments, list):
                    logger.debug(f"章节 {chapter.id} synthesis_plan格式不匹配或为空，跳过同步")
                    continue
                plan_updated = False
                
                # 遍历每个段落，更新匹配角色的ID配置
                for segment in segments:
                    speaker = segment.get('speaker', '')
                    
                    # 🔥 智能角色匹配：支持精确匹配和模糊匹配
                    matched_character = None
                    matched_voice_profile = None
                    matched_character_name = None
                    
                    # 1. 精确匹配
                    if speaker in character_mappings:
                        matched_character = character_mappings[speaker]
                        matched_character_name = speaker
                        logger.debug(f"🎯 [精确匹配-角色] 角色 '{speaker}' 找到Character配置: ID={matched_character.id}")
                    elif speaker in voice_profile_mappings:
                        matched_voice_profile = voice_profile_mappings[speaker]
                        matched_character_name = speaker
                        logger.debug(f"🎯 [精确匹配-语音] 角色 '{speaker}' 找到VoiceProfile配置: ID={matched_voice_profile.id}")
                    
                    # 2. 模糊匹配（如果精确匹配失败）
                    elif speaker:
                        # 先在角色配音库中模糊匹配
                        for config_name, character in character_mappings.items():
                            if (speaker in config_name) or (config_name in speaker):
                                matched_character = character
                                matched_character_name = config_name
                                logger.debug(f"🔍 [模糊匹配-角色] 角色 '{speaker}' 匹配到配置角色 '{config_name}': Character ID={character.id}")
                                break
                            
                            # 检查去除常见后缀后是否匹配
                            clean_speaker = speaker.rstrip('假临时备用')
                            clean_config = config_name.rstrip('假临时备用')
                            if clean_speaker == clean_config and len(clean_speaker) > 1:
                                matched_character = character
                                matched_character_name = config_name
                                logger.debug(f"🧹 [后缀匹配-角色] 角色 '{speaker}' 通过去除后缀匹配到 '{config_name}': Character ID={character.id}")
                                break
                        
                        # 如果角色配音库没找到，再在VoiceProfile中模糊匹配
                        if not matched_character:
                            for config_name, voice_profile in voice_profile_mappings.items():
                                if (speaker in config_name) or (config_name in speaker):
                                    matched_voice_profile = voice_profile
                                    matched_character_name = config_name
                                    logger.debug(f"🔍 [模糊匹配-语音] 角色 '{speaker}' 匹配到配置角色 '{config_name}': VoiceProfile ID={voice_profile.id}")
                                    break
                    
                    # 检查这个角色是否找到了匹配的配置
                    if matched_character or matched_voice_profile:
                        old_character_id = segment.get('character_id')
                        old_voice_id = segment.get('voice_id')
                        old_voice_name = segment.get('voice_name', '未分配')
                        
                        # 🚀 根据匹配类型设置正确的ID字段
                        if matched_character:
                            # 角色配音库：设置character_id，清除voice_id
                            new_character_id = matched_character.id
                            new_voice_name = matched_character.name
                            
                            # 检查是否需要更新
                            character_id_changed = old_character_id != new_character_id
                            voice_id_exists = old_voice_id is not None
                            voice_name_wrong = old_voice_name != new_voice_name
                            
                            if character_id_changed or voice_id_exists or voice_name_wrong:
                                segment['character_id'] = new_character_id
                                segment['voice_name'] = new_voice_name
                                
                                # 🔥 关键：清除voice_id避免ID空间冲突
                                if 'voice_id' in segment:
                                    del segment['voice_id']
                                
                                plan_updated = True
                                logger.info(f"✅ [角色同步] {speaker} (通过{matched_character_name}配置): character_id={new_character_id}, voice_name='{new_voice_name}' (清除voice_id)")
                        
                        elif matched_voice_profile:
                            # VoiceProfile：设置voice_id，清除character_id  
                            new_voice_id = matched_voice_profile.id
                            new_voice_name = matched_voice_profile.name
                            
                            # 检查是否需要更新
                            voice_id_changed = old_voice_id != new_voice_id
                            character_id_exists = old_character_id is not None
                            voice_name_wrong = old_voice_name != new_voice_name
                            
                            if voice_id_changed or character_id_exists or voice_name_wrong:
                                segment['voice_id'] = new_voice_id
                                segment['voice_name'] = new_voice_name
                                
                                # 🔥 关键：清除character_id避免ID空间冲突
                                if 'character_id' in segment:
                                    del segment['character_id']
                                
                                plan_updated = True
                                logger.info(f"✅ [语音同步] {speaker} (通过{matched_character_name}配置): voice_id={new_voice_id}, voice_name='{new_voice_name}' (清除character_id)")
                
                # 如果有更新，保存到数据库
                if plan_updated:
                    # 🔥 修复：根据数据结构保存回正确的位置
                    if 'segments' in synthesis_plan:
                        synthesis_plan['segments'] = segments
                    elif 'synthesis_plan' in synthesis_plan:
                        synthesis_plan['synthesis_plan'] = segments
                    
                    # 🔥 关键修复：强制SQLAlchemy检测JSON字段修改
                    from sqlalchemy.orm.attributes import flag_modified
                    analysis.synthesis_plan = synthesis_plan
                    flag_modified(analysis, 'synthesis_plan')
                    
                    # 🔥 CRITICAL FIX: 清空final_config避免API返回旧数据
                    # 当synthesis_plan更新时，自动清空final_config，确保API返回最新同步的数据
                    if analysis.final_config:
                        logger.info(f"🗑️ [清空缓存] 章节 {chapter.id} 清空final_config，避免API返回过期数据")
                        analysis.final_config = None
                        flag_modified(analysis, 'final_config')
                    
                    updated_count += 1
                    logger.info(f"✅ [章节同步] 章节 {chapter.id} '{chapter.title}' 同步完成")
                
            except Exception as e:
                logger.error(f"同步章节 {chapter.id} 失败: {str(e)}")
                continue
        
        # 提交所有更改
        db.commit()
        logger.info(f"🎉 [同步完成] 书籍 {book_id} 共同步了 {updated_count} 个章节的synthesis_plan")
        
        return updated_count
        
    except Exception as e:
        logger.error(f"同步角色语音配置失败: {str(e)}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        db.rollback()
        return 0 