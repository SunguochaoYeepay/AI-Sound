"""
依赖注入管理模块
统一管理应用的依赖服务实例
"""

from fastapi import Depends
from typing import Optional, Dict, Any
import logging

from .database import db_manager, get_database
from .config import settings
from ..adapters.factory import AdapterFactory

logger = logging.getLogger(__name__)


class DependencyManager:
    """依赖管理器"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._initialized = False
        self.adapter_factory = AdapterFactory()
    
    async def initialize(self) -> None:
        """初始化所有依赖服务"""
        if self._initialized:
            return
        
        logger.info("正在初始化依赖服务...")
        
        # 初始化数据库连接
        await db_manager.connect()
        
        # 初始化TTS引擎适配器
        await self._initialize_tts_engines()
        
        # 注册服务
        self.register_service("adapter_factory", self.adapter_factory)
        
        self._initialized = True
        logger.info("依赖服务初始化完成")
    
    async def _initialize_tts_engines(self) -> None:
        """初始化TTS引擎适配器"""
        logger.info("正在初始化TTS引擎适配器...")
        
        # 从环境变量获取引擎服务URL
        engine_configs = {
            "megatts3": {
                "type": "megatts3",
                "endpoint": settings.engines.megatts3_url,
                "enabled": True
            },
            "espnet": {
                "type": "espnet", 
                "endpoint": settings.engines.espnet_url,
                "enabled": True
            },
            "bert_vits2": {
                "type": "bert_vits2",
                "endpoint": settings.engines.bertvits2_url,
                "enabled": True
            }
        }
        
        # 注册引擎适配器
        for engine_id, config in engine_configs.items():
            if config.get("enabled", True):
                try:
                    await self.adapter_factory.register_adapter(
                        engine_id=engine_id,
                        engine_type=config["type"],
                        config=config
                    )
                    logger.info(f"TTS引擎适配器注册成功: {engine_id}")
                except Exception as e:
                    logger.error(f"TTS引擎适配器注册失败: {engine_id} - {e}")
        
        # 输出适配器统计信息
        stats = self.adapter_factory.get_adapter_stats()
        logger.info(f"TTS引擎适配器初始化完成: {stats}")
    
    async def cleanup(self) -> None:
        """清理所有依赖服务"""
        logger.info("正在清理依赖服务...")
        
        # 清理TTS引擎适配器
        await self.adapter_factory.cleanup_all()
        
        # 清理数据库连接
        await db_manager.disconnect()
        
        # 清理其他服务...
        
        self._services.clear()
        self._initialized = False
        logger.info("依赖服务清理完成")
    
    def register_service(self, name: str, service: Any) -> None:
        """注册服务"""
        self._services[name] = service
        logger.info(f"服务已注册: {name}")
    
    def get_service(self, name: str) -> Optional[Any]:
        """获取服务"""
        return self._services.get(name)


# 全局依赖管理器
dependency_manager = DependencyManager()


# FastAPI依赖函数
async def get_dependency_manager() -> DependencyManager:
    """获取依赖管理器"""
    return dependency_manager


async def get_db():
    """获取数据库连接（FastAPI依赖）"""
    return await get_database()


async def get_adapter_factory() -> AdapterFactory:
    """获取适配器工厂（FastAPI依赖）"""
    return dependency_manager.adapter_factory