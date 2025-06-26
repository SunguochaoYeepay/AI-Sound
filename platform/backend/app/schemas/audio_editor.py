"""
音频编辑器相关的数据模型
定义音频编辑功能的请求和响应模型
"""

from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator

class AudioFormat(str, Enum):
    """音频格式枚举"""
    MP3 = "mp3"
    WAV = "wav"
    FLAC = "flac"
    AAC = "aac"
    OGG = "ogg"
    M4A = "m4a"

class AudioQuality(str, Enum):
    """音频质量枚举"""
    LOW = "low"           # 128kbps
    MEDIUM = "medium"     # 192kbps
    HIGH = "high"         # 256kbps
    LOSSLESS = "lossless" # 无损

class TrackType(str, Enum):
    """音轨类型枚举"""
    DIALOGUE = "dialogue"      # 对话轨
    ENVIRONMENT = "environment"  # 环境音轨
    MUSIC = "music"           # 音乐轨
    EFFECT = "effect"         # 音效轨
    NARRATION = "narration"   # 旁白轨

# 基础配置模型
class AudioMixConfig(BaseModel):
    """音频混合配置"""
    dialogue_volume: float = Field(1.0, ge=0.0, le=2.0, description="对话音量 (0.0-2.0)")
    environment_volume: float = Field(0.3, ge=0.0, le=2.0, description="环境音量 (0.0-2.0)")
    fadein_duration: float = Field(0.5, ge=0.0, le=10.0, description="淡入时长 (秒)")
    fadeout_duration: float = Field(0.5, ge=0.0, le=10.0, description="淡出时长 (秒)")
    normalize_audio: bool = Field(True, description="是否标准化音频")
    output_format: AudioFormat = Field(AudioFormat.MP3, description="输出格式")
    output_quality: AudioQuality = Field(AudioQuality.MEDIUM, description="输出质量")

class AudioEffectConfig(BaseModel):
    """音频效果配置"""
    volume: float = Field(1.0, ge=0.0, le=2.0, description="音量调节")
    fadein: Optional[float] = Field(None, ge=0.0, le=10.0, description="淡入时长")
    fadeout: Optional[float] = Field(None, ge=0.0, le=10.0, description="淡出时长")
    normalize: bool = Field(False, description="是否标准化")
    noise_reduction: bool = Field(False, description="是否降噪")
    echo_delay: Optional[float] = Field(None, ge=0.0, le=2.0, description="回声延迟")
    echo_decay: Optional[float] = Field(None, ge=0.0, le=1.0, description="回声衰减")
    
    @validator('fadein', 'fadeout')
    def validate_fade_duration(cls, v):
        if v is not None and v < 0:
            raise ValueError('淡入淡出时长不能为负数')
        return v

class ChapterAudioConfig(BaseModel):
    """章节音频配置"""
    silence_duration: float = Field(1.0, ge=0.0, le=10.0, description="片段间静音时长")
    normalize_volume: bool = Field(True, description="是否标准化音量")
    apply_fade: bool = Field(True, description="是否应用淡入淡出")
    fade_duration: float = Field(0.3, ge=0.0, le=5.0, description="淡入淡出时长")
    crossfade_duration: float = Field(0.0, ge=0.0, le=5.0, description="交叉淡化时长")
    output_format: AudioFormat = Field(AudioFormat.MP3, description="输出格式")
    output_quality: AudioQuality = Field(AudioQuality.MEDIUM, description="输出质量")

# 请求模型
class AudioMixRequest(BaseModel):
    """音频混合请求"""
    dialogue_path: str = Field(..., description="对话音频文件路径")
    environment_path: str = Field(..., description="环境音频文件路径")
    output_filename: str = Field(..., description="输出文件名")
    config: AudioMixConfig = Field(default_factory=AudioMixConfig, description="混合配置")
    
    @validator('output_filename')
    def validate_filename(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('输出文件名不能为空')
        # 简单的文件名验证
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in v for char in invalid_chars):
            raise ValueError('文件名包含非法字符')
        return v.strip()

