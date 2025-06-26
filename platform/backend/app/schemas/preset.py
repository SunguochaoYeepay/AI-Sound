"""
预设配置相关Schema定义
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from .common import BaseResponseModel


class PresetCreate(BaseModel):
    """创建预设请求"""
    name: str = Field(min_length=1, max_length=200, description="预设名称")
    description: Optional[str] = Field(default=None, description="预设描述")
    config_type: str = Field(description="配置类型: voice_mapping, synthesis_params, analysis_params, analysis_complete")
    config_data: Dict[str, Any] = Field(description="配置数据")
    scope: str = Field(default="global", description="作用域: global, project, book")
    scope_id: Optional[int] = Field(default=None, description="作用域ID")


class PresetUpdate(BaseModel):
    """更新预设请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=200, description="预设名称")
    description: Optional[str] = Field(default=None, description="预设描述")
    config_data: Optional[Dict[str, Any]] = Field(default=None, description="配置数据")


class PresetResponse(BaseResponseModel):
    """预设响应"""
    name: str = Field(description="预设名称")
    description: Optional[str] = Field(description="预设描述")
    config_type: str = Field(description="配置类型")
    config_data: Dict[str, Any] = Field(description="配置数据")
    scope: str = Field(description="作用域")
    scope_id: Optional[int] = Field(description="作用域ID")
    usage_count: int = Field(description="使用次数")
    last_used: Optional[str] = Field(description="最后使用时间")


class PresetValidationResult(BaseModel):
    """预设验证结果"""
    valid: bool = Field(description="是否有效")
    errors: list[str] = Field(description="错误列表")
    warnings: list[str] = Field(description="警告列表")


class PresetImportRequest(BaseModel):
    """预设导入请求"""
    presets: list[Dict[str, Any]] = Field(description="预设数据列表")
    overwrite_existing: bool = Field(default=False, description="是否覆盖已存在的预设")


class PresetExportResponse(BaseModel):
    """预设导出响应"""
    presets: list[Dict[str, Any]] = Field(description="预设数据列表")
    export_time: str = Field(description="导出时间")
    total_count: int = Field(description="总数量") 