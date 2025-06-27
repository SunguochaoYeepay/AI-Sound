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
        
        # 记录任务信息
        task_info = {
            "task_id": task_id,
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
        
        logger.info(f"🎵 异步音乐生成任务已启动: {task_id}")
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "音乐生成任务已启动，请通过WebSocket监控进度"
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


@router.delete("/task/{task_id}")
async def cancel_task(task_id: str):
    """取消任务"""
    if task_id not in active_music_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task_info = active_music_tasks[task_id]
    if task_info["status"] in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="任务已完成，无法取消")
    
    # 标记为取消状态
    await update_task_progress(task_id, -1, "任务已取消", error="用户取消")
    
    return {"success": True, "message": f"任务 {task_id} 已取消"}