class ChapterAudioRequest(BaseModel):
    """章节音频请求"""
    audio_files: List[str] = Field(..., min_items=1, description="音频文件路径列表")
    output_filename: str = Field(..., description="输出文件名")
    config: ChapterAudioConfig = Field(default_factory=ChapterAudioConfig, description="章节配置")
    
    @validator('audio_files')
    def validate_audio_files(cls, v):
        if not v:
            raise ValueError('音频文件列表不能为空')
        return v
    
    @validator('output_filename')
    def validate_filename(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('输出文件名不能为空')
        return v.strip()

class AudioEffectRequest(BaseModel):
    """音频效果请求"""
    input_path: str = Field(..., description="输入音频文件路径")
    output_filename: str = Field(..., description="输出文件名")
    effects: AudioEffectConfig = Field(..., description="音频效果配置")

class BatchProcessRequest(BaseModel):
    """批量处理请求"""
    operation_type: str = Field(..., description="操作类型: mix|chapter|effects")
    requests: List[Union[AudioMixRequest, ChapterAudioRequest, AudioEffectRequest]] = Field(
        ..., min_items=1, description="批量请求列表"
    )
    parallel_limit: int = Field(3, ge=1, le=10, description="并行处理限制")

# 响应模型
class AudioMixResult(BaseModel):
    """音频混合结果"""
    success: bool = Field(..., description="是否成功")
    output_path: str = Field(..., description="输出文件路径")
    duration: float = Field(..., description="音频时长（秒）")
    file_size: int = Field(..., description="文件大小（字节）")
    format: str = Field(..., description="音频格式")
    bitrate: str = Field(..., description="比特率")
    download_url: str = Field(..., description="下载链接")
    processing_time: Optional[float] = Field(None, description="处理时间（秒）")

class ChapterAudioResult(BaseModel):
    """章节音频结果"""
    success: bool = Field(..., description="是否成功")
    output_path: str = Field(..., description="输出文件路径")
    duration: float = Field(..., description="总时长（秒）")
    segments_count: int = Field(..., description="音频片段数量")
    file_size: int = Field(..., description="文件大小（字节）")
    format: str = Field(..., description="音频格式")
    bitrate: str = Field(..., description="比特率")
    download_url: str = Field(..., description="下载链接")
    processing_time: Optional[float] = Field(None, description="处理时间（秒）")

class AudioEffectResult(BaseModel):
    """音频效果结果"""
    success: bool = Field(..., description="是否成功")
    output_path: str = Field(..., description="输出文件路径")
    duration: float = Field(..., description="音频时长（秒）")
    file_size: int = Field(..., description="文件大小（字节）")
    effects_applied: Dict[str, Any] = Field(..., description="已应用的效果")
    download_url: str = Field(..., description="下载链接")
    processing_time: Optional[float] = Field(None, description="处理时间（秒）")

class AudioInfoResult(BaseModel):
    """音频信息结果"""
    file_path: str = Field(..., description="文件路径")
    duration: float = Field(..., description="时长（秒）")
    fps: int = Field(..., description="采样率")
    channels: int = Field(..., description="声道数")
    file_size: int = Field(..., description="文件大小")
    format: str = Field(..., description="文件格式")
    bitrate: Optional[str] = Field(None, description="比特率")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

class UploadResult(BaseModel):
    """文件上传结果"""
    success: bool = Field(..., description="是否成功")
    filename: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")
    file_size: int = Field(..., description="文件大小")
    upload_time: str = Field(..., description="上传时间")
    audio_info: Optional[AudioInfoResult] = Field(None, description="音频信息")

class BatchProcessResult(BaseModel):
    """批量处理结果"""
    total_count: int = Field(..., description="总任务数")
    success_count: int = Field(..., description="成功任务数")
    failed_count: int = Field(..., description="失败任务数")
    results: List[Union[AudioMixResult, ChapterAudioResult, AudioEffectResult]] = Field(
        ..., description="处理结果列表"
    )
    total_processing_time: float = Field(..., description="总处理时间")

# 进度相关模型
class ProcessingStatus(str, Enum):
    """处理状态枚举"""
    PENDING = "pending"       # 等待中
    PROCESSING = "processing" # 处理中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败
    CANCELLED = "cancelled"   # 已取消

class TaskProgress(BaseModel):
    """任务进度"""
    task_id: str = Field(..., description="任务ID")
    status: ProcessingStatus = Field(..., description="处理状态")
    progress: float = Field(0.0, ge=0.0, le=100.0, description="进度百分比")
    message: str = Field("", description="状态消息")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    result: Optional[Union[AudioMixResult, ChapterAudioResult, AudioEffectResult]] = Field(
        None, description="处理结果"
    )
    error: Optional[str] = Field(None, description="错误信息")

# 编辑器项目相关模型
class AudioTrackConfig(BaseModel):
    """音轨配置"""
    track_name: str = Field(..., description="轨道名称")
    track_type: TrackType = Field(..., description="轨道类型")
    volume: float = Field(1.0, ge=0.0, le=2.0, description="音量")
    is_muted: bool = Field(False, description="是否静音")
    is_solo: bool = Field(False, description="是否独奏")
    effects: List[AudioEffectConfig] = Field(default_factory=list, description="效果链")

class AudioClipInfo(BaseModel):
    """音频片段信息"""
    clip_id: str = Field(..., description="片段ID")
    file_path: str = Field(..., description="文件路径")
    start_time: float = Field(0.0, ge=0.0, description="开始时间")
    duration: float = Field(..., gt=0.0, description="持续时间")
    volume: float = Field(1.0, ge=0.0, le=2.0, description="音量")
    effects: List[AudioEffectConfig] = Field(default_factory=list, description="片段效果")

class AudioProjectConfig(BaseModel):
    """音频项目配置"""
    project_name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    sample_rate: int = Field(44100, description="采样率")
    channels: int = Field(2, description="声道数")
    tracks: List[AudioTrackConfig] = Field(default_factory=list, description="音轨配置")
    
class EditorProjectRequest(BaseModel):
    """编辑器项目请求"""
    config: AudioProjectConfig = Field(..., description="项目配置")
    source_project_id: Optional[int] = Field(None, description="源项目ID")

class EditorProjectResult(BaseModel):
    """编辑器项目结果"""
    project_id: int = Field(..., description="项目ID")
    config: AudioProjectConfig = Field(..., description="项目配置")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

# 导出相关模型
class ExportConfig(BaseModel):
    """导出配置"""
    format: AudioFormat = Field(AudioFormat.MP3, description="导出格式")
    quality: AudioQuality = Field(AudioQuality.HIGH, description="导出质量")
    normalize: bool = Field(True, description="是否标准化")
    include_metadata: bool = Field(True, description="是否包含元数据")
    metadata: Optional[Dict[str, str]] = Field(None, description="自定义元数据")

class ExportRequest(BaseModel):
    """导出请求"""
    project_id: int = Field(..., description="项目ID")
    output_filename: str = Field(..., description="输出文件名")
    config: ExportConfig = Field(default_factory=ExportConfig, description="导出配置")

class ExportResult(BaseModel):
    """导出结果"""
    success: bool = Field(..., description="是否成功")
    output_path: str = Field(..., description="输出文件路径")
    file_size: int = Field(..., description="文件大小")
    format: str = Field(..., description="文件格式")
    download_url: str = Field(..., description="下载链接")
    export_time: datetime = Field(..., description="导出时间")
    processing_time: float = Field(..., description="处理时间")

# 系统状态模型
class SystemHealth(BaseModel):
    """系统健康状态"""
    status: str = Field(..., description="系统状态")
    moviepy_version: str = Field(..., description="MoviePy版本")
    ffmpeg_available: bool = Field(..., description="FFmpeg是否可用")
    temp_dir_writable: bool = Field(..., description="临时目录是否可写")
    storage_space_mb: float = Field(..., description="可用存储空间(MB)")
    active_tasks: int = Field(..., description="活跃任务数")
    timestamp: datetime = Field(..., description="检查时间")

# 错误模型
class AudioEditorError(BaseModel):
    """音频编辑器错误"""
    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    timestamp: datetime = Field(..., description="错误时间")

# 音视频编辑器项目相关模型
class AudioVideoProjectCreate(BaseModel):
    """创建音视频项目请求"""
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    project_type: str = Field(default="audio_editing", description="项目类型")

class AudioVideoProjectUpdate(BaseModel):
    """更新音视频项目请求"""
    name: Optional[str] = Field(None, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    project_type: Optional[str] = Field(None, description="项目类型")
    status: Optional[str] = Field(None, description="项目状态")

class EditorTrackCreate(BaseModel):
    """创建编辑器轨道请求"""
    track_name: str = Field(..., description="轨道名称")
    track_type: TrackType = Field(..., description="轨道类型")
    track_order: int = Field(0, ge=0, description="轨道顺序")
    track_color: Optional[str] = Field("#4CAF50", description="轨道颜色")
    volume: float = Field(1.0, ge=0.0, le=2.0, description="音量")
    is_muted: bool = Field(False, description="是否静音")
    is_solo: bool = Field(False, description="是否独奏")

class AudioClipCreate(BaseModel):
    """创建音频片段请求"""
    clip_name: str = Field(..., description="片段名称")
    file_path: str = Field(..., description="文件路径")
    start_time: float = Field(0.0, ge=0.0, description="开始时间")
    end_time: float = Field(..., gt=0.0, description="结束时间")
    volume: float = Field(1.0, ge=0.0, le=2.0, description="音量")
    is_muted: bool = Field(False, description="是否静音")
    clip_data: Optional[Dict[str, Any]] = Field(None, description="片段数据")
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        start_time = values.get('start_time', 0.0)
        if v <= start_time:
            raise ValueError('结束时间必须大于开始时间')
        return v

class ProjectImportRequest(BaseModel):
    """项目导入请求"""
    source_project_id: int = Field(..., description="源项目ID")
    project_name: Optional[str] = Field(None, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")

# 导出所有模型
__all__ = [
    # 枚举
    "AudioFormat", "AudioQuality", "TrackType", "ProcessingStatus",
    
    # 配置模型
    "AudioMixConfig", "AudioEffectConfig", "ChapterAudioConfig",
    "AudioTrackConfig", "AudioProjectConfig", "ExportConfig",
    
    # 请求模型
    "AudioMixRequest", "ChapterAudioRequest", "AudioEffectRequest",
    "BatchProcessRequest", "EditorProjectRequest", "ExportRequest",
    "AudioVideoProjectCreate", "AudioVideoProjectUpdate", "EditorTrackCreate", 
    "AudioClipCreate", "ProjectImportRequest",
    
    # 响应模型
    "AudioMixResult", "ChapterAudioResult", "AudioEffectResult",
    "AudioInfoResult", "UploadResult", "BatchProcessResult",
    "EditorProjectResult", "ExportResult",
    
    # 其他模型
    "TaskProgress", "AudioClipInfo", "SystemHealth", "AudioEditorError"
] 