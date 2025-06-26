"""
声音档案相关Schema定义
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from .common import BaseResponseModel


class VoiceProfileCreate(BaseModel):
    """创建声音档案请求"""
    name: str = Field(min_length=1, max_length=100, description="声音档案名称")
    description: Optional[str] = Field(default=None, description="声音档案描述")
    type: str = Field(description="声音类型 (male/female/child)")
    reference_audio_path: Optional[str] = Field(default=None, description="参考音频路径")
    color: str = Field(default="#06b6d4", description="显示颜色")
    parameters: Optional[Dict[str, Any]] = Field(
        default={"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0},
        description="声音参数"
    )


class VoiceProfileUpdate(BaseModel):
    """更新声音档案请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="声音档案名称")
    description: Optional[str] = Field(default=None, description="声音档案描述")
    type: Optional[str] = Field(default=None, description="声音类型")
    reference_audio_path: Optional[str] = Field(default=None, description="参考音频路径")
    color: Optional[str] = Field(default=None, description="显示颜色")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="声音参数")
    status: Optional[str] = Field(default=None, description="状态")


class VoiceProfileResponse(BaseResponseModel):
    """声音档案响应"""
    name: str = Field(description="声音档案名称")
    description: Optional[str] = Field(description="声音档案描述")
    type: str = Field(description="声音类型")
    reference_audio_path: Optional[str] = Field(description="参考音频路径")
    latent_file_path: Optional[str] = Field(description="潜在特征文件路径")
    sample_audio_path: Optional[str] = Field(description="样本音频路径")
    parameters: Dict[str, Any] = Field(description="声音参数")
    quality_score: float = Field(description="质量评分")
    usage_count: int = Field(description="使用次数")
    last_used: Optional[datetime] = Field(description="最后使用时间")
    color: str = Field(description="显示颜色")
    tags: list = Field(description="标签列表")
    status: str = Field(description="状态")


class VoiceProfileStats(BaseModel):
    """声音档案统计"""
    total_profiles: int = Field(description="总档案数")
    active_profiles: int = Field(description="活跃档案数")
    by_type: Dict[str, int] = Field(description="按类型统计")
    average_quality: float = Field(description="平均质量") 