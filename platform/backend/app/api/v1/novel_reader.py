"""
小说朗读API模块
对应 NovelReader.vue 功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Form
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, or_, and_
from typing import Dict, List, Any, Optional

from app.database import get_db
from app.models import NovelProject, TextSegment, VoiceProfile

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
                "estimated_completion": project.estimated_completion.isoformat() if project.estimated_completion else None
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
            speaker = segment.detected_speaker
            if speaker:
                if speaker not in character_stats:
                    character_stats[speaker] = {"count": 0, "voice_assigned": False}
                character_stats[speaker]["count"] += 1
                if segment.voice_profile_id:
                    character_stats[speaker]["voice_assigned"] = True
        
        project_data = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "progress": progress,
            "total_segments": project.total_segments,
            "processed_segments": project.processed_segments,
            "current_segment": project.current_segment,
            "character_mapping": project.character_mapping,
            "final_audio_path": project.final_audio_path,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "started_at": project.started_at.isoformat() if project.started_at else None,
            "completed_at": project.completed_at.isoformat() if project.completed_at else None,
            "estimated_completion": project.estimated_completion.isoformat() if project.estimated_completion else None,
            "character_stats": character_stats,
            "segments_preview": [
                {
                    "id": s.id,
                    "order": s.segment_order,
                    "text": s.text_content[:100] + "..." if len(s.text_content) > 100 else s.text_content,
                    "speaker": s.detected_speaker,
                    "voice_profile_id": s.voice_profile_id,
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
        
        # 获取最新的分段状态统计
        segment_stats = db.query(
            TextSegment.status,
            func.count(TextSegment.id).label('count')
        ).filter(TextSegment.project_id == project_id).group_by(TextSegment.status).all()
        
        stats_dict = {stat.status: stat.count for stat in segment_stats}
        
        # 计算进度
        total = project.total_segments
        processed = stats_dict.get('completed', 0)
        processing = stats_dict.get('processing', 0)
        failed = stats_dict.get('failed', 0)
        pending = stats_dict.get('pending', 0)
        
        progress_percentage = round((processed / total) * 100, 1) if total > 0 else 0
        
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
                    "estimated_completion": project.estimated_completion.isoformat() if project.estimated_completion else None
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
        
        if project.status not in ['pending', 'paused']:
            raise HTTPException(status_code=400, detail=f"项目状态为 {project.status}，无法启动")
        
        # 更新项目状态
        project.status = 'processing'
        db.commit()
        
        # 这里应该启动后台任务处理音频生成
        # 由于没有后台任务框架，暂时只更新状态
        
        return {
            "success": True,
            "message": "项目启动成功",
            "data": {
                "project_id": project.id,
                "status": project.status,
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