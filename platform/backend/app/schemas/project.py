"""
项目相关Schema定义
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from .common import BaseResponseModel


class ProjectCreate(BaseModel):
    """创建项目请求"""
    book_id: Optional[int] = Field(default=None, description="关联的书籍ID")
    name: str = Field(min_length=1, max_length=200, description="项目名称")
    description: Optional[str] = Field(default=None, description="项目描述")
    config: Optional[Dict[str, Any]] = Field(default=None, description="项目配置")


class ProjectUpdate(BaseModel):
    """更新项目请求"""
    book_id: Optional[int] = Field(default=None, description="关联的书籍ID")
    name: Optional[str] = Field(default=None, min_length=1, max_length=200, description="项目名称")
    description: Optional[str] = Field(default=None, description="项目描述")
    config: Optional[Dict[str, Any]] = Field(default=None, description="项目配置")


class ProjectResponse(BaseResponseModel):
    """项目响应"""
    book_id: Optional[int] = Field(description="关联的书籍ID")
    name: str = Field(description="项目名称")
    description: Optional[str] = Field(description="项目描述")
    config: Optional[Dict[str, Any]] = Field(description="项目配置")
    

class ProjectStatistics(BaseModel):
    """项目统计信息"""
    project_id: int = Field(description="项目ID")
    analysis_sessions_count: int = Field(description="分析会话数量")
    synthesis_tasks_count: int = Field(description="合成任务数量")
    completed_chapters: int = Field(description="已完成章节数")
    total_chapters: int = Field(description="总章节数")
    completion_rate: float = Field(description="完成率")
    total_audio_duration: Optional[float] = Field(description="总音频时长")
    last_activity: Optional[str] = Field(description="最后活动时间") 