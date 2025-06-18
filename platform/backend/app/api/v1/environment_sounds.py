#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import requests
import base64
import os
import json
from datetime import datetime

from app.database import get_db
from app.models.environment_sound import (
    EnvironmentSound, EnvironmentSoundCategory, EnvironmentSoundTag,
    EnvironmentSoundFavorite, EnvironmentSoundUsageLog, EnvironmentSoundPreset
)
from app.schemas.environment_sound import (
    EnvironmentSoundCreate, EnvironmentSoundUpdate, EnvironmentSoundResponse,
    EnvironmentSoundCategoryResponse, EnvironmentSoundTagResponse,
    EnvironmentSoundGenerateRequest, EnvironmentSoundGenerateResponse,
    EnvironmentSoundListResponse
)
from app.utils.file_manager import save_audio_file, get_audio_file_path
from app.config.environment import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

# TangoFlux API配置
TANGOFLUX_API_URL = "http://127.0.0.1:7930"

@router.get("/categories", response_model=List[EnvironmentSoundCategoryResponse])
async def get_categories(
    active_only: bool = Query(True, description="仅返回激活的分类"),
    db: Session = Depends(get_db)
):
    """获取环境音分类列表"""
    query = db.query(EnvironmentSoundCategory)
    if active_only:
        query = query.filter(EnvironmentSoundCategory.is_active == True)
    
    categories = query.order_by(EnvironmentSoundCategory.sort_order.desc()).all()
    return categories

