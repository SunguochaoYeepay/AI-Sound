"""
音频库管理API模块
统一管理所有生成的音频文件
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Form
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc, func, or_, and_, text
from typing import Dict, List, Any, Optional
import os
import json
import time
import logging
import wave
import zipfile
import io
from datetime import datetime, timedelta
from pathlib import Path

from database import get_db
from models import AudioFile, NovelProject, TextSegment, VoiceProfile, SystemLog
from utils import log_system_event, get_audio_duration

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/audio-library", tags=["音频库管理"])

# 音频文件存储路径
AUDIO_DIR = "/app/data/audio"

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
            joinedload(AudioFile.voice_profile),
            joinedload(AudioFile.segment)
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
        files_data = [audio_file.to_dict() for audio_file in audio_files]
        
        # 记录日志
        log_system_event(
            db=db,
            level="info", 
            message=f"查询音频文件列表: {len(files_data)}个文件",
            module="audio_library",
            details={"total": total_count, "page": page, "filters": {
                "project_id": project_id,
                "voice_profile_id": voice_profile_id,
                "audio_type": audio_type,
                "search": search
            }}
        )
        
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
        logger.error(f"获取音频文件列表失败: {str(e)}")
        log_system_event(
            db=db,
            level="error",
            message=f"获取音频文件列表失败: {str(e)}",
            module="audio_library"
        )
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
            joinedload(AudioFile.voice_profile),
            joinedload(AudioFile.segment)
        ).filter(AudioFile.id == file_id).first()
        
        if not audio_file:
            raise HTTPException(status_code=404, detail="音频文件不存在")
        
        return {
            "success": True,
            "data": audio_file.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取音频文件详情失败: {str(e)}")
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
        
        # 今日新增
        today = datetime.now().date()
        today_count = db.query(func.count(AudioFile.id)).filter(
            and_(
                AudioFile.status == 'active',
                func.date(AudioFile.created_at) == today
            )
        ).scalar()
        
        # 项目数量
        project_count = db.query(func.count(NovelProject.id)).scalar()
        
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
            func.sum(AudioFile.file_size).label('size')
        ).filter(AudioFile.status == 'active').group_by(AudioFile.audio_type).all()
        
        # 最近几天的趋势
        date_threshold = datetime.now() - timedelta(days=days)
        daily_stats = db.query(
            func.date(AudioFile.created_at).label('date'),
            func.count(AudioFile.id).label('count'),
            func.sum(AudioFile.file_size).label('size')
        ).filter(
            and_(
                AudioFile.status == 'active',
                AudioFile.created_at >= date_threshold
            )
        ).group_by(func.date(AudioFile.created_at)).order_by('date').all()
        
        return {
            "success": True,
            "data": {
                "overview": {
                    "totalFiles": total_files,
                    "totalSize": total_size,
                    "totalSizeMB": round(total_size / 1024 / 1024, 2),
                    "totalDuration": total_duration,
                    "totalDurationFormatted": format_duration(total_duration),
                    "todayCount": today_count,
                    "projectCount": project_count
                },
                "projectStats": [
                    {
                        "projectId": stat.id,
                        "projectName": stat.name,
                        "audioCount": stat.audio_count or 0,
                        "totalSize": stat.total_size or 0,
                        "totalSizeMB": round((stat.total_size or 0) / 1024 / 1024, 2),
                        "totalDuration": stat.total_duration or 0,
                        "totalDurationFormatted": format_duration(stat.total_duration or 0)
                    }
                    for stat in project_stats
                ],
                "typeStats": [
                    {
                        "audioType": stat.audio_type,
                        "count": stat.count,
                        "size": stat.size,
                        "sizeMB": round(stat.size / 1024 / 1024, 2)
                    }
                    for stat in type_stats
                ],
                "dailyStats": [
                    {
                        "date": str(stat.date) if stat.date else "",
                        "count": stat.count,
                        "size": stat.size,
                        "sizeMB": round(stat.size / 1024 / 1024, 2)
                    }
                    for stat in daily_stats
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"获取音频库统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取音频库统计失败: {str(e)}")

@router.delete("/files/{file_id}", summary="删除单个音频文件")
async def delete_audio_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    删除单个音频文件
    """
    try:
        audio_file = db.query(AudioFile).filter(AudioFile.id == file_id).first()
        if not audio_file:
            raise HTTPException(status_code=404, detail="音频文件不存在")
        
        # 删除物理文件
        if audio_file.file_path and os.path.exists(audio_file.file_path):
            os.remove(audio_file.file_path)
        
        # 删除数据库记录
        db.delete(audio_file)
        db.commit()
        
        # 记录日志
        log_system_event(
            db=db,
            level="info",
            message=f"删除音频文件: {audio_file.filename}",
            module="audio_library",
            details={"file_id": file_id, "filename": audio_file.filename}
        )
        
        return {
            "success": True,
            "message": "音频文件删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除音频文件失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除音频文件失败: {str(e)}")

