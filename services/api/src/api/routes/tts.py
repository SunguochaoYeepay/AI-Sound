"""
TTS合成API路由
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from typing import List, Optional
import logging

from ...models.tts import (
    SynthesisRequest, BatchSynthesisRequest,
    SynthesisResult, BatchSynthesisResult, TTSTask
)
from ...services.tts_service import TTSService
from ...core.config import settings
from ...core.dependencies import get_adapter_factory
from ...adapters.factory import AdapterFactory

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tts", tags=["tts"])


def get_tts_service(adapter_factory: AdapterFactory = Depends(get_adapter_factory)) -> TTSService:
    """获取TTS服务实例"""
    return TTSService(adapter_factory)


@router.post("/synthesize")
async def synthesize_text(request: SynthesisRequest, tts_service: TTSService = Depends(get_tts_service)):
    """同步文本合成"""
    try:
        if len(request.text) > settings.tts.max_text_length:
            raise HTTPException(
                status_code=400, 
                detail=f"文本长度超过限制 ({settings.tts.max_text_length} 字符)"
            )
        
        result = await tts_service.synthesize_text(request)
        
        # 转换为docs规范格式
        return {
            "success": True,
            "message": "合成成功",
            "data": {
                "audio_url": f"/api/tts/audio/{result.audio_file}",
                "duration": result.duration,
                "engine_used": result.engine_used or request.engine
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文本合成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize-async")
async def synthesize_text_async(request: SynthesisRequest, tts_service: TTSService = Depends(get_tts_service)):
    """异步文本合成"""
    try:
        if len(request.text) > settings.tts.max_text_length:
            raise HTTPException(
                status_code=400, 
                detail=f"文本长度超过限制 ({settings.tts.max_text_length} 字符)"
            )
        
        task_id = await tts_service.synthesize_text_async(request)
        return {"task_id": task_id, "message": "合成任务已创建"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建合成任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_synthesize_async(request: BatchSynthesisRequest, tts_service: TTSService = Depends(get_tts_service)):
    """异步批量文本合成"""
    try:
        # 检查文本数量限制
        if len(request.texts) > 100:
            raise HTTPException(status_code=400, detail="批量文本数量超过限制 (100)")
        
        # 检查每个文本的长度
        for i, text in enumerate(request.texts):
            if len(text) > settings.tts.max_text_length:
                raise HTTPException(
                    status_code=400, 
                    detail=f"第{i+1}个文本长度超过限制 ({settings.tts.max_text_length} 字符)"
                )
        
        task_id = await tts_service.batch_synthesize_async(request)
        
        return {
            "success": True,
            "message": "批量合成任务已创建",
            "data": {
                "task_id": task_id,
                "total_items": len(request.texts),
                "estimated_time": len(request.texts) * 2  # 预估每个文本2秒
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建批量合成任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=TTSTask)
async def get_task_status(task_id: str, tts_service: TTSService = Depends(get_tts_service)):
    """获取任务状态"""
    try:
        task = await tts_service.get_task_status(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务未找到")
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str, tts_service: TTSService = Depends(get_tts_service)):
    """取消任务"""
    try:
        success = await tts_service.cancel_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="任务未找到或无法取消")
        return {"message": "任务已取消"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/engines")
async def get_available_engines(tts_service: TTSService = Depends(get_tts_service)):
    """获取可用的TTS引擎列表"""
    try:
        engines = await tts_service.get_available_engines()
        return {"engines": engines}
    except Exception as e:
        logger.error(f"获取引擎列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formats")
async def get_supported_formats():
    """获取支持的音频格式列表"""
    try:
        from ...models.tts import AudioFormat
        formats = [format.value for format in AudioFormat]
        return {"formats": formats}
    except Exception as e:
        logger.error(f"获取格式列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """获取音频文件"""
    try:
        from pathlib import Path
        output_path = Path(settings.tts.output_path)
        file_path = output_path / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="音频文件未找到")
        
        # 根据文件扩展名设置媒体类型
        media_type_map = {
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac'
        }
        media_type = media_type_map.get(file_path.suffix.lower(), 'application/octet-stream')
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取音频文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))