@router.get("/tags", response_model=List[EnvironmentSoundTagResponse])
async def get_tags(
    popular_only: bool = Query(False, description="仅返回热门标签"),
    limit: int = Query(50, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """获取环境音标签列表"""
    query = db.query(EnvironmentSoundTag)
    
    if popular_only:
        query = query.filter(EnvironmentSoundTag.usage_count > 0)
        query = query.order_by(EnvironmentSoundTag.usage_count.desc())
    else:
        query = query.order_by(EnvironmentSoundTag.name)
    
    tags = query.limit(limit).all()
    return tags

@router.get("/presets", response_model=List[dict])
async def get_presets(
    category_id: Optional[int] = Query(None, description="分类ID筛选"),
    db: Session = Depends(get_db)
):
    """获取环境音预设列表"""
    query = db.query(EnvironmentSoundPreset).filter(EnvironmentSoundPreset.is_active == True)
    
    if category_id:
        query = query.filter(EnvironmentSoundPreset.category_id == category_id)
    
    presets = query.order_by(EnvironmentSoundPreset.sort_order.desc()).all()
    
    result = []
    for preset in presets:
        preset_data = {
            "id": preset.id,
            "name": preset.name,
            "description": preset.description,
            "default_duration": preset.default_duration,
            "default_steps": preset.default_steps,
            "default_cfg_scale": preset.default_cfg_scale,
            "category_id": preset.category_id
        }
        
        # 解析JSON字段
        if preset.prompt_templates:
            try:
                preset_data["prompt_templates"] = json.loads(preset.prompt_templates)
            except:
                preset_data["prompt_templates"] = []
        
        if preset.example_prompts:
            try:
                preset_data["example_prompts"] = json.loads(preset.example_prompts)
            except:
                preset_data["example_prompts"] = []
        
        result.append(preset_data)
    
    return result

@router.get("/", response_model=EnvironmentSoundListResponse)
async def get_environment_sounds(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category_id: Optional[int] = Query(None, description="分类ID筛选"),
    tag_ids: Optional[str] = Query(None, description="标签ID列表，逗号分隔"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="生成状态筛选"),
    featured_only: bool = Query(False, description="仅返回精选"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    db: Session = Depends(get_db)
):
    """获取环境音列表"""
    
    # 构建查询
    query = db.query(EnvironmentSound)
    
    # 筛选条件
    if category_id:
        query = query.filter(EnvironmentSound.category_id == category_id)
    
    if tag_ids:
        tag_id_list = [int(tid.strip()) for tid in tag_ids.split(",") if tid.strip().isdigit()]
        if tag_id_list:
            query = query.join(EnvironmentSound.tags).filter(EnvironmentSoundTag.id.in_(tag_id_list))
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            EnvironmentSound.name.ilike(search_term) |
            EnvironmentSound.prompt.ilike(search_term) |
            EnvironmentSound.description.ilike(search_term)
        )
    
    if status:
        query = query.filter(EnvironmentSound.generation_status == status)
    
    if featured_only:
        query = query.filter(EnvironmentSound.is_featured == True)
    
    # 排序
    if hasattr(EnvironmentSound, sort_by):
        sort_column = getattr(EnvironmentSound, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
    
    # 分页
    total = query.count()
    offset = (page - 1) * page_size
    sounds = query.offset(offset).limit(page_size).all()
    
    return {
        "sounds": sounds,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }

@router.get("/{sound_id}", response_model=EnvironmentSoundResponse)
async def get_environment_sound(
    sound_id: int,
    db: Session = Depends(get_db)
):
    """获取单个环境音详情"""
    sound = db.query(EnvironmentSound).filter(EnvironmentSound.id == sound_id).first()
    if not sound:
        raise HTTPException(status_code=404, detail="环境音不存在")
    
    return sound

@router.post("/generate", response_model=EnvironmentSoundGenerateResponse)
async def generate_environment_sound(
    request: EnvironmentSoundGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """生成环境音"""
    
    # 创建数据库记录
    sound = EnvironmentSound(
        name=request.name,
        prompt=request.prompt,
        description=request.description,
        duration=request.duration,
        steps=request.steps,
        cfg_scale=request.cfg_scale,
        category_id=request.category_id,
        generation_status="processing",
        created_by="system"  # TODO: 从认证信息获取用户
    )
    
    db.add(sound)
    db.commit()
    db.refresh(sound)
    
    # 后台任务生成音频
    background_tasks.add_task(
        generate_audio_task,
        sound.id,
        request.prompt,
        request.duration,
        request.steps,
        request.cfg_scale
    )
    
    return {
        "success": True,
        "message": "环境音生成任务已启动",
        "sound_id": sound.id,
        "estimated_time": request.duration * 0.5  # 估算生成时间
    }

@router.post("/{sound_id}/regenerate")
async def regenerate_environment_sound(
    sound_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """重新生成环境音"""
    sound = db.query(EnvironmentSound).filter(EnvironmentSound.id == sound_id).first()
    if not sound:
        raise HTTPException(status_code=404, detail="环境音不存在")
    
    # 更新状态
    sound.generation_status = "processing"
    sound.error_message = None
    db.commit()
    
    # 后台任务重新生成
    background_tasks.add_task(
        generate_audio_task,
        sound.id,
        sound.prompt,
        sound.duration,
        sound.steps,
        sound.cfg_scale
    )
    
    return {"success": True, "message": "重新生成任务已启动"}

@router.get("/{sound_id}/download")
async def download_environment_sound(
    sound_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """下载环境音文件"""
    sound = db.query(EnvironmentSound).filter(EnvironmentSound.id == sound_id).first()
    if not sound:
        raise HTTPException(status_code=404, detail="环境音不存在")
    
    if not sound.file_path or not os.path.exists(sound.file_path):
        raise HTTPException(status_code=404, detail="音频文件不存在")
    
    # 记录下载日志
    log_usage(db, sound_id, "download", request)
    
    # 更新下载计数
    sound.download_count += 1
    db.commit()
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=sound.file_path,
        filename=f"{sound.name}.wav",
        media_type="audio/wav"
    )

@router.post("/{sound_id}/play")
async def play_environment_sound(
    sound_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """播放环境音（记录播放日志）"""
    sound = db.query(EnvironmentSound).filter(EnvironmentSound.id == sound_id).first()
    if not sound:
        raise HTTPException(status_code=404, detail="环境音不存在")
    
    # 记录播放日志
    log_usage(db, sound_id, "play", request)
    
    # 更新播放计数
    sound.play_count += 1
    db.commit()
    
    return {"success": True, "message": "播放记录已更新"}

@router.post("/{sound_id}/favorite")
async def toggle_favorite(
    sound_id: int,
    db: Session = Depends(get_db)
):
    """切换收藏状态"""
    sound = db.query(EnvironmentSound).filter(EnvironmentSound.id == sound_id).first()
    if not sound:
        raise HTTPException(status_code=404, detail="环境音不存在")
    
    user_id = "system"  # TODO: 从认证信息获取用户ID
    
    # 检查是否已收藏
    favorite = db.query(EnvironmentSoundFavorite).filter(
        EnvironmentSoundFavorite.environment_sound_id == sound_id,
        EnvironmentSoundFavorite.user_id == user_id
    ).first()
    
    if favorite:
        # 取消收藏
        db.delete(favorite)
        sound.favorite_count = max(0, sound.favorite_count - 1)
        is_favorited = False
    else:
        # 添加收藏
        favorite = EnvironmentSoundFavorite(
            environment_sound_id=sound_id,
            user_id=user_id
        )
        db.add(favorite)
        sound.favorite_count += 1
        is_favorited = True
    
    db.commit()
    
    return {
        "success": True,
        "is_favorited": is_favorited,
        "favorite_count": sound.favorite_count
    }

@router.delete("/{sound_id}")
async def delete_environment_sound(
    sound_id: int,
    db: Session = Depends(get_db)
):
    """删除环境音"""
    sound = db.query(EnvironmentSound).filter(EnvironmentSound.id == sound_id).first()
    if not sound:
        raise HTTPException(status_code=404, detail="环境音不存在")
    
    # 删除文件
    if sound.file_path and os.path.exists(sound.file_path):
        try:
            os.remove(sound.file_path)
        except Exception as e:
            logger.warning(f"删除音频文件失败: {e}")
    
    # 删除数据库记录
    db.delete(sound)
    db.commit()
    
    return {"success": True, "message": "环境音已删除"}

# 辅助函数

async def generate_audio_task(
    sound_id: int,
    prompt: str,
    duration: float,
    steps: int,
    cfg_scale: float
):
    """后台生成音频任务"""
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        sound = db.query(EnvironmentSound).filter(EnvironmentSound.id == sound_id).first()
        if not sound:
            return
        
        # 调用TangoFlux API
        payload = {
            "prompt": prompt,
            "duration": duration,
            "steps": steps,
            "cfg_scale": cfg_scale
        }
        
        response = requests.post(
            f"{TANGOFLUX_API_URL}/api/v1/audio/generate",
            json=payload,
            timeout=300  # 5分钟超时
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                # 保存音频文件
                audio_data = base64.b64decode(result["audio_base64"])
                file_path = save_audio_file(
                    audio_data,
                    filename=f"env_sound_{sound_id}_{int(datetime.now().timestamp())}.wav",
                    subfolder="environment_sounds"
                )
                
                # 更新数据库
                sound.file_path = file_path
                sound.file_size = len(audio_data)
                sound.generation_time = result["parameters"]["generation_time"]
                sound.generation_status = "completed"
                sound.sample_rate = result["audio_info"]["sample_rate"]
                sound.channels = result["audio_info"]["channels"]
                
            else:
                sound.generation_status = "failed"
                sound.error_message = result.get("error", "生成失败")
        else:
            sound.generation_status = "failed"
            sound.error_message = f"API调用失败: {response.status_code}"
            
    except Exception as e:
        sound.generation_status = "failed"
        sound.error_message = str(e)
        logger.error(f"生成环境音失败: {e}")
    
    finally:
        db.commit()
        db.close()

def log_usage(db: Session, sound_id: int, action: str, request: Request):
    """记录使用日志"""
    try:
        log = EnvironmentSoundUsageLog(
            environment_sound_id=sound_id,
            action=action,
            user_id="system",  # TODO: 从认证信息获取
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        db.add(log)
        db.commit()
    except Exception as e:
        logger.warning(f"记录使用日志失败: {e}")
        db.rollback() 