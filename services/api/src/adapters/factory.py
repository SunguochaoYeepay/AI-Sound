"""
适配器工厂类
负责创建和管理不同类型的TTS引擎适配器
"""

import asyncio
from typing import Dict, Optional, Type, List, Any
import logging

from .base import BaseTTSAdapter, EngineStatus
from .espnet_adapter import ESPnetAdapter
from .megatts3_adapter import MegaTTS3Adapter

logger = logging.getLogger(__name__)


class AdapterFactory:
    """适配器工厂"""
    
    def __init__(self):
        # 注册的适配器类型
        self._adapter_types: Dict[str, Type[BaseTTSAdapter]] = {
            "espnet": ESPnetAdapter,
            "megatts3": MegaTTS3Adapter,
            "bert_vits2": MegaTTS3Adapter,  # 暂时使用MegaTTS3适配器
        }
        
        # 活跃的适配器实例
        self._adapters: Dict[str, BaseTTSAdapter] = {}
        
        # 适配器配置
        self._configs: Dict[str, Dict[str, Any]] = {}
    
    def register_adapter_type(self, engine_type: str, adapter_class: Type[BaseTTSAdapter]) -> None:
        """注册适配器类型"""
        self._adapter_types[engine_type] = adapter_class
        logger.info(f"适配器类型已注册: {engine_type} -> {adapter_class.__name__}")
    
    async def register_adapter(
        self, 
        engine_id: str, 
        engine_type: str, 
        config: Dict[str, Any]
    ) -> BaseTTSAdapter:
        """注册并创建适配器实例"""
        try:
            # 检查适配器类型是否支持
            if engine_type not in self._adapter_types:
                raise ValueError(f"不支持的引擎类型: {engine_type}")
            
            # 如果已存在，先清理
            if engine_id in self._adapters:
                await self.remove_adapter(engine_id)
            
            # 创建适配器实例
            adapter_class = self._adapter_types[engine_type]
            adapter = adapter_class(engine_id, config)
            
            # 初始化适配器
            try:
                await adapter.initialize()
                adapter.status = EngineStatus.READY
                logger.info(f"适配器初始化成功: {engine_id} ({engine_type})")
            except Exception as e:
                adapter.status = EngineStatus.ERROR
                logger.error(f"适配器初始化失败: {engine_id} - {e}")
                # 即使初始化失败也保存实例，便于后续重试
            
            # 保存适配器和配置
            self._adapters[engine_id] = adapter
            self._configs[engine_id] = config.copy()
            
            return adapter
            
        except Exception as e:
            logger.error(f"注册适配器失败: {engine_id} - {e}")
            raise
    
    async def get_adapter(self, engine_id: str) -> Optional[BaseTTSAdapter]:
        """获取适配器实例"""
        return self._adapters.get(engine_id)
    
    async def remove_adapter(self, engine_id: str) -> bool:
        """移除适配器"""
        try:
            adapter = self._adapters.get(engine_id)
            if adapter:
                # 清理资源
                await adapter.cleanup()
                logger.info(f"适配器已清理: {engine_id}")
            
            # 移除记录
            self._adapters.pop(engine_id, None)
            self._configs.pop(engine_id, None)
            
            return True
        except Exception as e:
            logger.error(f"移除适配器失败: {engine_id} - {e}")
            return False
    
    async def reload_adapter(self, engine_id: str) -> bool:
        """重新加载适配器"""
        try:
            config = self._configs.get(engine_id)
            if not config:
                return False
            
            adapter = self._adapters.get(engine_id)
            if not adapter:
                return False
            
            # 获取引擎类型
            engine_type = None
            for etype, adapter_class in self._adapter_types.items():
                if isinstance(adapter, adapter_class):
                    engine_type = etype
                    break
            
            if not engine_type:
                return False
            
            # 重新注册
            await self.register_adapter(engine_id, engine_type, config)
            return True
            
        except Exception as e:
            logger.error(f"重新加载适配器失败: {engine_id} - {e}")
            return False
    
    async def get_available_engines(self) -> List[str]:
        """获取可用的引擎列表"""
        available = []
        for engine_id, adapter in self._adapters.items():
            if adapter.is_ready:
                available.append(engine_id)
        return available
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """对所有适配器进行健康检查"""
        results = {}
        
        for engine_id, adapter in self._adapters.items():
            try:
                health_data = await adapter.health_check()
                results[engine_id] = {
                    "status": adapter.status.value,
                    "healthy": adapter.is_ready,
                    "details": health_data
                }
            except Exception as e:
                results[engine_id] = {
                    "status": "error",
                    "healthy": False,
                    "error": str(e)
                }
        
        return results
    
    async def cleanup_all(self) -> None:
        """清理所有适配器"""
        logger.info("正在清理所有适配器...")
        
        cleanup_tasks = []
        for engine_id in list(self._adapters.keys()):
            cleanup_tasks.append(self.remove_adapter(engine_id))
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        logger.info("所有适配器已清理完成")
    
    def get_adapter_stats(self) -> Dict[str, Any]:
        """获取适配器统计信息"""
        total = len(self._adapters)
        ready = sum(1 for adapter in self._adapters.values() if adapter.is_ready)
        error = sum(1 for adapter in self._adapters.values() if adapter.status == EngineStatus.ERROR)
        offline = sum(1 for adapter in self._adapters.values() if adapter.status == EngineStatus.OFFLINE)
        
        return {
            "total_adapters": total,
            "ready_adapters": ready,
            "error_adapters": error,
            "offline_adapters": offline,
            "supported_types": list(self._adapter_types.keys()),
            "adapters": {
                engine_id: {
                    "status": adapter.status.value,
                    "type": type(adapter).__name__,
                    "initialized": adapter.is_initialized
                }
                for engine_id, adapter in self._adapters.items()
            }
        }
    
    def get_supported_types(self) -> List[str]:
        """获取支持的引擎类型"""
        return list(self._adapter_types.keys())
    
    async def auto_discover_engines(self) -> List[Dict[str, Any]]:
        """自动发现可用的引擎（基于Docker容器标签等）"""
        # TODO: 实现基于Docker API的引擎自动发现
        discovered = []
        
        # 示例发现逻辑
        # try:
        #     import docker
        #     client = docker.from_env()
        #     containers = client.containers.list(
        #         filters={"label": "ai-sound.engine=true"}
        #     )
        #     for container in containers:
        #         labels = container.labels
        #         engine_info = {
        #             "id": container.name,
        #             "type": labels.get("ai-sound.engine.type"),
        #             "version": labels.get("ai-sound.engine.version"),
        #             "endpoint": f"http://{container.name}:8000",
        #             "capabilities": labels.get("ai-sound.engine.capabilities", "").split(",")
        #         }
        #         discovered.append(engine_info)
        # except Exception as e:
        #     logger.warning(f"引擎自动发现失败: {e}")
        
        return discovered