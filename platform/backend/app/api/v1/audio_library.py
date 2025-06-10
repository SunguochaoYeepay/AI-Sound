"""
音频库管理API模块
统一管理所有生成的音频文件
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc, func, or_, and_
from typing import Dict, List, Any, Optional

from app.database import get_db
from app.models import AudioFile, NovelProject, TextSegment, VoiceProfile

router = APIRouter(prefix="/audio-library", tags=["Audio Library"])

@router.get("/files", summary="获取音频文件列表")
async def get_audio_files(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    voice_profile_id: Optional[int] = Query(None, description="角色ID筛选"),
    audio_type: Optional[str] = Query(None, description="音频类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向")
):
    """
    获取音频文件列表，支持分页、筛选、搜索、排序
    """
    try:
        # 构建基础查询
        query = db.query(AudioFile).options(
            joinedload(AudioFile.project),
            joinedload(AudioFile.voice_profile)
        )
        
        # 应用筛选条件
        if project_id:
            query = query.filter(AudioFile.project_id == project_id)
        
        if voice_profile_id:
            query = query.filter(AudioFile.voice_profile_id == voice_profile_id)
        
        if audio_type:
            query = query.filter(AudioFile.audio_type == audio_type)
        
        if status:
            query = query.filter(AudioFile.status == status)
        
        # 搜索功能
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    AudioFile.filename.like(search_term),
                    AudioFile.original_name.like(search_term),
                    AudioFile.text_content.like(search_term)
                )
            )
        
        # 总数统计
        total_count = query.count()
        
        # 排序
        sort_column = getattr(AudioFile, sort_by, AudioFile.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # 分页
        offset = (page - 1) * page_size
        audio_files = query.offset(offset).limit(page_size).all()
        
        # 转换为字典格式
        files_data = []
        for audio_file in audio_files:
            file_data = {
                "id": audio_file.id,
                "filename": audio_file.filename,
                "original_name": audio_file.original_name,
                "file_path": audio_file.file_path,
                "file_size": audio_file.file_size,
                "duration": audio_file.duration,
                "audio_type": audio_file.audio_type,
                "text_content": audio_file.text_content,
                "is_favorite": audio_file.is_favorite,
                "status": audio_file.status,
                "created_at": audio_file.created_at.isoformat() if audio_file.created_at else None,
                "updated_at": audio_file.updated_at.isoformat() if audio_file.updated_at else None,
                "project": {
                    "id": audio_file.project.id,
                    "name": audio_file.project.name
                } if audio_file.project else None,
                "voice_profile": {
                    "id": audio_file.voice_profile.id,
                    "name": audio_file.voice_profile.name
                } if audio_file.voice_profile else None
            }
            files_data.append(file_data)
        
        return {
            "success": True,
            "data": files_data,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total_count,
                "totalPages": (total_count + page_size - 1) // page_size
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取音频文件列表失败: {str(e)}")

@router.get("/files/{file_id}", summary="获取单个音频文件详情")
async def get_audio_file_detail(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个音频文件的详细信息
    """
    try:
        audio_file = db.query(AudioFile).options(
            joinedload(AudioFile.project),
            joinedload(AudioFile.voice_profile)
        ).filter(AudioFile.id == file_id).first()
        
        if not audio_file:
            raise HTTPException(status_code=404, detail="音频文件不存在")
        
        file_data = {
            "id": audio_file.id,
            "filename": audio_file.filename,
            "original_name": audio_file.original_name,
            "file_path": audio_file.file_path,
            "file_size": audio_file.file_size,
            "duration": audio_file.duration,
            "audio_type": audio_file.audio_type,
            "text_content": audio_file.text_content,
            "is_favorite": audio_file.is_favorite,
            "status": audio_file.status,
            "created_at": audio_file.created_at.isoformat() if audio_file.created_at else None,
            "updated_at": audio_file.updated_at.isoformat() if audio_file.updated_at else None,
            "project": {
                "id": audio_file.project.id,
                "name": audio_file.project.name,
                "description": audio_file.project.description
            } if audio_file.project else None,
            "voice_profile": {
                "id": audio_file.voice_profile.id,
                "name": audio_file.voice_profile.name,
                "type": audio_file.voice_profile.type
            } if audio_file.voice_profile else None
        }
        
        return {
            "success": True,
            "data": file_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取音频文件详情失败: {str(e)}")

@router.get("/stats", summary="获取音频库统计信息")
async def get_audio_stats(
    db: Session = Depends(get_db),
    days: int = Query(30, description="统计天数")
):
    """
    获取音频库的统计信息
    """
    try:
        # 基础统计
        total_files = db.query(func.count(AudioFile.id)).filter(
            AudioFile.status == 'active'
        ).scalar()
        
        total_size = db.query(func.sum(AudioFile.file_size)).filter(
            AudioFile.status == 'active'
        ).scalar() or 0
        
        total_duration = db.query(func.sum(AudioFile.duration)).filter(
            AudioFile.status == 'active'
        ).scalar() or 0
        
        # 按项目统计
        project_stats = db.query(
            NovelProject.id,
            NovelProject.name,
            func.count(AudioFile.id).label('audio_count'),
            func.sum(AudioFile.file_size).label('total_size'),
            func.sum(AudioFile.duration).label('total_duration')
        ).outerjoin(AudioFile).filter(
            or_(AudioFile.status == 'active', AudioFile.id.is_(None))
        ).group_by(NovelProject.id, NovelProject.name).all()
        
        # 按音频类型统计
        type_stats = db.query(
            AudioFile.audio_type,
            func.count(AudioFile.id).label('count'),
            func.sum(AudioFile.file_size).label('total_size')
        ).filter(AudioFile.status == 'active').group_by(AudioFile.audio_type).all()
        
        return {
            "success": True,
            "data": {
                "summary": {
                    "total_files": total_files,
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "total_duration_seconds": total_duration,
                    "total_duration_minutes": round(total_duration / 60, 1)
                },
                "by_project": [
                    {
                        "project_id": p.id,
                        "project_name": p.name,
                        "audio_count": p.audio_count,
                        "total_size_mb": round((p.total_size or 0) / (1024 * 1024), 2),
                        "total_duration_minutes": round((p.total_duration or 0) / 60, 1)
                    }
                    for p in project_stats
                ],
                "by_type": [
                    {
                        "audio_type": t.audio_type,
                        "count": t.count,
                        "total_size_mb": round((t.total_size or 0) / (1024 * 1024), 2)
                    }
                    for t in type_stats
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.post("/files/{file_id}/favorite")
async def toggle_favorite(
    file_id: int,
    db: Session = Depends(get_db)
):
    """切换收藏状态"""
    try:
        audio_file = db.query(AudioFile).filter(AudioFile.id == file_id).first()
        if not audio_file:
            raise HTTPException(status_code=404, detail="音频文件不存在")
        
        # 切换收藏状态
        audio_file.is_favorite = not audio_file.is_favorite
        db.commit()
        
        return {
            "success": True,
            "message": f"{'添加到收藏' if audio_file.is_favorite else '取消收藏'}成功",
            "data": {
                "is_favorite": audio_file.is_favorite
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"切换收藏状态失败: {str(e)}")