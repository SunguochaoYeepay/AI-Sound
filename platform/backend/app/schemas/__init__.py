"""
数据Schema包
包含所有Pydantic模型定义，用于API请求/响应数据验证
"""

from .book import BookResponse, BookCreate, BookUpdate
from .chapter import ChapterResponse, ChapterCreate, ChapterUpdate
from .analysis import (
    AnalysisSessionResponse, AnalysisSessionCreate, AnalysisSessionUpdate,
    AnalysisResultResponse, AnalysisConfigUpdate, ConfigModification
)
from .synthesis import (
    SynthesisTaskResponse, SynthesisTaskCreate, SynthesisTaskUpdate
)
from .preset import (
    PresetResponse, PresetCreate, PresetUpdate
)
from .project import (
    ProjectResponse, ProjectCreate, ProjectUpdate
)
from .common import (
    PaginationParams, StatusResponse, ErrorResponse
)

__all__ = [
    # Book schemas
    'BookResponse', 'BookCreate', 'BookUpdate',
    
    # Chapter schemas
    'ChapterResponse', 'ChapterCreate', 'ChapterUpdate',
    
    # Analysis schemas
    'AnalysisSessionResponse', 'AnalysisSessionCreate', 'AnalysisSessionUpdate',
    'AnalysisResultResponse', 'AnalysisConfigUpdate', 'ConfigModification',
    
    # Synthesis schemas
    'SynthesisTaskResponse', 'SynthesisTaskCreate', 'SynthesisTaskUpdate',
    
    # Preset schemas
    'PresetResponse', 'PresetCreate', 'PresetUpdate',
    
    # Project schemas
    'ProjectResponse', 'ProjectCreate', 'ProjectUpdate',
    
    # Common schemas
    'PaginationParams', 'StatusResponse', 'ErrorResponse'
] 