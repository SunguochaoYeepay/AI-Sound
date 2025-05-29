"""
系统管理API路由
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import FileResponse
from typing import Dict, List, Optional, Any
import logging
import os
import json
from datetime import datetime
from pathlib import Path

from ...core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/stats")
async def get_system_stats():
    """获取系统统计信息"""
    try:
        import psutil
        import platform
        
        # CPU信息
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # 内存信息
        memory = psutil.virtual_memory()
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        
        # 系统信息
        system_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "uptime": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "core_count": cpu_count
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "usage_percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "usage_percent": (disk.used / disk.total) * 100
                },
                "system": system_info
            }
        }
    except Exception as e:
        logger.error(f"获取系统统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings")
async def get_settings():
    """获取系统设置"""
    try:
        # 返回系统配置的安全版本（去除敏感信息）
        safe_settings = {
            "app_name": settings.app_name,
            "version": settings.version,
            "debug": settings.debug,
            "tts": {
                "max_text_length": settings.tts.max_text_length,
                "default_engine": getattr(settings.tts, 'default_engine', 'gpt_sovits'),
                "output_format": getattr(settings.tts, 'output_format', 'wav'),
                "sample_rate": getattr(settings.tts, 'sample_rate', 22050)
            }
        }
        
        return {
            "success": True,
            "data": safe_settings
        }
    except Exception as e:
        logger.error(f"获取系统设置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings")
async def update_settings(settings_data: Dict[str, Any]):
    """更新系统设置"""
    try:
        # 这里应该实现设置更新逻辑
        # 为了安全起见，只允许更新特定的设置项
        allowed_keys = [
            "tts.max_text_length",
            "tts.default_engine", 
            "tts.output_format",
            "tts.sample_rate"
        ]
        
        updated_settings = {}
        for key, value in settings_data.items():
            if key in allowed_keys:
                updated_settings[key] = value
                logger.info(f"更新设置: {key} = {value}")
        
        return {
            "success": True,
            "message": f"已更新 {len(updated_settings)} 个设置项",
            "data": updated_settings
        }
    except Exception as e:
        logger.error(f"更新系统设置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings/export")
async def export_settings():
    """导出系统设置"""
    try:
        # 获取当前设置
        settings_response = await get_settings()
        settings_data = settings_response["data"]
        
        # 添加导出元数据
        export_data = {
            "export_time": datetime.now().isoformat(),
            "version": settings.version,
            "settings": settings_data
        }
        
        return {
            "success": True,
            "data": export_data,
            "filename": f"ai_sound_settings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
    except Exception as e:
        logger.error(f"导出系统设置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/import")
async def import_settings(import_data: Dict[str, Any]):
    """导入系统设置"""
    try:
        # 验证导入数据格式
        if "settings" not in import_data:
            raise HTTPException(status_code=400, detail="无效的导入数据格式")
        
        settings_to_import = import_data["settings"]
        
        # 导入设置（调用更新设置接口）
        result = await update_settings(settings_to_import)
        
        return {
            "success": True,
            "message": "设置导入成功",
            "data": result["data"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入系统设置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_logs(
    limit: int = Query(100, ge=1, le=1000, description="返回日志数量"),
    level: Optional[str] = Query(None, description="日志级别过滤"),
    search: Optional[str] = Query(None, description="搜索关键词")
):
    """获取系统日志"""
    try:
        # 这里应该从日志文件或日志系统中读取日志
        # 为了示例，我们返回一些模拟日志
        logs = []
        
        # 模拟日志条目
        sample_logs = [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": "系统启动成功",
                "module": "app"
            },
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO", 
                "message": "TTS引擎初始化完成",
                "module": "tts"
            },
            {
                "timestamp": datetime.now().isoformat(),
                "level": "WARNING",
                "message": "检测到新的引擎更新",
                "module": "engine"
            }
        ]
        
        # 应用过滤条件
        filtered_logs = sample_logs
        if level:
            filtered_logs = [log for log in filtered_logs if log["level"].lower() == level.lower()]
        if search:
            filtered_logs = [log for log in filtered_logs if search.lower() in log["message"].lower()]
        
        # 限制返回数量
        limited_logs = filtered_logs[:limit]
        
        return {
            "success": True,
            "data": {
                "logs": limited_logs,
                "total": len(limited_logs),
                "filters": {
                    "level": level,
                    "search": search,
                    "limit": limit
                }
            }
        }
    except Exception as e:
        logger.error(f"获取系统日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/download")
async def download_logs():
    """下载日志文件"""
    try:
        # 查找日志文件
        log_files = []
        
        # 常见的日志文件位置
        possible_log_paths = [
            "logs/app.log",
            "logs/error.log", 
            "app.log",
            "/tmp/ai_sound.log"
        ]
        
        for log_path in possible_log_paths:
            if os.path.exists(log_path):
                log_files.append(log_path)
        
        if not log_files:
            # 创建一个临时日志文件
            temp_log_path = "/tmp/ai_sound_logs.txt"
            with open(temp_log_path, 'w', encoding='utf-8') as f:
                f.write(f"AI-Sound 系统日志\n")
                f.write(f"生成时间: {datetime.now().isoformat()}\n")
                f.write("="*50 + "\n")
                f.write("暂无日志文件，这是临时生成的日志摘要。\n")
            
            return FileResponse(
                path=temp_log_path,
                media_type="text/plain",
                filename=f"ai_sound_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
        
        # 返回第一个找到的日志文件
        log_file = log_files[0]
        return FileResponse(
            path=log_file,
            media_type="text/plain",
            filename=f"ai_sound_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
    except Exception as e:
        logger.error(f"下载日志文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/logs")
async def clear_logs():
    """清空系统日志"""
    try:
        # 清空日志的逻辑
        # 注意：这是一个危险操作，实际实现时需要谨慎
        
        cleared_files = []
        
        # 常见的日志文件位置
        possible_log_paths = [
            "logs/app.log",
            "logs/error.log",
            "app.log"
        ]
        
        for log_path in possible_log_paths:
            if os.path.exists(log_path):
                try:
                    # 清空文件内容而不是删除文件
                    with open(log_path, 'w') as f:
                        f.write(f"# 日志已于 {datetime.now().isoformat()} 清空\n")
                    cleared_files.append(log_path)
                except Exception as e:
                    logger.warning(f"清空日志文件失败 {log_path}: {e}")
        
        return {
            "success": True,
            "message": f"已清空 {len(cleared_files)} 个日志文件",
            "data": {
                "cleared_files": cleared_files,
                "clear_time": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"清空系统日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 