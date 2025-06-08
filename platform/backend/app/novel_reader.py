"""
小说朗读API模块
对应 NovelReader.vue 功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, or_, and_
from typing import Dict, List, Any, Optional
import os
import json
import time
import logging
import asyncio
import re
from datetime import datetime, timedelta

from database import get_db
from models import NovelProject, TextSegment, VoiceProfile, SystemLog, AudioFile
from tts_client import MegaTTS3Client, TTSRequest, get_tts_client
from utils import log_system_event, update_usage_stats, save_upload_file
# from tts_memory_optimizer import synthesis_context, optimize_tts_memory  # 暂时禁用以避免torch依赖

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/novel-reader", tags=["小说朗读"])

# 文件存储路径
PROJECTS_DIR = "/app/data/projects"
TEXTS_DIR = "/app/data/texts"
AUDIO_DIR = "/app/data/audio"

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
    创建新的朗读项目（支持两种方式）
    方式1：基于书籍引用 (book_id)
    方式2：直接输入文本内容 (content)
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
            from models import Book
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

            
        # 解析初始角色映射
        try:
            initial_chars = json.loads(initial_characters) if initial_characters else []
            logger.info(f"[DEBUG] 解析初始角色 - 原始: {initial_characters}")
            logger.info(f"[DEBUG] 解析初始角色 - 结果: {initial_chars}")
        except json.JSONDecodeError as e:
            logger.error(f"[DEBUG] 初始角色JSON解析失败: {e}")
            raise HTTPException(status_code=400, detail="初始角色格式错误")
        
        # 解析项目设置
        try:
            project_settings = json.loads(settings) if settings else {}
            logger.info(f"[DEBUG] 解析项目设置 - 原始: {settings}")
            logger.info(f"[DEBUG] 解析项目设置 - 结果: {project_settings}")
        except json.JSONDecodeError as e:
            logger.error(f"[DEBUG] 项目设置JSON解析失败: {e}")
            raise HTTPException(status_code=400, detail="项目设置格式错误")
        
        # 创建项目记录（支持两种方式）
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
        project.set_character_mapping(char_mapping)
        
        # 设置项目配置
        if project_settings:
            project.set_settings(project_settings)
        
        db.add(project)
        logger.info(f"[DEBUG] 项目添加到会话: {project.name}")
        
        # 不在这里提交，等待所有操作完成后一起提交
        db.flush()  # 刷新以获取项目ID
        logger.info(f"[DEBUG] 项目刷新获取ID: {project.id}")
        
        # 自动进行文本分段（使用获取到的文本内容）
        try:
            logger.info(f"[DEBUG] 开始文本分段: {project.id}")
            segments_count = await auto_segment_text_no_commit(project.id, text_content, db)
            logger.info(f"项目 {project.id} 分段完成，分段数量: {segments_count}")
        except Exception as seg_error:
            logger.error(f"项目分段失败: {str(seg_error)}")
            # 分段失败不影响项目创建，可以后续手动分段
            segments_count = 0
        
        # 记录创建日志
        try:
            logger.info(f"[DEBUG] 开始记录创建日志: {project.id}")
            await log_system_event(
                db=db,
                level="info",
                message=f"朗读项目创建: {name}",
                module="novel_reader",
                details={
                    "project_id": project.id,
                    "book_id": book_id,
                    "book_title": book.title,
                    "text_length": len(book.content),
                    "initial_character_count": len(initial_chars),
                    "segments_count": segments_count
                }
            )
            logger.info(f"[DEBUG] 创建日志记录完成: {project.id}")
        except Exception as log_error:
            logger.error(f"创建日志记录失败: {str(log_error)}")
            # 日志失败不影响项目创建
        
        # 最终一次性提交所有更改
        try:
            db.commit()
            logger.info(f"[DEBUG] 最终提交完成: {project.id}")
        except Exception as final_commit_error:
            logger.error(f"最终提交失败: {str(final_commit_error)}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"保存项目失败: {str(final_commit_error)}")
        
        return {
            "success": True,
            "message": "项目创建成功",
            "data": project.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")

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
        project_list = [project.to_dict() for project in projects]
        
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
        logger.error(f"获取项目列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取列表失败: {str(e)}")

@router.get("/projects/{project_id}")
async def get_project_detail(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取项目详情
    对应前端项目详情页功能
    """
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        project_data = project.to_dict()
        
        # 获取关联的书籍信息
        book_info = None
        book_content_length = 0
        if hasattr(project, 'book_id') and project.book_id:
            from models import Book
            book = db.query(Book).filter(Book.id == project.book_id).first()
            if book:
                book_info = {
                    "id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "word_count": book.word_count,
                    "status": book.status,
                    "description": book.description
                }
                book_content_length = len(book.content) if book.content else 0
        
        # 获取文本段落列表
        segments = db.query(TextSegment).filter(
            TextSegment.project_id == project_id
        ).order_by(TextSegment.segment_order).all()
        
        project_data['segments'] = [segment.to_dict() for segment in segments]
        project_data['book'] = book_info  # 添加书籍信息
        
        # 统计信息（兼容旧项目的original_text和新项目的book引用）
        total_chars = book_content_length if book_content_length > 0 else (
            len(project.original_text) if hasattr(project, 'original_text') and project.original_text else 0
        )
        
        project_data['statistics'] = {
            "totalCharacters": total_chars,
            "totalSegments": len(segments),
            "completedSegments": len([s for s in segments if s.status == 'completed']),
            "failedSegments": len([s for s in segments if s.status == 'failed']),
            "pendingSegments": len([s for s in segments if s.status == 'pending']),
            "processingSegments": len([s for s in segments if s.status == 'processing'])
        }
        
        return {
            "success": True,
            "data": project_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取详情失败: {str(e)}")

@router.put("/projects/{project_id}")
async def update_project(
    project_id: int,
    name: str = Form(...),
    description: str = Form(""),
    character_mapping: str = Form("{}"),
    db: Session = Depends(get_db)
):
    """
    更新项目信息
    对应前端项目编辑功能
    """
    try:
        logger.info(f"[DEBUG] PUT请求开始 - project_id: {project_id}")
        logger.info(f"[DEBUG] 参数 - name: {name}, description: {description}")
        logger.info(f"[DEBUG] character_mapping原始值: {character_mapping}")
        logger.info(f"[DEBUG] character_mapping类型: {type(character_mapping)}")
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 检查名称重复（排除自己）
        logger.info(f"[DEBUG] 检查名称重复...")
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
            logger.info(f"[DEBUG] 解析角色映射 - 类型: {type(char_mapping)}")
        except json.JSONDecodeError as e:
            logger.error(f"[DEBUG] 角色映射JSON解析失败: {e}")
            raise HTTPException(status_code=400, detail="角色映射格式错误")
        
        # 更新项目信息
        old_name = project.name
        project.name = name
        project.description = description
        project.set_character_mapping(char_mapping)
        
        # 更新相关段落的声音分配（不自动提交）
        if char_mapping:
            await update_segments_voice_mapping_no_commit(project_id, char_mapping, db)
        
        # 记录更新日志（不自动提交）
        try:
            await log_system_event(
                db=db,
                level="info",
                message=f"项目更新: {old_name} -> {name}",
                module="novel_reader",
                details={
                    "project_id": project_id,
                    "old_name": old_name,
                    "new_name": name,
                    "character_mapping": char_mapping
                }
            )
        except Exception as log_error:
            logger.error(f"记录更新日志失败: {str(log_error)}")
            # 日志失败不影响项目更新
        
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
            "data": project.to_dict()
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
    force: bool = Query(False, description="强制删除"),
    db: Session = Depends(get_db)
):
    """
    删除项目
    对应前端项目删除功能
    """
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 检查是否正在处理中
        if not force and project.status == 'processing':
            raise HTTPException(status_code=400, detail="项目正在处理中，请使用强制删除")
        
        project_name = project.name
        
        # 删除相关文件
        files_to_delete = []
        
        # 删除最终音频文件
        if project.final_audio_path and os.path.exists(project.final_audio_path):
            files_to_delete.append(project.final_audio_path)
        
        # 删除所有段落的音频文件
        segments = db.query(TextSegment).filter(TextSegment.project_id == project_id).all()
        for segment in segments:
            if segment.audio_file_path and os.path.exists(segment.audio_file_path):
                files_to_delete.append(segment.audio_file_path)
        
        # 删除AudioFile表中的关联记录
        from models import AudioFile
        audio_files = db.query(AudioFile).filter(AudioFile.project_id == project_id).all()
        for audio_file in audio_files:
            if audio_file.file_path and os.path.exists(audio_file.file_path):
                if audio_file.file_path not in files_to_delete:
                    files_to_delete.append(audio_file.file_path)
            db.delete(audio_file)
        
        # 删除数据库记录（级联删除段落）
        db.delete(project)
        db.commit()
        
        # 删除物理文件
        deleted_files = []
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
                deleted_files.append(file_path)
            except Exception as e:
                logger.warning(f"删除文件失败 {file_path}: {str(e)}")
        
        # 记录删除日志
        await log_system_event(
            db=db,
            level="info",
            message=f"项目删除: {project_name}",
            module="novel_reader",
            details={
                "project_id": project_id,
                "project_name": project_name,
                "deleted_files": len(deleted_files),
                "force": force
            }
        )
        
        return {
            "success": True,
            "message": f"项目 '{project_name}' 删除成功",
            "deletedFiles": len(deleted_files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@router.post("/projects/{project_id}/segments")
async def regenerate_segments(
    project_id: int,
    strategy: str = Form("auto", description="分段策略"),
    custom_rules: str = Form("", description="自定义规则"),
    db: Session = Depends(get_db)
):
    """
    重新生成文本段落
    对应前端重新分段功能
    """
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if project.status == 'processing':
            raise HTTPException(status_code=400, detail="项目正在处理中，无法重新分段")
        
        # 删除现有段落
        db.query(TextSegment).filter(TextSegment.project_id == project_id).delete()
        db.commit()
        
        # 重新分段
        segments_created = await segment_text_by_strategy(
            project.original_text, 
            project_id, 
            strategy, 
            custom_rules,
            db
        )
        
        # 更新项目状态
        project.total_segments = segments_created
        project.processed_segments = 0
        project.current_segment = 0
        project.status = 'pending'
        db.commit()
        
        # 记录重新分段日志
        await log_system_event(
            db=db,
            level="info",
            message=f"项目重新分段: {project.name}",
            module="novel_reader",
            details={
                "project_id": project_id,
                "strategy": strategy,
                "segments_created": segments_created
            }
        )
        
        return {
            "success": True,
            "message": f"重新分段完成，生成 {segments_created} 个段落",
            "segmentsCount": segments_created
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新分段失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分段失败: {str(e)}")

@router.post("/projects/{project_id}/start-generation")
async def start_audio_generation(
    project_id: int,
    background_tasks: BackgroundTasks,
    parallel_tasks: int = Form(1, description="并行任务数"),
    db: Session = Depends(get_db)
):
    """
    开始音频生成
    对应前端开始生成功能
    """
    logger.info(f"[DEBUG] 开始音频生成请求: project_id={project_id}, parallel_tasks={parallel_tasks}")
    
    try:
        # 查询项目
        logger.info(f"[DEBUG] 查询项目 {project_id}...")
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        
        if not project:
            logger.error(f"[DEBUG] 项目 {project_id} 不存在")
            raise HTTPException(status_code=404, detail="项目不存在")
        
        logger.info(f"[DEBUG] 找到项目: {project.name}, 状态: {project.status}")
        
        if project.status == 'processing':
            logger.warning(f"[DEBUG] 项目已在处理中: {project.id}")
            raise HTTPException(status_code=400, detail="项目已在处理中")
        
        # 检查段落
        logger.info(f"[DEBUG] 检查项目段落...")
        segments = db.query(TextSegment).filter(TextSegment.project_id == project_id).all()
        logger.info(f"[DEBUG] 找到 {len(segments)} 个段落")
        
        if not segments:
            logger.error(f"[DEBUG] 项目 {project_id} 没有段落")
            raise HTTPException(status_code=400, detail="项目没有文本段落，请先进行分段")
        
        # 检查角色映射 - 增加详细日志
        logger.info(f"[DEBUG] 检查角色映射...")
        logger.info(f"[DEBUG] 原始 character_mapping 字段: {project.character_mapping}")
        logger.info(f"[DEBUG] character_mapping 类型: {type(project.character_mapping)}")
        
        char_mapping = project.get_character_mapping()
        logger.info(f"[DEBUG] 解析后的角色映射: {char_mapping}")
        logger.info(f"[DEBUG] 角色映射类型: {type(char_mapping)}")
        logger.info(f"[DEBUG] 角色映射是否为空: {not char_mapping}")
        
        if not char_mapping:
            logger.error(f"[DEBUG] 角色映射为空，拒绝请求")
            # 详细显示段落信息
            for segment in segments[:3]:  # 只显示前3个段落
                logger.error(f"[DEBUG] 段落 {segment.segment_order}: speaker='{segment.detected_speaker}', voice_id={segment.voice_profile_id}")
            raise HTTPException(status_code=400, detail="请先设置角色声音映射")
        
        # 验证声音映射的有效性
        logger.info(f"[DEBUG] 验证声音映射有效性...")
        for character, voice_id in char_mapping.items():
            logger.info(f"[DEBUG] 验证角色 '{character}' -> 声音ID {voice_id}")
            voice = db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
            if not voice or voice.status != 'active':
                logger.error(f"[DEBUG] 角色 '{character}' 的声音档案无效: voice={voice}, status={voice.status if voice else None}")
                raise HTTPException(status_code=400, detail=f"角色 '{character}' 的声音档案无效")
            logger.info(f"[DEBUG] 声音档案验证通过: {voice.name}")
        
        logger.info(f"[DEBUG] 所有验证通过，开始更新项目状态...")
        
        # 更新项目状态
        project.status = 'processing'
        project.started_at = datetime.utcnow()
        project.current_segment = 0
        project.processed_segments = 0
        
        # 重置所有段落状态
        logger.info(f"[DEBUG] 重置段落状态...")
        for segment in segments:
            if segment.status in ['completed', 'failed']:
                segment.status = 'pending'
                segment.error_message = None
        
        logger.info(f"[DEBUG] 提交数据库更改...")
        db.commit()
        
        logger.info(f"[DEBUG] 启动后台任务...")
        # 启动后台任务
        background_tasks.add_task(
            process_audio_generation,
            project_id,
            parallel_tasks
        )
        
        # 记录开始生成日志
        await log_system_event(
            db=db,
            level="info",
            message=f"开始音频生成: {project.name}",
            module="novel_reader",
            details={
                "project_id": project_id,
                "total_segments": len(segments),
                "parallel_tasks": parallel_tasks,
                "character_mapping": char_mapping
            }
        )
        
        logger.info(f"[DEBUG] 音频生成启动成功")
        
        return {
            "success": True,
            "message": "音频生成已开始",
            "totalSegments": len(segments),
            "parallelTasks": parallel_tasks
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DEBUG] 开始音频生成异常: {str(e)}")
        import traceback
        logger.error(f"[DEBUG] 详细错误信息: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"启动失败: {str(e)}")

@router.post("/projects/{project_id}/pause")
async def pause_generation(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    暂停音频生成
    对应前端暂停功能
    """
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if project.status != 'processing':
            raise HTTPException(status_code=400, detail="项目未在处理中")
        
        # 更新项目状态
        project.status = 'paused'
        db.commit()
        
        # 记录暂停日志
        await log_system_event(
            db=db,
            level="info",
            message=f"音频生成暂停: {project.name}",
            module="novel_reader",
            details={
                "project_id": project_id,
                "processed_segments": project.processed_segments,
                "total_segments": project.total_segments
            }
        )
        
        return {
            "success": True,
            "message": "音频生成已暂停"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"暂停生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"暂停失败: {str(e)}")

@router.post("/projects/{project_id}/resume")
async def resume_generation(
    project_id: int,
    background_tasks: BackgroundTasks,
    parallel_tasks: int = Form(1, description="并行任务数"),
    db: Session = Depends(get_db)
):
    """
    恢复音频生成
    对应前端恢复功能
    """
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if project.status != 'paused':
            raise HTTPException(status_code=400, detail="项目未处于暂停状态")
        
        # 更新项目状态
        project.status = 'processing'
        db.commit()
        
        # 重新启动后台任务
        background_tasks.add_task(
            process_audio_generation,
            project_id,
            parallel_tasks
        )
        
        # 记录恢复日志
        await log_system_event(
            db=db,
            level="info",
            message=f"音频生成恢复: {project.name}",
            module="novel_reader",
            details={
                "project_id": project_id,
                "parallel_tasks": parallel_tasks
            }
        )
        
        return {
            "success": True,
            "message": "音频生成已恢复"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"恢复失败: {str(e)}")

@router.get("/projects/{project_id}/progress")
async def get_generation_progress(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取生成进度
    对应前端进度监控功能
    """
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 获取段落统计
        segments = db.query(TextSegment).filter(TextSegment.project_id == project_id).all()
        
        stats = {
            "total": len(segments),
            "completed": len([s for s in segments if s.status == 'completed']),
            "failed": len([s for s in segments if s.status == 'failed']),
            "processing": len([s for s in segments if s.status == 'processing']),
            "pending": len([s for s in segments if s.status == 'pending'])
        }
        
        # 计算进度百分比
        progress_percent = 0
        if stats["total"] > 0:
            progress_percent = round((stats["completed"] / stats["total"]) * 100, 1)
        
        # 估算剩余时间
        estimated_completion = None
        if project.started_at and stats["completed"] > 0:
            try:
                # 确保时间戳兼容性
                now = datetime.utcnow()
                started_at = project.started_at
                
                # 如果started_at是aware datetime，转换为naive
                if started_at.tzinfo is not None:
                    started_at = started_at.replace(tzinfo=None)
                
                elapsed_time = now - started_at
                avg_time_per_segment = elapsed_time.total_seconds() / stats["completed"]
                remaining_segments = stats["total"] - stats["completed"]
                remaining_seconds = avg_time_per_segment * remaining_segments
                estimated_completion = (now + timedelta(seconds=remaining_seconds)).isoformat()
            except Exception as time_error:
                logger.warning(f"时间计算错误: {time_error}")
                estimated_completion = None
        
        # 最近完成的段落
        recent_completed = db.query(TextSegment).filter(
            and_(
                TextSegment.project_id == project_id,
                TextSegment.status == 'completed'
            )
        ).order_by(desc(TextSegment.id)).limit(5).all()
        
        recent_list = [
            {
                "id": segment.id,
                "order": segment.segment_order,
                "speaker": segment.detected_speaker,
                "processingTime": segment.processing_time
            }
            for segment in recent_completed
        ]
        
        return {
            "success": True,
            "progress": {
                "projectId": project_id,
                "status": project.status,
                "progressPercent": progress_percent,
                "statistics": stats,
                "startedAt": project.started_at.isoformat() if project.started_at else None,
                "estimatedCompletion": estimated_completion,
                "recentCompleted": recent_list
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取进度失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取进度失败: {str(e)}")

@router.get("/projects/{project_id}/download")
async def download_final_audio(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    下载最终音频文件
    对应前端下载功能
    """
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if project.status != 'completed':
            raise HTTPException(status_code=400, detail="项目尚未完成")
        
        if not project.final_audio_path or not os.path.exists(project.final_audio_path):
            raise HTTPException(status_code=404, detail="音频文件不存在")
        
        # 记录下载日志
        await log_system_event(
            db=db,
            level="info",
            message=f"下载最终音频: {project.name}",
            module="novel_reader",
            details={
                "project_id": project_id,
                "file_path": project.final_audio_path
            }
        )
        
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

# 工具函数

async def auto_segment_text(project_id: int, db: Session):
    """自动分段"""
    return await segment_text_by_strategy("", project_id, "auto", "", db)

async def auto_segment_text_no_commit(project_id: int, text: str, db: Session):
    """自动分段 - 不提交版本，用于项目创建流程"""
    return await segment_text_by_strategy_no_commit(text, project_id, "auto", "", db)

async def segment_text_by_strategy_no_commit(
    text: str, 
    project_id: int, 
    strategy: str, 
    custom_rules: str,
    db: Session
) -> int:
    """根据策略分段文本 - 不提交版本"""
    try:
        if not text:
            logger.warning("分段文本为空")
            return 0
        
        segments = []
        
        if strategy == "auto":
            # 自动分段：基于句号、感叹号、问号分段
            sentences = re.split(r'[。！？]', text)
            for i, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if sentence:
                    segments.append({
                        "order": i + 1,
                        "text": sentence + ("。" if i < len(sentences) - 1 else ""),
                        "speaker": detect_speaker(sentence)
                    })
        
        elif strategy == "paragraph":
            # 段落分段：基于换行符分段
            paragraphs = text.split('\n')
            order = 1
            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                if paragraph:
                    segments.append({
                        "order": order,
                        "text": paragraph,
                        "speaker": detect_speaker(paragraph)
                    })
                    order += 1
        
        elif strategy == "dialogue":
            # 对话分段：识别对话和叙述分开
            lines = text.split('\n')
            order = 1
            for line in lines:
                line = line.strip()
                if line:
                    segments.append({
                        "order": order,
                        "text": line,
                        "speaker": detect_speaker(line)
                    })
                    order += 1
        
        # 保存段落到数据库（不提交）
        for segment_data in segments:
            segment = TextSegment(
                project_id=project_id,
                segment_order=segment_data["order"],
                text_content=segment_data["text"],
                detected_speaker=segment_data["speaker"],
                status='pending'
            )
            db.add(segment)
        
        # 只刷新，不提交
        db.flush()
        logger.info(f"[DEBUG] 段落添加到会话，数量: {len(segments)}")
        return len(segments)
        
    except Exception as e:
        logger.error(f"文本分段失败: {str(e)}")
        return 0

async def segment_text_by_strategy(
    text: str, 
    project_id: int, 
    strategy: str, 
    custom_rules: str,
    db: Session
) -> int:
    """根据策略分段文本"""
    try:
        # 获取项目文本
        if not text:
            project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
            if not project or not project.original_text:
                return 0
            text = project.original_text
        
        segments = []
        
        if strategy == "auto":
            # 自动分段：基于句号、感叹号、问号分段
            sentences = re.split(r'[。！？]', text)
            for i, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if sentence:
                    segments.append({
                        "order": i + 1,
                        "text": sentence + ("。" if i < len(sentences) - 1 else ""),
                        "speaker": detect_speaker(sentence)
                    })
        
        elif strategy == "paragraph":
            # 段落分段：基于换行符分段
            paragraphs = text.split('\n')
            order = 1
            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                if paragraph:
                    segments.append({
                        "order": order,
                        "text": paragraph,
                        "speaker": detect_speaker(paragraph)
                    })
                    order += 1
        
        elif strategy == "dialogue":
            # 对话分段：识别对话和叙述分开
            lines = text.split('\n')
            order = 1
            for line in lines:
                line = line.strip()
                if line:
                    segments.append({
                        "order": order,
                        "text": line,
                        "speaker": detect_speaker(line)
                    })
                    order += 1
        
        elif strategy == "custom":
            # 自定义分段规则
            if custom_rules:
                try:
                    rules = json.loads(custom_rules)
                    delimiter = rules.get("delimiter", "。")
                    max_length = rules.get("max_length", 200)
                    
                    parts = text.split(delimiter)
                    current_segment = ""
                    order = 1
                    
                    for part in parts:
                        part = part.strip()
                        if not part:
                            continue
                        
                        if len(current_segment + part) <= max_length:
                            current_segment += part + delimiter
                        else:
                            if current_segment:
                                segments.append({
                                    "order": order,
                                    "text": current_segment.rstrip(delimiter),
                                    "speaker": detect_speaker(current_segment)
                                })
                                order += 1
                            current_segment = part + delimiter
                    
                    # 添加最后一个段落
                    if current_segment:
                        segments.append({
                            "order": order,
                            "text": current_segment.rstrip(delimiter),
                            "speaker": detect_speaker(current_segment)
                        })
                        
                except json.JSONDecodeError:
                    # 如果自定义规则解析失败，使用自动分段
                    return await segment_text_by_strategy(text, project_id, "auto", "", db)
        
        # 保存段落到数据库
        for segment_data in segments:
            segment = TextSegment(
                project_id=project_id,
                segment_order=segment_data["order"],
                text_content=segment_data["text"],
                detected_speaker=segment_data["speaker"],
                status='pending'
            )
            db.add(segment)
        
        db.commit()
        return len(segments)
        
    except Exception as e:
        logger.error(f"文本分段失败: {str(e)}")
        return 0

def detect_speaker(text: str) -> str:
    """检测说话人"""
    try:
        # 清理文本
        text = text.strip()
        if not text:
            return "温柔女声"
        
        # 1. 检测直接引语模式："小明说：'你好'"
        direct_quote_patterns = [
            r'^([^""''「」『』：:，。！？\s]{1,6})[说道讲叫喊问答回复表示][:：][""''「」『』]',
            r'^([^""''「」『』：:，。！？\s]{1,6})[说道讲叫喊问答回复表示]，[""''「」『』]',
            r'^([^""''「」『』：:，。！？\s]{1,6})[:：][""''「」『』]',
        ]
        
        for pattern in direct_quote_patterns:
            match = re.search(pattern, text)
            if match:
                speaker = match.group(1).strip()
                if len(speaker) <= 6 and speaker and not any(char in speaker for char in '。，！？；'):
                    # 验证是否像人名
                    if re.match(r'^[一-龯]{2,4}$', speaker) or re.match(r'^[A-Za-z\s]{2,8}$', speaker):
                        return speaker
        
        # 2. 检测对话标记："小明："
        speaker_mark_patterns = [
            r'^([^：:，。！？\s]{2,6})[:：]',
        ]
        
        for pattern in speaker_mark_patterns:
            match = re.search(pattern, text)
            if match:
                speaker = match.group(1).strip()
                if len(speaker) <= 6 and speaker and not any(char in speaker for char in '。，！？；'):
                    # 验证是否像人名
                    if re.match(r'^[一-龯]{2,4}$', speaker) or re.match(r'^[A-Za-z\s]{2,8}$', speaker):
                        return speaker
        
        # 3. 检测包含引号的对话
        if any(quote in text for quote in ['"', '"', '"', '「', '」', '『', '』', "'", "'"]):
            # 尝试提取说话人 - 更严格的模式
            quote_patterns = [
                r'^([^""''「」『』，。！？\s]{2,6})[^""''「」『』]{0,10}[""''「」『』]',
                r'[""''「」『』][^""''「」『』]+[""''「」『』][^，。！？]*?([^，。！？\s]{2,6})[说道]',
            ]
            
            for pattern in quote_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    for speaker in matches:
                        speaker = speaker.strip()
                        if len(speaker) <= 6 and speaker and not any(char in speaker for char in '。，！？；'):
                            # 严格验证是否像人名
                            if re.match(r'^[一-龯]{2,4}$', speaker) or re.match(r'^[A-Za-z\s]{2,8}$', speaker):
                                return speaker
        
        # 4. 检测常见对话动词后的内容 - 更严格
        dialogue_patterns = [
            r'^([^，。！？\s]{2,6})[说道讲叫喊问答回复表示]',
        ]
        
        for pattern in dialogue_patterns:
            match = re.search(pattern, text)
            if match:
                speaker = match.group(1).strip()
                if len(speaker) <= 6 and speaker and not any(char in speaker for char in '。，！？；'):
                    # 严格验证是否像人名
                    if re.match(r'^[一-龯]{2,4}$', speaker) or re.match(r'^[A-Za-z\s]{2,8}$', speaker):
                        return speaker
        
        # 5. 检测姓名模式 - 更保守，排除叙述性开头
        name_patterns = [
            r'^([一-龯]{2,4})[^一-龯]',  # 开头的中文姓名
            r'^([A-Z][a-z]+)[^a-z]',   # 开头的英文名
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                speaker = match.group(1).strip()
                # 排除常见的非人名词汇和叙述性开头
                excluded_words = [
                    '这个', '那个', '什么', '哪里', '为什么', '怎么', '可是', '但是', '所以', '因为', '如果', '虽然',
                    '遇到', '慢慢', '而这', '这一', '那一', '当他', '当她', '此时', '此后', '然后', '接着', '最后',
                    '林晓', '苏然', '陈宇', '从那', '经过', '虽然', '尽管', '无奈', '正发', '神奇', '在一', '而这'
                ]
                if speaker not in excluded_words and len(speaker) <= 4:
                    # 进一步验证：必须是真正的人名格式
                    if re.match(r'^[一-龯]{2,3}$', speaker) and not any(word in speaker for word in ['之后', '以后', '开始', '结束', '时候', '地方']):
                        return speaker
        
        # 默认返回温柔女声（确保存在的声音档案）
        return "温柔女声"
        
    except Exception:
        return "温柔女声"

async def update_segments_voice_mapping(project_id: int, char_mapping: Dict[str, str], db: Session):
    """更新段落的声音映射"""
    try:
        segments = db.query(TextSegment).filter(TextSegment.project_id == project_id).all()
        
        for segment in segments:
            if segment.detected_speaker in char_mapping:
                voice_id = char_mapping[segment.detected_speaker]
                # 验证声音ID是否有效
                voice = db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
                if voice and voice.status == 'active':
                    segment.voice_profile_id = voice_id
        
        db.commit()
        
    except Exception as e:
        logger.error(f"更新声音映射失败: {str(e)}")

async def process_audio_generation(project_id: int, parallel_tasks: int = 1):
    """后台音频生成任务 - 修改为真正的逐个处理"""
    try:
        from database import SessionLocal
        db = SessionLocal()
        
        try:
            project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
            if not project:
                return
            
            logger.info(f"[GENERATION] 开始音频生成: 项目 {project_id}, 并行数: {parallel_tasks}")
            
            # 获取TTS客户端
            tts_client = get_tts_client()
            
            # 处理逻辑：不再并发所有任务，而是分批处理
            while True:
                # 检查项目状态
                project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
                if not project or project.status != 'processing':
                    logger.info(f"[GENERATION] 项目状态变更，停止处理: {project.status if project else 'None'}")
                    break
                
                # 获取下一批待处理的段落（限制数量）
                pending_segments = db.query(TextSegment).filter(
                    and_(
                        TextSegment.project_id == project_id,
                        TextSegment.status == 'pending'
                    )
                ).order_by(TextSegment.segment_order).limit(parallel_tasks).all()
                
                if not pending_segments:
                    logger.info(f"[GENERATION] 没有待处理段落，检查完成状态")
                    # 检查是否全部完成
                    await check_project_completion(project_id, db)
                    break
                
                logger.info(f"[GENERATION] 处理批次: {len(pending_segments)} 个段落")
                
                # 强制顺序处理，避免显存不足
                if parallel_tasks == 1:
                    # 单线程顺序处理
                    for segment in pending_segments:
                        try:
                            logger.info(f"[GENERATION] 顺序处理段落 {segment.id}")
                            await process_single_segment_sequential(segment, tts_client, db)
                        except Exception as e:
                            logger.error(f"[GENERATION] 段落 {segment.id} 处理失败: {e}")
                else:
                    # 并发处理（仅当parallel_tasks > 1时）
                    semaphore = asyncio.Semaphore(parallel_tasks)
                    tasks = []
                    
                    for segment in pending_segments:
                        task = asyncio.create_task(
                            process_single_segment(segment, tts_client, semaphore, db)
                        )
                        tasks.append(task)
                    
                    # 等待这一批完成
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # 检查结果
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            logger.error(f"[GENERATION] 段落 {pending_segments[i].id} 处理失败: {result}")
                
                # 短暂休息，避免过度占用资源
                await asyncio.sleep(0.5)
            
            # 最终检查项目完成状态
            await check_project_completion(project_id, db)
            logger.info(f"[GENERATION] 音频生成完成: 项目 {project_id}")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[GENERATION] 音频生成后台任务失败: {str(e)}")
        import traceback
        logger.error(f"[GENERATION] 详细错误: {traceback.format_exc()}")

async def process_single_segment_sequential(segment: TextSegment, tts_client, db: Session):
    """顺序处理单个段落 - 无并发，专用于避免显存不足"""
    try:
        logger.info(f"[SEGMENT] 开始顺序处理段落 {segment.id}: {segment.text_content[:30]}...")
        
        # 更新段落状态
        segment.status = 'processing'
        db.commit()
        
        # 获取声音档案
        voice = db.query(VoiceProfile).filter(VoiceProfile.id == segment.voice_profile_id).first()
        if not voice:
            logger.error(f"[SEGMENT] 段落 {segment.id} 声音档案不存在: {segment.voice_profile_id}")
            segment.status = 'failed'
            segment.error_message = "声音档案不存在"
            db.commit()
            return
        
        # 检查声音文件
        if not voice.reference_audio_path or not os.path.exists(voice.reference_audio_path):
            logger.error(f"[SEGMENT] 段落 {segment.id} 声音文件不存在: {voice.reference_audio_path}")
            segment.status = 'failed'
            segment.error_message = "声音文件不存在"
            db.commit()
            return
        
        # 生成音频文件路径
        import uuid
        audio_filename = f"segment_{segment.id}_{uuid.uuid4().hex}.wav"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)
        
        # 确保目录存在
        os.makedirs(AUDIO_DIR, exist_ok=True)
        
        # 构建TTS请求
        start_time = time.time()
        tts_request = TTSRequest(
            text=segment.text_content,
            reference_audio_path=voice.reference_audio_path,
            output_audio_path=audio_path,
            time_step=20,  # 使用稳定的参数
            p_weight=1.0,
            t_weight=1.0,
            latent_file_path=voice.latent_file_path
        )
        
        logger.info(f"[SEGMENT] 调用TTS服务处理段落 {segment.id}")
        
        # 调用TTS服务
        response = await tts_client.synthesize_speech(tts_request)
        processing_time = time.time() - start_time
        
        if response.success:
            logger.info(f"[SEGMENT] 段落 {segment.id} TTS合成成功，耗时 {processing_time:.2f}s")
            
            # 验证生成的音频文件
            if os.path.exists(audio_path):
                file_size = os.path.getsize(audio_path)
                logger.info(f"[SEGMENT] 音频文件生成: {audio_path} ({file_size} bytes)")
                
                # 获取音频时长
                try:
                    from utils import get_audio_duration
                    duration = get_audio_duration(audio_path)
                except:
                    duration = 0.0
                
                # 更新段落记录
                segment.audio_file_path = audio_path
                segment.status = 'completed'
                segment.processing_time = processing_time
                segment.completed_at = datetime.utcnow()
                segment.error_message = None
                
                # 创建AudioFile记录
                audio_file = AudioFile(
                    filename=os.path.basename(audio_path),
                    original_name=f"段落{segment.segment_order}_{segment.detected_speaker or '未知'}",
                    file_path=audio_path,
                    file_size=file_size,
                    duration=duration,
                    project_id=segment.project_id,
                    segment_id=segment.id,
                    voice_profile_id=segment.voice_profile_id,
                    text_content=segment.text_content,
                    audio_type='segment',
                    processing_time=processing_time,
                    model_used='MegaTTS3',
                    status='active',
                    created_at=datetime.utcnow()
                )
                db.add(audio_file)
                
                # 更新声音档案使用计数
                if voice.usage_count is None:
                    voice.usage_count = 0
                voice.usage_count += 1
                voice.last_used = datetime.utcnow()
                
                db.commit()
                logger.info(f"[SEGMENT] 段落 {segment.id} 顺序处理完成，已创建AudioFile记录 ID: {audio_file.id}")
                
            else:
                logger.error(f"[SEGMENT] 段落 {segment.id} 音频文件未生成: {audio_path}")
                segment.status = 'failed'
                segment.error_message = f"音频文件未生成: {response.message}"
                db.commit()
        else:
            logger.error(f"[SEGMENT] 段落 {segment.id} TTS合成失败: {response.message}")
            segment.status = 'failed'
            segment.error_message = f"TTS合成失败: {response.message}"
            db.commit()
            
    except Exception as e:
        logger.error(f"[SEGMENT] 段落 {segment.id} 顺序处理异常: {str(e)}")
        import traceback
        logger.error(f"[SEGMENT] 详细错误: {traceback.format_exc()}")
        
        segment.status = 'failed'
        segment.error_message = f"处理异常: {str(e)}"
        db.commit()

async def process_single_segment(segment: TextSegment, tts_client, semaphore, db: Session):
    """处理单个段落 - 增加更多错误处理"""
    async with semaphore:
        try:
            logger.info(f"[SEGMENT] 开始处理段落 {segment.id}: {segment.text_content[:30]}...")
            
            # 更新段落状态
            segment.status = 'processing'
            db.commit()
            
            # 获取声音档案
            voice = db.query(VoiceProfile).filter(VoiceProfile.id == segment.voice_profile_id).first()
            if not voice:
                logger.error(f"[SEGMENT] 段落 {segment.id} 声音档案不存在: {segment.voice_profile_id}")
                segment.status = 'failed'
                segment.error_message = "声音档案不存在"
                db.commit()
                return
            
            # 检查声音文件
            if not voice.reference_audio_path or not os.path.exists(voice.reference_audio_path):
                logger.error(f"[SEGMENT] 段落 {segment.id} 声音文件不存在: {voice.reference_audio_path}")
                segment.status = 'failed'
                segment.error_message = "声音文件不存在"
                db.commit()
                return
            
            # 生成音频文件路径
            import uuid
            audio_filename = f"segment_{segment.id}_{uuid.uuid4().hex}.wav"
            audio_path = os.path.join(AUDIO_DIR, audio_filename)
            
            # 确保目录存在
            os.makedirs(AUDIO_DIR, exist_ok=True)
            
            # 构建TTS请求
            start_time = time.time()
            tts_request = TTSRequest(
                text=segment.text_content,
                reference_audio_path=voice.reference_audio_path,
                output_audio_path=audio_path,
                time_step=20,  # 使用稳定的参数
                p_weight=1.0,
                t_weight=1.0,
                latent_file_path=voice.latent_file_path
            )
            
            logger.info(f"[SEGMENT] 调用TTS服务处理段落 {segment.id}")
            
            # 调用TTS服务
            response = await tts_client.synthesize_speech(tts_request)
            processing_time = time.time() - start_time
            
            if response.success:
                logger.info(f"[SEGMENT] 段落 {segment.id} TTS合成成功，耗时 {processing_time:.2f}s")
                
                # 验证生成的音频文件
                if os.path.exists(audio_path):
                    file_size = os.path.getsize(audio_path)
                    logger.info(f"[SEGMENT] 音频文件生成: {audio_path} ({file_size} bytes)")
                    
                    # 获取音频时长
                    try:
                        from utils import get_audio_duration
                        duration = get_audio_duration(audio_path)
                    except:
                        duration = 0.0
                    
                    # 更新段落记录
                    segment.audio_file_path = audio_path
                    segment.status = 'completed'
                    segment.processing_time = processing_time
                    segment.completed_at = datetime.utcnow()
                    segment.error_message = None
                    
                    # 创建AudioFile记录 - 修复数据库脱节问题
                    audio_file = AudioFile(
                        filename=os.path.basename(audio_path),
                        original_name=f"段落{segment.segment_order}_{segment.detected_speaker or '未知'}",
                        file_path=audio_path,
                        file_size=file_size,
                        duration=duration,
                        project_id=segment.project_id,
                        segment_id=segment.id,
                        voice_profile_id=segment.voice_profile_id,
                        text_content=segment.text_content,
                        audio_type='segment',
                        processing_time=processing_time,
                        model_used='MegaTTS3',
                        status='active',
                        created_at=datetime.utcnow()
                    )
                    db.add(audio_file)
                    
                    # 更新声音档案使用计数 - 修复NoneType错误
                    if voice.usage_count is None:
                        voice.usage_count = 0
                    voice.usage_count += 1
                    voice.last_used = datetime.utcnow()
                    
                    db.commit()
                    logger.info(f"[SEGMENT] 段落 {segment.id} 处理完成，已创建AudioFile记录 ID: {audio_file.id}")
                    
                else:
                    logger.error(f"[SEGMENT] 段落 {segment.id} 音频文件未生成: {audio_path}")
                    segment.status = 'failed'
                    segment.error_message = f"音频文件未生成: {response.message}"
                    db.commit()
            else:
                logger.error(f"[SEGMENT] 段落 {segment.id} TTS合成失败: {response.message}")
                segment.status = 'failed'
                segment.error_message = f"TTS合成失败: {response.message}"
                db.commit()
                
        except Exception as e:
            logger.error(f"[SEGMENT] 段落 {segment.id} 处理异常: {str(e)}")
            import traceback
            logger.error(f"[SEGMENT] 详细错误: {traceback.format_exc()}")
            
            segment.status = 'failed'
            segment.error_message = f"处理异常: {str(e)}"
            db.commit()

async def check_project_completion(project_id: int, db: Session):
    """检查项目是否完成"""
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            return
        
        # 统计段落状态
        segments = db.query(TextSegment).filter(TextSegment.project_id == project_id).all()
        total = len(segments)
        completed = len([s for s in segments if s.status == 'completed'])
        failed = len([s for s in segments if s.status == 'failed'])
        
        if completed + failed == total:
            # 所有段落都处理完成
            if failed == 0:
                # 全部成功，合并音频
                await merge_audio_files(project, segments, db)
                project.status = 'completed'
                project.completed_at = datetime.utcnow()
            else:
                # 有失败的段落
                project.status = 'failed'
            
            db.commit()
            
            # 记录完成日志
            await log_system_event(
                db=db,
                level="info",
                message=f"项目{'完成' if failed == 0 else '失败'}: {project.name}",
                module="novel_reader",
                details={
                    "project_id": project_id,
                    "total_segments": total,
                    "completed_segments": completed,
                    "failed_segments": failed
                }
            )
            
    except Exception as e:
        logger.error(f"检查项目完成状态失败: {str(e)}")

async def merge_audio_files(project: NovelProject, segments: List[TextSegment], db: Session):
    """合并音频文件"""
    try:
        # 按顺序获取已完成的段落
        completed_segments = [s for s in segments if s.status == 'completed' and s.audio_file_path]
        completed_segments.sort(key=lambda x: x.segment_order)
        
        if not completed_segments:
            return
        
        # 生成最终音频文件路径
        import uuid
        final_filename = f"project_{project.id}_{uuid.uuid4().hex}.wav"
        final_path = os.path.join(AUDIO_DIR, final_filename)
        
        # 使用 pydub 合并音频文件
        try:
            from pydub import AudioSegment
            
            combined = AudioSegment.empty()
            for segment in completed_segments:
                if os.path.exists(segment.audio_file_path):
                    audio = AudioSegment.from_wav(segment.audio_file_path)
                    combined += audio
                    # 添加短暂停顿
                    combined += AudioSegment.silent(duration=500)  # 0.5秒停顿
            
            # 导出最终音频
            combined.export(final_path, format="wav")
            
            # 创建合并音频的AudioFile记录
            try:
                file_size = os.path.getsize(final_path)
                duration = len(combined) / 1000.0  # pydub时长单位是毫秒
                
                merged_audio_file = AudioFile(
                    filename=os.path.basename(final_path),
                    original_name=f"{project.name}_完整合成",
                    file_path=final_path,
                    file_size=file_size,
                    duration=duration,
                    project_id=project.id,
                    segment_id=None,
                    voice_profile_id=None,
                    text_content=f"项目《{project.name}》完整音频合成",
                    audio_type='project',
                    processing_time=None,
                    model_used='MegaTTS3',
                    status='active',
                    created_at=datetime.utcnow()
                )
                db.add(merged_audio_file)
                logger.info(f"已创建项目合并音频的AudioFile记录 ID: {merged_audio_file.id}")
            except Exception as e:
                logger.warning(f"创建合并音频的AudioFile记录失败: {str(e)}")
            
            # 更新项目记录
            project.final_audio_path = final_path
            db.commit()
            
            logger.info(f"音频合并完成: {final_path}")
            
        except ImportError:
            logger.warning("未安装 pydub，跳过音频合并")
            
    except Exception as e:
        logger.error(f"合并音频文件失败: {str(e)}")

async def update_segments_voice_mapping_no_commit(project_id: int, char_mapping: Dict[str, str], db: Session):
    """更新段落的声音映射 - 不自动提交"""
    try:
        logger.info(f"[DEBUG] 更新段落声音映射 - 项目ID: {project_id}")
        logger.info(f"[DEBUG] 角色映射: {char_mapping}")
        
        segments = db.query(TextSegment).filter(TextSegment.project_id == project_id).all()
        logger.info(f"[DEBUG] 找到 {len(segments)} 个段落")
        
        # 增加narrator/旁白的兼容性映射
        enhanced_mapping = dict(char_mapping)
        if 'narrator' in enhanced_mapping and '旁白' not in enhanced_mapping:
            enhanced_mapping['旁白'] = enhanced_mapping['narrator']
        if '旁白' in enhanced_mapping and 'narrator' not in enhanced_mapping:
            enhanced_mapping['narrator'] = enhanced_mapping['旁白']
        
        logger.info(f"[DEBUG] 增强后的角色映射: {enhanced_mapping}")
        
        updated_count = 0
        unmapped_speakers = set()
        
        for segment in segments:
            logger.info(f"[DEBUG] 段落{segment.segment_order}: detected_speaker='{segment.detected_speaker}'")
            
            speaker = segment.detected_speaker
            if not speaker:
                logger.warning(f"[DEBUG] 段落{segment.segment_order}: detected_speaker为空，跳过")
                continue
            
            if speaker in enhanced_mapping:
                voice_id = enhanced_mapping[speaker]
                # 验证声音ID是否有效
                voice = db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
                if voice and voice.status == 'active':
                    old_voice_id = segment.voice_profile_id
                    segment.voice_profile_id = voice_id
                    updated_count += 1
                    logger.info(f"[DEBUG] 段落{segment.segment_order}: {speaker} -> 声音ID {voice_id} ({voice.name}) (原:{old_voice_id})")
                else:
                    logger.warning(f"[DEBUG] 段落{segment.segment_order}: 声音ID {voice_id} 无效或声音档案不存在")
                    unmapped_speakers.add(f"{speaker}(无效声音ID:{voice_id})")
            else:
                logger.warning(f"[DEBUG] 段落{segment.segment_order}: 角色'{speaker}'未在映射中找到")
                unmapped_speakers.add(speaker)
        
        if unmapped_speakers:
            logger.warning(f"[DEBUG] 未映射的角色: {list(unmapped_speakers)}")
        
        logger.info(f"[DEBUG] 更新完成，共更新 {updated_count} 个段落")
        
        # 返回统计信息
        return {
            "updated_count": updated_count,
            "total_segments": len(segments),
            "unmapped_speakers": list(unmapped_speakers)
        }
        
    except Exception as e:
        logger.error(f"更新声音映射失败: {str(e)}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}") 
        return {
            "updated_count": 0,
            "total_segments": 0,
            "unmapped_speakers": [],
            "error": str(e)
        } 