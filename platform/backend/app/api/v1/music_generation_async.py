"""
异步音乐生成API - 使用WebSocket实时进度反馈
正确架构：前端WebSocket ← 后端 → SongGeneration WebSocket
"""

import asyncio
import uuid
import time
import logging
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.services.music_orchestrator import get_music_orchestrator
from app.websocket.manager import websocket_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/music-generation-async", tags=["异步音乐生成"])

# 存储活跃的音乐生成任务
active_music_tasks: Dict[str, Dict] = {}

class AsyncMusicGenerationRequest(BaseModel):
    """异步音乐生成请求"""
    name: str = Field(..., description="音乐名称（必填）", min_length=1, max_length=200)
    lyrics: str = Field(..., description="歌词内容（必填）")
    genre: Optional[str] = Field("Auto", description="音乐风格")
    description: Optional[str] = Field("", description="音乐描述（可选）")
    cfg_coef: float = Field(1.5, ge=0.1, le=3.0, description="CFG系数")
    temperature: float = Field(0.9, ge=0.1, le=2.0, description="温度")
    top_k: int = Field(50, ge=1, le=100, description="Top-K")
    chapter_id: Optional[str] = Field(None, description="章节ID")
    volume_level: float = Field(-12.0, ge=-30.0, le=0.0, description="音量级别（dB）")


def validate_lyrics_format(lyrics: str) -> Optional[str]:
    """
    验证歌词格式是否符合SongGeneration要求
    返回错误信息，如果验证通过则返回None
    """
    # 支持的结构标签
    SUPPORTED_STRUCTS = [
        '[verse]', '[chorus]', '[bridge]',
        '[intro-short]', '[intro-medium]', '[intro-long]',
        '[outro-short]', '[outro-medium]', '[outro-long]',
        '[inst-short]', '[inst-medium]', '[inst-long]',
        '[silence]'
    ]
    
    # 需要歌词的标签
    VOCAL_STRUCTS = ['[verse]', '[chorus]', '[bridge]']
    
    if not lyrics.strip():
        return "歌词不能为空"
    
    # 按双换行分割段落
    paragraphs = [p.strip() for p in lyrics.strip().split('\n\n') if p.strip()]
    
    if len(paragraphs) < 1:
        return "歌词至少需要一个段落"
    
    vocal_found = False
    
    for para in paragraphs:
        lines = para.splitlines()
        if not lines:
            continue
            
        struct_tag = lines[0].strip().lower()
        
        # 检查结构标签
        if struct_tag not in SUPPORTED_STRUCTS:
            return f"不支持的结构标签: {struct_tag}，支持的标签: {', '.join(SUPPORTED_STRUCTS)}"
        
        # 检查是否需要歌词内容
        if struct_tag in VOCAL_STRUCTS:
            vocal_found = True
            if len(lines) < 2 or not any(line.strip() for line in lines[1:]):
                return f"标签 {struct_tag} 需要包含歌词内容"
        else:
            # 纯音乐段落不应包含歌词
            if len(lines) > 1 and any(line.strip() for line in lines[1:]):
                return f"标签 {struct_tag} 不应包含歌词内容"
    
    if not vocal_found:
        return f"歌词必须包含至少一个人声段落: {', '.join(VOCAL_STRUCTS)}"
    
    return None


@router.post("/generate")
async def generate_music_async(request: AsyncMusicGenerationRequest, background_tasks: BackgroundTasks):
    """
    启动异步音乐生成任务
    返回task_id，前端通过WebSocket监控进度
    """
    try:
        # 🔧 添加歌词格式验证
        lyrics_error = validate_lyrics_format(request.lyrics)
        if lyrics_error:
            raise HTTPException(status_code=400, detail=f"歌词格式错误: {lyrics_error}")
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 🎯 预创建音乐生成任务记录（让用户立即看到"合成中"状态）
        orchestrator = get_music_orchestrator()
        db_task = await orchestrator.create_pending_music_task(
            task_id=task_id,
            name=request.name,
            content=request.lyrics,
            genre=request.genre,
            chapter_id=request.chapter_id,
            volume_level=request.volume_level,
            target_duration=30  # 默认30秒
        )
        
        # 记录任务信息
        task_info = {
            "task_id": task_id,
            "db_task_id": db_task.id,  # 数据库记录ID
            "status": "starting",
            "progress": 0.0,
            "message": "任务启动中...",
            "request": request.dict(),
            "start_time": time.time(),
            "result": None,
            "error": None
        }
        
        active_music_tasks[task_id] = task_info
        
        # 启动后台任务
        background_tasks.add_task(process_music_generation, task_id, request)
        
        logger.info(f"🎵 异步音乐生成任务已启动: {task_id}, DB ID: {db_task.id}")
        
        return {
            "success": True,
            "task_id": task_id,
            "db_task_id": db_task.id,
            "message": "音乐生成任务已启动，已在列表中显示合成状态"
        }
        
    except Exception as e:
        logger.error(f"启动异步音乐生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动任务失败: {str(e)}")


