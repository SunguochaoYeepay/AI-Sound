"""
TTS 引擎适配器
"""

from .megatts3_adapter import MegaTTS3Adapter
from .espnet_adapter import ESPnetAdapter

__all__ = ['MegaTTS3Adapter', 'ESPnetAdapter']