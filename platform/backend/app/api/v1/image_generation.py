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
from app.services.translation_service import TranslationService
from app.models import ImageGenerationTask, ImageGenerationPreset, BookChapter
from app.utils.exceptions import ServiceException
from app.clients.comfyui_client import ComfyUIClient
from sqlalchemy.orm import joinedload

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
    generated_prompt_chinese: Optional[str]
    negative_prompt: Optional[str]
    negative_prompt_chinese: Optional[str]
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


class TaskDescriptionUpdateRequest(BaseModel):
    """任务描述更新请求"""
    scene_description: Optional[str] = Field(None, description="场景描述")
    emotional_tone: Optional[str] = Field(None, description="情感色调")
    generated_prompt: Optional[str] = Field(None, description="生成的提示词")
    generated_prompt_chinese: Optional[str] = Field(None, description="中文提示词")
    auto_translate: Optional[bool] = Field(True, description="是否自动翻译中文提示词为英文")


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
                "original_prompt": task.original_prompt,
                "backend_added_tags": task.backend_added_tags,
                "generated_prompt": task.generated_prompt,
                "generated_prompt_chinese": task.generated_prompt_chinese,
                "negative_prompt": task.negative_prompt,
                "negative_prompt_chinese": task.negative_prompt_chinese,
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
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"获取图片生成任务失败: {str(e)}\n{error_details}")
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


@router.put("/tasks/{task_id}/description")
async def update_task_description(
    task_id: int,
    request: TaskDescriptionUpdateRequest,
    db: Session = Depends(get_db)
):
    """更新任务描述信息"""
    
    try:
        task = db.query(ImageGenerationTask).filter(ImageGenerationTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail=f"图片生成任务 {task_id} 不存在")
        
        # 更新字段
        if request.scene_description is not None:
            task.scene_description = request.scene_description
        if request.emotional_tone is not None:
            task.emotional_tone = request.emotional_tone
        
        # 处理提示词更新
        if request.generated_prompt_chinese is not None:
            # 保存中文提示词
            task.generated_prompt_chinese = request.generated_prompt_chinese
            logger.info(f"任务 {task_id} 保存中文提示词: {request.generated_prompt_chinese[:50]}...")
            
            # 如果启用自动翻译且有中文提示词，则翻译为英文
            if request.auto_translate and request.generated_prompt_chinese.strip():
                try:
                    logger.info(f"任务 {task_id} 开始翻译中文提示词")
                    translation_service = TranslationService()
                    english_prompt = await translation_service.translate_chinese_to_english(
                        request.generated_prompt_chinese
                    )
                    logger.info(f"任务 {task_id} 翻译结果: {english_prompt[:50]}...")
                    task.generated_prompt = english_prompt
                    logger.info(f"任务 {task_id} 中文提示词自动翻译完成")
                except Exception as e:
                    logger.warning(f"任务 {task_id} 提示词翻译失败: {str(e)}，保持原有英文提示词")
                    # 翻译失败时不更新英文提示词
        
        # 直接更新英文提示词（如果提供）
        if request.generated_prompt is not None:
            logger.info(f"任务 {task_id} 直接更新英文提示词: {request.generated_prompt[:50]}...")
            task.generated_prompt = request.generated_prompt
        
        db.commit()
        
        return {
            "success": True,
            "message": "任务描述更新成功",
            "data": {
                "task_id": task_id,
                "scene_description": task.scene_description,
                "emotional_tone": task.emotional_tone,
                "generated_prompt": task.generated_prompt,
                "generated_prompt_chinese": task.generated_prompt_chinese
            }
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"更新任务描述失败: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=f"更新任务描述失败: {str(e)}")


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


@router.get("/library", response_model=Dict[str, Any])
async def get_image_library(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    book_id: Optional[int] = Query(None, description="书籍ID筛选"),
    chapter_id: Optional[int] = Query(None, description="章节ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """获取图片库列表"""
    
    try:
        # 构建查询
        query = db.query(ImageGenerationTask).filter(
            ImageGenerationTask.status == 'completed',
            ImageGenerationTask.generated_image_url.isnot(None)
        ).options(
            joinedload(ImageGenerationTask.chapter).joinedload(BookChapter.book)
        )
        
        # 应用筛选条件
        if book_id:
            query = query.join(BookChapter).filter(BookChapter.book_id == book_id)
        
        if chapter_id:
            query = query.filter(ImageGenerationTask.chapter_id == chapter_id)
        
        if search:
            query = query.filter(
                ImageGenerationTask.segment_text.contains(search) |
                ImageGenerationTask.scene_description.contains(search) |
                ImageGenerationTask.generated_prompt.contains(search)
            )
        
        # 获取总数
        total_count = query.count()
        
        # 分页查询
        offset = (page - 1) * page_size
        tasks = query.order_by(ImageGenerationTask.completed_at.desc()).offset(offset).limit(page_size).all()
        
        # 构建响应数据
        image_list = []
        for task in tasks:
            image_list.append({
                "id": task.id,
                "chapter_id": task.chapter_id,
                "segment_index": task.segment_index,
                "segment_text": task.segment_text[:100] + "..." if len(task.segment_text) > 100 else task.segment_text,
                "scene_description": task.scene_description,
                "generated_prompt": task.generated_prompt,
                "image_url": task.generated_image_url,
                "image_width": task.image_width,
                "image_height": task.image_height,
                "generation_model": task.generation_model,
                "quality_score": task.quality_score,
                "user_rating": task.user_rating,
                "is_approved": task.is_approved,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "chapter_title": task.chapter.chapter_title if task.chapter else None,
                "book_title": task.chapter.book.title if task.chapter and task.chapter.book else None
            })
        
        return {
            "success": True,
            "data": {
                "images": image_list,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size
            }
        }
        
    except Exception as e:
        logger.error(f"获取图片库失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取图片库失败: {str(e)}")


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