"""
API v1版本路由汇总
集成所有v1版本的API路由
"""

import asyncio
import logging
from fastapi import APIRouter
from typing import Dict, Any

from .auth import router as auth_router
from .books import router as books_router
from .chapters import router as chapters_router
# from .analysis import router as analysis_router  # 🚀 已简化，不再使用会话模型
from .storyboard import router as storyboard_router
from .audio_script import router as audio_script_router
from .synthesis import router as synthesis_router
from .presets import router as presets_router
from .projects import router as projects_router
from .characters import router as characters_router
from .audio_library import router as audio_library_router
from .audio_sync import router as audio_sync_router
from .intelligent_analysis import router as intelligent_analysis_router
from .content_preparation import router as content_preparation_router
from .data_consistency import router as data_consistency_router
from .novel_reader import router as novel_reader_router
from .environment_sounds import router as environment_sounds_router
from .scene_analysis import router as scene_analysis_router
from .environment_generation import router as environment_generation_router

from .segment_analysis import router as segment_analysis_router
from .integrated_analysis import router as integrated_analysis_router
from .smart_segmentation import router as smart_segmentation_router

# Import sound editor router (for multi-track audio editor)
from .sound_editor import router as sound_editor_router
# Import background music router
from .background_music import router as background_music_router
# 🎵 Import music generation router
from .music_generation import router as music_generation_router
from .music_generation_async import router as music_generation_async_router
# 🖼️ Import image generation router
from .image_generation import router as image_generation_router
# Import TTS router
from .tts import router as tts_router
# Temporarily commented out due to missing model dependencies
# from .smart_editing import router as smart_editing_router
# from .collaboration import router as collaboration_router
from app.voice_clone import router as voice_clone_router
from app.monitor import router as monitor_router
from ..system import router as system_router

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

# 导入日志监控路由
from .logs import router as logs_router
# 导入备份恢复路由
from .backup import router as backup_router
from .users import router as users_router
from .roles import router as roles_router

# 注册各模块路由
api.include_router(auth_router)
api.include_router(books_router, tags=["Books"])
api.include_router(chapters_router, tags=["Chapters"])
# api.include_router(analysis_router, tags=["Analysis"])  # 🚀 已简化，不再使用会话模型
# api.include_router(storyboard_router, tags=["Storyboard Analysis"])  # 🚀 已简化，不再使用会话模型
api.include_router(audio_script_router, tags=["Audio Script"])
api.include_router(synthesis_router, tags=["Synthesis"])
api.include_router(presets_router, tags=["Presets"])
api.include_router(projects_router, tags=["Projects"])  # 🚀 重新启用项目管理API
api.include_router(characters_router, tags=["Characters"])
api.include_router(audio_library_router, tags=["Audio Library"])
api.include_router(audio_sync_router, tags=["Audio Sync"])
api.include_router(novel_reader_router, tags=["Novel Reader"])
api.include_router(voice_clone_router, tags=["Voice Clone"])
api.include_router(monitor_router, tags=["System Monitor"])
api.include_router(intelligent_analysis_router, tags=["Intelligent Analysis"])
api.include_router(content_preparation_router, tags=["Content Preparation"]) 
api.include_router(data_consistency_router, tags=["Data Consistency"])
api.include_router(environment_sounds_router, prefix="/environment-sounds", tags=["Environment Sounds"])
api.include_router(scene_analysis_router, tags=["Scene Analysis"])
api.include_router(environment_generation_router, tags=["Environment Generation"])

api.include_router(segment_analysis_router, prefix="/segment_analysis", tags=["Segment Analysis"])
api.include_router(integrated_analysis_router, tags=["Integrated Analysis"])
api.include_router(smart_segmentation_router, prefix="/smart-segmentation", tags=["Smart Segmentation"])
api.include_router(system_router, tags=["System Settings"])
api.include_router(logs_router, tags=["Log Monitor"])
api.include_router(backup_router, tags=["Database Backup"])
api.include_router(users_router, tags=["User Management"])
api.include_router(roles_router, tags=["Role Management"])

# Register sound editor router (multi-track audio editor)
api.include_router(sound_editor_router, tags=["Sound Editor"])
# Register background music router
api.include_router(background_music_router, prefix="/background-music", tags=["Background Music"])
# 🎵 Register music generation router
api.include_router(music_generation_router, tags=["Music Generation"])
api.include_router(music_generation_async_router, tags=["Async Music Generation"])
# 🖼️ Register image generation router
api.include_router(image_generation_router, tags=["Image Generation"])

# 🔥 新增：兼容的图片文件访问路由
@api.get("/files/image_generation/{filename}")
async def get_image_file_compat(filename: str):
    """兼容的图片文件访问接口"""
    from fastapi.responses import FileResponse
    from fastapi import HTTPException
    import os
    
    try:
        # 构建图片文件路径
        file_path = os.path.join("storage", "audio_editor", "exports", "image_generation", filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="图片文件不存在")
        
        # 返回文件
        return FileResponse(
            path=file_path,
            media_type="image/png",
            filename=filename,
            headers={"Content-Disposition": f"inline; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图片文件失败: {str(e)}")
# Register TTS router
api.include_router(tts_router, tags=["TTS"])
# Temporarily commented out due to missing model dependencies
# api.include_router(smart_editing_router, prefix="/smart-editing", tags=["Smart Editing"])
# api.include_router(collaboration_router, prefix="/collaboration", tags=["Collaboration"])

# 为了兼容main.py中的导入，创建别名
api_router = api
