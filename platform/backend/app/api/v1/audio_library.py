"""
音频库管理API模块
统一管理所有生成的音频文件
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc, func, or_, and_
from typing import Dict, List, Any, Optional
import os
import json
import time
import logging
from datetime import datetime

from app.database import get_db
from app.models import AudioFile, NovelProject, VoiceProfile  # TextSegment已废弃

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audio-library", tags=["Audio Library"])

# 音频文件存储路径
AUDIO_DIR = os.getenv("AUDIO_DIR", "data/audio")

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
        
        # 今日新增统计
        today = datetime.now().date()
        today_files = db.query(func.count(AudioFile.id)).filter(
            AudioFile.status == 'active',
            func.date(AudioFile.created_at) == today
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
                    "total_duration_minutes": round(total_duration / 60, 1),
                    "today_count": today_files
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

@router.get("/download/{file_id}", summary="下载单个音频文件")
async def download_audio_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    下载单个音频文件
    """
    try:
        logger.info(f"🔍 [下载请求] 查找音频文件 ID: {file_id}")
        
        audio_file = db.query(AudioFile).filter(AudioFile.id == file_id).first()
        if not audio_file:
            logger.error(f"❌ [下载失败] 音频文件不存在: ID={file_id}")
            raise HTTPException(status_code=404, detail=f"音频文件不存在: ID={file_id}")
        
        logger.info(f"✅ [找到文件] ID={audio_file.id}, filename={audio_file.filename}, path={audio_file.file_path}")
        
        if not audio_file.file_path:
            logger.error(f"❌ [下载失败] 文件路径为空: ID={file_id}")
            raise HTTPException(status_code=404, detail="音频文件路径为空")
        
        if not os.path.exists(audio_file.file_path):
            logger.error(f"❌ [下载失败] 物理文件不存在: ID={file_id}, path={audio_file.file_path}")
            raise HTTPException(status_code=404, detail=f"音频文件物理文件不存在: {audio_file.file_path}")
        
        # 生成下载文件名
        download_name = audio_file.original_name or audio_file.filename
        
        logger.info(f"📦 [开始下载] ID={file_id}, filename={download_name}, path={audio_file.file_path}")
        
        return FileResponse(
            path=audio_file.file_path,
            filename=download_name,
            media_type='audio/wav'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [下载异常] ID={file_id}, error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载音频文件失败: {str(e)}")

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

@router.post("/sync", summary="同步音频文件到数据库（Legacy）")
async def sync_audio_files_legacy(
    db: Session = Depends(get_db)
):
    """
    旧版音频文件同步功能（保持兼容性）
    推荐使用 /audio-sync/ 下的新版同步API
    """
    try:
        # 导入新的同步服务
        from app.services.audio_sync_service import audio_sync_service
        
        # 使用新服务进行同步
        result = audio_sync_service.sync_audio_files(db, full_scan=False)
        
        return {
            "success": True,
            "message": f"音频文件同步完成（使用增强版同步服务）",
            "synced_count": result.new_files + result.updated_files,
            "skipped_count": result.scanned_files - result.new_files - result.updated_files,
            "details": {
                "scanned_files": result.scanned_files,
                "new_files": result.new_files,
                "updated_files": result.updated_files,
                "orphaned_records": result.orphaned_records,
                "errors": result.errors
            }
        }
        
    except ImportError:
        # 如果新服务不可用，回退到旧版逻辑
        logger.warning("新版同步服务不可用，回退到旧版同步逻辑")
        
        if not os.path.exists(AUDIO_DIR):
            logger.warning(f"音频目录不存在: {AUDIO_DIR}")
            os.makedirs(AUDIO_DIR, exist_ok=True)
            return {
                "success": True,
                "message": "音频目录已创建，当前无文件需要同步",
                "synced_count": 0,
                "skipped_count": 0
            }
        
        synced_count = 0
        skipped_count = 0
        
        # 获取音频时长的辅助函数
        def get_audio_duration(file_path):
            try:
                import wave
                with wave.open(file_path, 'r') as wav_file:
                    frames = wav_file.getnframes()
                    rate = wav_file.getframerate()
                    return frames / float(rate)
            except:
                return 0.0
        
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
            elif filename.startswith('project_'):
                audio_type = 'project'
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
        
        logger.info(f"音频文件同步完成: 新增{synced_count}个，跳过{skipped_count}个")
        
        return {
            "success": True,
            "message": f"音频文件同步完成（旧版）",
            "synced_count": synced_count,
            "skipped_count": skipped_count
        }
        
    except Exception as e:
        logger.error(f"音频文件同步失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"音频文件同步失败: {str(e)}")