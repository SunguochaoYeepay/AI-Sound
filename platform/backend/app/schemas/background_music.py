"""
背景音乐相关的数据模式定义
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import json


class MusicCategoryBase(BaseModel):
    """音乐分类基础模式"""
    name: str = Field(..., description="分类名称")
    description: Optional[str] = Field(None, description="分类描述")
    icon: Optional[str] = Field(None, description="分类图标")


class MusicCategoryCreate(MusicCategoryBase):
    """创建音乐分类的数据模式"""
    pass


class MusicCategoryUpdate(BaseModel):
    """更新音乐分类的数据模式"""
    name: Optional[str] = Field(None, description="分类名称")
    description: Optional[str] = Field(None, description="分类描述")
    icon: Optional[str] = Field(None, description="分类图标")
    is_active: Optional[bool] = Field(None, description="是否启用")


class MusicCategoryResponse(MusicCategoryBase):
    """音乐分类响应模式"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BackgroundMusicBase(BaseModel):
    """背景音乐基础模式"""
    name: str = Field(..., description="音乐名称")
    description: Optional[str] = Field(None, description="音乐描述")
    category_id: int = Field(..., description="分类ID")
    emotion_tags: Optional[List[str]] = Field(default_factory=list, description="情感标签")
    style_tags: Optional[List[str]] = Field(default_factory=list, description="风格标签")
    quality_rating: Optional[float] = Field(None, ge=0, le=5, description="质量评分")

    @validator('emotion_tags', 'style_tags', pre=True)
    def parse_tags(cls, v):
        """解析标签，支持字符串或列表"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return [tag.strip() for tag in v.split(',') if tag.strip()]
        return v or []


class BackgroundMusicCreate(BackgroundMusicBase):
    """创建背景音乐的数据模式"""
    filename: str = Field(..., description="文件名")


class BackgroundMusicUpdate(BaseModel):
    """更新背景音乐的数据模式"""
    name: Optional[str] = Field(None, description="音乐名称")
    description: Optional[str] = Field(None, description="音乐描述")
    category_id: Optional[int] = Field(None, description="分类ID")
    emotion_tags: Optional[List[str]] = Field(None, description="情感标签")
    style_tags: Optional[List[str]] = Field(None, description="风格标签")
    quality_rating: Optional[float] = Field(None, ge=0, le=5, description="质量评分")
    is_active: Optional[bool] = Field(None, description="是否启用")

    @validator('emotion_tags', 'style_tags', pre=True)
    def parse_tags(cls, v):
        """解析标签，支持字符串或列表"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return [tag.strip() for tag in v.split(',') if tag.strip()]
        return v


class BackgroundMusicResponse(BackgroundMusicBase):
    """背景音乐响应模式"""
    id: int
    filename: str
    file_path: Optional[str]
    file_size: Optional[int]
    duration: Optional[float]
    usage_count: int
    last_used_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    category: Optional[MusicCategoryResponse] = None

    class Config:
        from_attributes = True


class BackgroundMusicListResponse(BaseModel):
    """背景音乐列表响应模式"""
    items: List[BackgroundMusicResponse]
    total: int
    skip: int
    limit: int


class MusicRecommendation(BaseModel):
    """音乐推荐模式"""
    music: BackgroundMusicResponse
    score: float = Field(..., description="推荐得分")
    reason: str = Field(..., description="推荐原因")


class MusicStatsResponse(BaseModel):
    """音乐库统计响应模式"""
    total_music: int = Field(..., description="音乐总数")
    total_categories: int = Field(..., description="分类总数")
    total_duration: float = Field(..., description="总时长(秒)")
    total_size: int = Field(..., description="总大小(字节)")
    active_music: int = Field(..., description="活跃音乐数")
    popular_categories: List[Dict[str, Any]] = Field(..., description="热门分类")
    recent_uploads: List[BackgroundMusicResponse] = Field(..., description="最近上传")


class EmotionMappingResponse(BaseModel):
    """情感映射响应模式"""
    emotion: str = Field(..., description="情感类型")
    music_count: int = Field(..., description="对应音乐数量")
    recommended_styles: List[str] = Field(..., description="推荐风格")


class BatchOperationRequest(BaseModel):
    """批量操作请求模式"""
    music_ids: List[int] = Field(..., description="音乐ID列表")
    operation: str = Field(..., description="操作类型: activate, deactivate, delete")


class BatchOperationResponse(BaseModel):
    """批量操作响应模式"""
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    failed_ids: List[int] = Field(..., description="失败的ID列表")
    message: str = Field(..., description="操作结果消息")


class MusicSearchRequest(BaseModel):
    """音乐搜索请求模式"""
    query: Optional[str] = Field(None, description="搜索关键词")
    category_ids: Optional[List[int]] = Field(None, description="分类ID列表")
    emotion_tags: Optional[List[str]] = Field(None, description="情感标签")
    style_tags: Optional[List[str]] = Field(None, description="风格标签")
    duration_min: Optional[float] = Field(None, description="最小时长")
    duration_max: Optional[float] = Field(None, description="最大时长")
    quality_min: Optional[float] = Field(None, description="最低质量评分")
    sort_by: Optional[str] = Field("created_at", description="排序字段")
    sort_order: Optional[str] = Field("desc", description="排序方向: asc, desc")


class PlaylistCreateRequest(BaseModel):
    """播放列表创建请求模式"""
    name: str = Field(..., description="播放列表名称")
    description: Optional[str] = Field(None, description="播放列表描述")
    music_ids: List[int] = Field(..., description="音乐ID列表")
    is_public: bool = Field(False, description="是否公开")


class MusicUploadResponse(BaseModel):
    """音乐上传响应模式"""
    success: bool = Field(..., description="上传是否成功")
    music: Optional[BackgroundMusicResponse] = Field(None, description="上传的音乐信息")
    error: Optional[str] = Field(None, description="错误信息")
    file_info: Dict[str, Any] = Field(..., description="文件信息")