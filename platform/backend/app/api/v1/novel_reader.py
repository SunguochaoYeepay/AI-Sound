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
from tempfile import NamedTemporaryFile
from pydub import AudioSegment

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
    """获取项目列表"""
    try:
        # 构建基础查询
        query = db.query(NovelProject)
        
        # 应用搜索过滤
        if search:
            query = query.filter(NovelProject.name.ilike(f"%{search}%"))
        
        # 应用状态过滤
        if status:
            query = query.filter(NovelProject.status == status)
        
        # 应用排序
        if sort_by == "created_at":
            query = query.order_by(desc(NovelProject.created_at) if sort_order == "desc" else asc(NovelProject.created_at))
        else:
            query = query.order_by(desc(NovelProject.id))
        
        # 获取总数
        total = query.count()
        
        # 应用分页
        projects = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # 转换为字典格式
        project_list = []
        for project in projects:
            project_data = project.to_dict()
            project_list.append(project_data)
        
        # 分页信息
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "success": True,
            "data": {
                "projects": project_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        }
        
    except Exception as e:
        logger.error(f"获取项目列表失败: {str(e)}")
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
        # 🚀 新架构：移除旧进度字段，使用动态计算
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
                "total_segments": 0,  # 新架构：创建时总数为0，等待智能准备
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
    """获取项目详情"""
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 转换为字典格式
        project_data = project.to_dict()
        
        return {
            "success": True,
            "data": project_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目详情失败: {str(e)}")

@router.get("/projects/{project_id}/progress")
async def get_generation_progress(
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目生成进度"""
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        return {
            "success": True,
            "data": {
                "project_id": project_id,
                "status": project.status,
                    "started_at": project.started_at.isoformat() if project.started_at else None,
                "completed_at": project.completed_at.isoformat() if project.completed_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目进度失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目进度失败: {str(e)}")

@router.post("/projects/{project_id}/start")
async def start_project_generation(
    project_id: int,
    background_tasks: BackgroundTasks,
    parallel_tasks: int = Form(1, description="并行任务数"),
    synthesis_mode: str = Form("chapters", description="合成模式"),
    chapter_ids: str = Form("", description="章节ID列表，逗号分隔"),
    continue_synthesis: bool = Form(False, description="继续合成模式：true=只生成缺失段落，false=重新合成所有段落"),
    db: Session = Depends(get_db)
):
    """启动项目音频生成"""
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if project.status not in ['pending', 'paused', 'completed', 'failed', 'processing', 'partial_completed']:
            raise HTTPException(status_code=400, detail=f"项目状态为 {project.status}，无法启动")
        
        # 检查智能准备结果
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
        
        # 🔥 修复：如果没有指定章节ID，要求用户选择章节
        if not selected_chapter_ids:
            raise HTTPException(
                status_code=400, 
                detail="请选择要合成的章节。如需合成所有章节，请在前端选择所有章节后再操作。"
            )
        
        # 获取智能准备结果
        from app.models import AnalysisResult, BookChapter
        analysis_query = db.query(AnalysisResult).join(
            BookChapter, AnalysisResult.chapter_id == BookChapter.id
        ).filter(
            BookChapter.book_id == project.book_id,
            AnalysisResult.status == 'completed',
            AnalysisResult.synthesis_plan.isnot(None)
        )
        
        # 只获取选中的章节
        analysis_query = analysis_query.filter(BookChapter.id.in_(selected_chapter_ids))
        logger.info(f"[DEBUG] 按章节筛选合成，选中 {len(selected_chapter_ids)} 个章节")
        
        analysis_results = analysis_query.all()
        
        if not analysis_results:
            raise HTTPException(
                status_code=400, 
                detail="所选章节未找到智能准备结果，请先在书籍管理页面完成智能准备"
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
        
        # 为synthesis_data添加章节信息
        from app.novel_reader import add_chapter_info_to_synthesis_data
        synthesis_data = add_chapter_info_to_synthesis_data(synthesis_data, analysis_results, db)
        logger.info(f"[CHAPTER_FIX] 已为 {len(synthesis_data)} 个段落添加章节信息")
        
        # 🚀 合成模式处理
        if continue_synthesis:
            # 继续合成模式：只生成缺失的段落
            logger.info(f"[CONTINUE_SYNTHESIS] 继续合成模式，检查已存在的音频文件...")
            
            # 获取已存在的音频文件
            existing_audio_files = db.query(AudioFile).filter(
                AudioFile.project_id == project_id,
                AudioFile.audio_type == 'segment',
                AudioFile.chapter_id.in_(selected_chapter_ids)
            ).all()
            
            # 获取已存在的段落ID
            existing_segment_ids = set()
            for audio_file in existing_audio_files:
                if audio_file.paragraph_index is not None:
                    existing_segment_ids.add(audio_file.paragraph_index)
            
            # 过滤出缺失的段落
            missing_segments = []
            for segment_data in synthesis_data:
                segment_id = segment_data.get('segment_id')
                if segment_id not in existing_segment_ids:
                    missing_segments.append(segment_data)
            
            synthesis_data = missing_segments
            logger.info(f"[CONTINUE_SYNTHESIS] 找到 {len(existing_segment_ids)} 个已存在的段落")
            logger.info(f"[CONTINUE_SYNTHESIS] 需要合成 {len(synthesis_data)} 个缺失的段落")
            
            if not synthesis_data:
                return {
                    "success": True,
                    "message": "所有章节的段落都已完成，无需继续合成",
                    "data": {
                        "project_id": project_id,
                        "existing_segments": len(existing_segment_ids),
                        "missing_segments": 0,
                        "selected_chapters": selected_chapter_ids
                    }
                }
        else:
            # 重新合成模式：清理所有现有音频文件
            logger.info(f"[RESTART_SYNTHESIS] 重新合成模式，清理选中章节 {selected_chapter_ids} 的现有音频文件...")
            
            # 删除数据库中的音频文件记录
            existing_audio_files = db.query(AudioFile).filter(
                AudioFile.project_id == project_id,
                AudioFile.audio_type == 'segment',
                AudioFile.chapter_id.in_(selected_chapter_ids)  # 只清理选中章节
            ).all()
            
            for audio_file in existing_audio_files:
                # 删除物理文件
                if audio_file.file_path and os.path.exists(audio_file.file_path):
                    try:
                        os.remove(audio_file.file_path)
                        logger.info(f"[RESTART_SYNTHESIS] 删除音频文件: {audio_file.file_path}")
                    except Exception as e:
                        logger.error(f"[RESTART_SYNTHESIS] 删除音频文件失败: {audio_file.file_path} - {e}")
                
                # 删除数据库记录
                db.delete(audio_file)
            
            # 清理选中章节的最终合成音频文件
            chapter_final_audio_files = db.query(AudioFile).filter(
                AudioFile.project_id == project_id,
                AudioFile.audio_type == 'chapter',
                AudioFile.chapter_id.in_(selected_chapter_ids)
            ).all()
            
            for audio_file in chapter_final_audio_files:
                if audio_file.file_path and os.path.exists(audio_file.file_path):
                    try:
                        os.remove(audio_file.file_path)
                        logger.info(f"[RESTART_SYNTHESIS] 删除章节最终音频文件: {audio_file.file_path}")
                    except Exception as e:
                        logger.error(f"[RESTART_SYNTHESIS] 删除章节最终音频文件失败: {audio_file.file_path} - {e}")
                db.delete(audio_file)
            
            db.commit()
            logger.info(f"[RESTART_SYNTHESIS] 音频文件清理完成")
        
        # 更新项目状态
        project.status = 'processing'
        project.started_at = datetime.utcnow()
        db.commit()
        
        # 启动合成任务
        from app.novel_reader import process_audio_generation_from_synthesis_plan
        background_tasks.add_task(
            process_audio_generation_from_synthesis_plan,
            project_id=project_id,
            synthesis_data=synthesis_data,
            parallel_tasks=parallel_tasks
        )
        
        # 根据合成模式返回不同的消息
        if continue_synthesis:
            message = f"继续合成启动成功，将生成 {len(synthesis_data)} 个缺失的段落"
        else:
            message = f"重新合成启动成功，将生成 {len(synthesis_data)} 个段落"
        
        return {
            "success": True,
            "message": message,
            "data": {
                "project_id": project_id,
                "total_segments": len(synthesis_data),
                "parallel_tasks": parallel_tasks,
                "selected_chapters": selected_chapter_ids,
                "synthesis_mode": "continue" if continue_synthesis else "restart"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动项目失败: {str(e)}")

@router.post("/projects/{project_id}/resume")
async def resume_generation(
    project_id: int,
    background_tasks: BackgroundTasks,
    parallel_tasks: int = Form(1, description="并行任务数"),
    chapter_ids: str = Form("", description="章节ID列表，逗号分隔"),
    db: Session = Depends(get_db)
):
    """恢复项目音频生成"""
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if project.status not in ['paused', 'failed']:
            raise HTTPException(status_code=400, detail=f"项目状态为 {project.status}，无法恢复。只能恢复暂停或失败状态的项目")
        
        # 更新项目状态
        project.status = 'processing'
        db.commit()
        
        # 调用启动API
        return await start_project_generation(
            project_id=project_id,
            background_tasks=background_tasks,
            parallel_tasks=parallel_tasks,
            synthesis_mode="chapters",
            chapter_ids=chapter_ids,
            db=db
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"恢复项目失败: {str(e)}")

@router.post("/projects/{project_id}/retry-failed-segments")
async def retry_all_failed_segments(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """重试所有失败的段落"""
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if not project.book_id:
            raise HTTPException(status_code=400, detail="项目未关联书籍，无法重试")
        
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
            raise HTTPException(status_code=400, detail="未找到智能准备结果")
        
        # 收集所有合成段落数据
        synthesis_data = []
        for result in analysis_results:
            if result.synthesis_plan and 'synthesis_plan' in result.synthesis_plan:
                plan_segments = result.synthesis_plan['synthesis_plan']
                synthesis_data.extend(plan_segments)
        
        # 为synthesis_data添加章节信息
        from app.novel_reader import add_chapter_info_to_synthesis_data
        synthesis_data = add_chapter_info_to_synthesis_data(synthesis_data, analysis_results, db)
        logger.info(f"[CHAPTER_FIX] 已为 {len(synthesis_data)} 个段落添加章节信息")
        
        # 更新项目状态
        project.status = 'processing'
        db.commit()
        
        # 启动合成任务
        from app.services.audio_generation_service import process_audio_generation_from_synthesis_plan
        background_tasks.add_task(
            process_audio_generation_from_synthesis_plan,
            project_id=project_id,
            synthesis_data=synthesis_data,
            parallel_tasks=1  # 重试时使用单线程
        )
        
        return {
            "success": True,
            "message": "开始重试失败的段落",
            "data": {
                "project_id": project_id,
                "total_segments": len(synthesis_data)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重试失败段落失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重试失败段落失败: {str(e)}")

@router.get("/projects/{project_id}/chapters/{chapter_id}/progress")
async def get_chapter_progress(
    project_id: int,
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """获取特定章节的合成进度"""
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 获取该章节的智能准备结果
        from app.models import AnalysisResult, BookChapter, AudioFile
        analysis_result = db.query(AnalysisResult).join(
            BookChapter, AnalysisResult.chapter_id == BookChapter.id
        ).filter(
            BookChapter.book_id == project.book_id,
            BookChapter.id == chapter_id,
            AnalysisResult.status == 'completed',
            AnalysisResult.synthesis_plan.isnot(None)
        ).first()
        
        if not analysis_result:
            return {
                "success": True,
                "data": {
                    "chapter_id": chapter_id,
                    "total_segments": 0,
                    "completed_segments": 0,
                    "progress_percentage": 0,
                    "status": "no_preparation"
                }
            }
        
        # 获取该章节应该有的段落数
        expected_segments = []
        if analysis_result.synthesis_plan and 'synthesis_plan' in analysis_result.synthesis_plan:
            segments = analysis_result.synthesis_plan['synthesis_plan']
            expected_segments = [s.get('segment_id') for s in segments if s.get('segment_id')]
        
        total_segments = len(expected_segments)
        
        if total_segments == 0:
            return {
                "success": True,
                "data": {
                    "chapter_id": chapter_id,
                    "total_segments": 0,
                    "completed_segments": 0,
                    "progress_percentage": 0,
                    "status": "no_segments"
                }
            }
        
        # 查询该章节已完成的AudioFile数量
        completed_audio_files = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.audio_type == 'segment',
            AudioFile.chapter_id == chapter_id,
            AudioFile.paragraph_index.in_(expected_segments)
        ).all()
        
        # 去重：同一个段落ID可能有多个AudioFile记录，只计算唯一的段落ID
        completed_segment_ids = list(set([af.paragraph_index for af in completed_audio_files]))
        completed_segments = len(completed_segment_ids)
        progress_percentage = round((completed_segments / total_segments) * 100, 1) if total_segments > 0 else 0
        
        # 判断章节状态
        if completed_segments == total_segments:
            chapter_status = "completed"
        elif completed_segments > 0:
            chapter_status = "partial"
        elif project.status == 'processing':
            chapter_status = "processing"
        else:
            chapter_status = "pending"
        
        return {
            "success": True,
            "data": {
                "chapter_id": chapter_id,
                "total_segments": total_segments,
                "completed_segments": completed_segments,
                "progress_percentage": progress_percentage,
                "status": chapter_status
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取章节进度失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取章节进度失败: {str(e)}")

@router.get("/projects/{project_id}/segments/status")
async def get_segments_status(
    project_id: int,
    chapter_id: Optional[int] = Query(None, description="章节ID"),
    db: Session = Depends(get_db)
):
    """获取项目段落合成状态"""
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 查询条件
        audio_query = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.audio_type == 'segment'
        )
        
        # 如果指定章节，只查询该章节
        if chapter_id:
            audio_query = audio_query.filter(AudioFile.chapter_id == chapter_id)
        
        # 获取所有音频文件
        audio_files = audio_query.all()
        
        # 构建段落状态映射
        segments_status = {}
        for audio_file in audio_files:
            segment_key = str(audio_file.paragraph_index or audio_file.segment_id or audio_file.id)
            segments_status[segment_key] = {
                "status": "completed",
                "audio_file_id": audio_file.id,
                "chapter_id": audio_file.chapter_id,
                "chapter_number": audio_file.chapter_number,
                "speaker": audio_file.speaker or audio_file.character_name,
                "text_content": audio_file.text_content,
                "filename": audio_file.filename,
                "file_path": audio_file.file_path,
                "duration": audio_file.duration,
                "file_size": audio_file.file_size,
                "voice_profile_id": audio_file.voice_profile_id,
                "processing_time": audio_file.processing_time,
                "created_at": audio_file.created_at.isoformat() if audio_file.created_at else None,
                "download_url": f"/api/v1/novel_reader/projects/{project_id}/segments/{segment_key}/download"
            }
        
        # 按章节组织数据
        chapters_status = {}
        for segment_key, segment_data in segments_status.items():
            chapter_id = segment_data["chapter_id"] or 0
            chapter_key = f"chapter_{chapter_id}"
            
            if chapter_key not in chapters_status:
                chapters_status[chapter_key] = {
                    "chapter_id": chapter_id,
                    "chapter_number": segment_data["chapter_number"],
                    "segments_count": 0,
                    "completed_count": 0,
                    "segments": {}
                }
            
            chapters_status[chapter_key]["segments"][segment_key] = segment_data
            chapters_status[chapter_key]["segments_count"] += 1
            if segment_data["status"] == "completed":
                chapters_status[chapter_key]["completed_count"] += 1
        
        # 获取项目总体状态
        total_segments = len(segments_status)
        completed_segments = sum(1 for s in segments_status.values() if s["status"] == "completed")
        
        logger.info(f"🔍 项目 {project_id} 段落状态查询: 总段落={total_segments}, 已完成={completed_segments}")
        
        return {
            "success": True,
            "data": {
                "project_id": project_id,
                "project_status": project.status,
                "total_segments": total_segments,
                "completed_segments": completed_segments,
                "progress_percentage": round((completed_segments / total_segments) * 100, 1) if total_segments > 0 else 0,
                "chapters": chapters_status,
                "segments": segments_status
            },
            "message": "段落状态获取成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取段落状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取段落状态失败: {str(e)}")

@router.get("/projects/{project_id}/chapters/{chapter_id}/segments/status")
async def get_chapter_segments_status(
    project_id: int,
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """获取指定章节的段落合成状态"""
    try:
        # 验证项目和章节存在性
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        from app.models import BookChapter
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 查询该章节的所有音频文件
        audio_files = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.chapter_id == chapter_id,
            AudioFile.audio_type == 'segment'
        ).order_by(AudioFile.paragraph_index.asc()).all()
        
        # 构建段落详细状态
        segments_detail = []
        for audio_file in audio_files:
            segment_detail = {
                "audio_file_id": audio_file.id,
                "segment_id": audio_file.segment_id,
                "paragraph_index": audio_file.paragraph_index,
                "status": "completed",
                "speaker": audio_file.speaker or audio_file.character_name,
                "text_content": audio_file.text_content,
                "filename": audio_file.filename,
                "file_path": audio_file.file_path,
                "duration": audio_file.duration,
                "file_size": audio_file.file_size,
                "voice_profile_id": audio_file.voice_profile_id,
                "processing_time": audio_file.processing_time,
                "created_at": audio_file.created_at.isoformat() if audio_file.created_at else None,
                "download_url": f"/api/v1/novel_reader/projects/{project_id}/segments/{audio_file.paragraph_index or audio_file.segment_id or audio_file.id}/download"
            }
            segments_detail.append(segment_detail)
        
        # 章节统计信息
        chapter_stats = {
            "chapter_id": chapter.id,
            "chapter_number": chapter.chapter_number,
            "chapter_title": chapter.chapter_title,
            "synthesis_status": chapter.synthesis_status,
            "total_segments": len(segments_detail),
            "completed_segments": len(segments_detail),
            "progress_percentage": 100.0 if segments_detail else 0.0
        }
        
        return {
            "success": True,
            "data": {
                "chapter_stats": chapter_stats,
                "segments": segments_detail
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取章节段落状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取章节段落状态失败: {str(e)}")

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
        
        # 设置取消信息
        # 🚀 新架构：动态计算取消时的进度
        current_progress = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.audio_type == 'segment'
        ).count()
        project.error_message = f"合成已被用户取消，已处理 {current_progress} 个段落"
        
        # 注意：不重置进度字段，保留取消时的进度信息
        # project.processed_segments = 0  # 保留当前进度
        # project.total_segments = None   # 保留总数
        # project.current_segment = None  # 保留当前段落
        # project.failed_segments = 0     # 保留失败数
        
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
        
        # 删除项目相关的所有音频文件（final_audio_path属性不存在，改为删除项目目录）
        from pathlib import Path
        project_output_dir = Path(f"outputs/projects/{project_id}")
        if project_output_dir.exists():
            try:
                import shutil
                shutil.rmtree(project_output_dir)
                logger.info(f"删除项目输出目录: {project_output_dir}")
            except Exception as e:
                logger.warning(f"删除项目输出目录失败: {project_output_dir}, 错误: {e}")
        
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
        
        # 🔥 关键修复：为synthesis_data添加章节信息
        from app.novel_reader import add_chapter_info_to_synthesis_data
        synthesis_data = add_chapter_info_to_synthesis_data(synthesis_data, analysis_results, db)
        logger.info(f"[CHAPTER_FIX] 已为 {len(synthesis_data)} 个段落添加章节信息")
        
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

# 🔧 移除项目下载功能 - 用户不需要项目下载功能
# @router.get("/projects/{project_id}/download")
# async def download_final_audio(project_id: int, db: Session = Depends(get_db)):
#     """下载最终音频文件 - 已移除"""
#     raise HTTPException(status_code=404, detail="项目下载功能已移除")

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
        # 🚀 新架构：不再重置旧进度字段
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
        logger.info(f"🎵 [段落音频请求] 项目:{project_id}, 段落:{segment_id}")
        
        # 🔥 方法1：直接按paragraph_index查找段落音频
        audio_file = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.paragraph_index == segment_id,
            AudioFile.audio_type == 'segment'
        ).first()
        
        if audio_file:
            logger.info(f"✅ [找到段落音频] 段落:{segment_id}, 文件:{audio_file.filename}")
            
            if not os.path.exists(audio_file.file_path):
                logger.error(f"❌ [文件不存在] 段落:{segment_id}, 路径:{audio_file.file_path}")
                raise HTTPException(status_code=404, detail="音频文件物理文件不存在")
            
            return FileResponse(
                path=audio_file.file_path,
                filename=f"chapter_{audio_file.chapter_id}_segment_{segment_id}_{audio_file.character_name or 'unknown'}.wav",
                media_type="audio/wav"
            )
        
        # 🔥 方法2：如果没有找到段落音频，查找该段落所属的章节音频
        logger.info(f"🔍 [段落音频未找到] 尝试查找章节音频...")
        
        # 从智能准备结果中查找该段落所属的章节
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project or not project.book_id:
            logger.error(f"❌ [项目无效] 项目:{project_id} 未关联书籍")
            raise HTTPException(status_code=400, detail="项目未关联书籍")
        
        # 查找该segment_id所属的章节
        from app.models import AnalysisResult, BookChapter
        analysis_results = db.query(AnalysisResult).join(
            BookChapter, AnalysisResult.chapter_id == BookChapter.id
        ).filter(
            BookChapter.book_id == project.book_id,
            AnalysisResult.status == 'completed',
            AnalysisResult.synthesis_plan.isnot(None)
        ).all()
        
        target_chapter_id = None
        target_segment_data = None
        
        for result in analysis_results:
            if result.synthesis_plan and 'synthesis_plan' in result.synthesis_plan:
                for segment_data in result.synthesis_plan['synthesis_plan']:
                    if segment_data.get('segment_id') == segment_id:
                        target_chapter_id = result.chapter_id
                        target_segment_data = segment_data
                        break
            if target_chapter_id:
                break
        
        if not target_chapter_id:
            logger.error(f"❌ [段落不存在] 段落:{segment_id} 在智能准备结果中不存在")
            raise HTTPException(status_code=404, detail=f"段落 {segment_id} 不存在")
        
        # 查找该章节的完整音频文件
        chapter_audio = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.chapter_id == target_chapter_id,
            AudioFile.audio_type == 'chapter'
        ).first()
        
        if chapter_audio and os.path.exists(chapter_audio.file_path):
            logger.info(f"✅ [找到章节音频] 段落:{segment_id} 属于章节:{target_chapter_id}, 返回章节音频")
            
            # 构建更友好的文件名
            chapter = db.query(BookChapter).filter(BookChapter.id == target_chapter_id).first()
            chapter_title = chapter.chapter_title if chapter else f"Chapter_{target_chapter_id}"
            speaker = target_segment_data.get('speaker', 'unknown') if target_segment_data else 'unknown'
            
            return FileResponse(
                path=chapter_audio.file_path,
                filename=f"chapter_{target_chapter_id}_{chapter_title}_segment_{segment_id}_{speaker}.wav",
                media_type="audio/wav"
            )
        
        # 🔥 方法3：如果章节音频也没有，查找该章节的所有段落音频并临时合并
        logger.info(f"🔍 [章节音频未找到] 尝试查找该章节的段落音频...")
        
        chapter_segment_audios = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.chapter_id == target_chapter_id,
            AudioFile.audio_type == 'segment'
        ).order_by(AudioFile.paragraph_index).all()
        
        if not chapter_segment_audios:
            logger.error(f"❌ [无音频文件] 段落:{segment_id} 所属章节:{target_chapter_id} 没有任何音频文件")
            raise HTTPException(status_code=404, detail=f"段落 {segment_id} 所属章节没有音频文件")
        
        # 如果只有一个音频文件，直接返回
        if len(chapter_segment_audios) == 1:
            single_audio = chapter_segment_audios[0]
            if os.path.exists(single_audio.file_path):
                logger.info(f"✅ [返回单个音频] 段落:{segment_id}, 文件:{single_audio.filename}")
                return FileResponse(
                    path=single_audio.file_path,
                    filename=f"chapter_{single_audio.chapter_id}_segment_{segment_id}_{single_audio.character_name or 'unknown'}.wav",
                    media_type="audio/wav"
                )
        
        # 🔥 方法4：临时合并该章节的所有段落音频（作为后备方案）
        logger.info(f"🔧 [临时合并] 段落:{segment_id} 临时合并章节音频...")
        
        try:
            from pydub import AudioSegment
            import tempfile
            
            merged_audio = None
            silence = AudioSegment.silent(duration=500)  # 500ms间隔
            
            for audio_file in chapter_segment_audios:
                if os.path.exists(audio_file.file_path):
                    segment_audio = AudioSegment.from_wav(audio_file.file_path)
                    if merged_audio is None:
                        merged_audio = segment_audio
                    else:
                        merged_audio = merged_audio + silence + segment_audio
            
            if merged_audio:
                # 创建临时文件
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    merged_audio.export(tmp_file.name, format="wav")
                    
                    logger.info(f"✅ [临时合并完成] 段落:{segment_id}, 临时文件:{tmp_file.name}")
                    
                    return FileResponse(
                        path=tmp_file.name,
                        filename=f"chapter_{target_chapter_id}_segment_{segment_id}_merged.wav",
                        media_type="audio/wav"
                    )
        
        except Exception as merge_error:
            logger.error(f"❌ [临时合并失败] 段落:{segment_id}, 错误:{str(merge_error)}")
        
        # 🔥 最终错误：提供详细的调试信息
        logger.error(f"❌ [所有方法失败] 段落:{segment_id} 无法找到对应音频")
        
        # 提供调试信息
        all_audio_files = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.audio_type == 'segment'
        ).all()
        
        available_segments = []
        for af in all_audio_files:
            available_segments.append({
                "paragraph_index": af.paragraph_index,
                "chapter_id": af.chapter_id,
                "filename": af.filename
            })
        
        raise HTTPException(
            status_code=404,
            detail=f"段落 {segment_id} 的音频文件不存在。调试信息：目标章节 {target_chapter_id}，可用段落：{available_segments[:5]}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [段落音频下载异常] 段落:{segment_id}, 错误:{str(e)}")
        raise HTTPException(status_code=500, detail=f"下载段落音频失败: {str(e)}")

@router.get("/projects/{project_id}/chapters/{chapter_id}/download")
async def download_chapter_audio(
    project_id: int,
    chapter_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    下载整个章节的音频文件
    """
    try:
        logger.info(f"🎵 [章节音频下载] 开始处理 - 项目ID: {project_id}, 章节ID: {chapter_id}")
        
        # 🔍 详细调试：查询该项目的所有音频文件
        all_project_audio = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.audio_type == 'segment'
        ).all()
        logger.info(f"🔍 [调试] 项目 {project_id} 总共有 {len(all_project_audio)} 个segment音频文件")
        
        # 🔍 详细调试：按章节分组统计，并显示每个文件的详细信息
        chapter_file_details = {}
        for af in all_project_audio:
            chapter_key = af.chapter_id or af.chapter_number or 'unknown'
            if chapter_key not in chapter_file_details:
                chapter_file_details[chapter_key] = []
            chapter_file_details[chapter_key].append({
                'id': af.id,
                'filename': af.filename,
                'chapter_id': af.chapter_id,
                'chapter_number': af.chapter_number,
                'paragraph_index': af.paragraph_index,
                'speaker': af.speaker,
                'file_path': af.file_path,
                'created_at': af.created_at.isoformat() if af.created_at else 'unknown',
                'file_size': af.file_size
            })
        
        logger.info(f"🔍 [调试] 按章节分组的文件详情:")
        for chapter_key, files in chapter_file_details.items():
            logger.info(f"  📁 章节 {chapter_key}: {len(files)} 个文件")
            for file in files:
                logger.info(f"    🎵 文件: {file['filename']} (ID:{file['id']}, 段落:{file['paragraph_index']}, 说话人:{file['speaker']}, 创建时间:{file['created_at']})")
        
        # 🔍 详细调试：查询目标章节的音频文件
        logger.info(f"🎯 [目标查询] 查找章节 {chapter_id} 的音频文件...")
        
        # 方法1：通过chapter_id查询
        audio_files_by_id = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.audio_type == 'segment',
            AudioFile.chapter_id == chapter_id
        ).order_by(AudioFile.paragraph_index).all()
        
        # 方法2：通过chapter_number查询
        audio_files_by_number = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.audio_type == 'segment',
            AudioFile.chapter_number == chapter_id
        ).order_by(AudioFile.paragraph_index).all()
        
        # 方法3：合并查询（原始逻辑）
        audio_files_combined = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.audio_type == 'segment'
        ).filter(
            or_(
                AudioFile.chapter_id == chapter_id,
                AudioFile.chapter_number == chapter_id
            )
        ).order_by(AudioFile.paragraph_index).all()
        
        logger.info(f"🔍 [查询结果对比]:")
        logger.info(f"  方法1 (chapter_id={chapter_id}): {len(audio_files_by_id)} 个文件")
        logger.info(f"  方法2 (chapter_number={chapter_id}): {len(audio_files_by_number)} 个文件")
        logger.info(f"  方法3 (合并查询): {len(audio_files_combined)} 个文件")
        
        # 使用合并查询的结果
        audio_files = audio_files_combined
        
        # 🔍 详细调试：显示最终查询结果
        logger.info(f"🎵 [最终结果] 找到 {len(audio_files)} 个音频文件:")
        for i, af in enumerate(audio_files):
            logger.info(f"  {i+1}. {af.filename} (ID:{af.id}, 章节ID:{af.chapter_id}, 章节号:{af.chapter_number}, 段落:{af.paragraph_index}, 说话人:{af.speaker})")
            logger.info(f"     文件路径: {af.file_path}")
            logger.info(f"     创建时间: {af.created_at}")
            logger.info(f"     文件大小: {af.file_size} bytes")
        
        if not audio_files:
            logger.warning(f"❌ [查询失败] 未找到章节 {chapter_id} 的音频文件")
            logger.info(f"🔍 [可能原因] 请检查:")
            logger.info(f"  1. 章节ID {chapter_id} 是否正确")
            logger.info(f"  2. 该章节是否已经合成过音频")
            logger.info(f"  3. 音频文件的chapter_id或chapter_number字段是否正确设置")
            
            raise HTTPException(
                status_code=404,
                detail=f"未找到章节 {chapter_id} 的音频文件。请检查章节是否已完成合成。"
            )
        
        # 🔍 详细调试：验证文件是否真实存在
        valid_audio_files = []
        for af in audio_files:
            if not af.file_path:
                logger.warning(f"⚠️ [文件检查] 音频文件 {af.filename} 的file_path为空")
                continue
            if not os.path.exists(af.file_path):
                logger.warning(f"⚠️ [文件检查] 音频文件不存在: {af.file_path}")
                continue
            valid_audio_files.append(af)
        
        if not valid_audio_files:
            logger.error(f"❌ [文件验证失败] 章节 {chapter_id} 的所有音频文件都不存在")
            raise HTTPException(
                status_code=404,
                detail=f"章节 {chapter_id} 的音频文件不存在，请重新合成"
            )
        
        # 获取有效音频文件路径列表
        audio_paths = [af.file_path for af in valid_audio_files]
        
        logger.info(f"🎵 [合并准备] 准备合并 {len(audio_paths)} 个有效音频文件:")
        for i, path in enumerate(audio_paths):
            logger.info(f"  {i+1}. {path}")
        
        # 🔍 详细调试：检查是否是同一个文件
        unique_files = set(audio_paths)
        if len(unique_files) == 1:
            logger.warning(f"⚠️ [重复文件警告] 所有音频文件都指向同一个文件: {list(unique_files)[0]}")
            logger.warning(f"   这可能是导致'播放的永远是最新生成的音频文件'问题的原因！")
        else:
            logger.info(f"✅ [文件唯一性] 找到 {len(unique_files)} 个不同的音频文件")
        
        # 合并音频文件
        try:
            combined_audio = AudioSegment.empty()
            silence = AudioSegment.silent(duration=500)  # 500ms的静音间隔
            
            for i, path in enumerate(audio_paths):
                logger.info(f"🎵 [合并进度] 正在处理第 {i+1}/{len(audio_paths)} 个音频文件: {path}")
                
                try:
                    segment = AudioSegment.from_file(path)
                    combined_audio += segment
                    if i < len(audio_paths) - 1:  # 最后一个片段后不加静音
                        combined_audio += silence
                    logger.info(f"✅ [合并成功] 成功添加音频片段，当前总时长: {len(combined_audio)/1000:.2f}秒")
                except Exception as e:
                    logger.error(f"❌ [合并失败] 处理音频文件失败: {path}, 错误: {str(e)}")
                    continue
            
            logger.info(f"🎉 [合并完成] 音频合并完成，总时长: {len(combined_audio)/1000:.2f}秒")
            
            # 创建临时文件
            with NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                combined_audio.export(temp_file.name, format="wav")
                logger.info(f"📁 [临时文件] 已创建: {temp_file.name}")
                
                # 返回音频文件
                def cleanup_temp_file():
                    try:
                        os.unlink(temp_file.name)
                        logger.info(f"🗑️ [清理] 临时文件已删除: {temp_file.name}")
                    except:
                        pass
                
                background_tasks.add_task(cleanup_temp_file)
                
                return FileResponse(
                    temp_file.name,
                    media_type="audio/wav",
                    filename=f"chapter_{chapter_id}.wav"
                )
                
        except Exception as e:
            logger.error(f"❌ [合并异常] 合并音频文件失败: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"合并音频文件失败: {str(e)}"
            )
            
    except Exception as e:
        logger.error(f"❌ [下载失败] 下载章节音频失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"下载章节音频失败: {str(e)}"
        )

