"""
适配器工厂
管理不同TTS引擎的适配器实例
"""

import asyncio
from typing import Dict, Optional, Any, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AdapterStatus(str, Enum):
    """适配器状态"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class BaseAdapter:
    """基础适配器类"""
    
    def __init__(self, engine_id: str, engine_type: str, config: Dict[str, Any]):
        self.engine_id = engine_id
        self.engine_type = engine_type
        self.config = config
        self.status = AdapterStatus.OFFLINE
        self._is_ready = False
    
    @property
    def is_ready(self) -> bool:
        """检查适配器是否就绪"""
        return self._is_ready and self.status == AdapterStatus.READY
    
    async def initialize(self) -> None:
        """初始化适配器"""
        try:
            self.status = AdapterStatus.INITIALIZING
            # 模拟初始化过程
            await asyncio.sleep(0.1)
            self.status = AdapterStatus.READY
            self._is_ready = True
            logger.info(f"适配器初始化成功: {self.engine_id}")
        except Exception as e:
            self.status = AdapterStatus.ERROR
            self._is_ready = False
            logger.error(f"适配器初始化失败: {self.engine_id} - {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if not self._is_ready:
                raise RuntimeError("适配器未就绪")
            
            return {
                "status": "healthy",
                "engine_id": self.engine_id,
                "engine_type": self.engine_type,
                "response_time": 50.0,
                "memory_usage": "128MB",
                "cpu_usage": "5%"
            }
        except Exception as e:
            self.status = AdapterStatus.ERROR
            raise
    
    async def get_voices(self) -> List[Dict[str, Any]]:
        """获取支持的声音列表"""
        try:
            if not self._is_ready:
                raise RuntimeError("适配器未就绪")
            
            # 返回模拟的声音列表
            return [
                {
                    "id": "default_voice",
                    "name": "默认声音",
                    "display_name": "默认声音",
                    "language": "zh-CN",
                    "gender": "female"
                }
            ]
        except Exception as e:
            logger.error(f"获取声音列表失败: {e}")
            raise
    
    async def synthesize(self, **kwargs) -> Dict[str, Any]:
        """语音合成"""
        try:
            if not self._is_ready:
                raise RuntimeError("适配器未就绪")
            
            # 模拟合成过程
            await asyncio.sleep(0.5)
            
            return {
                "success": True,
                "duration": 2.5,
                "file_size": "128KB",
                "output_path": kwargs.get("output_path", "/tmp/output.wav")
            }
        except Exception as e:
            logger.error(f"语音合成失败: {e}")
            raise
    
    async def synthesize_safe(self, **kwargs):
        """安全的合成方法（包装异常处理）"""
        try:
            # 确保适配器就绪
            if not self._is_ready:
                await self.initialize()
            
            # 设置状态为忙碌
            self.status = AdapterStatus.BUSY
            
            try:
                # 执行合成
                result = await self.synthesize(**kwargs)
                self.status = AdapterStatus.READY
                
                # 创建标准化的结果对象
                from .base import SynthesisResult
                return SynthesisResult(
                    success=result.get("success", True),
                    output_path=result.get("output_path"),
                    duration=result.get("duration"),
                    sample_rate=kwargs.get("sample_rate", 22050),
                    error_message=result.get("error_message")
                )
            except Exception as e:
                self.status = AdapterStatus.ERROR
                raise
                
        except Exception as e:
            logger.error(f"引擎 {self.engine_id} 合成失败: {e}")
            from .base import SynthesisResult
            return SynthesisResult(
                success=False,
                error_message=str(e)
            )
    
    async def cleanup(self) -> None:
        """清理资源"""
        try:
            self.status = AdapterStatus.OFFLINE
            self._is_ready = False
            logger.info(f"适配器已清理: {self.engine_id}")
        except Exception as e:
            logger.error(f"适配器清理失败: {self.engine_id} - {e}")


class AdapterFactory:
    """适配器工厂"""
    
    def __init__(self):
        self._adapters: Dict[str, BaseAdapter] = {}
        self._initialized = False
    
    async def register_adapter(
        self, 
        engine_id: str, 
        engine_type: str, 
        config: Dict[str, Any]
    ) -> None:
        """注册适配器"""
        try:
            # 创建适配器实例
            adapter = BaseAdapter(engine_id, engine_type, config)
            
            # 初始化适配器
            await adapter.initialize()
            
            # 注册到工厂
            self._adapters[engine_id] = adapter
            
            logger.info(f"适配器注册成功: {engine_id} ({engine_type})")
        except Exception as e:
            logger.error(f"适配器注册失败: {engine_id} - {e}")
            raise
    
    async def get_adapter(self, engine_id: str) -> Optional[BaseAdapter]:
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
        ready_adapters = sum(1 for adapter in self._adapters.values() if adapter.is_ready)
        
        adapter_list = []
        for engine_id, adapter in self._adapters.items():
            adapter_list.append({
                "engine_id": engine_id,
                "engine_type": adapter.engine_type,
                "status": adapter.status.value,
                "is_ready": adapter.is_ready
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
                    "name": adapter.engine_type.upper(),
                    "type": adapter.engine_type,
                    "status": "healthy" if adapter.is_ready else "unhealthy",
                    "is_ready": adapter.is_ready,
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