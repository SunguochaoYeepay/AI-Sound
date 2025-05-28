"""
引擎状态API路由
"""

import logging
from fastapi import HTTPException
from typing import Dict, Any

from .server import app, get_tts_router, get_service_monitor
from src.tts.engine import TTSEngineType

logger = logging.getLogger(__name__)

# 使用router.get而不是app.get，避免与routes.py中的路由冲突
from fastapi import APIRouter

# 创建一个路由器实例
engine_router = APIRouter()

@engine_router.get("/api/engines/health")
async def get_engines_health():
    """获取所有引擎健康状态"""
    try:
        # 获取服务监控器
        monitor = get_service_monitor()
        if not monitor:
            raise HTTPException(
                status_code=500,
                detail="服务监控器未初始化"
            )
        
        # 获取健康状态
        health_status = monitor.get_health_status()
        
        # 如果没有健康状态数据，立即执行一次检查
        if not health_status:
            await monitor._check_services()
            health_status = monitor.get_health_status()
            
        return health_status
    except Exception as e:
        logger.error(f"获取引擎健康状态失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取引擎健康状态失败: {str(e)}"
        )

@engine_router.get("/api/engines/{engine_type}/health")
async def get_engine_health(engine_type: str):
    """获取指定引擎健康状态"""
    try:
        router = get_tts_router()
        if router is None:
            raise HTTPException(
                status_code=500,
                detail="TTS引擎路由器未初始化"
            )
            
        # 获取健康状态
        health_status = router.get_health_status()
        
        # 如果没有该引擎的健康状态数据，立即执行一次检查
        if engine_type not in health_status:
            try:
                engine_enum = TTSEngineType(engine_type)
                await router.check_engine_health(engine_enum)
                health_status = router.get_health_status()
            except ValueError:
                raise HTTPException(
                    status_code=404,
                    detail=f"引擎类型 {engine_type} 不存在"
                )
        
        # 返回指定引擎的健康状态
        if engine_type in health_status:
            return health_status[engine_type]
        else:
            raise HTTPException(
                status_code=404,
                detail=f"引擎 {engine_type} 健康状态不可用"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取引擎 {engine_type} 健康状态失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取引擎健康状态失败: {str(e)}"
        )

@engine_router.get("/api/engines")
async def get_engines_list():
    """获取所有引擎列表"""
    try:
        router = get_tts_router()
        if router is None:
            raise HTTPException(
                status_code=500,
                detail="TTS引擎路由器未初始化"
            )
            
        # 获取所有引擎
        engines_dict = router.get_registered_engines()
        
        # 转换为可序列化的格式
        engines = []
        for engine_type, _ in engines_dict.items():
            engines.append({
                "type": engine_type.value,
                "name": engine_type.value.upper()
            })
            
        return {"engines": engines}
    except Exception as e:
        logger.error(f"获取引擎列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取引擎列表失败: {str(e)}"
        )