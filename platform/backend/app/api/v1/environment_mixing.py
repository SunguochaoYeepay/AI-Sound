"""
环境混音API
提供环境混音作品的管理、生成和下载功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import json

from app.database import get_db
from app.models import NovelProject
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/environment/mixing", tags=["环境混音"])

# 请求模型
class MixingConfigRequest(BaseModel):
    """环境混音配置请求"""
    environment_config: Dict[str, Any]
    chapter_ids: Optional[List[int]] = None
    mixing_options: Optional[Dict[str, Any]] = None

# 响应模型
class MixingResultResponse(BaseModel):
    """混音结果响应"""
    id: int
    project_id: int
    name: Optional[str]
    status: str
    file_path: Optional[str]
    file_url: Optional[str]
    duration: Optional[float]
    environment_tracks_count: Optional[int]
    created_at: str
    updated_at: Optional[str]

class MixingStatsResponse(BaseModel):
    """混音统计响应"""
    total_mixings: int
    completed_mixings: int
    processing_mixings: int
    failed_mixings: int
    total_tracks: int

@router.get("/results")
async def get_mixing_results(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    status: Optional[str] = Query(None, description="状态筛选"),
    db: Session = Depends(get_db)
):
    """
    获取环境混音结果列表
    """
    try:
        # 模拟数据 - 实际应该从数据库查询
        mock_results = [
            {
                "id": 1,
                "project_id": 42,
                "name": "三体环境混音",
                "status": "completed",
                "file_path": "/storage/mixings/mixing_1.wav",
                "file_url": "/api/v1/environment/mixing/1/audio",
                "duration": 1800.5,
                "environment_tracks_count": 8,
                "created_at": "2025-06-23T08:30:00",
                "updated_at": "2025-06-23T09:15:00"
            },
            {
                "id": 2,
                "project_id": 34,
                "name": "科幻场景混音",
                "status": "processing",
                "file_path": None,
                "file_url": None,
                "duration": None,
                "environment_tracks_count": 5,
                "created_at": "2025-06-23T10:00:00",
                "updated_at": "2025-06-23T10:30:00"
            }
        ]
        
        # 应用筛选
        filtered_results = mock_results
        
        if search:
            filtered_results = [r for r in filtered_results if search.lower() in (r.get('name') or '').lower()]
        
        if project_id:
            filtered_results = [r for r in filtered_results if r.get('project_id') == project_id]
            
        if status:
            filtered_results = [r for r in filtered_results if r.get('status') == status]
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_results = filtered_results[start:end]
        
        return {
            "success": True,
            "data": paginated_results,
            "total": len(filtered_results),
            "page": page,
            "page_size": page_size,
            "message": "环境混音结果获取成功"
        }
        
    except Exception as e:
        logger.error(f"获取环境混音结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取环境混音结果失败: {str(e)}")

@router.get("/stats")
async def get_mixing_stats(
    db: Session = Depends(get_db)
):
    """
    获取环境混音统计数据
    """
    try:
        # 模拟统计数据 - 实际应该从数据库统计
        stats = {
            "total_mixings": 15,
            "completed_mixings": 12,
            "processing_mixings": 2,
            "failed_mixings": 1,
            "total_tracks": 85
        }
        
        return {
            "success": True,
            "data": stats,
            "message": "环境混音统计数据获取成功"
        }
        
    except Exception as e:
        logger.error(f"获取环境混音统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取环境混音统计失败: {str(e)}")

@router.post("/{project_id}/start")
async def start_environment_mixing(
    project_id: int,
    config: MixingConfigRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    开始环境混音
    """
    try:
        # 验证项目是否存在
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        logger.info(f"开始为项目 {project_id} 生成环境混音")
        logger.info(f"环境配置: {config.environment_config}")
        
        # 模拟开始混音任务
        mixing_id = f"mixing_{project_id}_{int(datetime.now().timestamp())}"
        
        # 这里应该启动后台任务
        # background_tasks.add_task(process_environment_mixing, project_id, config.dict())
        
        return {
            "success": True,
            "data": {
                "mixing_id": mixing_id,
                "project_id": project_id,
                "status": "started",
                "estimated_duration": "5-10分钟",
                "message": "环境混音任务已启动"
            },
            "message": "环境混音任务启动成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动环境混音失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动环境混音失败: {str(e)}")

