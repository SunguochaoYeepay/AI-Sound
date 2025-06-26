"""
角色检测器模块
包含多种角色识别和分析的实现方案
"""

from .character_detectors import ProgrammaticCharacterDetector
from .advanced_character_detector import AdvancedCharacterDetector
from .ollama_character_detector import OllamaCharacterDetector

__all__ = [
    'ProgrammaticCharacterDetector',
    'AdvancedCharacterDetector', 
    'OllamaCharacterDetector'
] 