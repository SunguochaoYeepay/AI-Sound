"""
通用Schema定义
包含通用的请求/响应模型
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime


class PaginationParams(BaseModel):
    """分页参数"""
    skip: int = Field(default=0, ge=0, description="跳过的记录数")
    limit: int = Field(default=20, ge=1, le=100, description="每页记录数")


class StatusResponse(BaseModel):
    """状态响应"""
    success: bool = Field(description="操作是否成功")
    message: str = Field(description="响应消息")
    data: Optional[Dict[str, Any]] = Field(default=None, description="响应数据")


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(description="错误类型")
    message: str = Field(description="错误消息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")


class BaseTimestampMixin(BaseModel):
    """时间戳混入类"""
    created_at: Optional[datetime] = Field(description="创建时间")
    updated_at: Optional[datetime] = Field(description="更新时间")


class BaseResponseModel(BaseTimestampMixin):
    """基础响应模型"""
    id: int = Field(description="唯一标识符")
    
    class Config:
        from_attributes = True


class ProgressInfo(BaseModel):
    """进度信息"""
    status: str = Field(description="状态")
    progress: int = Field(ge=0, le=100, description="进度百分比")
    current_step: Optional[str] = Field(default=None, description="当前步骤")
    total_items: Optional[int] = Field(default=None, description="总项目数")
    completed_items: Optional[int] = Field(default=None, description="已完成项目数")
    failed_items: Optional[int] = Field(default=None, description="失败项目数")
    error_message: Optional[str] = Field(default=None, description="错误消息")


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    filename: str = Field(description="文件名")
    file_path: str = Field(description="文件路径")
    file_size: int = Field(description="文件大小（字节）")
    content_type: str = Field(description="文件类型")


class WebSocketMessage(BaseModel):
    """WebSocket消息格式"""
    type: str = Field(description="消息类型")
    data: Dict[str, Any] = Field(description="消息数据")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="时间戳") 