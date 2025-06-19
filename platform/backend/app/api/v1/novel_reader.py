"""
小说朗读API模块
对应 NovelReader.vue 功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, or_, and_
from typing import Dict, List, Any, Optional
import json
import logging
import re
import os
from datetime import datetime

from app.database import get_db
from app.models import NovelProject, AudioFile, VoiceProfile  # TextSegment已废弃

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
            # 🚀 新架构：基于AudioFile计算进度
            audio_count = db.query(AudioFile).filter(
                AudioFile.project_id == project.id,
                AudioFile.audio_type == 'segment'
            ).count()
            
            total_count = project.total_segments or 0
            progress = round((audio_count / total_count) * 100, 1) if total_count > 0 else 0
            
            project_data = {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "progress": progress,
                "total_segments": total_count,  # 🚀 基于项目设置
                "processed_segments": audio_count,  # 🚀 基于AudioFile实际数量
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
        
        # 🚀 新架构：不再进行传统文本分段，使用智能准备模式
        # 项目创建时不分段，等待智能准备结果进行合成
        segments_count = 0
        project.total_segments = 0
        project.processed_segments = 0
        logger.info(f"项目 {project.id} 创建完成，新架构将使用智能准备结果进行合成")
        
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
        
        # 🚀 新架构：基于AudioFile获取段落信息
        audio_segments = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.audio_type == 'segment'
        ).all()
        
        # 计算进度百分比
        progress = 0
        completed_count = len(audio_segments)  # AudioFile存在即表示已完成
        total_count = project.total_segments or 0
        if total_count > 0:
            progress = round((completed_count / total_count) * 100, 1)
        
        # 🚀 新架构：基于AudioFile的角色统计
        character_stats = {}
        for audio_file in audio_segments:
            speaker = audio_file.speaker or audio_file.character_name
            if speaker:
                if speaker not in character_stats:
                    character_stats[speaker] = {"count": 0, "voice_assigned": False}
                character_stats[speaker]["count"] += 1
                if audio_file.voice_profile_id:
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
            "total_segments": total_count,  # 🚀 基于智能准备实际总数
            "processed_segments": completed_count,  # 🚀 基于AudioFile实际数量
            "current_segment": project.current_segment,
            # 🚀 新架构：提供基于AudioFile的统计信息
            "statistics": {
                "totalSegments": total_count,
                "completedSegments": completed_count,
                "failedSegments": max(0, total_count - completed_count) if project.status in ['partial_completed', 'failed'] else 0,
                "processingSegments": 1 if project.status == 'processing' else 0,
                "pendingSegments": max(0, total_count - completed_count) if project.status == 'pending' else 0
            },
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
            # 🚀 新架构：基于AudioFile的段落预览
            "segments_preview": [
                {
                    "id": audio_file.id,
                    "order": audio_file.paragraph_index,
                    "text": audio_file.text_content[:100] + "..." if audio_file.text_content and len(audio_file.text_content) > 100 else audio_file.text_content,
                    "speaker": audio_file.speaker or audio_file.character_name,
                    "voice_profile_id": audio_file.voice_profile_id,
                    "status": "completed",  # AudioFile存在即已完成
                    "chapter_number": audio_file.chapter_number,
                    "filename": audio_file.filename,
                    "duration": audio_file.duration
                }
                for audio_file in sorted(audio_segments, key=lambda x: x.paragraph_index or 0)[:10]  # 按段落索引排序，只返回前10个
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
        
        # 🚀 新架构：基于AudioFile的实际统计数据
        audio_count = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.audio_type == 'segment'
        ).count()
        
        total = project.total_segments or 0  # 智能准备确定的总数
        processed = audio_count  # 实际已合成的数量
        
        # 数据验证和修复
        if total > 0 and processed > total:
            logger.warning(f"项目 {project_id} 数据异常: processed_segments({processed}) > total_segments({total})")
            # 详细记录数据状态
            logger.warning(f"  项目状态: {project.status}")
            logger.warning(f"  项目processed_segments字段: {project.processed_segments}")
            logger.warning(f"  AudioFile实际数量: {processed}")
            logger.warning(f"  项目total_segments字段: {project.total_segments}")
            
            # 根据项目状态决定修复策略
            if project.status in ['completed', 'partial_completed']:
                # 已完成的项目，以AudioFile数量为准，更新total_segments
                logger.info(f"  修复策略: 更新total_segments为实际AudioFile数量 {processed}")
                project.total_segments = processed
                total = processed
            else:
                # 进行中或其他状态的项目，以total_segments为准，更新processed_segments
                logger.info(f"  修复策略: 限制processed_segments为total_segments {total}")
            processed = total
            project.processed_segments = processed
            
            db.commit()
            logger.info(f"  数据修复完成: total={total}, processed={processed}")
        
        # 确保processed_segments字段与实际AudioFile数量同步
        if project.processed_segments != processed:
            logger.debug(f"同步项目processed_segments: {project.processed_segments} -> {processed}")
            project.processed_segments = processed
            db.commit()
        
        # 计算进度
        progress_percentage = round((processed / total) * 100, 1) if total > 0 else 0
        
        # 计算其他状态的段落数量
        if project.status == 'processing':
            processing = max(0, total - processed)
            pending = 0
            failed = 0
        elif project.status == 'completed':
            processing = 0
            pending = 0
            failed = 0
        elif project.status == 'failed':
            processing = 0
            pending = 0
            failed = max(0, total - processed)
        elif project.status == 'partial_completed':
            processing = 0
            pending = 0
            # 对于部分完成状态，假设剩余的都是失败的
            failed = max(0, total - processed)
        else:  # pending
            processing = 0
            pending = total
            failed = 0
        
        # 记录调试信息
        logger.info(f"🔍 项目 {project_id} 进度查询: 状态={project.status}, 总数={total}, 完成={processed}, 进度={progress_percentage}%")
        logger.info(f"🔍 AudioFile实际数量: {audio_count}, 项目total_segments: {project.total_segments}, 项目processed_segments: {project.processed_segments}")
        
        progress_data = {
            "success": True,
            "data": {
                "project_id": project.id,
                "status": project.status,
                "progress_percentage": progress_percentage,
                "current_segment": project.current_segment,
                "current_processing": f"当前段落: {project.current_segment}" if project.current_segment else "",
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
                },
                "debug_info": {
                    "raw_total_segments": project.total_segments,
                    "raw_processed_segments": project.processed_segments,
                    "audio_file_count": audio_count,
                    "calculated_progress": progress_percentage
                }
            }
        }
        
        logger.info(f"🔍 返回进度数据: {progress_data}")
        return progress_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取进度失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取进度失败: {str(e)}")

@router.post("/projects/{project_id}/start")
async def start_project_generation(
    project_id: int,
    background_tasks: BackgroundTasks,
    parallel_tasks: int = Form(1, description="并行任务数"),
    synthesis_mode: str = Form("chapters", description="合成模式"),
    chapter_ids: str = Form("", description="章节ID列表，逗号分隔"),
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
        
                # 解析章节ID列表
        selected_chapter_ids = []
        if chapter_ids.strip():
            try:
                selected_chapter_ids = [int(id.strip()) for id in chapter_ids.split(',') if id.strip()]
                logger.info(f"[DEBUG] 用户选择的章节ID: {selected_chapter_ids}")
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的章节ID格式")
        
        # 获取智能准备结果
        from app.models import AnalysisResult, BookChapter
        analysis_query = db.query(AnalysisResult).join(
            BookChapter, AnalysisResult.chapter_id == BookChapter.id
        ).filter(
            BookChapter.book_id == project.book_id,
            AnalysisResult.status == 'completed',
            AnalysisResult.synthesis_plan.isnot(None)
        )
        
        # 如果指定了章节ID，则只获取选中的章节
        if selected_chapter_ids:
            analysis_query = analysis_query.filter(BookChapter.id.in_(selected_chapter_ids))
            logger.info(f"[DEBUG] 按章节筛选合成，选中 {len(selected_chapter_ids)} 个章节")
        else:
            logger.info(f"[DEBUG] 合成所有章节")
        
        analysis_results = analysis_query.all()
        
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
        
        # 🚀 用户点击重新合成 = 强制重新合成！不要过度智能判断！
        logger.info(f"[FORCE_RESYNTH] 用户要求重新合成，清理现有数据并重新开始")
        
        # 清理该项目的现有AudioFile（用户要求重新合成就是要从头开始）
        existing_audio_files = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.audio_type == 'segment'
        ).all()
        
        logger.info(f"[FORCE_RESYNTH] 删除 {len(existing_audio_files)} 个现有音频文件")
        for audio_file in existing_audio_files:
            # 删除物理文件
            if audio_file.file_path and os.path.exists(audio_file.file_path):
                try:
                    os.remove(audio_file.file_path)
                    logger.debug(f"[FORCE_RESYNTH] 删除音频文件: {audio_file.file_path}")
                except Exception as e:
                    logger.warning(f"[FORCE_RESYNTH] 删除音频文件失败: {e}")
            
            # 删除数据库记录
            db.delete(audio_file)
        
        db.commit()
        logger.info(f"[FORCE_RESYNTH] 清理完成，准备重新合成")
        
        # 重置项目状态
        project.status = 'processing'
        project.total_segments = len(synthesis_data)
        project.processed_segments = 0
        project.current_segment = 0
        project.started_at = datetime.utcnow()
        project.completed_at = None
        project.error_message = None
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

@router.post("/projects/{project_id}/cancel")
async def cancel_generation(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    取消项目生成
    将项目状态设置为 'cancelled'，并清理相关进度数据
    """
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if project.status not in ['processing', 'paused']:
            raise HTTPException(status_code=400, detail=f"项目状态为 {project.status}，无法取消")
        
        # 更新项目状态为取消
        project.status = 'cancelled'
        
        # 重置进度相关字段
        project.processed_segments = 0
        project.total_segments = None
        project.current_segment = None
        project.failed_segments = 0
        
        db.commit()
        
        return {
            "success": True,
            "message": "项目已取消",
            "data": {
                "project_id": project.id,
                "status": project.status
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"取消项目失败: {str(e)}")

@router.post("/projects/{project_id}/resume")
async def resume_generation(
    project_id: int,
    background_tasks: BackgroundTasks,
    parallel_tasks: int = Form(1, description="并行任务数"),
    chapter_ids: str = Form("", description="章节ID列表，逗号分隔"),
    db: Session = Depends(get_db)
):
    """
    恢复项目音频生成
    只能恢复处于暂停状态的项目
    """
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if project.status != 'paused':
            raise HTTPException(status_code=400, detail=f"项目状态为 {project.status}，无法恢复。只能恢复暂停状态的项目")
        
        # 检查智能准备结果（使用智能准备模式）
        if not project.book_id:
            raise HTTPException(status_code=400, detail="项目未关联书籍，无法使用智能准备")
        
                # 解析章节ID列表
        selected_chapter_ids = []
        if chapter_ids.strip():
            try:
                selected_chapter_ids = [int(id.strip()) for id in chapter_ids.split(',') if id.strip()]
                logger.info(f"[DEBUG] 用户选择的章节ID: {selected_chapter_ids}")
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的章节ID格式")
        
        # 获取智能准备结果
        from app.models import AnalysisResult, BookChapter
        analysis_query = db.query(AnalysisResult).join(
            BookChapter, AnalysisResult.chapter_id == BookChapter.id
        ).filter(
            BookChapter.book_id == project.book_id,
            AnalysisResult.status == 'completed',
            AnalysisResult.synthesis_plan.isnot(None)
        )
        
        # 如果指定了章节ID，则只获取选中的章节
        if selected_chapter_ids:
            analysis_query = analysis_query.filter(BookChapter.id.in_(selected_chapter_ids))
            logger.info(f"[DEBUG] 按章节筛选合成，选中 {len(selected_chapter_ids)} 个章节")
        else:
            logger.info(f"[DEBUG] 合成所有章节")
        
        analysis_results = analysis_query.all()
        
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
        
        # 更新项目状态为处理中，但不重置进度（保持从暂停位置继续）
        project.status = 'processing'
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
            "message": "项目恢复成功",
            "data": {
                "project_id": project.id,
                "status": project.status,
                "total_segments": len(synthesis_data),
                "parallel_tasks": parallel_tasks,
                "current_progress": project.processed_segments or 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"恢复项目失败: {str(e)}")

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
        
        # 检查关联数据
        audio_files_count = db.query(AudioFile).filter(AudioFile.project_id == project_id).count()
        
        # 检查TextSegment（虽然已废弃，但可能还有历史数据）
        from app.models.text_segment import TextSegment
        text_segments_count = db.query(TextSegment).filter(TextSegment.project_id == project_id).count()
        
        # 检查分析会话
        from app.models.analysis_session import AnalysisSession
        analysis_sessions_count = db.query(AnalysisSession).filter(AnalysisSession.project_id == project_id).count()
        
        # 检查合成任务
        from app.models.synthesis_task import SynthesisTask
        synthesis_tasks_count = db.query(SynthesisTask).filter(SynthesisTask.project_id == project_id).count()
        
        total_related_data = audio_files_count + text_segments_count + analysis_sessions_count + synthesis_tasks_count
        
        if not force and total_related_data > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"项目有关联数据（{audio_files_count}个音频文件，{text_segments_count}个文本段落，{analysis_sessions_count}个分析会话，{synthesis_tasks_count}个合成任务），请使用强制删除"
            )
        
        # 强制删除时，删除所有关联数据
        if force and total_related_data > 0:
            # 1. 删除AudioFile记录和实际文件
            if audio_files_count > 0:
                audio_files = db.query(AudioFile).filter(AudioFile.project_id == project_id).all()
                for audio_file in audio_files:
                    # 删除实际文件
                    if audio_file.file_path and os.path.exists(audio_file.file_path):
                        try:
                            os.remove(audio_file.file_path)
                            logger.info(f"删除音频文件: {audio_file.file_path}")
                        except Exception as e:
                            logger.warning(f"删除音频文件失败: {audio_file.file_path}, 错误: {e}")
                    # 删除数据库记录
                    db.delete(audio_file)
            
            # 2. 删除TextSegment记录（历史数据）
            if text_segments_count > 0:
                text_segments = db.query(TextSegment).filter(TextSegment.project_id == project_id).all()
                for segment in text_segments:
                    # 如果有音频文件路径，也删除
                    if segment.audio_file_path and os.path.exists(segment.audio_file_path):
                        try:
                            os.remove(segment.audio_file_path)
                            logger.info(f"删除历史音频文件: {segment.audio_file_path}")
                        except Exception as e:
                            logger.warning(f"删除历史音频文件失败: {segment.audio_file_path}, 错误: {e}")
                    db.delete(segment)
            
            # 3. 删除AnalysisSession记录（会级联删除相关数据）
            if analysis_sessions_count > 0:
                analysis_sessions = db.query(AnalysisSession).filter(AnalysisSession.project_id == project_id).all()
                for session in analysis_sessions:
                    db.delete(session)
            
            # 4. 删除SynthesisTask记录
            if synthesis_tasks_count > 0:
                synthesis_tasks = db.query(SynthesisTask).filter(SynthesisTask.project_id == project_id).all()
                for task in synthesis_tasks:
                    db.delete(task)
        
        # 删除项目最终音频文件
        if project.final_audio_path and os.path.exists(project.final_audio_path):
            try:
                os.remove(project.final_audio_path)
                logger.info(f"删除项目最终音频文件: {project.final_audio_path}")
            except Exception as e:
                logger.warning(f"删除项目最终音频文件失败: {project.final_audio_path}, 错误: {e}")
        
        # 最后删除项目本身
        db.delete(project)
        db.commit()
        
        logger.info(f"成功删除项目 {project_id} 及其所有关联数据")
        
        return {
            "success": True,
            "message": "项目删除成功",
            "data": {
                "deleted_project_id": project_id,
                "deleted_audio_files": audio_files_count,
                "deleted_text_segments": text_segments_count,
                "deleted_analysis_sessions": analysis_sessions_count,
                "deleted_synthesis_tasks": synthesis_tasks_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")

@router.post("/projects/{project_id}/retry-segment/{segment_id}")
async def retry_segment(
    project_id: int,
    segment_id: int,
    db: Session = Depends(get_db)
):
    """
    🚀 新架构：重试单个失败的段落（基于AudioFile不存在判断失败）
    """
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 🚀 新架构：检查该段落是否已有AudioFile
        existing_audio = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.paragraph_index == segment_id,
            AudioFile.audio_type == 'segment'
        ).first()
        
        if existing_audio:
            raise HTTPException(status_code=400, detail="该段落已经合成成功，无需重试")
        
        # 🚀 新架构：重试失败段落本质上是重新启动智能准备合成
        if not project.book_id:
            raise HTTPException(status_code=400, detail="项目未关联书籍，无法重试")
        
        # 获取智能准备结果，找到对应segment_id的数据
        from app.models import AnalysisResult, BookChapter
        analysis_results = db.query(AnalysisResult).join(
            BookChapter, AnalysisResult.chapter_id == BookChapter.id
        ).filter(
            BookChapter.book_id == project.book_id,
            AnalysisResult.status == 'completed',
            AnalysisResult.synthesis_plan.isnot(None)
        ).all()
        
        # 查找对应的segment数据
        target_segment_data = None
        for result in analysis_results:
            if result.synthesis_plan and 'synthesis_plan' in result.synthesis_plan:
                plan_segments = result.synthesis_plan['synthesis_plan']
                for segment_data in plan_segments:
                    if segment_data.get('segment_id') == segment_id:
                        target_segment_data = segment_data
                        break
                if target_segment_data:
                    break
        
        if not target_segment_data:
            raise HTTPException(status_code=404, detail=f"未找到段落{segment_id}的智能准备数据")
        
        # 更新项目状态为处理中
        if project.status in ['failed', 'partial_completed']:
            project.status = 'processing'
        
        db.commit()
        
        return {
            "success": True,
            "message": f"段落{segment_id}重试已启动",
            "data": {
                "project_id": project_id,
                "segment_id": segment_id,
                "message": "将在下次完整合成时重新处理该段落"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"重试段落失败: {str(e)}")

@router.post("/projects/{project_id}/retry-failed-segments")
async def retry_all_failed_segments(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    🚀 新架构：重试所有失败的段落（基于AudioFile缺失判断失败）
    """
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if not project.book_id:
            raise HTTPException(status_code=400, detail="项目未关联书籍，无法重试")
        
        # 🚀 新架构：获取智能准备结果，确定应该有哪些段落
        from app.models import AnalysisResult, BookChapter
        analysis_results = db.query(AnalysisResult).join(
            BookChapter, AnalysisResult.chapter_id == BookChapter.id
        ).filter(
            BookChapter.book_id == project.book_id,
            AnalysisResult.status == 'completed',
            AnalysisResult.synthesis_plan.isnot(None)
        ).all()
        
        if not analysis_results:
            raise HTTPException(status_code=400, detail="未找到智能准备结果")
        
        # 收集所有应该合成的段落ID
        expected_segments = set()
        synthesis_data = []
        for result in analysis_results:
            if result.synthesis_plan and 'synthesis_plan' in result.synthesis_plan:
                plan_segments = result.synthesis_plan['synthesis_plan']
                for segment_data in plan_segments:
                    segment_id = segment_data.get('segment_id')
                    if segment_id:
                        expected_segments.add(segment_id)
                synthesis_data.extend(plan_segments)
        
        # 🚀 新架构：查找已存在的AudioFile段落ID
        existing_audio_files = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.audio_type == 'segment',
            AudioFile.paragraph_index.isnot(None)
        ).all()
        
        existing_segments = set(af.paragraph_index for af in existing_audio_files)
        
        # 计算失败（缺失）的段落
        failed_segments = expected_segments - existing_segments
        
        if not failed_segments:
            return {
                "success": True,
                "message": "没有失败的段落需要重试，所有段落已完成",
                "data": {
                    "project_id": project_id,
                    "retried_segments": 0,
                    "total_segments": len(expected_segments),
                    "completed_segments": len(existing_segments)
                }
            }
        
        # 更新项目状态为处理中
        project.status = 'processing'
        db.commit()
        
        # 🚀 启动智能准备模式重新合成（只处理失败的段落）
        if synthesis_data:
            # 过滤出失败段落的数据
            failed_synthesis_data = [
                segment_data for segment_data in synthesis_data
                if segment_data.get('segment_id') in failed_segments
            ]
            
            if failed_synthesis_data:
                # 启动后台任务处理音频生成
                from app.novel_reader import process_audio_generation_from_synthesis_plan
                background_tasks.add_task(
                    process_audio_generation_from_synthesis_plan,
                    project_id,
                    failed_synthesis_data,
                    1  # 默认并行任务数为1
                )
        
        return {
            "success": True,
            "message": f"已启动重试 {len(failed_segments)} 个失败段落",
            "data": {
                "project_id": project_id,
                "retried_segments": len(failed_segments),
                "total_segments": len(expected_segments),
                "completed_segments": len(existing_segments),
                "project_status": project.status
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"重试失败段落失败: {str(e)}")

@router.get("/projects/{project_id}/failed-segments")
async def get_failed_segments(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    🚀 获取项目失败段落详情（基于AudioFile缺失判断失败）
    """
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if not project.book_id:
            raise HTTPException(status_code=400, detail="项目未关联书籍，无法获取失败段落信息")
        
        # 🚀 新架构：获取智能准备结果，确定应该有哪些段落
        from app.models import AnalysisResult, BookChapter
        analysis_results = db.query(AnalysisResult).join(
            BookChapter, AnalysisResult.chapter_id == BookChapter.id
        ).filter(
            BookChapter.book_id == project.book_id,
            AnalysisResult.status == 'completed',
            AnalysisResult.synthesis_plan.isnot(None)
        ).all()
        
        if not analysis_results:
            return {
                "success": True,
                "data": [],
                "message": "未找到智能准备结果，无法确定失败段落"
            }
        
        # 收集所有应该合成的段落信息
        expected_segments = {}  # segment_id -> segment_data
        for result in analysis_results:
            if result.synthesis_plan and 'synthesis_plan' in result.synthesis_plan:
                plan_segments = result.synthesis_plan['synthesis_plan']
                for segment_data in plan_segments:
                    segment_id = segment_data.get('segment_id')
                    if segment_id:
                        expected_segments[segment_id] = {
                            "segment_id": segment_id,
                            "text": segment_data.get('text', ''),
                            "speaker": segment_data.get('speaker', ''),
                            "voice_id": segment_data.get('voice_id'),
                            "chapter_id": result.chapter_id,
                            "chapter_number": result.chapter.chapter_number if result.chapter else None,
                            "parameters": segment_data.get('parameters', {})
                        }
        
        # 🚀 新架构：查找已存在的AudioFile段落ID
        existing_audio_files = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.audio_type == 'segment',
            AudioFile.paragraph_index.isnot(None)
        ).all()
        
        existing_segments = set(af.paragraph_index for af in existing_audio_files)
        
        # 计算失败（缺失）的段落
        failed_segments = []
        for segment_id, segment_info in expected_segments.items():
            if segment_id not in existing_segments:
                # 判断失败原因
                error_type = "synthesis_failed"
                error_message = "音频合成失败"
                
                # 检查声音配置
                voice_id = segment_info.get('voice_id')
                if not voice_id:
                    error_type = "voice_not_configured"
                    error_message = "未配置声音档案"
                else:
                    # 检查声音档案是否存在
                    voice = db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
                    if not voice:
                        error_type = "voice_not_found"
                        error_message = f"声音档案不存在 (ID: {voice_id})"
                    else:
                        # 检查声音文件是否完整
                        file_validation = voice.validate_files()
                        if not file_validation['valid']:
                            error_type = "voice_files_missing"
                            error_message = f"声音文件缺失: {', '.join(file_validation['missing_files'])}"
                
                failed_segments.append({
                    "segment_id": segment_id,
                    "index": segment_id,
                    "speaker": segment_info.get('speaker', '未知角色'),
                    "text": segment_info.get('text', '')[:100] + ("..." if len(segment_info.get('text', '')) > 100 else ""),
                    "full_text": segment_info.get('text', ''),
                    "voice_id": voice_id,
                    "chapter_id": segment_info.get('chapter_id'),
                    "chapter_number": segment_info.get('chapter_number'),
                    "error_type": error_type,
                    "error_message": error_message,
                    "parameters": segment_info.get('parameters', {}),
                    "retry_available": True
                })
        
        # 按段落ID排序
        failed_segments.sort(key=lambda x: x['segment_id'])
        
        logger.info(f"项目 {project_id} 失败段落查询: 预期{len(expected_segments)}个，已完成{len(existing_segments)}个，失败{len(failed_segments)}个")
        
        return {
            "success": True,
            "data": failed_segments,
            "summary": {
                "total_expected": len(expected_segments),
                "completed": len(existing_segments),
                "failed": len(failed_segments),
                "project_status": project.status
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取失败段落失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取失败段落失败: {str(e)}")

@router.get("/projects/{project_id}/download-partial")
async def download_partial_audio(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    下载部分完成的音频文件
    """
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 查找已完成的音频文件
        completed_audio_files = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.status == 'active',
            AudioFile.audio_type == 'segment'
        ).order_by(AudioFile.created_at).all()
        
        if not completed_audio_files:
            raise HTTPException(status_code=404, detail="没有已完成的音频文件")
        
        # 如果只有一个文件，直接返回
        if len(completed_audio_files) == 1:
            audio_file = completed_audio_files[0]
            if not os.path.exists(audio_file.file_path):
                raise HTTPException(status_code=404, detail="音频文件不存在")
            
            return FileResponse(
                audio_file.file_path,
                media_type='audio/wav',
                filename=f"{project.name}_partial.wav"
            )
        
        # 合并多个音频文件
        try:
            from pydub import AudioSegment
            import tempfile
            
            merged_audio = None
            silence = AudioSegment.silent(duration=500)  # 500ms间隔
            
            for audio_file in completed_audio_files:
                if os.path.exists(audio_file.file_path):
                    segment_audio = AudioSegment.from_wav(audio_file.file_path)
                    if merged_audio is None:
                        merged_audio = segment_audio
                    else:
                        merged_audio = merged_audio + silence + segment_audio
            
            if merged_audio is None:
                raise HTTPException(status_code=404, detail="没有有效的音频文件")
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                merged_audio.export(tmp_file.name, format="wav")
                
                return FileResponse(
                    tmp_file.name,
                    media_type='audio/wav',
                    filename=f"{project.name}_partial.wav"
                )
                
        except ImportError:
            raise HTTPException(status_code=500, detail="音频处理库未安装，无法合并音频")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"音频合并失败: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载部分音频失败: {str(e)}")

@router.get("/projects/{project_id}/download")
async def download_final_audio(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    下载最终音频文件
    对应前端下载功能
    """
    from fastapi.responses import FileResponse
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if project.status != 'completed':
            raise HTTPException(status_code=400, detail="项目尚未完成")
        
        if not project.final_audio_path:
            raise HTTPException(status_code=404, detail="最终音频文件路径不存在")
        
        # 检查文件是否存在
        if not os.path.exists(project.final_audio_path):
            logger.warning(f"音频文件不存在: {project.final_audio_path}")
            raise HTTPException(status_code=404, detail="音频文件不存在")
        
        logger.info(f"下载最终音频: 项目{project_id}, 文件: {project.final_audio_path}")
        
        return FileResponse(
            path=project.final_audio_path,
            filename=f"{project.name}_final.wav",
            media_type="audio/wav"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载音频失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")

# ====== 章节级别合成API ======
@router.post("/projects/{project_id}/chapters/{chapter_id}/start")
async def start_chapter_synthesis(
    project_id: int,
    chapter_id: int,
    background_tasks: BackgroundTasks,
    parallel_tasks: int = Form(1, description="并行任务数"),
    enable_environment: bool = Form(False, description="启用环境音混合"),
    environment_volume: float = Form(0.3, description="环境音音量"),
    db: Session = Depends(get_db)
):
    """
    开始单章节合成
    """
    try:
        # 如果启用了环境音，调用主要的 novel_reader API
        if enable_environment:
            from app.novel_reader import start_audio_generation as main_start_generation
            
            # 构造表单数据
            from fastapi import Request
            import json
            
            # 直接调用 novel_reader 的 start_audio_generation 函数
            # 但需要模拟表单参数
            class MockForm:
                def __init__(self, **kwargs):
                    self.__dict__.update(kwargs)
            
            # 使用mock参数调用主函数（绕过路由装饰器）
            from app.novel_reader import router as main_router
            from fastapi.background import BackgroundTasks as MainBackgroundTasks
            
            # 直接导入并调用函数
            from app import novel_reader
            return await novel_reader.start_audio_generation(
                project_id=project_id,
                background_tasks=background_tasks,
                parallel_tasks=parallel_tasks,
                enable_environment=enable_environment,
                environment_volume=environment_volume,
                db=db
            )
        else:
            # 普通TTS合成，调用现有逻辑
            return await start_project_generation(
                project_id=project_id,
                background_tasks=background_tasks,
                parallel_tasks=parallel_tasks,
                synthesis_mode="chapters",
                chapter_ids=str(chapter_id),
                db=db
            )
    except Exception as e:
        logger.error(f"开始章节合成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"开始章节合成失败: {str(e)}")

@router.post("/projects/{project_id}/chapters/{chapter_id}/restart")
async def restart_chapter_synthesis(
    project_id: int,
    chapter_id: int,
    background_tasks: BackgroundTasks,
    parallel_tasks: int = Form(1, description="并行任务数"),
    db: Session = Depends(get_db)
):
    """
    重新开始单章节合成
    """
    try:
        # 先重置项目状态，然后启动
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 重置相关进度（保持项目其他状态）
        project.processed_segments = 0
        project.current_segment = 0
        project.started_at = None
        project.completed_at = None
        db.commit()
        
        # 调用通用的项目启动API
        return await start_project_generation(
            project_id=project_id,
            background_tasks=background_tasks,
            parallel_tasks=parallel_tasks,
            synthesis_mode="chapters",
            chapter_ids=str(chapter_id),
            db=db
        )
    except Exception as e:
        logger.error(f"重新开始章节合成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重新开始章节合成失败: {str(e)}")

@router.post("/projects/{project_id}/chapters/{chapter_id}/resume")
async def resume_chapter_synthesis(
    project_id: int,
    chapter_id: int,
    background_tasks: BackgroundTasks,
    parallel_tasks: int = Form(1, description="并行任务数"),
    db: Session = Depends(get_db)
):
    """
    继续单章节合成
    """
    try:
        # 调用通用的恢复API，但只处理指定章节
        return await resume_generation(
            project_id=project_id,
            background_tasks=background_tasks,
            parallel_tasks=parallel_tasks,
            chapter_ids=str(chapter_id),
            db=db
        )
    except Exception as e:
        logger.error(f"继续章节合成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"继续章节合成失败: {str(e)}")

@router.post("/projects/{project_id}/chapters/{chapter_id}/retry-failed")
async def retry_chapter_failed_segments(
    project_id: int,
    chapter_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    重试单章节的失败段落
    """
    try:
        # 这里可以调用现有的重试失败段落API
        # 但需要根据章节过滤失败的段落
        return await retry_all_failed_segments(
            project_id=project_id,
            background_tasks=background_tasks,
            db=db
        )
    except Exception as e:
        logger.error(f"重试章节失败段落失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重试章节失败段落失败: {str(e)}")

@router.get("/projects/{project_id}/segments/{segment_id}/download")
async def download_segment_audio(
    project_id: int,
    segment_id: int,
    db: Session = Depends(get_db)
):
    """
    下载单个段落音频
    """
    try:
        # 查找段落对应的AudioFile
        audio_file = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.paragraph_index == segment_id,
            AudioFile.audio_type == 'segment'
        ).first()
        
        if not audio_file:
            raise HTTPException(status_code=404, detail=f"段落 {segment_id} 的音频文件不存在")
        
        if not os.path.exists(audio_file.file_path):
            raise HTTPException(status_code=404, detail="音频文件物理文件不存在")
        
        logger.info(f"下载段落音频: 项目{project_id}, 段落{segment_id}, 文件: {audio_file.file_path}")
        
        return FileResponse(
            path=audio_file.file_path,
            filename=f"segment_{segment_id}_{audio_file.character_name or 'unknown'}.wav",
            media_type="audio/wav"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载段落音频失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载段落音频失败: {str(e)}")

@router.get("/projects/{project_id}/chapters/{chapter_id}/download")
async def download_chapter_audio(
    project_id: int,
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """
    下载单章节音频
    注意：当前实现暂时返回完整项目音频，后续可以实现章节级别的音频文件
    """
    try:
        # 暂时返回完整项目音频
        # TODO: 实现章节级别的音频文件生成和下载
        return await download_final_audio(project_id=project_id, db=db)
    except Exception as e:
        logger.error(f"下载章节音频失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载章节音频失败: {str(e)}")