@router.post("/projects/{project_id}/reset-status")
async def reset_project_status(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    重置项目状态 - 解决项目状态卡死问题
    """
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 重置为可用状态
        project.status = 'pending'
        db.commit()
        
        return {
            "success": True,
            "message": "项目状态已重置为可用状态",
            "data": {
                "project_id": project.id,
                "status": project.status
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"重置失败: {str(e)}")

@router.post("/projects/{project_id}/fix-chapter-mapping/{chapter_id}")
async def fix_chapter_audio_mapping(
    project_id: int,
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """
    修复音频文件的章节关联
    将项目的音频文件正确关联到指定章节
    """
    try:
        logger.info(f"🔧 开始修复项目 {project_id} 的音频文件章节关联到章节 {chapter_id}")
        
        # 1. 查询项目信息
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 2. 查询章节信息
        from app.models import BookChapter
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        logger.info(f"📁 项目: {project.name}, 📖 章节: {chapter.chapter_title}")
        
        # 3. 查询该项目的所有音频文件
        audio_files = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.audio_type == 'segment'
        ).all()
        
        logger.info(f"🎵 项目音频文件总数: {len(audio_files)}")
        
        # 找出缺少章节关联的文件
        null_chapter_files = [af for af in audio_files if not af.chapter_id and not af.chapter_number]
        
        logger.info(f"🔧 需要修复的文件数: {len(null_chapter_files)}")
        
        # 4. 修复章节关联
        if null_chapter_files:
            for af in null_chapter_files:
                af.chapter_id = chapter_id
                af.chapter_number = getattr(chapter, 'chapter_number', None)
                logger.info(f"   修复文件 ID={af.id}: chapter_id={af.chapter_id}, chapter_number={af.chapter_number}")
            
            db.commit()
            logger.info(f"✅ 成功修复 {len(null_chapter_files)} 个音频文件的章节关联")
            
            # 5. 验证修复结果
            updated_audio_files = db.query(AudioFile).filter(
                AudioFile.project_id == project_id,
                AudioFile.audio_type == 'segment'
            ).filter(
                or_(
                    AudioFile.chapter_id == chapter_id,
                    AudioFile.chapter_number == chapter_id
                )
            ).all()
            
            logger.info(f"🔍 修复后匹配到的音频文件: {len(updated_audio_files)}")
            
            return {
                "success": True,
                "message": f"成功修复 {len(null_chapter_files)} 个音频文件的章节关联",
                "data": {
                    "project_id": project_id,
                    "chapter_id": chapter_id,
                    "total_files": len(audio_files),
                    "fixed_files": len(null_chapter_files),
                    "matched_files_after_fix": len(updated_audio_files)
                }
            }
        else:
            logger.info("✅ 所有音频文件都已有章节关联，无需修复")
            return {
                "success": True,
                "message": "所有音频文件都已有章节关联，无需修复",
                "data": {
                    "project_id": project_id,
                    "chapter_id": chapter_id,
                    "total_files": len(audio_files),
                    "fixed_files": 0
                }
            }
    
    except Exception as e:
        logger.error(f"修复章节关联失败: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"修复章节关联失败: {str(e)}"
        )