async def process_music_generation(task_id: str, request: AsyncMusicGenerationRequest):
    """
    处理音乐生成任务（后台执行）
    通过WebSocket向前端推送进度
    """
    try:
        logger.info(f"🎵 开始处理音乐生成任务: {task_id}")
        
        # 更新任务状态
        await update_task_progress(task_id, 0.05, "正在初始化音乐生成引擎...")
        
        orchestrator = get_music_orchestrator()
        
        # 定义进度回调函数，将SongGeneration的进度转发给前端
        async def progress_callback(progress: float, message: str):
            await update_task_progress(task_id, progress, message)
        
        await update_task_progress(task_id, 0.1, "开始场景分析...")
        
        # 调用音乐编排器生成音乐（使用带进度的方法）
        result = await orchestrator.generate_music_for_content_with_progress(
            content=request.lyrics,
            chapter_id=request.chapter_id,
            custom_style=request.genre,
            volume_level=request.volume_level,
            advanced_params={
                "description": request.description,
                "cfg_coef": request.cfg_coef,
                "temperature": request.temperature,
                "top_k": request.top_k
            },
            progress_callback=progress_callback
        )
        
        if result:
            # 生成成功
            await update_task_progress(task_id, 1.0, "音乐生成完成！", result=result)
            logger.info(f"✅ 音乐生成任务完成: {task_id}")
        else:
            # 生成失败
            await update_task_progress(task_id, -1, "音乐生成失败", error="引擎返回空结果")
            logger.error(f"❌ 音乐生成任务失败: {task_id}")
            
    except Exception as e:
        logger.error(f"❌ 音乐生成任务异常: {task_id} - {e}")
        await update_task_progress(task_id, -1, f"生成异常: {str(e)}", error=str(e))


async def update_task_progress(task_id: str, progress: float, message: str, result: Optional[Dict] = None, error: Optional[str] = None):
    """
    更新任务进度并通过WebSocket推送给前端
    """
    if task_id in active_music_tasks:
        task_info = active_music_tasks[task_id]
        task_info.update({
            "progress": progress,
            "message": message,
            "status": "completed" if progress >= 1.0 else ("failed" if progress < 0 else "processing"),
            "result": result,
            "error": error,
            "updated_at": time.time()
        })
        
        # 🎯 同时更新数据库记录
        orchestrator = get_music_orchestrator()
        from app.models.music_generation import MusicGenerationStatus
        
        # 确定状态
        if progress >= 1.0:
            db_status = MusicGenerationStatus.COMPLETED
        elif progress < 0:
            db_status = MusicGenerationStatus.FAILED
        else:
            db_status = MusicGenerationStatus.PROCESSING
        
        # 更新数据库
        await orchestrator.update_music_task_progress(
            task_id=task_id,
            progress=max(0.0, progress),  # 避免负进度
            status=db_status,
            audio_path=result.get("audio_path") if result else None,
            audio_url=result.get("audio_url") if result else None,
            error_message=error
        )
        
        # 通过WebSocket推送进度更新
        await websocket_manager.broadcast_message({
            "type": "music_generation_progress",
            "data": {
                "task_id": task_id,
                "progress": progress,
                "message": message,
                "status": task_info["status"],
                "result": result,
                "error": error
            }
        })
        
        logger.info(f"📊 任务进度更新 {task_id}: {progress:.1%} - {message}")
        
        # 清理完成的任务（1小时后）
        if progress >= 1.0 or progress < 0:
            asyncio.create_task(cleanup_task_after_delay(task_id, 3600))


