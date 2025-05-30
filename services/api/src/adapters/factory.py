"""
适配器工厂
管理不同TTS引擎的适配器实例
"""

import asyncio
from typing import Dict, Optional, Any, List
from enum import Enum
import logging

from .base import BaseTTSAdapter, SynthesisParams, SynthesisResult, EngineStatus, ParameterMapper
from .megatts3_adapter import MegaTTS3Adapter
from .espnet_adapter import ESPnetAdapter

logger = logging.getLogger(__name__)


class AdapterStatus(str, Enum):
    """适配器状态"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class AdapterFactory:
    """适配器工厂"""
    
    def __init__(self):
        self._adapters: Dict[str, BaseTTSAdapter] = {}
        self._initialized = False
        # 引擎类型映射
        self._adapter_classes = {
            "megatts3": MegaTTS3Adapter,
            "espnet": ESPnetAdapter,
            "bert_vits2": MegaTTS3Adapter,  # 暂时使用MegaTTS3适配器
        }
    
    async def register_adapter(
        self, 
        engine_id: str, 
        engine_type: str, 
        config: Dict[str, Any]
    ) -> None:
        """注册适配器"""
        try:
            # 根据引擎类型创建对应的适配器
            adapter_class = self._adapter_classes.get(engine_type)
            if not adapter_class:
                logger.warning(f"不支持的引擎类型: {engine_type}，使用基础适配器")
                # 如果不支持的类型，创建一个基础适配器
                adapter = BaseTTSAdapter(engine_id, config)
            else:
                # 创建具体的适配器实例
                adapter = adapter_class(engine_id, config)
            
            # 初始化适配器
            await adapter.initialize()
            
            # 注册到工厂
            self._adapters[engine_id] = adapter
            
            logger.info(f"适配器注册成功: {engine_id} ({engine_type})")
        except Exception as e:
            logger.error(f"适配器注册失败: {engine_id} - {e}")
            raise
    
    async def get_adapter(self, engine_id: str) -> Optional[BaseTTSAdapter]:
        """获取适配器"""
        return self._adapters.get(engine_id)
    
    async def remove_adapter(self, engine_id: str) -> bool:
        """移除适配器"""
        try:
            adapter = self._adapters.get(engine_id)
            if adapter:
                await adapter.cleanup()
                del self._adapters[engine_id]
                logger.info(f"适配器已移除: {engine_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"移除适配器失败: {engine_id} - {e}")
            raise
    
    async def cleanup_all(self) -> None:
        """清理所有适配器"""
        try:
            for engine_id, adapter in self._adapters.items():
                try:
                    await adapter.cleanup()
                except Exception as e:
                    logger.error(f"清理适配器失败: {engine_id} - {e}")
            
            self._adapters.clear()
            logger.info("所有适配器已清理")
        except Exception as e:
            logger.error(f"清理所有适配器失败: {e}")
    
    def get_adapter_stats(self) -> Dict[str, Any]:
        """获取适配器统计信息"""
        total_adapters = len(self._adapters)
        ready_adapters = sum(1 for adapter in self._adapters.values() if adapter.status == EngineStatus.READY)
        
        adapter_list = []
        for engine_id, adapter in self._adapters.items():
            adapter_list.append({
                "engine_id": engine_id,
                "engine_type": getattr(adapter, 'engine_type', 'unknown'),
                "status": adapter.status.value,
                "is_ready": adapter.status == EngineStatus.READY
            })
        
        return {
            "total_adapters": total_adapters,
            "ready_adapters": ready_adapters,
            "error_adapters": total_adapters - ready_adapters,
            "adapters": adapter_list
        }
    
    async def get_available_engines(self) -> List[Dict[str, Any]]:
        """获取可用引擎列表"""
        try:
            engines = []
            for engine_id, adapter in self._adapters.items():
                engine_info = {
                    "id": engine_id,
                    "name": getattr(adapter, 'engine_type', 'unknown').upper(),
                    "type": getattr(adapter, 'engine_type', 'unknown'),
                    "status": "healthy" if adapter.status == EngineStatus.READY else "unhealthy",
                    "is_ready": adapter.status == EngineStatus.READY,
                    "endpoint": adapter.config.get("endpoint", ""),
                    "capabilities": {
                        "supports_streaming": False,
                        "supports_emotions": False,
                        "max_text_length": 1000,
                        "supported_formats": ["wav", "mp3"]
                    }
                }
                engines.append(engine_info)
            
            return engines
        except Exception as e:
            logger.error(f"获取可用引擎列表失败: {e}")
            return []