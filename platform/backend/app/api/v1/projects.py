"""
项目管理API
提供TTS项目管理功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Form, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, or_, and_
from typing import List, Optional, Dict, Any
import json
import logging
from datetime import datetime

from app.database import get_db
from app.models import NovelProject, VoiceProfile, Book  # 🚀 TextSegment已删除
from app.utils import log_system_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("")
async def get_projects(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query("", description="搜索关键词"),
    status: str = Query("", description="状态过滤"),
    book_id: Optional[int] = Query(None, description="书籍ID过滤"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    db: Session = Depends(get_db)
):
    """获取项目列表"""
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
        
        # 书籍ID过滤
        if book_id:
            query = query.filter(NovelProject.book_id == book_id)
        
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
            # 🚀 新架构：动态计算进度
            progress = 0
            
            # 获取实际完成的音频文件数量
            audio_count = db.query(AudioFile).filter(
                AudioFile.project_id == project.id,
                AudioFile.audio_type == 'segment'
            ).count()
            
            # 获取智能准备的总段落数量
            total_count = 0
            if project.book_id:
                from app.models import AnalysisResult, BookChapter
                analysis_results = db.query(AnalysisResult).join(
                    BookChapter, AnalysisResult.chapter_id == BookChapter.id
                ).filter(
                    BookChapter.book_id == project.book_id,
                    AnalysisResult.status == 'completed',
                    AnalysisResult.synthesis_plan.isnot(None)
                ).all()
                
                for result in analysis_results:
                    if result.synthesis_plan and 'synthesis_plan' in result.synthesis_plan:
                        segments = result.synthesis_plan['synthesis_plan']
                        total_count += len(segments)
            
            # 计算进度百分比
            if total_count > 0:
                progress = round((audio_count / total_count) * 100, 1)
            
            project_data = project.to_dict()
            project_data['progress'] = progress
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
                "status": status,
                "book_id": book_id
            }
        }
        
    except Exception as e:
        logger.error(f"获取项目列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")

@router.post("")
async def create_project(
    name: str = Form(...),
    description: str = Form(""),
    content: str = Form(""),
    book_id: Optional[int] = Form(None),
    initial_characters: str = Form("[]"),
    settings: str = Form("{}"),
    db: Session = Depends(get_db)
):
    """创建项目"""
    try:
        # 验证项目名称
        if not name or len(name.strip()) == 0:
            raise HTTPException(status_code=400, detail="项目名称不能为空")
        
        # 检查项目名称是否已存在
        existing = db.query(NovelProject).filter(NovelProject.name == name).first()
        if existing:
            raise HTTPException(status_code=400, detail="项目名称已存在")
        
        # 获取文本内容
        text_content = ""
        actual_book_id = None
        
        if book_id:
            # 基于书籍创建
            book = db.query(Book).filter(Book.id == book_id).first()
            if not book:
                raise HTTPException(status_code=404, detail="指定的书籍不存在")
            
            if not book.content or len(book.content.strip()) == 0:
                raise HTTPException(status_code=400, detail="书籍内容为空，无法创建项目")
            
            text_content = book.content
            actual_book_id = book_id
        elif content and content.strip():
            # 直接输入文本
            text_content = content.strip()
            actual_book_id = None
        else:
            raise HTTPException(status_code=400, detail="必须提供书籍ID或文本内容")
        
        # 解析初始角色映射
        try:
            initial_chars = json.loads(initial_characters) if initial_characters else []
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="初始角色格式错误")
        
        # 解析项目设置
        try:
            project_settings = json.loads(settings) if settings else {}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="项目设置格式错误")
        
        # 创建项目记录
        project = NovelProject(
            name=name,
            description=description,
            book_id=actual_book_id,
            status='pending',
            created_at=datetime.utcnow()
        )
        
        # 设置初始角色映射
        char_mapping = {}
        if initial_chars:
            for char_info in initial_chars:
                if isinstance(char_info, dict) and 'name' in char_info and 'voice_id' in char_info:
                    char_mapping[char_info['name']] = char_info['voice_id']
        
        if hasattr(project, 'set_character_mapping'):
            project.set_character_mapping(char_mapping)
        elif hasattr(project, 'character_mapping'):
            project.character_mapping = json.dumps(char_mapping)
        
        # 设置项目配置
        if project_settings and hasattr(project, 'set_settings'):
            project.set_settings(project_settings)
        
        db.add(project)
        db.flush()  # 获取项目ID
        
        # 🚀 新架构：不再需要传统分段，使用智能准备模式
        segments_count = 0
        # 新架构：项目创建时不分段，等待智能准备结果进行合成
        
        db.commit()
        
        # 记录创建日志
        await log_system_event(
            db=db,
            level="info",
            message=f"项目创建: {name}",
            module="projects",
            details={
                "project_id": project.id,
                "book_id": book_id,
                "segments_count": segments_count
            }
        )
        
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

@router.get("/{project_id}")
async def get_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目详情"""
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 🚀 新架构：基于AudioFile获取信息
        from app.models import AudioFile
        audio_files = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.audio_type == 'segment'
        ).all()
        
        # 🚨 项目级别进度计算已废弃
        logger.warning(f"⚠️ 项目详情API中的进度计算已废弃，项目ID: {project_id}")
        progress = 0  # 不再计算项目级别进度
        
        # 获取角色统计
        character_stats = {}
        for audio_file in audio_files:
            speaker = audio_file.speaker or audio_file.character_name
            if speaker:
                if speaker not in character_stats:
                    character_stats[speaker] = {"count": 0, "voice_assigned": False}
                character_stats[speaker]["count"] += 1
                if audio_file.voice_profile_id:
                    character_stats[speaker]["voice_assigned"] = True
        
        project_data = project.to_dict()
        project_data.update({
            "progress": progress,
            "character_stats": character_stats,
            "audio_files_preview": [
                {
                    "id": a.id,
                    "order": a.paragraph_index,
                    "text": a.text_content[:100] + "..." if a.text_content and len(a.text_content) > 100 else (a.text_content or ""),
                    "speaker": a.speaker or a.character_name,
                    "voice_profile_id": a.voice_profile_id,
                    "status": a.status,
                    "duration": a.duration
                }
                for a in audio_files[:10]  # 只返回前10个音频文件预览
            ]
        })
        
        return {
            "success": True,
            "data": project_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目详情失败: {str(e)}")

@router.patch("/{project_id}")
async def update_project(
    project_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    character_mapping: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """更新项目信息"""
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 更新字段
        if name is not None:
            if not name.strip():
                raise HTTPException(status_code=400, detail="项目名称不能为空")
            
            # 检查名称冲突
            existing = db.query(NovelProject).filter(
                NovelProject.name == name,
                NovelProject.id != project_id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="项目名称已存在")
            
            project.name = name.strip()
        
        if description is not None:
            project.description = description.strip()
        
        if character_mapping is not None:
            try:
                char_mapping = json.loads(character_mapping)
                if hasattr(project, 'set_character_mapping'):
                    project.set_character_mapping(char_mapping)
                elif hasattr(project, 'character_mapping'):
                    project.character_mapping = character_mapping
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="角色映射格式错误")
        
        project.updated_at = datetime.utcnow()
        db.commit()
        
        # 记录更新日志
        await log_system_event(
            db=db,
            level="info",
            message=f"项目更新: {project.name}",
            module="projects",
            details={"project_id": project_id}
        )
        
        return {
            "success": True,
            "message": "项目更新成功",
            "data": project.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    force: bool = Query(False, description="强制删除"),
    db: Session = Depends(get_db)
):
    """删除项目"""
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 检查是否正在处理
        if not force and project.status == 'processing':
            raise HTTPException(
                status_code=400, 
                detail="项目正在处理中，请使用强制删除"
            )
        
        project_name = project.name
        
        # 🚀 新架构：删除关联的AudioFile
        from app.models import AudioFile
        db.query(AudioFile).filter(AudioFile.project_id == project_id).delete()
        
        # 删除项目
        db.delete(project)
        db.commit()
        
        # 记录删除日志
        await log_system_event(
            db=db,
            level="info",
            message=f"项目删除: {project_name}",
            module="projects",
            details={"project_id": project_id, "force": force}
        )
        
        return {
            "success": True,
            "message": "项目删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

# 注释掉projects API的进度端点，统一使用novel_reader API
# @router.get("/{project_id}/progress")
# async def get_project_progress(
#     project_id: int,
#     db: Session = Depends(get_db)
# ):
#     """获取项目进度 - 已弃用，请使用 /api/v1/novel-reader/projects/{project_id}/progress"""
#     pass

@router.post("/{project_id}/start")
async def start_project_generation(
    project_id: int,
    parallel_tasks: int = Form(1, description="并行任务数"),
    db: Session = Depends(get_db)
):
    """开始项目生成"""
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if project.status == 'processing':
            raise HTTPException(status_code=400, detail="项目已在处理中")
        
        if project.status == 'completed':
            raise HTTPException(status_code=400, detail="项目已完成")
        
        # 更新项目状态
        project.status = 'processing'
        project.started_at = datetime.utcnow()
        # 🚀 新架构：移除current_segment字段，不再需要设置
        db.commit()
        
        # 记录开始日志
        await log_system_event(
            db=db,
            level="info",
            message=f"项目开始生成: {project.name}",
            module="projects",
            details={
                "project_id": project_id,
                "parallel_tasks": parallel_tasks
            }
        )
        
        return {
            "success": True,
            "message": "项目生成已开始",
            "data": {
                "project_id": project_id,
                "status": project.status,
                "parallel_tasks": parallel_tasks
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动项目生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动失败: {str(e)}")

@router.post("/{project_id}/pause")
async def pause_project_generation(
    project_id: int,
    db: Session = Depends(get_db)
):
    """暂停项目生成"""
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
            message=f"项目暂停: {project.name}",
            module="projects",
            details={"project_id": project_id}
        )
        
        return {
            "success": True,
            "message": "项目已暂停",
            "data": {
                "project_id": project_id,
                "status": project.status
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"暂停项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"暂停失败: {str(e)}") 