@router.post("/batch-delete", summary="批量删除音频文件")
async def batch_delete_audio_files(
    file_ids: List[int],
    db: Session = Depends(get_db)
):
    """
    批量删除音频文件
    """
    try:
        if not file_ids:
            raise HTTPException(status_code=400, detail="请选择要删除的文件")
        
        # 查询要删除的文件
        audio_files = db.query(AudioFile).filter(AudioFile.id.in_(file_ids)).all()
        
        deleted_count = 0
        deleted_files = []
        
        for audio_file in audio_files:
            try:
                # 删除物理文件
                if audio_file.file_path and os.path.exists(audio_file.file_path):
                    os.remove(audio_file.file_path)
                
                deleted_files.append({
                    "id": audio_file.id,
                    "filename": audio_file.filename
                })
                
                # 删除数据库记录
                db.delete(audio_file)
                deleted_count += 1
                
            except Exception as e:
                logger.warning(f"删除单个文件失败: {audio_file.filename}, 错误: {str(e)}")
        
        db.commit()
        
        # 记录日志
        log_system_event(
            db=db,
            level="info",
            message=f"批量删除音频文件: {deleted_count}个文件",
            module="audio_library",
            details={"deleted_files": deleted_files}
        )
        
        return {
            "success": True,
            "message": f"成功删除 {deleted_count} 个音频文件",
            "deleted_count": deleted_count,
            "deleted_files": deleted_files
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量删除音频文件失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量删除音频文件失败: {str(e)}")

@router.get("/download/{file_id}", summary="下载单个音频文件")
async def download_audio_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    下载单个音频文件
    """
    try:
        audio_file = db.query(AudioFile).filter(AudioFile.id == file_id).first()
        if not audio_file:
            raise HTTPException(status_code=404, detail="音频文件不存在")
        
        if not os.path.exists(audio_file.file_path):
            raise HTTPException(status_code=404, detail="音频文件物理文件不存在")
        
        # 生成下载文件名
        download_name = audio_file.original_name or audio_file.filename
        
        return FileResponse(
            path=audio_file.file_path,
            filename=download_name,
            media_type='audio/wav'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载音频文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载音频文件失败: {str(e)}")

@router.post("/batch-download", summary="批量下载音频文件")
async def batch_download_audio_files(
    file_ids: List[int],
    project_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    批量下载音频文件，打包为ZIP
    """
    try:
        if not file_ids and not project_id:
            raise HTTPException(status_code=400, detail="请选择要下载的文件或项目")
        
        # 构建查询
        query = db.query(AudioFile).options(joinedload(AudioFile.project))
        
        if file_ids:
            query = query.filter(AudioFile.id.in_(file_ids))
        elif project_id:
            query = query.filter(AudioFile.project_id == project_id)
        
        audio_files = query.all()
        
        if not audio_files:
            raise HTTPException(status_code=404, detail="没有找到音频文件")
        
        # 创建内存中的ZIP文件
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for audio_file in audio_files:
                if os.path.exists(audio_file.file_path):
                    # 使用项目名称作为目录结构
                    if audio_file.project:
                        arc_name = f"{audio_file.project.name}/{audio_file.original_name or audio_file.filename}"
                    else:
                        arc_name = audio_file.original_name or audio_file.filename
                    
                    zip_file.write(audio_file.file_path, arc_name)
        
        zip_buffer.seek(0)
        
        # 生成ZIP文件名
        if project_id and audio_files[0].project:
            zip_filename = f"{audio_files[0].project.name}_音频文件.zip"
        else:
            zip_filename = f"音频文件_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        # 记录日志
        log_system_event(
            db=db,
            level="info",
            message=f"批量下载音频文件: {len(audio_files)}个文件",
            module="audio_library",
            details={"file_count": len(audio_files), "project_id": project_id}
        )
        
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量下载音频文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量下载音频文件失败: {str(e)}")

@router.put("/files/{file_id}/favorite", summary="设置音频文件收藏状态")
async def set_audio_favorite(
    file_id: int,
    is_favorite: bool = Form(...),
    db: Session = Depends(get_db)
):
    """
    设置音频文件的收藏状态
    """
    try:
        audio_file = db.query(AudioFile).filter(AudioFile.id == file_id).first()
        if not audio_file:
            raise HTTPException(status_code=404, detail="音频文件不存在")
        
        audio_file.is_favorite = is_favorite
        audio_file.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "message": f"音频文件{'收藏' if is_favorite else '取消收藏'}成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置收藏状态失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"设置收藏状态失败: {str(e)}")

def format_duration(duration_seconds: float) -> str:
    """格式化时长显示"""
    if not duration_seconds:
        return "00:00"
    
    total_seconds = int(duration_seconds)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    
    if minutes >= 60:
        hours = minutes // 60
        minutes = minutes % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

# 音频文件同步功能（将现有音频文件导入数据库）
@router.post("/sync", summary="同步音频文件到数据库")
async def sync_audio_files(
    db: Session = Depends(get_db)
):
    """
    扫描音频目录，将现有文件同步到数据库
    """
    try:
        if not os.path.exists(AUDIO_DIR):
            raise HTTPException(status_code=404, detail="音频目录不存在")
        
        synced_count = 0
        skipped_count = 0
        
        for filename in os.listdir(AUDIO_DIR):
            if not filename.lower().endswith(('.wav', '.mp3', '.flac', '.m4a')):
                continue
            
            # 检查是否已存在
            existing = db.query(AudioFile).filter(AudioFile.filename == filename).first()
            if existing:
                skipped_count += 1
                continue
            
            file_path = os.path.join(AUDIO_DIR, filename)
            file_size = os.path.getsize(file_path)
            
            # 获取音频时长
            try:
                duration = get_audio_duration(file_path)
            except:
                duration = 0.0
            
            # 解析文件名，尝试关联项目和段落
            project_id = None
            segment_id = None
            audio_type = 'unknown'
            
            if filename.startswith('segment_'):
                audio_type = 'segment'
                # 尝试从文件名解析段落ID
                parts = filename.split('_')
                if len(parts) >= 2 and parts[1].isdigit():
                    segment_order = int(parts[1])
                    # 查找对应的段落
                    segment = db.query(TextSegment).filter(
                        TextSegment.segment_order == segment_order
                    ).first()
                    if segment:
                        segment_id = segment.id
                        project_id = segment.project_id
            elif filename.startswith('project_'):
                audio_type = 'project'
                # 尝试从文件名解析项目ID
                parts = filename.split('_')
                if len(parts) >= 2 and parts[1].isdigit():
                    project_id = int(parts[1])
            elif filename.startswith('tts_'):
                audio_type = 'single'
            elif filename.startswith('test_'):
                audio_type = 'test'
            
            # 创建数据库记录
            audio_file = AudioFile(
                filename=filename,
                original_name=filename,
                file_path=file_path,
                file_size=file_size,
                duration=duration,
                project_id=project_id,
                segment_id=segment_id,
                audio_type=audio_type,
                status='active',
                created_at=datetime.fromtimestamp(os.path.getctime(file_path))
            )
            
            db.add(audio_file)
            synced_count += 1
        
        db.commit()
        
        # 记录日志
        log_system_event(
            db=db,
            level="info",
            message=f"音频文件同步完成: 新增{synced_count}个，跳过{skipped_count}个",
            module="audio_library",
            details={"synced": synced_count, "skipped": skipped_count}
        )
        
        return {
            "success": True,
            "message": f"音频文件同步完成",
            "synced_count": synced_count,
            "skipped_count": skipped_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"音频文件同步失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"音频文件同步失败: {str(e)}") 