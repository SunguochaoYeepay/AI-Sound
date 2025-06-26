from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class TemplateCategory(str, Enum):
    """模板分类"""
    AUDIOBOOK = "audiobook"
    PODCAST = "podcast"
    MUSIC = "music"
    DIALOGUE = "dialogue"
    NARRATION = "narration"
    COMMERCIAL = "commercial"


class ExportFormat(str, Enum):
    """导出格式"""
    MP3 = "mp3"
    WAV = "wav"
    FLAC = "flac"
    AAC = "aac"
    OGG = "ogg"


class ExportStatus(str, Enum):
    """导出状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ShareType(str, Enum):
    """分享类型"""
    VIEW = "view"
    EDIT = "edit"
    DOWNLOAD = "download"


class SyncStatus(str, Enum):
    """同步状态"""
    LOCAL = "local"
    SYNCING = "syncing"
    SYNCED = "synced"
    CONFLICT = "conflict"
    ERROR = "error"


# 项目模板相关模式
class ProjectTemplateBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    category: TemplateCategory
    preview_image: Optional[str] = None
    config_data: Dict[str, Any]
    is_public: bool = True


class ProjectTemplateCreate(ProjectTemplateBase):
    pass


class ProjectTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[TemplateCategory] = None
    preview_image: Optional[str] = None
    config_data: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None


class ProjectTemplate(ProjectTemplateBase):
    id: int
    usage_count: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 编辑历史相关模式
class EditHistoryBase(BaseModel):
    operation_type: str = Field(..., max_length=50)
    operation_data: Dict[str, Any]
    snapshot_data: Optional[Dict[str, Any]] = None


class EditHistoryCreate(EditHistoryBase):
    project_id: int


class EditHistory(EditHistoryBase):
    id: int
    project_id: int
    version_number: int
    user_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# 导出任务相关模式
class ExportSettings(BaseModel):
    """导出设置"""
    bitrate: Optional[int] = 128  # kbps
    sample_rate: Optional[int] = 44100  # Hz
    channels: Optional[int] = 2  # 1=mono, 2=stereo
    quality: Optional[str] = "high"  # low, medium, high
    normalize: Optional[bool] = True
    fade_in: Optional[float] = 0.0  # seconds
    fade_out: Optional[float] = 0.0  # seconds


class ExportTaskCreate(BaseModel):
    project_id: int
    export_format: ExportFormat
    export_settings: ExportSettings


class ExportTaskUpdate(BaseModel):
    status: Optional[ExportStatus] = None
    progress: Optional[int] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    error_message: Optional[str] = None


class ExportTask(BaseModel):
    id: int
    project_id: int
    export_format: ExportFormat
    export_settings: ExportSettings
    status: ExportStatus
    progress: int
    file_path: Optional[str]
    file_size: Optional[int]
    error_message: Optional[str]
    user_id: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# 项目分享相关模式
class ProjectShareCreate(BaseModel):
    project_id: int
    share_type: ShareType = ShareType.VIEW
    password: Optional[str] = None
    expires_at: Optional[datetime] = None


class ProjectShareUpdate(BaseModel):
    share_type: Optional[ShareType] = None
    password: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class ProjectShare(BaseModel):
    id: int
    project_id: int
    share_token: str
    share_type: ShareType
    password: Optional[str]
    expires_at: Optional[datetime]
    access_count: int
    is_active: bool
    created_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# 云端同步相关模式
class SyncStatusUpdate(BaseModel):
    local_version: Optional[int] = None
    cloud_version: Optional[int] = None
    sync_status: Optional[SyncStatus] = None
    sync_error: Optional[str] = None
    cloud_storage_path: Optional[str] = None


class SyncStatusResponse(BaseModel):
    id: int
    project_id: int
    local_version: int
    cloud_version: int
    sync_status: SyncStatus
    last_sync_at: Optional[datetime]
    sync_error: Optional[str]
    cloud_storage_path: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 批量操作模式
class BatchExportRequest(BaseModel):
    project_ids: List[int]
    export_format: ExportFormat
    export_settings: ExportSettings


class BatchExportResponse(BaseModel):
    task_ids: List[int]
    total_projects: int
    estimated_time: int  # seconds 