async def cleanup_task_after_delay(task_id: str, delay_seconds: int):
    """延迟清理任务"""
    await asyncio.sleep(delay_seconds)
    if task_id in active_music_tasks:
        del active_music_tasks[task_id]
        logger.info(f"🧹 已清理过期任务: {task_id}")


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in active_music_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task_info = active_music_tasks[task_id]
    return {
        "task_id": task_id,
        "status": task_info["status"],
        "progress": task_info["progress"],
        "message": task_info["message"],
        "result": task_info.get("result"),
        "error": task_info.get("error"),
        "elapsed_time": time.time() - task_info["start_time"]
    }


@router.get("/tasks")
async def list_active_tasks():
    """列出所有活跃任务"""
    return {
        "active_tasks": len(active_music_tasks),
        "tasks": {
            task_id: {
                "status": info["status"],
                "progress": info["progress"],
                "message": info["message"],
                "elapsed_time": time.time() - info["start_time"]
            }
            for task_id, info in active_music_tasks.items()
        }
    }


@router.get("/music-tasks")
async def list_music_generation_tasks(
    page: int = 1,
    page_size: int = 10,
    status: Optional[str] = None
):
    """
    获取音乐生成任务列表（包括pending/processing/completed状态）
    用于前端音乐库显示所有音乐（生成中+已完成）
    """
    try:
        from app.database import get_db
        from app.models.music_generation import MusicGenerationTask, MusicGenerationStatus
        from sqlalchemy import desc
        
        db_session = next(get_db())
        
        # 构建查询
        query = db_session.query(MusicGenerationTask)
        
        # 状态过滤
        if status:
            query = query.filter(MusicGenerationTask.status == status)
        
        # 分页
        total = query.count()
        tasks = query.order_by(desc(MusicGenerationTask.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        # 格式化结果
        items = []
        for task in tasks:
            # 获取内存中的实时进度（如果有的话）
            memory_info = active_music_tasks.get(task.task_id, {})
            
            items.append({
                "id": task.id,
                "task_id": task.task_id,
                "name": f"音乐生成_{task.id}",  # 临时名称
                "content": task.content[:50] + "..." if len(task.content) > 50 else task.content,
                "status": task.status.value if task.status else "unknown",
                "progress": memory_info.get("progress", task.progress),
                "message": memory_info.get("message", ""),
                "custom_style": task.custom_style,
                "audio_url": task.audio_url,
                "audio_path": task.audio_path,
                "duration": task.actual_duration,
                "file_size": task.file_size,
                "volume_level": task.volume_level,
                "error_message": task.error_message,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                # 为了兼容前端，添加category信息
                "category": {"name": "AI生成"},
                "category_name": "AI生成"
            })
        
        db_session.close()
        
        return {
            "success": True,
            "data": {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
        
    except Exception as e:
        logger.error(f"获取音乐生成任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.delete("/task/{task_id}")
async def delete_task(task_id: str):
    """删除任务（支持内存活跃任务和数据库任务）"""
    try:
        from app.database import get_db
        from app.models.music_generation import MusicGenerationTask
        import os
        
        db_session = next(get_db())
        
        # 1. 首先从数据库查找任务
        db_task = db_session.query(MusicGenerationTask).filter(
            MusicGenerationTask.task_id == task_id
        ).first()
        
        if not db_task:
            db_session.close()
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 2. 如果任务在内存中且正在处理，则取消
        if task_id in active_music_tasks:
            task_info = active_music_tasks[task_id]
            if task_info["status"] == "processing":
                # 标记为取消状态
                await update_task_progress(task_id, -1, "任务已取消", error="用户取消")
                logger.info(f"🔄 已取消正在处理的任务: {task_id}")
            
            # 从内存中移除
            del active_music_tasks[task_id]
        
        # 3. 删除音频文件（如果存在）
        if db_task.audio_path and os.path.exists(db_task.audio_path):
            try:
                os.remove(db_task.audio_path)
                logger.info(f"🗑️ 已删除音频文件: {db_task.audio_path}")
            except Exception as e:
                logger.warning(f"⚠️ 删除音频文件失败: {e}")
        
        # 4. 从数据库删除任务记录
        db_session.delete(db_task)
        db_session.commit()
        db_session.close()
        
        logger.info(f"✅ 成功删除音乐生成任务: {task_id} (DB ID: {db_task.id})")
        
        return {
            "success": True, 
            "message": f"任务 {task_id} 已删除",
            "deleted_task_id": task_id,
            "deleted_db_id": db_task.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 删除任务失败: {task_id} - {e}")
        if 'db_session' in locals():
            db_session.rollback()
            db_session.close()
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")