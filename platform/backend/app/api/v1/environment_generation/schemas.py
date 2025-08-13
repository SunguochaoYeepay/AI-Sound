"""
环境音生成API的请求/响应模型
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class EnvironmentGenerationRequest(BaseModel):
    """环境音生成请求"""
    project_id: int
    synthesis_plan: List[Dict[str, Any]]
    options: Optional[Dict[str, Any]] = {}


class ValidationEditRequest(BaseModel):
    """校对编辑请求"""
    track_index: int
    manual_edits: Dict[str, Any]


class ValidationApprovalRequest(BaseModel):
    """校对审批请求"""
    track_index: int
    validation_result: str  # approved/rejected/needs_revision
    notes: Optional[str] = None


class ChapterEnvironmentAnalysisRequest(BaseModel):
    """章节环境音分析请求 - 新流程"""
    chapter_ids: List[int]
    analysis_options: Optional[Dict[str, Any]] = {}


class EnvironmentMatchingRequest(BaseModel):
    """环境音匹配请求"""
    analysis_result: Dict[str, Any]
    matching_options: Optional[Dict[str, Any]] = {}


class EnvironmentProjectCreateRequest(BaseModel):
    """环境音项目创建请求"""
    name: str
    description: Optional[str] = ""
    book_id: Optional[int] = None
    chapter_ids: Optional[List[int]] = []
    analysis_options: Optional[Dict[str, Any]] = {}


class TimelineExportRequest(BaseModel):
    """时间轴导出请求"""
    timeline_data: Dict[str, Any]
    export_format: str = 'generic'  # generic, premiere_pro, davinci_resolve
    output_path: Optional[str] = None


class BatchGenerationRequest(BaseModel):
    """批量生成环境音请求"""
    tracks: List[Dict[str, Any]]
    options: Optional[Dict[str, Any]] = {}


class EnvironmentProjectUpdateRequest(BaseModel):
    """环境音项目更新请求"""
    analysis_result: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    chapter_id: Optional[int] = None  # 添加章节ID字段
