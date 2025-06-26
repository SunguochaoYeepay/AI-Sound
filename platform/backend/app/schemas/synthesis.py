"""
音频合成相关Schema定义
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from .common import BaseResponseModel


class SynthesisTaskCreate(BaseModel):
    """创建合成任务请求"""
    project_id: int = Field(description="项目ID")
    analysis_result_id: Optional[int] = Field(default=None, description="分析结果ID")
    chapter_id: Optional[int] = Field(default=None, description="章节ID")
    synthesis_plan: Dict[str, Any] = Field(description="合成计划配置")
    batch_size: int = Field(default=10, ge=1, le=50, description="批处理大小")


class SynthesisTaskUpdate(BaseModel):
    """更新合成任务请求"""
    synthesis_plan: Optional[Dict[str, Any]] = Field(default=None, description="合成计划配置")
    batch_size: Optional[int] = Field(default=None, ge=1, le=50, description="批处理大小")


class SynthesisTaskResponse(BaseResponseModel):
    """合成任务响应"""
    project_id: int = Field(description="项目ID")
    analysis_result_id: Optional[int] = Field(description="分析结果ID")
    chapter_id: Optional[int] = Field(description="章节ID")
    synthesis_plan: Dict[str, Any] = Field(description="合成计划配置")
    batch_size: int = Field(description="批处理大小")
    status: str = Field(description="任务状态")
    progress: int = Field(description="进度百分比")
    total_segments: int = Field(description="总段落数")
    completed_segments: int = Field(description="已完成段落数")
    current_segment: Optional[int] = Field(description="当前处理段落ID")
    failed_segments: Optional[List[Dict[str, Any]]] = Field(description="失败段落列表")
    error_message: Optional[str] = Field(description="错误消息")
    retry_count: int = Field(description="重试次数")
    max_retries: int = Field(description="最大重试次数")
    output_files: Optional[List[Dict[str, Any]]] = Field(description="输出文件列表")
    final_audio_path: Optional[str] = Field(description="最终音频文件路径")
    processing_time: Optional[int] = Field(description="处理时间")
    started_at: Optional[str] = Field(description="开始时间")
    completed_at: Optional[str] = Field(description="完成时间")


class SynthesisParams(BaseModel):
    """合成参数"""
    voice_provider: str = Field(description="TTS提供商")
    voice_config: Dict[str, Any] = Field(description="声音配置")
    audio_format: str = Field(default="wav", description="音频格式")
    sample_rate: int = Field(default=22050, description="采样率")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="语速")
    pitch: float = Field(default=1.0, ge=0.5, le=2.0, description="音调")
    volume: float = Field(default=1.0, ge=0.1, le=2.0, description="音量")


class VoiceMapping(BaseModel):
    """声音映射"""
    character_name: str = Field(description="角色名称")
    voice_id: str = Field(description="声音ID")
    voice_params: Optional[Dict[str, Any]] = Field(default=None, description="声音参数")


class SynthesisPlan(BaseModel):
    """合成计划"""
    voice_mappings: List[VoiceMapping] = Field(description="声音映射列表")
    synthesis_params: SynthesisParams = Field(description="合成参数")
    segment_processing: Dict[str, Any] = Field(description="段落处理配置")
    audio_post_processing: Optional[Dict[str, Any]] = Field(default=None, description="音频后处理配置")


class SynthesisProgressUpdate(BaseModel):
    """合成进度更新"""
    task_id: int = Field(description="任务ID")
    status: str = Field(description="状态")
    progress: int = Field(ge=0, le=100, description="进度百分比")
    completed_segments: int = Field(description="已完成段落数")
    current_segment: Optional[int] = Field(description="当前处理段落ID")
    error_message: Optional[str] = Field(description="错误消息")


class AudioFileInfo(BaseModel):
    """音频文件信息"""
    file_path: str = Field(description="文件路径")
    file_name: str = Field(description="文件名")
    file_size: int = Field(description="文件大小")
    duration: float = Field(description="音频时长")
    format: str = Field(description="音频格式")
    sample_rate: int = Field(description="采样率")
    voice_id: str = Field(description="使用的声音ID")
    segment_id: int = Field(description="对应的段落ID") 