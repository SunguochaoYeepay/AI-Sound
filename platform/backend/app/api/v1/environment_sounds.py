#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import logging
import requests
import base64
import os
import json
import tempfile
import threading
import time
from datetime import datetime, timedelta
import aiohttp
import asyncio

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
from app.clients.file_manager import save_audio_file, get_audio_file_path
from app.config.environment import get_environment_config

router = APIRouter()
logger = logging.getLogger(__name__)
env_config = get_environment_config()

# TangoFlux服务配置
TANGOFLUX_SERVICE_URL = os.getenv("TANGOFLUX_URL", "http://localhost:7930")

def get_tangoflux_client():
    """获取TangoFlux客户端（HTTP调用）"""
    return {
        "base_url": TANGOFLUX_SERVICE_URL,
        "timeout": 300  # 5分钟超时
    }

async def call_tangoflux_generate(prompt: str, duration: float, steps: int, cfg_scale: float) -> bytes:
    """调用TangoFlux服务生成音频"""
    client = get_tangoflux_client()
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=client["timeout"])) as session:
            data = {
                "prompt": prompt,
                "duration": duration,
                "steps": steps,
                "guidance_scale": cfg_scale  # TangoFlux API使用guidance_scale参数名
            }
            
            # 调用TangoFlux API的正确端点
            async with session.post(f"{client['base_url']}/api/v1/audio/generate", json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    # TangoFlux返回base64编码的音频数据
                    if result.get("success") and "audio_base64" in result:
                        import base64
                        return base64.b64decode(result["audio_base64"])
                    else:
                        raise Exception("TangoFlux服务返回格式错误")
                else:
                    error_text = await response.text()
                    raise Exception(f"TangoFlux服务错误: {response.status} - {error_text}")
                    
    except asyncio.TimeoutError:
        raise Exception("TangoFlux服务调用超时")
    except Exception as e:
        logger.error(f"TangoFlux服务调用失败: {e}")
        raise Exception(f"TangoFlux服务不可用: {str(e)}")

@router.get("/categories", response_model=List[EnvironmentSoundCategoryResponse])
async def get_categories(
    active_only: bool = Query(True, description="仅返回激活的分类"),
    db: Session = Depends(get_db)
):
    """获取环境音分类列表"""
    query = db.query(EnvironmentSoundCategory)
    # 恢复is_active筛选
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

@router.get("/")
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
    
    try:
        # 构建查询
        query = db.query(EnvironmentSound)
        
        # 筛选条件
        if category_id:
            query = query.filter(EnvironmentSound.category_id == category_id)
        
        # 暂时跳过标签筛选，需要建立标签关联表
        # if tag_ids:
        #     try:
        #         tag_id_list = [int(tid.strip()) for tid in tag_ids.split(",") if tid.strip().isdigit()]
        #         if tag_id_list:
        #             # TODO: 实现标签关联查询
        #             pass
        #     except Exception as e:
        #         logger.warning(f"标签筛选失败: {e}")
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                EnvironmentSound.name.ilike(search_term) |
                EnvironmentSound.prompt.ilike(search_term) |
                EnvironmentSound.description.ilike(search_term)
            )
        
        if status:
            query = query.filter(EnvironmentSound.generation_status == status)
        
        # 现在可以使用is_featured字段了
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
        
        # 转换为字典格式
        sound_list = []
        for sound in sounds:
            sound_dict = sound.to_dict()
            sound_list.append(sound_dict)
        
        return {
            "success": True,
            "data": {
                "sounds": sound_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": (total + page_size - 1) // page_size
            }
        }
        
    except Exception as e:
        logger.error(f"获取环境音列表失败: {e}")
        return {
            "success": False,
            "message": f"获取环境音列表失败: {str(e)}"
        }

