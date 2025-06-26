from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.collaboration import (
    ProjectTemplateCreate, ProjectTemplateUpdate, ProjectTemplate,
    EditHistory,
    ExportTaskCreate, ExportTask, ExportFormat,
    ProjectShareCreate, ProjectShareUpdate, ProjectShare,
    SyncStatusResponse,
    BatchExportRequest, BatchExportResponse
)
from app.services.collaboration_service import CollaborationService

router = APIRouter()
collaboration_service = CollaborationService()


# ==================== 项目模板接口 ====================

@router.post("/templates", response_model=ProjectTemplate)
async def create_template(
    template_data: ProjectTemplateCreate,
    db: Session = Depends(get_db)
):
    """创建项目模板"""
    try:
        return collaboration_service.create_template(db, template_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates", response_model=List[ProjectTemplate])
async def get_templates(
    category: Optional[str] = Query(None, description="模板分类"),
    public_only: bool = Query(True, description="仅显示公开模板"),
    db: Session = Depends(get_db)
):
    """获取项目模板列表"""
    return collaboration_service.get_templates(db, category, public_only)


@router.get("/templates/categories")
async def get_template_categories():
    """获取模板分类列表"""
    return {
        "categories": [
            {"value": "audiobook", "label": "有声书"},
            {"value": "podcast", "label": "播客"},
            {"value": "music", "label": "音乐"},
            {"value": "dialogue", "label": "对话"},
            {"value": "narration", "label": "旁白"},
            {"value": "commercial", "label": "商业广告"}
        ]
    }


@router.post("/templates/{template_id}/use", response_model=ProjectTemplate)
async def use_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """使用模板"""
    template = collaboration_service.use_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


# ==================== 版本控制接口 ====================

@router.get("/projects/{project_id}/history", response_model=List[EditHistory])
async def get_edit_history(
    project_id: int,
    limit: int = Query(50, description="返回记录数量限制"),
    db: Session = Depends(get_db)
):
    """获取项目编辑历史"""
    return collaboration_service.get_edit_history(db, project_id, limit)


@router.post("/projects/{project_id}/revert/{version_number}")
async def revert_to_version(
    project_id: int,
    version_number: int,
    db: Session = Depends(get_db)
):
    """回滚到指定版本"""
    snapshot_data = collaboration_service.revert_to_version(db, project_id, version_number)
    if not snapshot_data:
        raise HTTPException(status_code=404, detail="Version not found or no snapshot data")
    
    return {
        "message": f"Successfully reverted to version {version_number}",
        "snapshot_data": snapshot_data
    }


# ==================== 导出任务接口 ====================

@router.post("/export", response_model=ExportTask)
async def create_export_task(
    task_data: ExportTaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """创建导出任务"""
    try:
        task = collaboration_service.create_export_task(db, task_data)
        
        # 添加后台处理任务
        background_tasks.add_task(collaboration_service.process_export_task, db, task.id)
        
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/tasks", response_model=List[ExportTask])
async def get_export_tasks(
    project_id: Optional[int] = Query(None, description="项目ID"),
    db: Session = Depends(get_db)
):
    """获取导出任务列表"""
    return collaboration_service.get_export_tasks(db, project_id)


@router.get("/export/tasks/{task_id}", response_model=ExportTask)
async def get_export_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """获取导出任务详情"""
    tasks = collaboration_service.get_export_tasks(db)
    task = next((t for t in tasks if t.id == task_id), None)
    
    if not task:
        raise HTTPException(status_code=404, detail="Export task not found")
    
    return task


@router.get("/export/formats")
async def get_export_formats():
    """获取支持的导出格式"""
    return {
        "formats": [
            {
                "value": "mp3",
                "label": "MP3",
                "description": "通用音频格式，文件小，兼容性好",
                "extensions": [".mp3"]
            },
            {
                "value": "wav",
                "label": "WAV",
                "description": "无损音频格式，音质最佳",
                "extensions": [".wav"]
            },
            {
                "value": "flac",
                "label": "FLAC",
                "description": "无损压缩格式，音质好，文件较小",
                "extensions": [".flac"]
            },
            {
                "value": "aac",
                "label": "AAC",
                "description": "高效音频编码，音质好，文件小",
                "extensions": [".aac", ".m4a"]
            },
            {
                "value": "ogg",
                "label": "OGG",
                "description": "开源音频格式，音质好",
                "extensions": [".ogg"]
            }
        ]
    }


@router.post("/export/batch", response_model=BatchExportResponse)
async def batch_export(
    request: BatchExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """批量导出项目"""
    try:
        response = collaboration_service.batch_export(db, request)
        
        # 添加后台处理任务
        for task_id in response.task_ids:
            background_tasks.add_task(collaboration_service.process_export_task, db, task_id)
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 项目分享接口 ====================

@router.post("/share", response_model=ProjectShare)
async def create_project_share(
    share_data: ProjectShareCreate,
    db: Session = Depends(get_db)
):
    """创建项目分享"""
    try:
        return collaboration_service.create_project_share(db, share_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/share/{share_token}", response_model=ProjectShare)
async def get_project_share(
    share_token: str,
    db: Session = Depends(get_db)
):
    """通过分享令牌获取项目"""
    share = collaboration_service.get_project_share(db, share_token)
    if not share:
        raise HTTPException(status_code=404, detail="Share not found or expired")
    return share


@router.put("/share/{share_id}", response_model=ProjectShare)
async def update_project_share(
    share_id: int,
    update_data: ProjectShareUpdate,
    db: Session = Depends(get_db)
):
    """更新项目分享设置"""
    share = collaboration_service.update_project_share(db, share_id, update_data)
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    return share


# ==================== 云端同步接口 ====================

@router.get("/sync/{project_id}", response_model=SyncStatusResponse)
async def get_sync_status(
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目同步状态"""
    sync_status = collaboration_service.get_sync_status(db, project_id)
    if not sync_status:
        raise HTTPException(status_code=404, detail="Project not found")
    return sync_status


@router.post("/sync/{project_id}/upload")
async def sync_to_cloud(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """同步项目到云端"""
    # 添加后台同步任务
    background_tasks.add_task(collaboration_service.sync_to_cloud, db, project_id)
    
    return {
        "message": "Sync to cloud started",
        "project_id": project_id
    }


@router.post("/sync/{project_id}/download")
async def sync_from_cloud(
    project_id: int,
    db: Session = Depends(get_db)
):
    """从云端同步项目"""
    # 这里应该实现从云端下载的逻辑
    return {
        "message": "Sync from cloud completed",
        "project_id": project_id
    }


# ==================== 统计接口 ====================

@router.get("/stats/templates")
async def get_template_stats(db: Session = Depends(get_db)):
    """获取模板使用统计"""
    templates = collaboration_service.get_templates(db)
    
    category_stats = {}
    total_usage = 0
    
    for template in templates:
        category = template.category
        if category not in category_stats:
            category_stats[category] = {"count": 0, "usage": 0}
        
        category_stats[category]["count"] += 1
        category_stats[category]["usage"] += template.usage_count
        total_usage += template.usage_count
    
    return {
        "total_templates": len(templates),
        "total_usage": total_usage,
        "category_stats": category_stats,
        "popular_templates": sorted(templates, key=lambda x: x.usage_count, reverse=True)[:5]
    }


@router.get("/stats/exports")
async def get_export_stats(db: Session = Depends(get_db)):
    """获取导出统计"""
    tasks = collaboration_service.get_export_tasks(db)
    
    format_stats = {}
    status_stats = {}
    
    for task in tasks:
        # 格式统计
        format_key = task.export_format
        if format_key not in format_stats:
            format_stats[format_key] = 0
        format_stats[format_key] += 1
        
        # 状态统计
        status_key = task.status
        if status_key not in status_stats:
            status_stats[status_key] = 0
        status_stats[status_key] += 1
    
    return {
        "total_exports": len(tasks),
        "format_stats": format_stats,
        "status_stats": status_stats,
        "recent_exports": tasks[:10]
    } 