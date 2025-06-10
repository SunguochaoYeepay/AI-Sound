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
from app.models import NovelProject, TextSegment, VoiceProfile, Book
from app.utils import log_system_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("")
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
                "status": status
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
        
        # 简单的文本分段（实际项目中应该有更复杂的逻辑）
        segments_count = 0
        if text_content:
            # 按段落分割
            paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]
            
            for i, para in enumerate(paragraphs):
                if len(para) > 10:  # 忽略太短的段落
                    segment = TextSegment(
                        project_id=project.id,
                        segment_order=i + 1,
                        text_content=para,
                        status='pending',
                        created_at=datetime.utcnow()
                    )
                    db.add(segment)
                    segments_count += 1
            
            project.total_segments = segments_count
        
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
        
        # 获取分段信息
        segments = db.query(TextSegment).filter(TextSegment.project_id == project_id).all()
        
        # 计算进度百分比
        progress = 0
        if project.total_segments > 0:
            progress = round((project.processed_segments / project.total_segments) * 100, 1)
        
        # 获取角色统计
        character_stats = {}
        for segment in segments:
            speaker = getattr(segment, 'detected_speaker', None)
            if speaker:
                if speaker not in character_stats:
                    character_stats[speaker] = {"count": 0, "voice_assigned": False}
                character_stats[speaker]["count"] += 1
                if getattr(segment, 'voice_profile_id', None):
                    character_stats[speaker]["voice_assigned"] = True
        
        project_data = project.to_dict()
        project_data.update({
            "progress": progress,
            "character_stats": character_stats,
            "segments_preview": [
                {
                    "id": s.id,
                    "order": s.segment_order,
                    "text": s.text_content[:100] + "..." if len(s.text_content) > 100 else s.text_content,
                    "speaker": getattr(s, 'detected_speaker', None),
                    "voice_profile_id": getattr(s, 'voice_profile_id', None),
                    "status": s.status
                }
                for s in segments[:10]  # 只返回前10个分段预览
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
        
        # 删除关联的分段
        db.query(TextSegment).filter(TextSegment.project_id == project_id).delete()
        
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

@router.get("/{project_id}/progress")
async def get_project_progress(
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目进度"""
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 获取分段状态统计
        segment_stats = db.query(
            TextSegment.status,
            func.count(TextSegment.id).label('count')
        ).filter(TextSegment.project_id == project_id).group_by(TextSegment.status).all()
        
        status_counts = {stat.status: stat.count for stat in segment_stats}
        
        # 计算进度
        total = project.total_segments or 0
        processed = project.processed_segments or 0
        progress = round((processed / total) * 100, 1) if total > 0 else 0
        
        return {
            "success": True,
            "data": {
                "project_id": project_id,
                "status": project.status,
                "progress": progress,
                "total_segments": total,
                "processed_segments": processed,
                "segment_status_counts": status_counts,
                "current_segment": project.current_segment,
                "estimated_completion": project.estimated_completion.isoformat() if project.estimated_completion else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目进度失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取进度失败: {str(e)}")

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
        project.current_segment = 1
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