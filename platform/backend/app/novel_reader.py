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

from app.database import get_db
from .models import NovelProject, VoiceProfile, Book, SystemLog, AudioFile, BookChapter  # 🚀 TextSegment已删除
from app.tts_client import MegaTTS3Client, TTSRequest, get_tts_client
from app.utils import log_system_event, update_usage_stats, save_upload_file
from app.websocket.manager import websocket_manager
# from tts_memory_optimizer import synthesis_context, optimize_tts_memory  # 暂时禁用以避免torch依赖

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/novel-reader", tags=["小说朗读"])

# 文件存储路径
PROJECTS_DIR = os.getenv("PROJECTS_DIR", "data/projects")
TEXTS_DIR = os.getenv("TEXTS_DIR", "data/texts")
AUDIO_DIR = os.getenv("AUDIO_DIR", "data/audio")

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
        
        # 🚀 新架构：不再需要传统分段，直接使用智能准备模式
        # 项目创建时不进行分段，等待智能准备结果
        segments_count = 0
        logger.info(f"项目 {project.id} 创建完成，新架构将使用智能准备结果进行合成")
        
        # 记录创建日志
        try:
            logger.info(f"[DEBUG] 开始记录创建日志: {project.id}")
            
            # 安全获取book信息
            book_title = "直接输入文本"
            if book_id:
                book = db.query(Book).filter(Book.id == book_id).first()
                if book:
                    book_title = book.title
            
            await log_system_event(
                db=db,
                level="info",
                message=f"朗读项目创建: {name}",
                module="novel_reader",
                details={
                    "project_id": project.id,
                    "book_id": book_id,
                    "book_title": book_title,
                    "text_length": len(text_content),
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
            from app.models import Book
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
        
        # 🚀 新架构：废弃TextSegment，使用AudioFile
        project_data['segments'] = []  # 段落列表已废弃
        project_data['book'] = book_info  # 添加书籍信息
        
        # 🚀 新架构：基于AudioFile的统计信息  
        total_chars = book_content_length if book_content_length > 0 else (
            len(project.original_text) if hasattr(project, 'original_text') and project.original_text else 0
        )
        
        # 从AudioFile获取实际统计
        audio_files = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.audio_type == 'segment'
        ).all()
        
        completed_segments = len(audio_files)  # 有AudioFile = 完成
        
        # 🚨 项目级别统计已废弃
        logger.warning(f"⚠️ 项目详情API中的跨章节统计已废弃，项目ID: {project_id}")
        
        project_data['statistics'] = {
            "totalCharacters": total_chars,
            "totalSegments": 0,  # 项目级别统计已废弃
            "completedSegments": completed_segments,  # 仅保留AudioFile计数
            "failedSegments": 0,  # 项目级别统计已废弃
            "pendingSegments": 0,  # 项目级别统计已废弃
            "processingSegments": 0  # 新架构没有processing状态
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
    book_id: Optional[int] = Form(None),
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
        
        # 验证项目名称
        if not name or name.strip() == "" or name.lower() == "undefined":
            logger.error(f"[DEBUG] 项目名称无效: '{name}'")
            raise HTTPException(status_code=400, detail="项目名称不能为空或无效")
        
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
        
        # 更新书籍关联
        if book_id is not None:
            project.book_id = book_id
            logger.info(f"[DEBUG] 更新book_id: {book_id}")
        
        project.set_character_mapping(char_mapping)
        
        # 🚀 新架构：不再需要更新TextSegment，角色映射保存在项目配置中
        # if char_mapping:
        #     await update_segments_voice_mapping_no_commit(project_id, char_mapping, db)
        
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
        
        # 🚀 新架构：不再需要查询TextSegment，直接处理AudioFile
        
        # 删除AudioFile表中的关联记录
        from app.models import AudioFile
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

# 传统分段功能已废弃 - 统一使用智能准备模式
# @router.post("/projects/{project_id}/segments")
# async def regenerate_segments(...): 已删除

@router.post("/projects/{project_id}/start-generation")
async def start_audio_generation(
    project_id: int,
    background_tasks: BackgroundTasks,
    parallel_tasks: int = Form(1, description="并行任务数"),
    enable_environment: bool = Form(False, description="启用环境音混合"),
    environment_volume: float = Form(0.3, description="环境音音量"),
    db: Session = Depends(get_db)
):
    """
    开始音频生成 - 智能准备唯一策略
    只支持使用智能准备结果进行合成
    """
    logger.info(f"[DEBUG] 开始音频生成请求: project_id={project_id}, parallel_tasks={parallel_tasks}, enable_environment={enable_environment}")
    
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
        
        # 检查智能准备结果（唯一数据源）
        logger.info(f"[DEBUG] 检查智能准备结果...")
        if not project.book_id:
            logger.error(f"[DEBUG] 项目未关联书籍")
            raise HTTPException(status_code=400, detail="项目未关联书籍，无法使用智能准备")
        
        # 获取智能准备结果
        from .models import AnalysisResult
        analysis_results = db.query(AnalysisResult).join(
            BookChapter, AnalysisResult.chapter_id == BookChapter.id
        ).filter(
            BookChapter.book_id == project.book_id,
            AnalysisResult.status == 'completed',
            AnalysisResult.synthesis_plan.isnot(None)
        ).all()
        
        logger.info(f"[DEBUG] 找到 {len(analysis_results)} 个智能准备结果")
        
        if not analysis_results:
            logger.error(f"[DEBUG] 未找到智能准备结果")
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
            logger.error(f"[DEBUG] 智能准备结果中没有合成段落数据")
            raise HTTPException(
                status_code=400, 
                detail="智能准备结果中没有合成段落数据，请重新进行智能准备"
            )
        
        logger.info(f"[DEBUG] 从智能准备结果获取 {len(synthesis_data)} 个合成段落")
        
        # 验证智能准备结果中的声音ID有效性
        logger.info(f"[DEBUG] 验证声音档案...")
        voice_ids_to_check = set()
        segments_without_voice = []
        
        for i, segment in enumerate(synthesis_data):
            voice_id = segment.get('voice_id')
            if voice_id:
                voice_ids_to_check.add(voice_id)
            else:
                segments_without_voice.append(i + 1)
        
        if segments_without_voice:
            logger.error(f"[DEBUG] 部分段落缺少声音配置: {segments_without_voice[:10]}...")  # 只显示前10个
            raise HTTPException(
                status_code=400, 
                detail=f"有 {len(segments_without_voice)} 个段落缺少声音配置，请在书籍管理页面重新进行智能准备"
            )
        
        # 批量验证声音档案
        invalid_voices = []
        for voice_id in voice_ids_to_check:
            voice = db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
            if not voice or voice.status != 'active':
                invalid_voices.append(voice_id)
                logger.error(f"[DEBUG] 声音档案无效: voice_id={voice_id}")
            else:
                logger.info(f"[DEBUG] 声音档案验证通过: {voice.name} (ID: {voice_id})")
        
        if invalid_voices:
            raise HTTPException(
                status_code=400, 
                detail=f"声音档案无效或未激活: {invalid_voices}，请检查声音配置"
            )
        
        logger.info(f"[DEBUG] 所有验证通过，开始启动合成...")
        
        # 🔥 音频文件清理逻辑已移至 start_project_generation 中处理
        # 这里不再需要清理音频文件，因为调用此函数前已经清理过了
        logger.info(f"[DEBUG] 跳过音频文件清理，已在启动时处理")
        
        # 更新项目状态
        project.status = 'processing'
        project.started_at = datetime.utcnow()
        # 🚀 新架构：移除旧进度字段的设置
        # project.current_segment = 0
        # project.processed_segments = 0
        # project.total_segments = len(synthesis_data)
        
        logger.info(f"[DEBUG] 提交数据库更改...")
        db.commit()
        
        logger.info(f"[DEBUG] 启动智能准备模式的后台任务...")
        
        if enable_environment:
            # 使用环境音混合协调器
            from app.services.sequential_synthesis_coordinator import SequentialSynthesisCoordinator
            coordinator = SequentialSynthesisCoordinator()
            
            async def environment_synthesis_wrapper():
                try:
                    result = await coordinator.synthesize_with_environment(
                        project_id=project_id,
                        synthesis_data=synthesis_data,
                        enable_environment=True,
                        environment_volume=environment_volume,
                        parallel_tasks=parallel_tasks
                    )
                    logger.info(f"[ENV_SYNTHESIS] 环境音混合完成: {result}")
                except Exception as e:
                    logger.error(f"[ENV_SYNTHESIS] 环境音混合失败: {str(e)}")
                    
            background_tasks.add_task(environment_synthesis_wrapper)
        else:
            # 传统TTS合成
            background_tasks.add_task(
                process_audio_generation_from_synthesis_plan,
                project_id,
                synthesis_data,
                parallel_tasks
            )
        
        # 记录开始生成日志
        await log_system_event(
            db=db,
            level="info",
            message=f"开始音频生成（智能准备模式）: {project.name}",
            module="novel_reader",
            details={
                "project_id": project_id,
                "total_segments": len(synthesis_data),
                "parallel_tasks": parallel_tasks,
                "data_source": "智能准备结果"
            }
        )
        
        logger.info(f"[DEBUG] 智能准备模式任务启动成功")
        synthesis_mode = "环境音混合模式" if enable_environment else "智能准备模式"
        return {
            "success": True,
            "message": f"音频生成已启动（{synthesis_mode}）",
            "total_segments": len(synthesis_data),
            "parallel_tasks": parallel_tasks,
            "enable_environment": enable_environment,
            "environment_volume": environment_volume if enable_environment else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DEBUG] 启动音频生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动音频生成失败: {str(e)}")

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
                "status": project.status
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
        
        # 🚀 新架构：重新启动时也使用智能准备模式
        # 恢复时需要重新获取智能准备结果
        # background_tasks.add_task(
        #     process_audio_generation_from_synthesis_plan,
        #     project_id,
        #     synthesis_data,
        #     parallel_tasks
        # )
        # 暂时不支持恢复功能，需要重新启动
        raise HTTPException(status_code=400, detail="请重新启动音频生成")
        
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
    🚨 废弃警告：项目级别进度API已废弃
    请使用章节级别的进度API: /projects/{project_id}/chapters/{chapter_id}/progress
    """
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        logger.warning(f"⚠️ 项目级别进度API已废弃，项目ID: {project_id}")
        
        return {
            "success": True,
            "deprecated": True,
            "message": "项目级别进度API已废弃，请使用章节级别的进度API",
            "progress": {
                "projectId": project_id,
                "status": project.status,
                "progressPercent": 0,
                "statistics": {
                    "total": 0,
                    "completed": 0,
                    "failed": 0,
                    "processing": 0,
                    "pending": 0
                },
                "startedAt": project.started_at.isoformat() if project.started_at else None,
                "estimatedCompletion": None,
                "recentCompleted": []
            },
            "migration_info": {
                "recommended_api": f"/projects/{project_id}/chapters/{{chapter_id}}/progress",
                "description": "现在使用章节级别的进度追踪，每个章节独立管理"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取进度失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取进度失败: {str(e)}")

# 🔧 移除项目下载功能 - 用户不需要项目下载功能
# @router.get("/projects/{project_id}/download")
# async def download_final_audio(project_id: int, db: Session = Depends(get_db)):
#     """下载最终音频文件 - 已移除"""
#     raise HTTPException(status_code=404, detail="项目下载功能已移除")

# 传统分段工具函数已废弃 - 统一使用智能准备模式

# 🚀 已删除：segment_text_by_strategy_no_commit - 旧架构函数，新架构不使用

# 🚀 已删除：segment_text_by_strategy - 旧架构函数，新架构不使用

# 🚀 已删除：detect_speaker - 旧架构函数，新架构使用AI智能检测器

# 🚀 已删除：update_segments_voice_mapping - 旧架构函数，新架构不需要

# 🚀 已删除：process_audio_generation - 旧架构函数，新架构使用process_audio_generation_from_synthesis_plan

# 🚀 已删除：process_single_segment_sequential - 旧架构函数，新架构不使用

# 🚀 已删除：process_single_segment - 旧架构函数，新架构不使用

# 🚀 已删除：check_project_completion - 旧架构函数，新架构不使用

# 🚀 已删除：merge_audio_files - 旧架构函数，新架构使用merge_audio_files_from_plan

# 🚀 已删除：update_segments_voice_mapping_no_commit - 旧架构函数，新架构不使用 

async def process_audio_generation_from_synthesis_plan(
    project_id: int, 
    synthesis_data: List[Dict], 
    parallel_tasks: int = 1
):
    """
    基于智能准备结果直接进行音频合成
    不依赖 TextSegment 表，直接使用 JSON 数据
    """
    logger.info(f"[SYNTHESIS_PLAN] 开始处理项目 {project_id} 的音频合成，共 {len(synthesis_data)} 个段落")
    
    try:
        # 获取数据库连接
        db = next(get_db())
        
        # 获取项目信息
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            logger.error(f"[SYNTHESIS_PLAN] 项目 {project_id} 不存在")
            return
        
        # 初始化TTS客户端
        tts_client = get_tts_client()
        
        logger.info(f"[SYNTHESIS_PLAN] TTS服务状态检查...")
        health_status = await tts_client.health_check()
        if health_status.get("status") != "healthy":
            logger.error(f"[SYNTHESIS_PLAN] TTS服务不可用: {health_status}")
            project.status = 'failed'
            project.error_message = f"TTS服务不可用: {health_status.get('error', '未知错误')}"
            db.commit()
            return
        
        # 确保输出目录存在
        project_output_dir = f"outputs/projects/{project_id}"
        os.makedirs(project_output_dir, exist_ok=True)
        
        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(parallel_tasks)
        
        # 初始化WebSocket管理器用于进度推送
        from app.websocket.manager import websocket_manager
        
        # 处理每个段落
        completed_count = 0
        failed_segments = []
        output_files = []
        
        async def process_segment(segment_data, segment_index):
            """处理单个段落 - 序列化版本"""
            try:
                # 🚨 在段落处理开始时也检查取消状态
                db.refresh(project)
                if project.status == 'cancelled':
                    logger.warning(f"[SYNTHESIS_PLAN] 段落处理中检测到项目已取消，停止处理段落 {segment_index + 1}")
                    return {"error": "项目已被取消"}
                
                segment_id = segment_data.get('segment_id', segment_index + 1)
                text = segment_data.get('text', '')
                speaker = segment_data.get('speaker', '未知')
                voice_id = segment_data.get('voice_id')
                character_id = segment_data.get('character_id')
                parameters = segment_data.get('parameters', {})
                
                logger.info(f"[SYNTHESIS_PLAN] 处理段落 {segment_id}: {speaker} - {text[:50]}...")
                
                if not text.strip():
                    logger.warning(f"[SYNTHESIS_PLAN] 段落 {segment_id} 文本为空，跳过")
                    return None
                
                # 🚀 架构改进：支持两种方式获取音频配置
                # 方式1（推荐）：通过character_id获取最新配音
                # 方式2（向后兼容）：通过voice_id获取VoiceProfile
                character = None
                voice = None
                
                if character_id:
                    # 🎯 新架构：通过character_id获取角色最新配音
                    try:
                        from app.models.character import Character
                        character = db.query(Character).filter(Character.id == character_id).first()
                        if character and character.reference_audio_path:
                            logger.info(f"[NEW_ARCH] 段落 {segment_id} 使用角色配音：{character.name} (ID: {character.id})")
                            # 创建兼容的voice对象
                            class VoiceCompat:
                                def __init__(self, char):
                                    self.id = char.id
                                    self.name = char.name
                                    self.reference_audio_path = char.reference_audio_path
                                    self.latent_file_path = char.latent_file_path
                                    self.status = char.status
                                
                                def validate_files(self):
                                    return {'valid': True, 'missing_files': []}
                            
                            voice = VoiceCompat(character)
                        else:
                            logger.error(f"[NEW_ARCH] 段落 {segment_id} 角色ID {character_id} 不存在或未配置音频，请在角色配音库中配置声音")
                            return {"error": f"段落 {segment_id} 角色'{speaker}'未配置声音，请在角色配音库中上传音频文件"}
                    except Exception as e:
                        logger.error(f"[NEW_ARCH] 段落 {segment_id} 查找角色失败: {e}")
                        return {"error": f"段落 {segment_id} 角色查找失败: {e}"}
                
                elif voice_id:
                    # 🔄 旧架构：通过voice_id获取VoiceProfile（向后兼容）
                    try:
                        voice = db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
                        if voice:
                            logger.info(f"[OLD_ARCH] 段落 {segment_id} 使用VoiceProfile：{voice.name} (ID: {voice.id})")
                        else:
                            logger.error(f"[OLD_ARCH] 段落 {segment_id} VoiceProfile不存在: {voice_id}")
                    except Exception as e:
                        logger.error(f"[OLD_ARCH] 段落 {segment_id} 查找VoiceProfile失败: {e}")
                
                if not voice:
                    logger.error(f"[SYNTHESIS_PLAN] 段落 {segment_id} 无法获取声音配置 (character_id: {character_id}, voice_id: {voice_id})")
                    return {"error": f"段落 {segment_id} 缺少声音配置"}
                
                # 验证声音文件
                file_validation = voice.validate_files()
                if not file_validation['valid']:
                    logger.error(f"[SYNTHESIS_PLAN] 段落 {segment_id} 声音文件缺失: {file_validation['missing_files']}")
                    return {"error": f"段落 {segment_id} 声音文件缺失"}
                
                # 生成音频文件路径
                safe_speaker = "".join(c for c in speaker if c.isalnum() or c in (' ', '-', '_')).rstrip()
                # 🔥 修复：根据实际使用的voice对象ID生成文件名，避免ID混用
                voice_identifier = voice.id if hasattr(voice, 'id') else 'unknown'
                
                # 🚨 重要修复：在文件名中添加章节ID，避免不同章节的段落文件相互覆盖
                chapter_id = segment_data.get('chapter_id', 'unknown')
                audio_filename = f"chapter_{chapter_id}_segment_{segment_id:04d}_{safe_speaker}_{voice_identifier}.wav"
                audio_path = os.path.join(project_output_dir, audio_filename)
                
                # 🔥 关键修复：优先使用角色配音库的个性化参数
                final_parameters = {}
                
                # 方式1：从角色配音库获取参数（推荐）
                if character and hasattr(character, 'voice_parameters') and character.voice_parameters:
                    try:
                        import json
                        char_params = json.loads(character.voice_parameters) if isinstance(character.voice_parameters, str) else character.voice_parameters
                        logger.info(f"[PARAMS] 使用角色配音库参数：{char_params}")
                        final_parameters = {
                            'timeStep': char_params.get('timeStep', char_params.get('time_step', 32)),
                            'pWeight': char_params.get('pWeight', char_params.get('p_weight', 1.4)),
                            'tWeight': char_params.get('tWeight', char_params.get('t_weight', 3.0))
                        }
                    except Exception as e:
                        logger.warning(f"[PARAMS] 解析角色参数失败，使用默认参数: {e}")
                        final_parameters = {'timeStep': 32, 'pWeight': 1.4, 'tWeight': 3.0}
                else:
                    # 方式2：使用synthesis_plan的通用参数（向后兼容）
                    final_parameters = {
                        'timeStep': parameters.get('timeStep', 32),
                        'pWeight': parameters.get('pWeight', 1.4),
                        'tWeight': parameters.get('tWeight', 3.0)
                    }
                    logger.info(f"[PARAMS] 使用通用参数：{final_parameters}")
                
                # 准备TTS请求
                tts_request = TTSRequest(
                    text=text,
                    reference_audio_path=voice.reference_audio_path,
                    output_audio_path=audio_path,
                    time_step=final_parameters['timeStep'],
                    p_weight=final_parameters['pWeight'],
                    t_weight=final_parameters['tWeight'],
                    latent_file_path=voice.latent_file_path
                )
                
                # 调用TTS合成
                start_time = time.time()
                response = await tts_client.synthesize_speech(tts_request)
                processing_time = time.time() - start_time
                
                if response.success:
                    # 验证生成的音频文件
                    if os.path.exists(audio_path):
                        file_size = os.path.getsize(audio_path)
                        
                        # 获取音频时长
                        try:
                            from app.utils import get_audio_duration
                            duration = get_audio_duration(audio_path)
                        except:
                            duration = 0.0
                        
                        # 🚀 获取章节信息用于新架构
                        chapter_number = segment_data.get('chapter_number')
                        chapter_id = segment_data.get('chapter_id')
                        if not chapter_number and chapter_id:
                            # 尝试从数据库获取章节号
                            try:
                                from app.models import BookChapter
                                chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
                                if chapter:
                                    chapter_number = chapter.chapter_number
                                    logger.info(f"[NEW_ARCH] 段落 {segment_id} 从数据库获取章节号: {chapter_number}")
                            except Exception as e:
                                logger.error(f"[NEW_ARCH] 获取章节信息失败: {e}")
                        
                        # 🚀 注释掉防重复检查：用户点击重新合成时已清理了所有现有文件
                        # 重新合成时不需要检查重复，因为启动时已经清理过了
                        logger.debug(f"[SYNTHESIS_PLAN] 开始合成段落 {segment_id}，角色: {speaker}")
                        
                        # 🔥 修复：正确设置character_id和voice_profile_id，避免ID空间冲突
                        # 根据voice对象的来源正确设置ID字段
                        audio_character_id = None
                        audio_voice_profile_id = None
                        
                        if character_id:
                            # 新架构：使用角色配音库
                            audio_character_id = character_id
                            logger.debug(f"[NEW_ARCH] AudioFile使用character_id: {character_id}")
                        elif voice_id and hasattr(voice, 'id') and not hasattr(voice, '__dict__'):
                            # 旧架构：使用VoiceProfile（voice是真正的VoiceProfile对象）
                            audio_voice_profile_id = voice.id
                            logger.debug(f"[OLD_ARCH] AudioFile使用voice_profile_id: {voice.id}")
                        else:
                            logger.warning(f"[SYNTHESIS_PLAN] 段落 {segment_id} 无法确定ID类型，使用voice对象ID")
                            # 如果无法确定，根据voice对象类型判断
                            if hasattr(voice, '__dict__') and 'VoiceCompat' in str(type(voice)):
                                # VoiceCompat对象来自Character
                                audio_character_id = voice.id
                            else:
                                # 真正的VoiceProfile对象
                                audio_voice_profile_id = voice.id if hasattr(voice, 'id') else None
                        
                        # 保存AudioFile记录（新架构：包含完整合成信息）
                        audio_file = AudioFile(
                            filename=audio_filename,
                            original_name=f"段落{segment_id}_{speaker}",
                            file_path=audio_path,
                            file_size=file_size,
                            duration=duration,
                            project_id=project_id,
                            chapter_id=chapter_id,
                            chapter_number=chapter_number,
                            character_name=speaker,  # 角色名
                            speaker=speaker,  # 说话人
                            paragraph_index=segment_id,  # 段落索引
                            character_id=audio_character_id,  # 🚀 新架构：Character ID
                            voice_profile_id=audio_voice_profile_id,  # 🚀 旧架构：VoiceProfile ID
                            text_content=text,
                            audio_type='segment',
                            processing_time=processing_time,
                            model_used='MegaTTS3',
                            status='active',
                            created_at=datetime.utcnow()
                        )
                        db.add(audio_file)
                        db.commit()
                        db.refresh(audio_file)
                        
                        # 🚀 新架构：完全基于AudioFile，不再创建TextSegment
                        # AudioFile已包含所有必要信息：文本内容、说话人、章节等
                        
                        logger.info(f"[SYNTHESIS_PLAN] 段落 {segment_id} 合成成功，耗时 {processing_time:.2f}s")
                        
                        return {
                            "segment_id": segment_id,
                            "audio_file_id": audio_file.id,
                            "file_path": audio_path,
                            "duration": duration,
                            "speaker": speaker,
                            "character_id": audio_character_id,  # 🚀 新架构：返回正确的character_id
                            "voice_profile_id": audio_voice_profile_id,  # 🚀 旧架构：返回正确的voice_profile_id
                            "chapter_id": chapter_id  # 🔥 新增：返回章节ID用于音频合并
                        }
                    else:
                        logger.error(f"[SYNTHESIS_PLAN] 段落 {segment_id} 音频文件未生成")
                        return {"error": f"段落 {segment_id} 音频文件未生成"}
                else:
                    logger.error(f"[SYNTHESIS_PLAN] 段落 {segment_id} TTS合成失败: {response.message}")
                    return {"error": f"段落 {segment_id} TTS合成失败: {response.message}"}
                    
            except Exception as e:
                logger.error(f"[SYNTHESIS_PLAN] 段落 {segment_index + 1} 处理异常: {str(e)}")
                return {"error": f"段落 {segment_index + 1} 处理异常: {str(e)}"}
        
        # 序列化处理段落 - 防止GPU过载
        logger.info(f"[SYNTHESIS_PLAN] 开始序列化处理 {len(synthesis_data)} 个段落...")
        results = []
        for i, segment in enumerate(synthesis_data):
            logger.info(f"[SYNTHESIS_PLAN] 处理进度: {i+1}/{len(synthesis_data)}")
            
            # 🚨 关键修复：每次处理前检查项目是否被取消
            db.refresh(project)  # 刷新项目状态
            if project.status == 'cancelled':
                logger.warning(f"[SYNTHESIS_PLAN] 项目 {project_id} 已被取消，停止处理")
                project.error_message = f"合成已被用户取消，已处理 {i}/{len(synthesis_data)} 个段落"
                db.commit()
                return
            
            # 🔧 实时统计已完成段落数（基于当前project状态）
            current_completed = db.query(AudioFile).filter(
                AudioFile.project_id == project_id,
                AudioFile.audio_type == 'segment'
            ).count()
            
            # 发送段落开始处理的进度更新到前端
            try:
                await websocket_manager.publish_to_topic(
                    f"synthesis_{project_id}",
                    {
                        "type": "progress_update",
                        "data": {
                            "type": "synthesis",
                            "project_id": project_id,
                            "status": "running",
                            "progress": round((i / len(synthesis_data)) * 100),
                            "completed_segments": current_completed,
                            "total_segments": len(synthesis_data),
                            "failed_segments": len(failed_segments),
                            "current_processing": f"正在处理段落 {i+1} - {segment.get('speaker', '未知角色')}: {segment.get('text', '')[:50]}...",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }
                )
            except Exception as ws_error:
                logger.error(f"[SYNTHESIS_PLAN] WebSocket进度推送失败: {str(ws_error)}")
            
            try:
                result = await process_segment(segment, i)
                results.append(result)
                
                # 🔧 每完成一个段落就实时发送进度更新
                if result and not isinstance(result, Exception) and "error" not in result:
                    updated_completed = db.query(AudioFile).filter(
                        AudioFile.project_id == project_id,
                        AudioFile.audio_type == 'segment'
                    ).count()
                    
                    try:
                        await websocket_manager.publish_to_topic(
                            f"synthesis_{project_id}",
                            {
                                "type": "progress_update",
                                "data": {
                                    "type": "synthesis",
                                    "project_id": project_id,
                                    "status": "running",
                                    "progress": round(((i + 1) / len(synthesis_data)) * 100),
                                    "completed_segments": updated_completed,
                                    "total_segments": len(synthesis_data),
                                    "failed_segments": len(failed_segments),
                                    "current_processing": f"已完成段落 {i+1} - {segment.get('speaker', '未知角色')}",
                                    "timestamp": datetime.utcnow().isoformat()
                                }
                            }
                        )
                    except Exception as ws_error:
                        logger.error(f"[SYNTHESIS_PLAN] 完成进度推送失败: {str(ws_error)}")
                        
            except Exception as e:
                logger.error(f"[SYNTHESIS_PLAN] 段落 {i+1} 处理异常: {str(e)}")
                results.append(e)
        
        # 统计处理结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"[SYNTHESIS_PLAN] 段落 {i + 1} 处理异常: {str(result)}")
                failed_segments.append({
                    "segment_index": i + 1,
                    "error": str(result),
                    "timestamp": datetime.utcnow().isoformat()
                })
            elif result and "error" in result:
                logger.error(f"[SYNTHESIS_PLAN] 段落处理失败: {result['error']}")
                failed_segments.append({
                    "segment_index": i + 1,
                    "error": result["error"],
                    "timestamp": datetime.utcnow().isoformat()
                })
            elif result:
                # 重新合成模式：所有成功的结果都计数（不存在"existing"状态）
                completed_count += 1
                output_files.append(result)
                logger.info(f"[SYNTHESIS_PLAN] 段落 {result['segment_id']} 合成完成")
        
        # 🚀 新架构：只记录章节级别的处理结果
        logger.info(f"[SYNTHESIS_PLAN] 章节处理结果: 预期{len(synthesis_data)}个，成功{completed_count}个")
        db.commit()
        
        logger.info(f"[SYNTHESIS_PLAN] 处理完成: 成功 {completed_count}/{len(synthesis_data)} 个段落")
        
        # 如果有成功的段落，尝试合并音频
        final_audio_path = None
        if output_files:
            try:
                logger.info(f"[SYNTHESIS_PLAN] 开始合并 {len(output_files)} 个音频文件...")
                final_audio_path = await merge_audio_files_from_plan(project, output_files, db)
                logger.info(f"[SYNTHESIS_PLAN] 音频合并完成: {final_audio_path}")
            except Exception as e:
                logger.error(f"[SYNTHESIS_PLAN] 音频合并失败: {str(e)}")
        
        # 🚀 项目级别状态管理已废弃 - 现在只关注章节级别的处理
        
        # 🚀 最终数据一致性确认（使用之前计算的final_total）
        project.completed_at = datetime.utcnow()
        project.final_audio_path = final_audio_path
        
        # 🔧 关键修复：更新章节合成状态
        logger.info(f"[SYNTHESIS_PLAN] 开始更新章节合成状态...")
        try:
            # 获取所有相关章节ID
            chapter_ids = set()
            for segment in synthesis_data:
                chapter_id = segment.get('chapter_id')
                if chapter_id:
                    chapter_ids.add(chapter_id)
            
            # 更新章节状态
            if chapter_ids:
                from app.models import BookChapter
                
                for chapter_id in chapter_ids:
                    # 检查该章节是否有完成的音频文件
                    chapter_audio_count = db.query(AudioFile).filter(
                        AudioFile.project_id == project_id,
                        AudioFile.chapter_id == chapter_id,
                        AudioFile.audio_type == 'segment'
                    ).count()
                    
                    # 更新章节状态
                    chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
                    if chapter and chapter_audio_count > 0:
                        chapter.synthesis_status = 'completed'
                        logger.info(f"[SYNTHESIS_PLAN] 章节 {chapter_id} 状态更新为 completed ({chapter_audio_count} 个音频文件)")
                    elif chapter:
                        chapter.synthesis_status = 'failed'
                        logger.info(f"[SYNTHESIS_PLAN] 章节 {chapter_id} 状态更新为 failed (无音频文件)")
            
            # 如果没有chapter_id，尝试从project的book中获取
            elif project.book_id:
                from app.models import Book, BookChapter
                book = db.query(Book).filter(Book.id == project.book_id).first()
                if book:
                    chapters = db.query(BookChapter).filter(BookChapter.book_id == book.id).all()
                    for chapter in chapters:
                        # 检查该章节是否有完成的音频文件
                        chapter_audio_count = db.query(AudioFile).filter(
                            AudioFile.project_id == project_id,
                            AudioFile.chapter_number == chapter.chapter_number,
                            AudioFile.audio_type == 'segment'
                        ).count()
                        
                        if chapter_audio_count > 0:
                            chapter.synthesis_status = 'completed'
                            logger.info(f"[SYNTHESIS_PLAN] 章节 {chapter.id} (第{chapter.chapter_number}章) 状态更新为 completed")
                        else:
                            chapter.synthesis_status = 'failed'
                            logger.info(f"[SYNTHESIS_PLAN] 章节 {chapter.id} (第{chapter.chapter_number}章) 状态更新为 failed")
            
        except Exception as e:
            logger.error(f"[SYNTHESIS_PLAN] 更新章节状态失败: {str(e)}")
        
        # 🚀 项目状态日志已废弃 - 现在只关注章节级别的处理
        
        if failed_segments:
            # 生成详细的错误摘要
            error_summary = generate_detailed_error_summary(failed_segments, len(synthesis_data))
            project.error_message = error_summary
        
        db.commit()
        
        # 🔥 新增：按章节合并音频文件
        chapter_audio_files = {}
        if completed_count > 0:
            try:
                logger.info(f"[SYNTHESIS_PLAN] 开始按章节合并音频文件...")
                
                # 按章节组织音频文件
                for result in results:
                    if isinstance(result, dict) and 'chapter_id' in result and result.get('file_path'):
                        chapter_id = result['chapter_id']
                        if chapter_id not in chapter_audio_files:
                            chapter_audio_files[chapter_id] = []
                        chapter_audio_files[chapter_id].append(result)
                
                # 为每个章节生成合并的音频文件
                for chapter_id, audio_files in chapter_audio_files.items():
                    if not audio_files:
                        continue
                    
                    try:
                        # 按段落顺序排序
                        audio_files.sort(key=lambda x: x.get('segment_id', 0))
                        
                        # 生成章节音频文件
                        chapter_audio_path = await merge_chapter_audio_files(
                            project_id, chapter_id, audio_files, db
                        )
                        
                        if chapter_audio_path:
                            logger.info(f"[SYNTHESIS_PLAN] 章节 {chapter_id} 音频合并完成: {chapter_audio_path}")
                            
                            # 更新章节状态为完成
                            chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
                            if chapter:
                                chapter.synthesis_status = 'completed'
                                db.commit()
                        else:
                            logger.warning(f"[SYNTHESIS_PLAN] 章节 {chapter_id} 音频合并失败")
                            
                    except Exception as e:
                        logger.error(f"[SYNTHESIS_PLAN] 章节 {chapter_id} 音频合并异常: {str(e)}")
                        
            except Exception as e:
                logger.error(f"[SYNTHESIS_PLAN] 章节音频合并过程异常: {str(e)}")
        
        # 🚀 发送章节级别的完成状态到前端
        chapter_progress = round((completed_count / len(synthesis_data)) * 100) if len(synthesis_data) > 0 else 0
        await websocket_manager.publish_to_topic(
            f"synthesis_{project_id}",
            {
                "type": "progress_update",
                "data": {
                    "type": "synthesis",
                    "project_id": project_id,
                    "status": "completed" if completed_count == len(synthesis_data) else "failed",
                    "progress": chapter_progress,
                    "completed_segments": completed_count,
                    "total_segments": len(synthesis_data),
                    "failed_segments": len(failed_segments),
                    "current_processing": f"章节合成{'完成' if completed_count == len(synthesis_data) else '结束'}",
                    "final_audio_path": None,  # 现在不再有全局的最终音频文件
                    "chapter_audio_files": len(chapter_audio_files),  # 生成的章节音频文件数量
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        )
        
        # 🚀 记录章节级别的完成日志
        await log_system_event(
            db=db,
            level="info",
            message=f"章节音频生成完成: {project.name}",
            module="novel_reader",
            details={
                "project_id": project_id,
                "chapter_expected": len(synthesis_data),
                "chapter_actual": completed_count,
                "new_generated": completed_count,
                "failed_segments": len(failed_segments),
                "final_audio_path": final_audio_path,
                "data_source": "智能准备结果",
                "chapter_status": "completed" if completed_count == len(synthesis_data) else "failed"
            }
        )
        
        logger.info(f"[SYNTHESIS_PLAN] 项目 {project_id} 音频合成任务完成")
        
        # 🔧 项目完成状态更新
        try:
            # 更新章节状态
            chapter_ids = list(chapter_audio_files.keys())
            for chapter_id in chapter_ids:
                # 检查章节完整音频文件是否存在
                chapter_complete_audio = db.query(AudioFile).filter(
                    AudioFile.project_id == project_id,
                    AudioFile.chapter_id == chapter_id,
                    AudioFile.audio_type == 'chapter'
                ).first()
                
                # 更新章节状态
                chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
                if chapter:
                    # 如果有章节完整音频文件，状态为完成
                    if chapter_complete_audio and os.path.exists(chapter_complete_audio.file_path):
                        chapter.synthesis_status = 'completed'
                        logger.info(f"[SYNTHESIS_PLAN] 章节 {chapter_id} 状态更新为 completed (有完整音频文件)")
                    else:
                        chapter.synthesis_status = 'failed'
                        logger.info(f"[SYNTHESIS_PLAN] 章节 {chapter_id} 状态更新为 failed (无音频文件)")
            
            # 🔥 更新项目状态
            if failed_segments:
                project.status = 'failed'
                # 生成详细的错误摘要
                error_summary = generate_detailed_error_summary(failed_segments, len(synthesis_data))
                project.error_message = error_summary
                logger.info(f"[SYNTHESIS_PLAN] 项目 {project_id} 状态更新为 failed")
            elif len(chapter_audio_files) > 0:
                project.status = 'completed'
                project.error_message = None
                logger.info(f"[SYNTHESIS_PLAN] 项目 {project_id} 状态更新为 completed")
            else:
                project.status = 'partial_completed'
                project.error_message = f"部分完成：{completed_count}/{len(synthesis_data)} 个段落"
                logger.info(f"[SYNTHESIS_PLAN] 项目 {project_id} 状态更新为 partial_completed")
            
            project.completed_at = datetime.utcnow()
            db.commit()
        
        except Exception as e:
            logger.error(f"[SYNTHESIS_PLAN] 更新章节和项目状态失败: {str(e)}")
        
        db.commit()
        
    except Exception as e:
        logger.error(f"[SYNTHESIS_PLAN] 项目 {project_id} 音频合成任务异常: {str(e)}", exc_info=True)
        try:
            db = next(get_db())
            project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
            if project:
                # 🚀 项目状态设置已废弃，只保留错误信息记录
                # 生成更详细的错误信息
                error_details = analyze_synthesis_exception(e)
                project.error_message = error_details
                project.completed_at = datetime.utcnow()
                db.commit()
                
                # 发送详细错误信息到前端
                await websocket_manager.publish_to_topic(
                    f"synthesis_{project_id}",
                    {
                        "type": "progress_update", 
                        "data": {
                            "type": "synthesis",
                            "project_id": project_id,
                            "status": "failed",
                            "error_message": error_details,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }
                )
        except Exception as inner_e:
            logger.error(f"更新项目失败状态时出错: {str(inner_e)}")
    finally:
        try:
            db.close()
        except:
            pass


def generate_detailed_error_summary(failed_segments: List[Dict], total_segments: int) -> str:
    """生成详细的错误摘要"""
    if not failed_segments:
        return "未知错误"
    
    # 统计错误类型
    error_types = {}
    for segment in failed_segments:
        error = segment.get('error', '未知错误')
        # 简化错误类型分类
        if 'TTS' in error or 'tts' in error.lower():
            error_type = 'TTS服务异常'
        elif 'GPU' in error or 'CUDA' in error or 'memory' in error.lower():
            error_type = 'GPU/显存问题'
        elif 'timeout' in error.lower() or '超时' in error:
            error_type = '请求超时'
        elif 'voice' in error.lower() or '声音' in error:
            error_type = '声音配置问题'
        elif 'network' in error.lower() or '网络' in error:
            error_type = '网络连接问题'
        elif 'encoding' in error.lower() or '编码' in error:
            error_type = '文本编码问题'
        else:
            error_type = '其他错误'
        
        error_types[error_type] = error_types.get(error_type, 0) + 1
    
    # 构建详细错误信息
    total_failed = len(failed_segments)
    success_rate = round(((total_segments - total_failed) / total_segments) * 100, 1)
    
    error_summary = f"{total_failed}个段落合成失败 (成功率: {success_rate}%)"
    
    # 添加错误类型统计
    if error_types:
        error_details = []
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            error_details.append(f"{error_type} ({count}个)")
        error_summary += f"，主要原因: {', '.join(error_details[:3])}"  # 只显示前3个主要错误类型
        
        # 如果有更多错误类型，显示省略信息
        if len(error_details) > 3:
            error_summary += f" 等{len(error_details)}种问题"
    
    return error_summary


def analyze_synthesis_exception(exception: Exception) -> str:
    """分析合成异常并返回用户友好的错误信息"""
    error_str = str(exception).lower()
    error_type = type(exception).__name__
    
    # 根据异常类型和内容提供具体的错误信息
    if 'connection' in error_str or 'timeout' in error_str:
        return f"网络连接问题：TTS服务连接超时或中断，请检查服务状态后重试"
    elif 'gpu' in error_str or 'cuda' in error_str or 'memory' in error_str:
        return f"GPU资源问题：显存不足或CUDA错误，建议减少并行任务数或等待GPU资源释放"
    elif 'json' in error_str or 'parse' in error_str:
        return f"数据解析错误：智能准备结果格式异常，请重新进行智能准备"
    elif 'permission' in error_str or 'access' in error_str:
        return f"文件访问权限问题：无法创建或写入音频文件，请检查目录权限"
    elif 'disk' in error_str or 'space' in error_str:
        return f"磁盘空间不足：请清理存储空间后重试"
    elif 'tts' in error_str:
        return f"TTS服务异常：语音合成引擎内部错误，请检查TTS服务状态"
    elif error_type == 'KeyError':
        return f"配置缺失错误：合成计划中缺少必要的配置信息，请重新进行智能准备"
    elif error_type == 'TypeError' or error_type == 'ValueError':
        return f"数据类型错误：合成参数格式不正确，请检查角色声音配置"
    elif error_type == 'FileNotFoundError':
        return f"文件缺失错误：找不到必要的音频文件或配置文件"
    else:
        # 提供通用但比"系统内部错误"更有用的信息
        return f"合成任务异常 ({error_type}): {str(exception)[:100]}{'...' if len(str(exception)) > 100 else ''}"


async def merge_audio_files_from_plan(
    project: NovelProject, 
    output_files: List[Dict], 
    db: Session
) -> str:
    """
    基于合成计划结果合并音频文件
    """
    try:
        from pydub import AudioSegment
        import os
        
        # 按segment_id排序
        sorted_files = sorted(output_files, key=lambda x: x.get('segment_id', 0))
        
        logger.info(f"[MERGE] 开始合并 {len(sorted_files)} 个音频文件...")
        
        # 初始化合并音频
        merged_audio = None
        silence = AudioSegment.silent(duration=500)  # 500ms间隔
        
        for file_info in sorted_files:
            file_path = file_info.get('file_path')
            if file_path and os.path.exists(file_path):
                try:
                    segment_audio = AudioSegment.from_wav(file_path)
                    if merged_audio is None:
                        merged_audio = segment_audio
                    else:
                        merged_audio = merged_audio + silence + segment_audio
                    logger.debug(f"[MERGE] 已添加音频: {file_path}")
                except Exception as e:
                    logger.error(f"[MERGE] 读取音频文件失败: {file_path}, 错误: {str(e)}")
            else:
                logger.warning(f"[MERGE] 音频文件不存在: {file_path}")
        
        if merged_audio is None:
            raise Exception("没有有效的音频文件可合并")
        
        # 导出最终音频文件
        final_filename = f"final_audio_{project.id}_{int(time.time())}.wav"
        final_path = f"outputs/projects/{project.id}/{final_filename}"
        
        merged_audio.export(final_path, format="wav")
        
        file_size = os.path.getsize(final_path)
        duration = len(merged_audio) / 1000.0  # 转换为秒
        
        # 保存最终音频文件记录
        final_audio_file = AudioFile(
            filename=final_filename,
            original_name=f"{project.name}_完整音频",
            file_path=final_path,
            file_size=file_size,
            duration=duration,
            project_id=project.id,
            audio_type='final',
            model_used='MegaTTS3',
            status='active',
            created_at=datetime.utcnow()
        )
        db.add(final_audio_file)
        db.commit()
        
        logger.info(f"[MERGE] 音频合并完成: {final_path} ({duration:.1f}s, {file_size} bytes)")
        
        return final_path
        
    except Exception as e:
        logger.error(f"[MERGE] 音频合并失败: {str(e)}")
        raise e 

def add_chapter_info_to_synthesis_data(synthesis_data: List[Dict], analysis_results, db: Session) -> List[Dict]:
    """
    为合成数据添加章节信息
    确保每个segment都有完整的章节信息
    """
    # 建立章节ID到章节信息的映射
    chapter_info_map = {}
    for result in analysis_results:
        chapter_id = result.chapter_id
        if chapter_id not in chapter_info_map:
            chapter_info_map[chapter_id] = {
                'chapter_id': chapter_id,
                'chapter_number': result.chapter.chapter_number,
                'chapter_title': result.chapter.chapter_title or result.chapter.title,
                'book_id': result.chapter.book_id
            }
    
    # 为每个segment添加章节信息
    for segment in synthesis_data:
        if 'chapter_id' in segment and segment['chapter_id'] in chapter_info_map:
            chapter_info = chapter_info_map[segment['chapter_id']]
            segment.update(chapter_info)
            logger.debug(f"[CHAPTER_INFO] 段落 {segment.get('segment_id')} 添加章节信息: 第{chapter_info['chapter_number']}章 {chapter_info['chapter_title']}")
    
    return synthesis_data


async def merge_chapter_audio_files(
    project_id: int, 
    chapter_id: int, 
    audio_files: List[Dict], 
    db: Session
) -> Optional[str]:
    """
    合并单个章节的所有音频文件为一个完整的章节音频文件
    
    Args:
        project_id: 项目ID
        chapter_id: 章节ID
        audio_files: 章节内的音频文件列表
        db: 数据库会话
        
    Returns:
        合并后的章节音频文件路径，失败时返回None
    """
    try:
        from pydub import AudioSegment
        import os
        
        if not audio_files:
            logger.warning(f"[MERGE_CHAPTER] 章节 {chapter_id} 没有音频文件需要合并")
            return None
        
        # 获取章节信息
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            logger.error(f"[MERGE_CHAPTER] 章节 {chapter_id} 不存在")
            return None
        
        chapter_title = chapter.chapter_title or chapter.title or f"Chapter_{chapter_id}"
        chapter_number = chapter.chapter_number or chapter_id
        
        logger.info(f"[MERGE_CHAPTER] 开始合并章节 {chapter_id} ({chapter_title}) 的 {len(audio_files)} 个音频文件")
        
        # 初始化合并音频
        merged_audio = None
        silence = AudioSegment.silent(duration=800)  # 800ms段落间隔
        total_duration = 0
        merged_segments = 0
        
        # 按段落顺序合并音频
        for i, audio_file in enumerate(audio_files):
            file_path = audio_file.get('file_path')
            segment_id = audio_file.get('segment_id', i + 1)
            
            if not file_path or not os.path.exists(file_path):
                logger.warning(f"[MERGE_CHAPTER] 音频文件不存在: {file_path}")
                continue
            
            try:
                # 加载音频段落
                segment_audio = AudioSegment.from_wav(file_path)
                
                if merged_audio is None:
                    merged_audio = segment_audio
                else:
                    # 添加段落间隔，然后合并
                    merged_audio = merged_audio + silence + segment_audio
                
                total_duration += len(segment_audio)
                merged_segments += 1
                
                logger.debug(f"[MERGE_CHAPTER] 已合并段落 {segment_id}: {len(segment_audio)}ms")
                
            except Exception as e:
                logger.error(f"[MERGE_CHAPTER] 读取音频文件失败: {file_path}, 错误: {str(e)}")
                continue
        
        if merged_audio is None or merged_segments == 0:
            logger.error(f"[MERGE_CHAPTER] 章节 {chapter_id} 没有有效的音频文件可合并")
            return None
        
        # 生成章节音频文件路径
        project_output_dir = f"outputs/projects/{project_id}"
        os.makedirs(project_output_dir, exist_ok=True)
        
        # 文件名：chapter_章节号_章节标题.wav
        safe_title = "".join(c for c in chapter_title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')
        chapter_filename = f"chapter_{chapter_number:03d}_{safe_title}.wav"
        chapter_audio_path = os.path.join(project_output_dir, chapter_filename)
        
        # 导出章节音频文件
        merged_audio.export(chapter_audio_path, format="wav")
        
        # 计算文件信息
        file_size = os.path.getsize(chapter_audio_path)
        duration_seconds = len(merged_audio) / 1000.0
        
        # 保存章节音频文件记录到数据库
        chapter_audio_file = AudioFile(
            filename=chapter_filename,
            original_name=f"第{chapter_number}章_{chapter_title}",
            file_path=chapter_audio_path,
            file_size=file_size,
            duration=duration_seconds,
            project_id=project_id,
            chapter_id=chapter_id,
            chapter_number=chapter_number,
            character_name=None,  # 章节音频没有特定角色
            speaker="多角色",  # 章节音频包含多个角色
            paragraph_index=None,  # 章节音频不对应特定段落
            character_id=None,
            voice_profile_id=None,
            text_content=f"第{chapter_number}章完整音频",
            audio_type='chapter',  # 标记为章节音频
            processing_time=0,  # 合并不需要处理时间
            model_used='AudioMerge',
            status='active',
            created_at=datetime.utcnow(),
            metadata={
                'merged_segments': merged_segments,
                'total_segment_files': len(audio_files),
                'chapter_title': chapter_title,
                'merge_method': 'pydub_concatenate'
            }
        )
        
        db.add(chapter_audio_file)
        db.commit()
        db.refresh(chapter_audio_file)
        
        logger.info(f"[MERGE_CHAPTER] 章节 {chapter_id} 音频合并完成: {chapter_audio_path}")
        logger.info(f"[MERGE_CHAPTER] 合并统计: {merged_segments}/{len(audio_files)} 个段落, 总时长: {duration_seconds:.2f}s")
        
        return chapter_audio_path
        
    except Exception as e:
        logger.error(f"[MERGE_CHAPTER] 章节 {chapter_id} 音频合并失败: {str(e)}")
        return None