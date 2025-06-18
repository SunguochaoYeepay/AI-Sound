#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# 基础模型
class EnvironmentSoundBase(BaseModel):
    name: str = Field(..., description="环境音名称")
    description: Optional[str] = Field(None, description="环境音描述")
    prompt: str = Field(..., description="生成提示词")
    duration: float = Field(default=10.0, ge=1.0, le=60.0, description="音频时长(秒)")
    category_id: int = Field(..., description="分类ID")

class EnvironmentSoundCreate(EnvironmentSoundBase):
    tag_ids: Optional[List[int]] = Field(default=[], description="标签ID列表")
    generation_params: Optional[Dict[str, Any]] = Field(default={}, description="生成参数")

class EnvironmentSoundUpdate(BaseModel):
    name: Optional[str] = Field(None, description="环境音名称")
    description: Optional[str] = Field(None, description="环境音描述")
    prompt: Optional[str] = Field(None, description="生成提示词")
    duration: Optional[float] = Field(None, ge=1.0, le=60.0, description="音频时长(秒)")
    category_id: Optional[int] = Field(None, description="分类ID")
    tag_ids: Optional[List[int]] = Field(None, description="标签ID列表")
    is_featured: Optional[bool] = Field(None, description="是否精选")

class EnvironmentSoundResponse(EnvironmentSoundBase):
    id: int
    file_path: Optional[str] = Field(None, description="音频文件路径")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    generation_status: str = Field(..., description="生成状态")
    generation_progress: int = Field(default=0, description="生成进度(0-100)")
    error_message: Optional[str] = Field(None, description="错误信息")
    is_featured: bool = Field(default=False, description="是否精选")
    play_count: int = Field(default=0, description="播放次数")
    download_count: int = Field(default=0, description="下载次数")
    favorite_count: int = Field(default=0, description="收藏次数")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 分类相关
class EnvironmentSoundCategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    icon: Optional[str]
    color: Optional[str]
    sound_count: int = Field(default=0, description="该分类下的音效数量")
    sort_order: int = Field(default=0, description="排序顺序")
    is_active: bool = Field(default=True, description="是否激活")
    
    class Config:
        from_attributes = True

# 标签相关
class EnvironmentSoundTagResponse(BaseModel):
    id: int
    name: str
    color: Optional[str]
    usage_count: int = Field(default=0, description="使用次数")
    
    class Config:
        from_attributes = True

# 生成请求
class EnvironmentSoundGenerateRequest(BaseModel):
    name: str = Field(..., description="环境音名称")
    prompt: str = Field(..., description="生成提示词")
    duration: float = Field(default=10.0, ge=1.0, le=60.0, description="音频时长(秒)")
    steps: int = Field(default=25, ge=10, le=100, description="生成步数")
    cfg_scale: float = Field(default=4.5, ge=1.0, le=20.0, description="CFG缩放")
    category_id: int = Field(..., description="分类ID")
    tag_ids: Optional[List[int]] = Field(default=[], description="标签ID列表")
    description: Optional[str] = Field(None, description="环境音描述")

class EnvironmentSoundGenerateResponse(BaseModel):
    sound_id: int = Field(..., description="环境音ID")
    status: str = Field(..., description="生成状态")
    message: str = Field(..., description="状态消息")
    estimated_time: Optional[int] = Field(None, description="预估完成时间(秒)")

# 列表响应
class EnvironmentSoundListResponse(BaseModel):
    sounds: List[EnvironmentSoundResponse]
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    pages: int = Field(..., description="总页数") 