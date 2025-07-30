"""
图片生成API
提供图片生成相关的RESTful接口
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import os

from app.database import get_db
from app.services.image_generation_service import ImageGenerationService
from app.models import ImageGenerationTask, ImageGenerationPreset, BookChapter
from app.utils.exceptions import ServiceException
from app.clients.comfyui_client import ComfyUIClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/image-generation", tags=["图片生成"])


@router.get("/files/image_generation/{filename}")
async def get_generated_image(filename: str):
    """获取生成的图片文件"""
    
    try:
        # 构建图片文件路径
        file_path = os.path.join("storage", "audio_editor", "exports", "image_generation", filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="图片文件不存在")
        
        # 返回文件，设置为inline模式以便浏览器预览
        return FileResponse(
            path=file_path,
            media_type="image/png",
            filename=filename,
            headers={"Content-Disposition": f"inline; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"获取图片文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取图片文件失败: {str(e)}")


# 请求响应模型
class ImageGenerationTaskCreateRequest(BaseModel):
    """创建图片生成任务请求"""
    chapter_id: int = Field(..., description="章节ID")
    analysis_result_id: Optional[int] = Field(None, description="分析结果ID")
    generation_config: Optional[Dict] = Field(default_factory=dict, description="生成配置")


class ImageGenerationTaskResponse(BaseModel):
    """图片生成任务响应"""
    id: int
    chapter_id: int
    segment_index: int
    segment_text: str
    scene_description: Optional[str]
    generated_prompt: Optional[str]
    status: str
    image_url: Optional[str]
    created_at: Optional[str]
    completed_at: Optional[str]


class BatchGenerationRequest(BaseModel):
    """批量生成请求"""
    chapter_id: int = Field(..., description="章节ID")
    task_ids: Optional[List[int]] = Field(None, description="指定任务ID列表（可选）")


class ImageGenerationPresetCreate(BaseModel):
    """创建图片生成预设请求"""
    name: str = Field(..., description="预设名称")
    description: Optional[str] = Field(None, description="预设描述")
    category: str = Field(default="general", description="预设分类")
    default_workflow: Optional[Dict] = Field(None, description="默认工作流")
    prompt_template: Optional[str] = Field(None, description="提示词模板")
    negative_prompt_template: Optional[str] = Field(None, description="负面提示词模板")
    style_keywords: Optional[List[str]] = Field(default_factory=list, description="风格关键词")
    default_params: Optional[Dict] = Field(default_factory=dict, description="默认参数")


class TaskRatingRequest(BaseModel):
    """任务评分请求"""
    rating: int = Field(..., ge=1, le=5, description="用户评分 1-5")


class TaskApprovalRequest(BaseModel):
    """任务审核请求"""
    approved: bool = Field(..., description="是否通过审核")


@router.post("/tasks/create", response_model=Dict[str, Any])
async def create_image_generation_tasks(
    request: ImageGenerationTaskCreateRequest,
    db: Session = Depends(get_db)
):
    """为章节创建图片生成任务"""
    
    try:
        service = ImageGenerationService(db)
        
        # 检查章节是否存在
        chapter = db.query(BookChapter).filter(BookChapter.id == request.chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail=f"章节 {request.chapter_id} 不存在")
        
        # 创建图片生成任务
        tasks = await service.create_image_generation_tasks_from_chapter(
            chapter_id=request.chapter_id,
            analysis_result_id=request.analysis_result_id,
            generation_config=request.generation_config
        )
        
        return {
            "success": True,
            "message": f"成功为章节 {request.chapter_id} 创建了 {len(tasks)} 个图片生成任务",
            "data": {
                "chapter_id": request.chapter_id,
                "total_tasks": len(tasks),
                "tasks": tasks
            }
        }
        
    except ServiceException as e:
        logger.error(f"创建图片生成任务失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建图片生成任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建图片生成任务失败: {str(e)}")


@router.post("/tasks/{task_id}/generate")
async def start_single_image_generation(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """开始单个图片生成任务"""
    
    try:
        service = ImageGenerationService(db)
        
        # 检查任务是否存在
        task = db.query(ImageGenerationTask).filter(ImageGenerationTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail=f"图片生成任务 {task_id} 不存在")
        
        # 在后台执行生成任务
        background_tasks.add_task(service.generate_single_image, task_id)
        
        return {
            "success": True,
            "message": f"图片生成任务 {task_id} 已开始",
            "data": {
                "task_id": task_id,
                "status": "processing"
            }
        }
        
    except ServiceException as e:
        logger.error(f"开始图片生成失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"开始图片生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"开始图片生成失败: {str(e)}")


@router.post("/tasks/batch-generate", response_model=Dict[str, Any])
async def start_batch_image_generation(
    request: BatchGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """批量开始图片生成"""
    
    try:
        service = ImageGenerationService(db)
        
        # 检查章节是否存在
        chapter = db.query(BookChapter).filter(BookChapter.id == request.chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail=f"章节 {request.chapter_id} 不存在")
        
        # 在后台执行批量生成
        background_tasks.add_task(
            service.batch_generate_images,
            request.chapter_id,
            request.task_ids
        )
        
        return {
            "success": True,
            "message": f"章节 {request.chapter_id} 的批量图片生成已开始",
            "data": {
                "chapter_id": request.chapter_id,
                "status": "processing"
            }
        }
        
    except ServiceException as e:
        logger.error(f"批量图片生成失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"批量图片生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量图片生成失败: {str(e)}")


@router.get("/chapters/{chapter_id}/status", response_model=Dict[str, Any])
async def get_chapter_image_generation_status(
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """获取章节图片生成状态"""
    
    try:
        service = ImageGenerationService(db)
        
        # 检查章节是否存在
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail=f"章节 {chapter_id} 不存在")
        
        status = service.get_chapter_image_generation_status(chapter_id)
        
        return {
            "success": True,
            "data": status
        }
        
    except Exception as e:
        logger.error(f"获取章节图片生成状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_image_generation_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """获取图片生成任务详情"""
    
    try:
        task = db.query(ImageGenerationTask).filter(ImageGenerationTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail=f"图片生成任务 {task_id} 不存在")
        
        return {
            "success": True,
            "data": {
                "id": task.id,
                "chapter_id": task.chapter_id,
                "segment_index": task.segment_index,
                "segment_text": task.segment_text,
                "segment_type": task.segment_type,
                "scene_description": task.scene_description,
                "character_info": task.character_info,
                "emotional_tone": task.emotional_tone,
                "style_keywords": task.style_keywords,
                "generated_prompt": task.generated_prompt,
                "negative_prompt": task.negative_prompt,
                "status": task.status,
                "progress": task.progress,
                "error_message": task.error_message,
                "generated_image_url": task.generated_image_url,
                "generated_image_path": task.generated_image_path,
                "generation_seed": task.generation_seed,
                "generation_time": task.generation_time,
                "quality_score": task.quality_score,
                "user_rating": task.user_rating,
                "is_approved": task.is_approved,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            }
        }
        
    except Exception as e:
        logger.error(f"获取图片生成任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务失败: {str(e)}")


@router.put("/tasks/{task_id}/rating")
async def update_task_rating(
    task_id: int,
    request: TaskRatingRequest,
    db: Session = Depends(get_db)
):
    """更新任务用户评分"""
    
    try:
        task = db.query(ImageGenerationTask).filter(ImageGenerationTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail=f"图片生成任务 {task_id} 不存在")
        
        task.user_rating = request.rating
        db.commit()
        
        return {
            "success": True,
            "message": "评分更新成功",
            "data": {
                "task_id": task_id,
                "user_rating": request.rating
            }
        }
        
    except Exception as e:
        logger.error(f"更新任务评分失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新评分失败: {str(e)}")


@router.put("/tasks/{task_id}/approve")
async def approve_task(
    task_id: int,
    request: TaskApprovalRequest,
    db: Session = Depends(get_db)
):
    """审核通过/拒绝任务"""
    
    try:
        task = db.query(ImageGenerationTask).filter(ImageGenerationTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail=f"图片生成任务 {task_id} 不存在")
        
        task.is_approved = request.approved
        db.commit()
        
        return {
            "success": True,
            "message": f"任务已{'通过' if request.approved else '拒绝'}审核",
            "data": {
                "task_id": task_id,
                "is_approved": request.approved
            }
        }
        
    except Exception as e:
        logger.error(f"审核任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"审核任务失败: {str(e)}")


@router.delete("/tasks/{task_id}")
async def delete_image_generation_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """删除图片生成任务"""
    
    try:
        task = db.query(ImageGenerationTask).filter(ImageGenerationTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail=f"图片生成任务 {task_id} 不存在")
        
        # 删除本地图片文件
        if task.generated_image_path:
            if os.path.exists(task.generated_image_path):
                os.remove(task.generated_image_path)
        
        db.delete(task)
        db.commit()
        
        return {
            "success": True,
            "message": f"图片生成任务 {task_id} 已删除"
        }
        
    except Exception as e:
        logger.error(f"删除图片生成任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")


# 预设管理API
@router.post("/presets", response_model=Dict[str, Any])
async def create_image_generation_preset(
    request: ImageGenerationPresetCreate,
    db: Session = Depends(get_db)
):
    """创建图片生成预设"""
    
    try:
        preset = ImageGenerationPreset(
            name=request.name,
            description=request.description,
            category=request.category,
            default_workflow=request.default_workflow,
            prompt_template=request.prompt_template,
            negative_prompt_template=request.negative_prompt_template,
            style_keywords=request.style_keywords,
            default_params=request.default_params
        )
        
        db.add(preset)
        db.commit()
        db.refresh(preset)
        
        return {
            "success": True,
            "message": "图片生成预设创建成功",
            "data": {
                "id": preset.id,
                "name": preset.name,
                "category": preset.category
            }
        }
        
    except Exception as e:
        logger.error(f"创建图片生成预设失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建预设失败: {str(e)}")


@router.get("/presets", response_model=Dict[str, Any])
async def list_image_generation_presets(
    category: Optional[str] = None,
    is_public: Optional[bool] = True,
    db: Session = Depends(get_db)
):
    """获取图片生成预设列表"""
    
    try:
        query = db.query(ImageGenerationPreset)
        
        if category:
            query = query.filter(ImageGenerationPreset.category == category)
        
        if is_public is not None:
            query = query.filter(ImageGenerationPreset.is_public == is_public)
        
        presets = query.order_by(ImageGenerationPreset.usage_count.desc()).all()
        
        preset_list = []
        for preset in presets:
            preset_list.append({
                "id": preset.id,
                "name": preset.name,
                "description": preset.description,
                "category": preset.category,
                "usage_count": preset.usage_count,
                "success_rate": preset.success_rate,
                "is_public": preset.is_public,
                "created_at": preset.created_at.isoformat() if preset.created_at else None
            })
        
        return {
            "success": True,
            "data": {
                "total": len(preset_list),
                "presets": preset_list
            }
        }
        
    except Exception as e:
        logger.error(f"获取图片生成预设列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取预设列表失败: {str(e)}")


@router.get("/presets/{preset_id}", response_model=Dict[str, Any])
async def get_image_generation_preset(
    preset_id: int,
    db: Session = Depends(get_db)
):
    """获取图片生成预设详情"""
    
    try:
        preset = db.query(ImageGenerationPreset).filter(ImageGenerationPreset.id == preset_id).first()
        if not preset:
            raise HTTPException(status_code=404, detail=f"图片生成预设 {preset_id} 不存在")
        
        return {
            "success": True,
            "data": {
                "id": preset.id,
                "name": preset.name,
                "description": preset.description,
                "category": preset.category,
                "default_workflow": preset.default_workflow,
                "prompt_template": preset.prompt_template,
                "negative_prompt_template": preset.negative_prompt_template,
                "style_keywords": preset.style_keywords,
                "default_params": preset.default_params,
                "recommended_models": preset.recommended_models,
                "is_public": preset.is_public,
                "usage_count": preset.usage_count,
                "success_rate": preset.success_rate,
                "created_at": preset.created_at.isoformat() if preset.created_at else None,
                "updated_at": preset.updated_at.isoformat() if preset.updated_at else None
            }
        }
        
    except Exception as e:
        logger.error(f"获取图片生成预设失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取预设失败: {str(e)}")


@router.get("/comfyui/test-connection")
async def test_comfyui_connection():
    """测试ComfyUI连接"""
    
    try:
        client = ComfyUIClient()
        is_connected = await client.test_connection()
        
        return {
            "success": True,
            "data": {
                "connected": is_connected,
                "server_address": client.server_address
            }
        }
        
    except Exception as e:
        logger.error(f"测试ComfyUI连接失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/comfyui/models")
async def get_comfyui_models():
    """获取ComfyUI可用模型"""
    
    try:
        client = ComfyUIClient()
        models = await client.get_models()
        
        return {
            "success": True,
            "data": {
                "models": models
            }
        }
        
    except Exception as e:
        logger.error(f"获取ComfyUI模型失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }