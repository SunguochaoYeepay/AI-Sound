"""
系统管理API
提供系统状态检查、环境验证、路径修复等功能
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.utils.path_manager import validate_environment, get_path_manager
from app.models import VoiceProfile
from app.config.logging_config import get_logging_info, logging_config
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["系统管理"])


@router.get("/health")
async def health_check():
    """系统健康检查"""
    return {
        "status": "healthy",
        "message": "系统运行正常"
    }


@router.get("/environment")
async def get_environment_info():
    """获取环境信息"""
    try:
        env_info = validate_environment()
        return {
            "success": True,
            "data": env_info
        }
    except Exception as e:
        logger.error(f"获取环境信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取环境信息失败: {str(e)}")


@router.post("/fix-voice-paths")
async def fix_voice_paths(db: Session = Depends(get_db)):
    """修复声音档案路径"""
    try:
        path_manager = get_path_manager()
        result = path_manager.auto_fix_voice_profile_paths(db)
        
        return {
            "success": True,
            "message": f"路径修复完成，共修复 {result['fixed']} 个声音档案",
            "data": result
        }
    except Exception as e:
        logger.error(f"修复声音档案路径失败: {e}")
        raise HTTPException(status_code=500, detail=f"修复失败: {str(e)}")


@router.get("/validate-voice-files")
async def validate_voice_files(db: Session = Depends(get_db)):
    """验证所有声音文件完整性"""
    try:
        voices = db.query(VoiceProfile).all()
        
        result = {
            "total": len(voices),
            "valid": 0,
            "invalid": 0,
            "details": []
        }
        
        for voice in voices:
            validation = voice.validate_files()
            
            voice_info = {
                "id": voice.id,
                "name": voice.name,
                "valid": validation['valid'],
                "missing_files": validation['missing_files']
            }
            
            if validation['valid']:
                result['valid'] += 1
            else:
                result['invalid'] += 1
            
            result['details'].append(voice_info)
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"验证声音文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")


@router.get("/storage-info")
async def get_storage_info():
    """获取存储信息"""
    try:
        path_manager = get_path_manager()
        
        storage_info = {}
        for path_type, path in path_manager.base_paths.items():
            import os
            storage_info[path_type] = {
                "path": path,
                "exists": os.path.exists(path),
                "size": get_directory_size(path) if os.path.exists(path) else 0
            }
        
        return {
            "success": True,
            "data": {
                "environment": "docker" if path_manager.is_docker else "local",
                "storage_paths": storage_info
            }
        }
    except Exception as e:
        logger.error(f"获取存储信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取存储信息失败: {str(e)}")


@router.get("/logging-info")
async def get_logging_system_info():
    """获取日志系统信息"""
    try:
        info = get_logging_info()
        return {
            "success": True,
            "data": info
        }
    except Exception as e:
        logger.error(f"获取日志系统信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取日志信息失败: {str(e)}")


@router.post("/logs/cleanup")
async def cleanup_old_logs(days: int = 30):
    """清理旧日志文件"""
    try:
        cleaned_count = logging_config.cleanup_old_logs(days)
        return {
            "success": True,
            "message": f"已清理 {cleaned_count} 个旧日志文件",
            "data": {
                "cleaned_files": cleaned_count,
                "cleanup_days": days
            }
        }
    except Exception as e:
        logger.error(f"清理日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理日志失败: {str(e)}")


@router.get("/logs/modules")
async def get_log_modules_status():
    """获取各模块日志状态"""
    try:
        modules_info = {
            "background_music.log": {
                "description": "背景音乐相关日志",
                "modules": [
                    "app.services.background_music_service",
                    "app.services.background_music_generation_service",
                    "app.api.v1.background_music"
                ]
            },
            "music_generation.log": {
                "description": "音乐生成相关日志",
                "modules": [
                    "app.services.song_generation_service",
                    "app.services.music_orchestrator",
                    "app.api.v1.music_generation",
                    "app.api.v1.music_generation_async",
                    "app.clients.songgeneration_engine"
                ]
            },
            "tts_voice.log": {
                "description": "TTS和语音相关日志",
                "modules": [
                    "app.tts_client",
                    "app.clients.tts_client",
                    "app.api.v1.characters"
                ]
            },
            "environment_sounds.log": {
                "description": "环境音相关日志",
                "modules": [
                    "app.services.environment_generation_service",
                    "app.services.tangoflux_environment_generator",
                    "app.clients.tangoflux_client",
                    "app.api.v1.environment_generation"
                ]
            },
            "intelligent_analysis.log": {
                "description": "智能分析相关日志",
                "modules": [
                    "app.services.llm_scene_analyzer",
                    "app.services.intelligent_scene_analyzer",
                    "app.services.chapter_analysis_service",
                    "app.api.v1.intelligent_analysis"
                ]
            },
            "audio_processing.log": {
                "description": "音频处理相关日志",
                "modules": [
                    "app.services.audio_editor_service",
                    "app.services.audio_sync_service",
                    "app.clients.audio_processor",
                    "app.api.v1.audio_editor"
                ]
            },
            "api_requests.log": {
                "description": "API请求相关日志",
                "modules": [
                    "app.middleware.logging_middleware",
                    "app.api.v1.system"
                ]
            },
            "database.log": {
                "description": "数据库相关日志",
                "modules": [
                    "app.database"
                ]
            },
            "websocket.log": {
                "description": "WebSocket相关日志",
                "modules": [
                    "app.websocket.manager"
                ]
            }
        }
        
        return {
            "success": True,
            "data": {
                "total_log_files": len(modules_info),
                "modules": modules_info,
                "log_files_info": get_logging_info()
            }
        }
    except Exception as e:
        logger.error(f"获取模块日志状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模块日志状态失败: {str(e)}")


def get_directory_size(path: str) -> int:
    """获取目录大小（字节）"""
    import os
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
    except (OSError, PermissionError):
        pass
    return total_size