@router.get("/{mixing_id}/download")
async def download_mixing(
    mixing_id: int,
    db: Session = Depends(get_db)
):
    """
    下载环境混音作品
    """
    try:
        # 模拟文件下载
        # 实际应该检查混音是否存在，返回文件流
        
        from fastapi.responses import FileResponse
        import os
        
        # 检查文件是否存在
        file_path = f"/path/to/mixing/{mixing_id}.wav"
        if not os.path.exists(file_path):
            # 返回一个空的音频文件响应
            raise HTTPException(status_code=404, detail="混音文件不存在")
        
        return FileResponse(
            file_path,
            media_type="audio/wav",
            filename=f"环境混音_{mixing_id}.wav"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载环境混音失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载环境混音失败: {str(e)}")

@router.delete("/{mixing_id}")
async def delete_mixing(
    mixing_id: int,
    db: Session = Depends(get_db)
):
    """
    删除环境混音作品
    """
    try:
        # 模拟删除操作
        # 实际应该从数据库删除记录并删除文件
        
        logger.info(f"删除环境混音 {mixing_id}")
        
        return {
            "success": True,
            "data": {
                "mixing_id": mixing_id,
                "deleted_at": datetime.now().isoformat()
            },
            "message": "环境混音作品删除成功"
        }
        
    except Exception as e:
        logger.error(f"删除环境混音失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除环境混音失败: {str(e)}")

@router.get("/{mixing_id}")
async def get_mixing_detail(
    mixing_id: int,
    db: Session = Depends(get_db)
):
    """
    获取环境混音详情
    """
    try:
        # 模拟混音详情
        mixing_detail = {
            "id": mixing_id,
            "project_id": 42,
            "name": f"环境混音 {mixing_id}",
            "status": "completed",
            "file_path": f"/storage/mixings/mixing_{mixing_id}.wav",
            "file_url": f"/api/v1/environment/mixing/{mixing_id}/audio",
            "duration": 1800.5,
            "environment_tracks_count": 8,
            "config": {
                "environment_volume": 0.3,
                "fade_duration": 2.0,
                "crossfade_enabled": True
            },
            "tracks": [
                {"name": "森林鸟鸣", "volume": 0.4, "start_time": 0, "duration": 1800},
                {"name": "溪流声", "volume": 0.3, "start_time": 300, "duration": 1200},
                {"name": "风声", "volume": 0.2, "start_time": 0, "duration": 1800}
            ],
            "created_at": "2025-06-23T08:30:00",
            "updated_at": "2025-06-23T09:15:00"
        }
        
        return {
            "success": True,
            "data": mixing_detail,
            "message": "环境混音详情获取成功"
        }
        
    except Exception as e:
        logger.error(f"获取环境混音详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取环境混音详情失败: {str(e)}")

@router.get("/{mixing_id}/audio")
async def get_mixing_audio(
    mixing_id: int,
    db: Session = Depends(get_db)
):
    """
    获取环境混音音频文件
    用于前端播放
    """
    try:
        from fastapi.responses import FileResponse
        import os
        
        # 模拟音频文件路径
        file_path = f"/path/to/mixing/{mixing_id}.wav"
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            # 返回404而不是异常，前端可以处理
            raise HTTPException(status_code=404, detail="音频文件不存在")
        
        return FileResponse(
            file_path,
            media_type="audio/wav",
            headers={
                "Accept-Ranges": "bytes",
                "Content-Disposition": f"inline; filename=mixing_{mixing_id}.wav"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取环境混音音频失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取环境混音音频失败: {str(e)}") 