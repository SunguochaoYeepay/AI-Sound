"""
小说朗读API模块
对应 NovelReader.vue 功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Form, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, or_, and_
from typing import Dict, List, Any, Optional
import json
import logging
import re
import os
from datetime import datetime

from app.database import get_db
from app.models import NovelProject, TextSegment, AudioFile, VoiceProfile

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/novel-reader", tags=["Novel Reader"])

@router.get("/projects")
async def get_projects(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query("", description="搜索关键词"),
    status: str = Query("", description="状态过滤"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    db: Session = Depends(get_db)
):
    """
    获取朗读项目列表
    对应前端项目列表显示功能
    """
    try:
        # 构建查询
        query = db.query(NovelProject)
        
        # 搜索过滤
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    NovelProject.name.like(search_pattern),
                    NovelProject.description.like(search_pattern)
                )
            )
        
        # 状态过滤
        if status and status in ['pending', 'processing', 'paused', 'completed', 'failed']:
            query = query.filter(NovelProject.status == status)
        
        # 排序
        sort_field = getattr(NovelProject, sort_by, NovelProject.created_at)
        if sort_order == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))
        
        # 统计总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        projects = query.offset(offset).limit(page_size).all()
        
        # 转换为字典格式
        project_list = []
        for project in projects:
            # 计算进度百分比
            progress = 0
            if project.total_segments > 0:
                progress = round((project.processed_segments / project.total_segments) * 100, 1)
            
            project_data = {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "progress": progress,
                "total_segments": project.total_segments,
                "processed_segments": project.processed_segments,
                "current_segment": project.current_segment,
                "final_audio_path": project.final_audio_path,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "started_at": project.started_at.isoformat() if project.started_at else None,
                "completed_at": project.completed_at.isoformat() if project.completed_at else None,
                "estimated_completion": None  # 字段不存在于模型中
            }
            project_list.append(project_data)
        
        # 分页信息
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "success": True,
            "data": project_list,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": total_pages,
                "hasMore": page < total_pages
            },
            "filters": {
                "search": search,
                "status": status
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")

@router.post("/projects")
async def create_project(
    name: str = Form(...),
    description: str = Form(""),
    content: str = Form(""),
    book_id: Optional[int] = Form(None),
    initial_characters: str = Form("[]"),
    settings: str = Form("{}"),
    db: Session = Depends(get_db)
):
    """
    创建新的朗读项目
    支持基于书籍引用或直接输入文本内容
    """
    try:
        # 验证项目名称
        if not name or len(name.strip()) == 0:
            raise HTTPException(status_code=400, detail="项目名称不能为空")
        
        # 检查项目名称是否已存在
        existing = db.query(NovelProject).filter(NovelProject.name == name).first()
        if existing:
            raise HTTPException(status_code=400, detail="项目名称已存在")
        
        # 获取文本内容：优先使用书籍，其次使用直接输入的内容
        text_content = ""
        actual_book_id = None
        
        if book_id:
            # 方式1：基于书籍
            from app.models import Book
            book = db.query(Book).filter(Book.id == book_id).first()
            if not book:
                raise HTTPException(status_code=404, detail="指定的书籍不存在")
            
            if not book.content or len(book.content.strip()) == 0:
                raise HTTPException(status_code=400, detail="书籍内容为空，无法创建项目")
            
            text_content = book.content
            actual_book_id = book_id
        elif content and content.strip():
            # 方式2：直接输入文本
            text_content = content.strip()
            actual_book_id = None
        else:
            raise HTTPException(status_code=400, detail="必须提供书籍ID或文本内容")

        # 解析初始角色映射
        try:
            initial_chars = json.loads(initial_characters) if initial_characters else []
            logger.info(f"解析初始角色: {initial_chars}")
        except json.JSONDecodeError as e:
            logger.error(f"初始角色JSON解析失败: {e}")
            raise HTTPException(status_code=400, detail="初始角色格式错误")
        
        # 解析项目设置
        try:
            project_settings = json.loads(settings) if settings else {}
            logger.info(f"解析项目设置: {project_settings}")
        except json.JSONDecodeError as e:
            logger.error(f"项目设置JSON解析失败: {e}")
            raise HTTPException(status_code=400, detail="项目设置格式错误")
        
        # 创建项目记录
        project = NovelProject(
            name=name,
            description=description,
            book_id=actual_book_id,
            status='pending'
        )
        
        # 设置初始角色映射（如果有）
        char_mapping = {}
        if initial_chars:
            for char_info in initial_chars:
                if isinstance(char_info, dict) and 'name' in char_info and 'voice_id' in char_info:
                    char_mapping[char_info['name']] = char_info['voice_id']
        
        # 使用项目模型的方法设置角色映射
        if hasattr(project, 'set_character_mapping'):
            project.set_character_mapping(char_mapping)
        
        # 设置项目配置
        if project_settings and hasattr(project, 'set_settings'):
            project.set_settings(project_settings)
        
        db.add(project)
        db.flush()  # 获取项目ID
        
        # 简单的文本分段（这里简化处理，实际应该有更复杂的分段逻辑）
        import re
        sentences = re.split(r'[。！？.!?]', text_content)
        segments_count = 0
        
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                segment = TextSegment(
                    project_id=project.id,
                    paragraph_index=i + 1,
                    content=sentence.strip(),
                    status='pending'
                )
                db.add(segment)
                segments_count += 1
        
        # 更新项目统计
        project.total_segments = segments_count
        project.processed_segments = 0
        
        db.commit()
        
        return {
            "success": True,
            "message": "项目创建成功",
            "data": {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "total_segments": project.total_segments,
                "book_id": project.book_id,
                "created_at": project.created_at.isoformat() if project.created_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")

@router.get("/projects/{project_id}")
async def get_project_detail(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取项目详情
    包含项目基本信息、分段信息、角色映射等
    """
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 获取分段信息
        segments = db.query(TextSegment).filter(TextSegment.project_id == project_id).all()
        
        # 计算进度百分比
        progress = 0
        if project.total_segments > 0:
            progress = round((project.processed_segments / project.total_segments) * 100, 1)
        
        # 获取角色统计
        character_stats = {}
        for segment in segments:
            speaker = segment.speaker
            if speaker:
                if speaker not in character_stats:
                    character_stats[speaker] = {"count": 0, "voice_assigned": False}
                character_stats[speaker]["count"] += 1
                if segment.voice_id:
                    character_stats[speaker]["voice_assigned"] = True
        
        # 获取项目相关的音频文件
        audio_files = db.query(AudioFile).filter(
            AudioFile.project_id == project_id
        ).order_by(AudioFile.created_at.desc()).all()
        
        audio_files_data = []
        for audio_file in audio_files:
            audio_files_data.append({
                "id": audio_file.id,
                "filename": audio_file.filename,
                "original_name": audio_file.original_name,
                "file_path": audio_file.file_path,
                "file_size": audio_file.file_size,
                "duration": audio_file.duration,
                "audio_type": audio_file.audio_type,
                "text_content": audio_file.text_content,
                "status": audio_file.status,
                "created_at": audio_file.created_at.isoformat() if audio_file.created_at else None,
                "url": f"/audio/{audio_file.filename}" if audio_file.filename else None
            })
        
        # 获取关联书籍信息
        book_data = None
        if project.book_id:
            from app.models import Book
            book = db.query(Book).filter(Book.id == project.book_id).first()
            if book:
                book_data = {
                    "id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "status": book.status
                }

        project_data = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "progress": progress,
            "total_segments": project.total_segments,
            "processed_segments": project.processed_segments,
            "current_segment": project.current_segment,
            "character_mapping": project.get_character_mapping(),
            "final_audio_path": project.final_audio_path,
            "book_id": project.book_id,
            "book": book_data,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "started_at": project.started_at.isoformat() if project.started_at else None,
            "completed_at": project.completed_at.isoformat() if project.completed_at else None,
            "estimated_completion": None,  # 字段不存在于模型中
            "character_stats": character_stats,
            "audio_files": audio_files_data,
            "segments_preview": [
                {
                    "id": s.id,
                    "order": s.paragraph_index,
                    "text": s.content[:100] + "..." if len(s.content) > 100 else s.content,
                    "speaker": s.speaker,
                    "voice_profile_id": s.voice_id,
                    "status": s.status
                }
                for s in segments[:10]  # 只返回前10个分段预览
            ]
        }
        
        return {
            "success": True,
            "data": project_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目详情失败: {str(e)}")

@router.get("/projects/{project_id}/progress")
async def get_generation_progress(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取项目生成进度
    实时返回当前处理状态
    """
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 使用项目级别的统计数据（智能准备模式）
        total = project.total_segments or 0
        processed = project.processed_segments or 0
        
        # 计算进度
        progress_percentage = round((processed / total) * 100, 1) if total > 0 else 0
        
        # 计算其他状态的段落数量
        if project.status == 'processing':
            processing = total - processed
            pending = 0
            failed = 0
        elif project.status == 'completed':
            processing = 0
            pending = 0
            failed = 0
        elif project.status == 'failed':
            processing = 0
            pending = 0
            failed = total - processed
        else:  # pending
            processing = 0
            pending = total
            failed = 0
        
        return {
            "success": True,
            "data": {
                "project_id": project.id,
                "status": project.status,
                "progress_percentage": progress_percentage,
                "current_segment": project.current_segment,
                "segments": {
                    "total": total,
                    "completed": processed,
                    "processing": processing,
                    "failed": failed,
                    "pending": pending
                },
                "timestamps": {
                    "started_at": project.started_at.isoformat() if project.started_at else None,
                    "estimated_completion": None  # 字段不存在于模型中
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取进度失败: {str(e)}")

@router.post("/projects/{project_id}/start")
async def start_project_generation(
    project_id: int,
    background_tasks: BackgroundTasks,
    parallel_tasks: int = Form(1, description="并行任务数"),
    db: Session = Depends(get_db)
):
    """
    启动项目音频生成
    """
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if project.status not in ['pending', 'paused', 'completed', 'failed', 'processing', 'partial_completed']:
            raise HTTPException(status_code=400, detail=f"项目状态为 {project.status}，无法启动")
        
        # 检查智能准备结果（使用智能准备模式）
        if not project.book_id:
            raise HTTPException(status_code=400, detail="项目未关联书籍，无法使用智能准备")
        
        # 获取智能准备结果
        from app.models import AnalysisResult, BookChapter
        analysis_results = db.query(AnalysisResult).join(
            BookChapter, AnalysisResult.chapter_id == BookChapter.id
        ).filter(
            BookChapter.book_id == project.book_id,
            AnalysisResult.status == 'completed',
            AnalysisResult.synthesis_plan.isnot(None)
        ).all()
        
        if not analysis_results:
            raise HTTPException(
                status_code=400, 
                detail="未找到智能准备结果，请先在书籍管理页面完成智能准备"
            )
        
        # 收集所有合成段落数据
        synthesis_data = []
        for result in analysis_results:
            if result.synthesis_plan and 'synthesis_plan' in result.synthesis_plan:
                plan_segments = result.synthesis_plan['synthesis_plan']
                synthesis_data.extend(plan_segments)
        
        if not synthesis_data:
            raise HTTPException(
                status_code=400, 
                detail="智能准备结果中没有合成段落数据，请重新进行智能准备"
            )
        
        # 根据状态决定是否重置进度
        if project.status in ['completed', 'processing']:
            # 完全重置：已完成或正在处理中的项目
            project.processed_segments = 0
            project.current_segment = 0
            project.started_at = None
            project.completed_at = None
        elif project.status == 'failed':
            # 部分重置：失败项目重置时间但保留进度（用户可能想重试失败的部分）
            project.started_at = None
            project.completed_at = None
        # partial_completed 状态不重置，继续上次的进度
        
        # 更新项目状态
        project.status = 'processing'
        project.total_segments = len(synthesis_data)
        project.started_at = datetime.utcnow()
        db.commit()
        
        # 启动后台任务处理音频生成
        from app.novel_reader import process_audio_generation_from_synthesis_plan
        background_tasks.add_task(
            process_audio_generation_from_synthesis_plan,
            project_id,
            synthesis_data,
            parallel_tasks
        )
        
        return {
            "success": True,
            "message": "项目启动成功",
            "data": {
                "project_id": project.id,
                "status": project.status,
                "total_segments": len(synthesis_data),
                "parallel_tasks": parallel_tasks
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"启动项目失败: {str(e)}")

@router.post("/projects/{project_id}/pause")
async def pause_generation(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    暂停项目生成
    """
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if project.status != 'processing':
            raise HTTPException(status_code=400, detail=f"项目状态为 {project.status}，无法暂停")
        
        # 更新项目状态
        project.status = 'paused'
        db.commit()
        
        return {
            "success": True,
            "message": "项目已暂停",
            "data": {
                "project_id": project.id,
                "status": project.status
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"暂停项目失败: {str(e)}")

@router.put("/projects/{project_id}")
async def update_project(
    project_id: int,
    name: str = Form(...),
    description: str = Form(""),
    character_mapping: str = Form("{}"),
    book_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """
    更新项目信息
    包括角色映射、项目名称、描述等
    """
    try:
        logger.info(f"[DEBUG] PUT请求开始 - project_id: {project_id}")
        logger.info(f"[DEBUG] 参数 - name: {name}, description: {description}")
        logger.info(f"[DEBUG] character_mapping原始值: {character_mapping}")
        
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 验证项目名称
        if not name or name.strip() == "" or name.lower() == "undefined":
            logger.error(f"[DEBUG] 项目名称无效: '{name}'")
            raise HTTPException(status_code=400, detail="项目名称不能为空或无效")
        
        # 检查名称重复（排除自己）
        existing = db.query(NovelProject).filter(
            and_(
                NovelProject.name == name,
                NovelProject.id != project_id
            )
        ).first()
        
        if existing:
            logger.error(f"[DEBUG] 项目名称已存在: {name}")
            raise HTTPException(status_code=400, detail="项目名称已存在")
        
        # 解析角色映射
        try:
            char_mapping = json.loads(character_mapping) if character_mapping else {}
            logger.info(f"[DEBUG] 解析角色映射 - 原始: {character_mapping}")
            logger.info(f"[DEBUG] 解析角色映射 - 结果: {char_mapping}")
        except json.JSONDecodeError as e:
            logger.error(f"[DEBUG] 角色映射JSON解析失败: {e}")
            raise HTTPException(status_code=400, detail="角色映射格式错误")
        
        # 更新项目信息
        old_name = project.name
        project.name = name
        project.description = description
        
        # 更新书籍关联
        if book_id is not None:
            project.book_id = book_id
            logger.info(f"[DEBUG] 更新book_id: {book_id}")
        
        # 更新角色映射
        if hasattr(project, 'set_character_mapping'):
            project.set_character_mapping(char_mapping)
            logger.info(f"[DEBUG] 使用set_character_mapping方法")
        else:
            # 由于模型没有character_mapping字段，使用set_character_mapping方法
            project.set_character_mapping(char_mapping)
            logger.info(f"[DEBUG] 使用set_character_mapping方法作为备选")
        
        # 最终一次性提交所有更改
        try:
            db.commit()
            db.refresh(project)
            logger.info(f"[DEBUG] 项目更新提交成功: {project_id}")
        except Exception as commit_error:
            logger.error(f"项目更新提交失败: {str(commit_error)}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"更新失败: {str(commit_error)}")
        
        return {
            "success": True,
            "message": "项目更新成功",
            "data": {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "character_mapping": project.get_character_mapping(),
                "updated_at": project.updated_at.isoformat() if project.updated_at else None
            }
        }
        
    except HTTPException as he:
        logger.error(f"[DEBUG] PUT请求HTTPException: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"[DEBUG] PUT请求Exception: {str(e)}")
        import traceback
        logger.error(f"[DEBUG] PUT详细错误: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    force: bool = Query(False, description="是否强制删除"),
    db: Session = Depends(get_db)
):
    """
    删除项目
    - 如果force=True，强制删除包括关联的音频文件和段落
    - 如果force=False，仅在项目无关联数据时允许删除
    """
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 检查项目是否有关联数据
        segments_count = db.query(TextSegment).filter(TextSegment.project_id == project_id).count()
        audio_files_count = db.query(AudioFile).filter(AudioFile.project_id == project_id).count()
        
        if not force and (segments_count > 0 or audio_files_count > 0):
            raise HTTPException(
                status_code=400, 
                detail=f"项目有关联数据（{segments_count}个段落，{audio_files_count}个音频文件），请使用强制删除"
            )
        
        # 删除关联的音频文件记录和实际文件
        if audio_files_count > 0:
            audio_files = db.query(AudioFile).filter(AudioFile.project_id == project_id).all()
            for audio_file in audio_files:
                # 删除实际文件
                if audio_file.file_path and os.path.exists(audio_file.file_path):
                    try:
                        os.remove(audio_file.file_path)
                    except Exception as e:
                        logger.warning(f"删除音频文件失败: {audio_file.file_path}, 错误: {e}")
                # 删除数据库记录
                db.delete(audio_file)
        
        # 删除关联的文本段落
        if segments_count > 0:
            db.query(TextSegment).filter(TextSegment.project_id == project_id).delete()
        
        # 删除项目本身
        db.delete(project)
        db.commit()
        
        return {
            "success": True,
            "message": "项目删除成功",
            "data": {
                "deleted_project_id": project_id,
                "deleted_segments": segments_count,
                "deleted_audio_files": audio_files_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")