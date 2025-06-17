"""
API v1版本路由汇总
集成所有v1版本的API路由
"""

import asyncio
import logging
from fastapi import APIRouter
from typing import Dict, Any

from .books import router as books_router
from .chapters import router as chapters_router
from .analysis import router as analysis_router
from .synthesis import router as synthesis_router
from .presets import router as presets_router
from .projects import router as projects_router
from .characters import router as characters_router
from .audio_library import router as audio_library_router
from .intelligent_analysis import router as intelligent_analysis_router
from .content_preparation import router as content_preparation_router
from .novel_reader import router as novel_reader_router
from app.voice_clone import router as voice_clone_router
from app.monitor import router as monitor_router

# 导入需要的健康检查组件
from app.database import health_check as db_health_check
from app.tts_client import get_tts_client
from app.clients.file_manager import file_manager
from app.websocket.manager import websocket_manager

logger = logging.getLogger(__name__)

# 创建v1版本的主路由
api = APIRouter()

# v1 API健康检查端点 - 使用完整的健康检查逻辑
@api.get("/health")
async def v1_health_check() -> Dict[str, Any]:
    """v1 API健康检查"""
    try:
        # 数据库健康检查
        db_status = db_health_check()
        
        # TTS客户端健康检查
        tts_client = get_tts_client()
        tts_status = await tts_client.health_check()
        
        # WebSocket管理器状态
        ws_status = websocket_manager.get_status()
        
        # 文件管理器状态
        storage_stats = file_manager.get_storage_stats()
        
        all_healthy = (
            db_status.get("status") == "healthy" and
            all(tts_status.values()) and
            ws_status.get("status") == "running"
        )
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "version": "v1",
            "timestamp": asyncio.get_event_loop().time(),
            "services": {
                "database": db_status,
                "tts_client": tts_status,
                "websocket_manager": ws_status,
                "storage": storage_stats
            }
        }
        
    except Exception as e:
        logger.error(f"v1 API健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "version": "v1",
            "error": str(e)
        }

# 注册各模块路由
api.include_router(books_router, tags=["Books"])
api.include_router(chapters_router, tags=["Chapters"])
api.include_router(analysis_router, tags=["Analysis"])
api.include_router(synthesis_router, tags=["Synthesis"])
api.include_router(presets_router, tags=["Presets"])
# api.include_router(projects_router, tags=["Projects"])  # 🚀 已迁移到novel_reader，暂时注释避免冲突
api.include_router(characters_router, tags=["Characters"])
api.include_router(audio_library_router, tags=["Audio Library"])
api.include_router(novel_reader_router, tags=["Novel Reader"])
api.include_router(voice_clone_router, tags=["Voice Clone"])
api.include_router(monitor_router, tags=["System Monitor"])
api.include_router(intelligent_analysis_router, tags=["Intelligent Analysis"])
api.include_router(content_preparation_router, tags=["Content Preparation"]) 