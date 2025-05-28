"""
基础适配器接口和抽象类
定义TTS引擎适配器的标准接口
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EngineStatus(str, Enum):
    """引擎状态"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class SynthesisParams:
    """合成参数类"""
    
    def __init__(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
        pitch: float = 0.0,
        volume: float = 1.0,
        sample_rate: int = 22050,
        output_path: Optional[str] = None,
        **kwargs
    ):
        self.text = text
        self.voice_id = voice_id
        self.speed = speed
        self.pitch = pitch
        self.volume = volume
        self.sample_rate = sample_rate
        self.output_path = output_path
        self.extra_params = kwargs


class SynthesisResult:
    """合成结果类"""
    
    def __init__(
        self,
        success: bool,
        output_path: Optional[str] = None,
        duration: Optional[float] = None,
        sample_rate: Optional[int] = None,
        error_message: Optional[str] = None,
        **kwargs
    ):
        self.success = success
        self.output_path = output_path
        self.duration = duration
        self.sample_rate = sample_rate
        self.error_message = error_message
        self.extra_data = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "output_path": self.output_path,
            "duration": self.duration,
            "sample_rate": self.sample_rate,
            "error_message": self.error_message,
            **self.extra_data
        }


class BaseTTSAdapter(ABC):
    """TTS适配器基类"""
    
    def __init__(self, engine_id: str, config: Dict[str, Any]):
        self.engine_id = engine_id
        self.config = config
        self.status = EngineStatus.OFFLINE
        self._initialized = False
        self._lock = asyncio.Lock()
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化引擎"""
        pass
    
    @abstractmethod
    async def synthesize(self, params: SynthesisParams) -> SynthesisResult:
        """执行语音合成"""
        pass
    
    @abstractmethod
    async def get_voices(self) -> List[Dict[str, Any]]:
        """获取可用声音列表"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """清理资源"""
        pass
    
    @property
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized
    
    @property
    def is_ready(self) -> bool:
        """检查是否就绪"""
        return self.status == EngineStatus.READY
    
    async def ensure_initialized(self) -> None:
        """确保已初始化"""
        if not self._initialized:
            async with self._lock:
                if not self._initialized:
                    await self.initialize()
                    self._initialized = True
    
    def validate_params(self, params: SynthesisParams) -> None:
        """验证合成参数"""
        if not params.text:
            raise ValueError("文本不能为空")
        if not params.voice_id:
            raise ValueError("声音ID不能为空")
        if not (0.1 <= params.speed <= 3.0):
            raise ValueError("语速必须在0.1-3.0之间")
        if not (-12.0 <= params.pitch <= 12.0):
            raise ValueError("音调必须在-12.0-12.0之间")
        if not (0.1 <= params.volume <= 2.0):
            raise ValueError("音量必须在0.1-2.0之间")
    
    def map_parameters(self, params: SynthesisParams) -> Dict[str, Any]:
        """将通用参数映射为引擎特定参数"""
        # 默认实现，子类可以重写
        return {
            "text": params.text,
            "voice_id": params.voice_id,
            "speed": params.speed,
            "pitch": params.pitch,
            "volume": params.volume,
            "sample_rate": params.sample_rate,
            "output_path": params.output_path
        }
    
    async def synthesize_safe(self, **kwargs) -> SynthesisResult:
        """安全的合成方法（包装异常处理）"""
        try:
            # 确保引擎已初始化
            await self.ensure_initialized()
            
            # 创建参数对象
            params = SynthesisParams(**kwargs)
            
            # 验证参数
            self.validate_params(params)
            
            # 设置状态为忙碌
            self.status = EngineStatus.BUSY
            
            try:
                # 执行合成
                result = await self.synthesize(params)
                self.status = EngineStatus.READY
                return result
            except Exception as e:
                self.status = EngineStatus.ERROR
                raise
                
        except Exception as e:
            logger.error(f"引擎 {self.engine_id} 合成失败: {e}")
            return SynthesisResult(
                success=False,
                error_message=str(e)
            )


class AsyncTTSAdapter(BaseTTSAdapter):
    """异步TTS适配器基类"""
    
    def __init__(self, engine_id: str, config: Dict[str, Any]):
        super().__init__(engine_id, config)
        self._executor = None
    
    async def initialize(self) -> None:
        """初始化异步执行器"""
        # 可以在这里设置线程池执行器
        pass
    
    async def cleanup(self) -> None:
        """清理异步资源"""
        if self._executor:
            self._executor.shutdown(wait=True)


class ParameterMapper:
    """参数映射器"""
    
    @staticmethod
    def linear_map(value: float, input_range: tuple, output_range: tuple) -> float:
        """线性映射"""
        input_min, input_max = input_range
        output_min, output_max = output_range
        
        # 限制输入范围
        value = max(input_min, min(input_max, value))
        
        # 线性映射
        input_span = input_max - input_min
        output_span = output_max - output_min
        
        if input_span == 0:
            return output_min
        
        ratio = (value - input_min) / input_span
        return output_min + ratio * output_span
    
    @staticmethod
    def discrete_map(value: Any, mapping: Dict[Any, Any], default: Any = None) -> Any:
        """离散值映射"""
        return mapping.get(value, default)
    
    @staticmethod
    def speed_to_rate(speed: float) -> float:
        """将语速转换为引擎特定的速率"""
        # 通用映射：速度1.0对应速率1.0
        return speed
    
    @staticmethod
    def pitch_to_semitones(pitch: float) -> float:
        """将音调转换为半音"""
        return pitch