"""
适配器模块
提供TTS引擎适配器的统一接口和实现
"""

from .base import BaseTTSAdapter, SynthesisParams, SynthesisResult, EngineStatus, ParameterMapper
from .factory import AdapterFactory
from .espnet_adapter import ESPnetAdapter
from .megatts3_adapter import MegaTTS3Adapter

__all__ = [
    "BaseTTSAdapter",
    "SynthesisParams", 
    "SynthesisResult",
    "EngineStatus",
    "ParameterMapper",
    "AdapterFactory",
    "ESPnetAdapter",
    "MegaTTS3Adapter"
]