@router.get("/stats")
async def get_environment_sound_stats(db: Session = Depends(get_db)):
    """获取环境音统计数据"""
    
    # 总数统计
    total_sounds = db.query(EnvironmentSound).count()
    completed_sounds = db.query(EnvironmentSound).filter(EnvironmentSound.generation_status == "completed").count()
    processing_sounds = db.query(EnvironmentSound).filter(EnvironmentSound.generation_status == "processing").count()
    failed_sounds = db.query(EnvironmentSound).filter(EnvironmentSound.generation_status == "failed").count()
    
    # 播放和下载统计（这些字段暂时不存在，先设为0）
    total_plays = 0  # TODO: 从usage_logs表计算
    total_downloads = 0  # TODO: 从usage_logs表计算
    total_favorites = 0  # TODO: 从favorites表计算
    
    # 分类统计
    try:
        category_stats = db.query(
            EnvironmentSound.category,
            func.count(EnvironmentSound.id).label('count')
        ).group_by(EnvironmentSound.category).all()
    except Exception:
        category_stats = []
    
    # 今日新增
    today = datetime.now().date()
    today_sounds = db.query(EnvironmentSound).filter(
        func.date(EnvironmentSound.created_at) == today
    ).count()
    
    return {
        "total_sounds": total_sounds,
        "completed_sounds": completed_sounds,
        "processing_sounds": processing_sounds,
        "failed_sounds": failed_sounds,
        "total_plays": total_plays,
        "total_downloads": total_downloads,
        "total_favorites": total_favorites,
        "today_sounds": today_sounds,
        "category_stats": [{"name": name, "count": count} for name, count in category_stats],
        "completion_rate": round(completed_sounds / total_sounds * 100, 1) if total_sounds > 0 else 0
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
    
    # 如果未指定分类，使用默认分类
    category_id = request.category_id
    if category_id is None:
        # 查找默认分类（通用分类）
        default_category = db.query(EnvironmentSoundCategory).filter(
            EnvironmentSoundCategory.name.ilike("%通用%")
        ).first()
        if not default_category:
            # 如果没有通用分类，使用第一个可用分类
            default_category = db.query(EnvironmentSoundCategory).filter(
                EnvironmentSoundCategory.is_active == True
            ).first()
        
        if default_category:
            category_id = default_category.id
        else:
            raise HTTPException(status_code=400, detail="未找到可用的环境音分类，请先创建分类")
    
    # 创建数据库记录
    sound = EnvironmentSound(
        name=request.name,
        prompt=request.prompt,
        description=request.description,
        duration=request.duration,
        steps=request.steps,
        cfg_scale=request.cfg_scale,
        category_id=category_id,
        generation_status="processing"
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
        "sound_id": sound.id,
        "status": "processing",
        "message": "环境音生成任务已启动",
        "estimated_time": int(request.duration * 0.5)  # 估算生成时间
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
    # sound.error_message = None  # 字段暂不存在
    db.commit()
    
    # 后台任务重新生成  
    background_tasks.add_task(
        generate_audio_task,
        sound.id,
        sound.prompt,
        sound.duration,
        sound.steps or 100,  # 默认值
        sound.cfg_scale or 7.5  # 默认值
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
    
    # TODO: 更新下载计数（字段暂不存在）
    # sound.download_count += 1
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
    
    # TODO: 更新播放计数（字段暂不存在）
    # sound.play_count += 1
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
        EnvironmentSoundFavorite.sound_id == sound_id,
        EnvironmentSoundFavorite.user_id == user_id
    ).first()
    
    if favorite:
        # 取消收藏
        db.delete(favorite)
        # sound.favorite_count = max(0, sound.favorite_count - 1)  # 字段暂不存在
        is_favorited = False
    else:
        # 添加收藏
        favorite = EnvironmentSoundFavorite(
            sound_id=sound_id,
            user_id=user_id
        )
        db.add(favorite)
        # sound.favorite_count += 1  # 字段暂不存在
        is_favorited = True
    
    db.commit()
    
    return {
        "success": True,
        "is_favorited": is_favorited,
        "favorite_count": 0  # TODO: 从favorites表计算
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

@router.post("/debug/fix-processing")
async def fix_processing_sounds(db: Session = Depends(get_db)):
    """调试端点：修复处理中的环境音状态"""
    try:
        # 查找处理中超过10分钟的环境音
        threshold_time = datetime.now() - timedelta(minutes=10)
        
        processing_sounds = db.query(EnvironmentSound).filter(
            EnvironmentSound.generation_status == "processing",
            EnvironmentSound.created_at < threshold_time
        ).all()
        
        fixed_count = 0
        for sound in processing_sounds:
            sound.generation_status = "failed"
            # sound.error_message = "生成超时，已自动修复状态"  # 字段暂不存在
            fixed_count += 1
            logger.info(f"修复环境音 {sound.id} 状态: {sound.name}")
        
        db.commit()
        
        return {
            "success": True,
            "message": f"成功修复 {fixed_count} 个环境音状态",
            "fixed_count": fixed_count
        }
        
    except Exception as e:
        logger.error(f"修复处理中状态失败: {e}")
        return {
            "success": False,
            "message": f"修复失败: {str(e)}"
        }

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
            logger.error(f"环境音 {sound_id} 不存在")
            return
        
        logger.info(f"开始生成环境音 {sound_id}: {prompt}")
        
        # 调用TangoFlux服务生成音频
        audio_data = await call_tangoflux_generate(prompt, duration, steps, cfg_scale)
        logger.info(f"TangoFlux生成完成，音频大小: {len(audio_data)} bytes")
        
        # 直接保存音频文件，无需临时文件
        file_path = await save_audio_file(
            audio_data,
            filename=f"env_sound_{sound_id}_{int(datetime.now().timestamp())}.wav",
            subfolder="environment_sounds"
        )
        logger.info(f"音频文件保存完成: {file_path}")
        
        # 更新数据库（只使用存在的字段）
        sound.file_path = file_path
        sound.file_size = len(audio_data)
        sound.generation_status = "completed"
        # sound.sample_rate = 44100  # 字段暂不存在
        # sound.channels = 2  # 字段暂不存在
        # sound.generated_at = datetime.now()  # 字段暂不存在
        
        db.commit()
        logger.info(f"环境音 {sound_id} 生成成功: {file_path}")
            
    except Exception as e:
        logger.error(f"生成环境音 {sound_id} 失败: {e}", exc_info=True)
        try:
            if sound:
                sound.generation_status = "failed"
                # sound.error_message = str(e)  # 字段暂不存在
                db.commit()
                logger.info(f"环境音 {sound_id} 状态已更新为失败")
        except Exception as update_error:
            logger.error(f"更新环境音 {sound_id} 失败状态时出错: {update_error}")
    
    finally:
        try:
            db.close()
        except Exception as close_error:
            logger.error(f"关闭数据库连接失败: {close_error}")

def log_usage(db: Session, sound_id: int, action: str, request: Request):
    """记录使用日志"""
    try:
        log = EnvironmentSoundUsageLog(
            sound_id=sound_id,
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