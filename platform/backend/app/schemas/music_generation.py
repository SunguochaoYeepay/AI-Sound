"""
音乐生成API的数据模型
定义请求和响应的Pydantic模式
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

# 基础模型
class ChapterMusicRequest(BaseModel):
    """章节音乐请求基础模型"""
    chapter_id: Union[str, int] = Field(..., description="章节ID")
    content: str = Field(..., description="章节内容")

class MusicGenerationRequest(BaseModel):
    """音乐生成请求"""
    chapter_id: Union[str, int] = Field(..., description="章节ID")
    content: str = Field(..., description="章节内容", max_length=50000)
    target_duration: Optional[int] = Field(30, description="目标时长（秒）", ge=10, le=300)
    custom_style: Optional[str] = Field(None, description="自定义音乐风格")
    volume_level: Optional[float] = Field(-12.0, description="音量等级（dB）", ge=-30.0, le=0.0)
    fade_mode: Optional[str] = Field("standard", description="淡入淡出模式", pattern="^(standard|smooth|quick)$")

class BatchChapterRequest(BaseModel):
    """批量章节请求"""
    chapter_id: Union[str, int] = Field(..., description="章节ID")
    content: str = Field(..., description="章节内容", max_length=50000)
    title: Optional[str] = Field(None, description="章节标题")

class BatchMusicGenerationRequest(BaseModel):
    """批量音乐生成请求"""
    chapters: List[BatchChapterRequest] = Field(..., description="章节列表", min_items=1, max_items=20)
    default_duration: Optional[int] = Field(30, description="默认时长（秒）", ge=10, le=300)
    default_volume_level: Optional[float] = Field(-12.0, description="默认音量等级（dB）", ge=-30.0, le=0.0)
    fade_mode: Optional[str] = Field("standard", description="淡入淡出模式", pattern="^(standard|smooth|quick)$")
    max_concurrent: Optional[int] = Field(2, description="最大并发数", ge=1, le=5)

class MusicStylePreviewRequest(BaseModel):
    """音乐风格预览请求"""
    content_sample: str = Field(..., description="内容样本", max_length=5000)

# 响应模型
class MusicInfo(BaseModel):
    """音乐信息"""
    audio_path: str = Field(..., description="音频文件路径")
    audio_url: Optional[str] = Field(None, description="音频访问URL")
    duration: int = Field(..., description="音频时长（秒）")
    volume_level: float = Field(..., description="音量等级（dB）")
    generation_time: Optional[float] = Field(None, description="生成耗时（秒）")

class PrimaryScene(BaseModel):
    """主要场景信息"""
    type: str = Field(..., description="场景类型")
    emotion: str = Field(..., description="情绪")
    intensity: float = Field(..., description="强度", ge=0.0, le=1.0)
    keywords: List[str] = Field(..., description="关键词")
    confidence: float = Field(..., description="置信度", ge=0.0, le=1.0)

class SceneAnalysis(BaseModel):
    """场景分析结果"""
    primary_scene: PrimaryScene = Field(..., description="主要场景")
    overall_mood: str = Field(..., description="整体氛围")
    tempo_preference: int = Field(..., description="节奏偏好（BPM）")
    volume_suggestion: float = Field(..., description="音量建议（dB）")
    transition_points: List[Dict[str, Any]] = Field(..., description="转换点")

class MusicConfig(BaseModel):
    """音乐配置"""
    style: str = Field(..., description="风格")
    duration: int = Field(..., description="时长（秒）")
    volume_level: float = Field(..., description="音量等级（dB）")
    fade_in: float = Field(..., description="淡入时间（秒）")
    fade_out: float = Field(..., description="淡出时间（秒）")
    intensity: float = Field(..., description="强度")
    tempo_preference: int = Field(..., description="节奏偏好（BPM）")

class StyleRecommendation(BaseModel):
    """风格推荐"""
    style: str = Field(..., description="风格名称")
    priority: int = Field(..., description="优先级")
    confidence: float = Field(..., description="置信度", ge=0.0, le=1.0)
    description: str = Field(..., description="描述")
    keywords: List[str] = Field(..., description="关键词")
    duration: int = Field(..., description="建议时长（秒）")

class MusicGenerationResponse(BaseModel):
    """音乐生成响应"""
    chapter_id: Union[str, int] = Field(..., description="章节ID")
    generation_status: str = Field(..., description="生成状态", pattern="^(completed|failed|processing)$")
    music_info: MusicInfo = Field(..., description="音乐信息")
    scene_analysis: SceneAnalysis = Field(..., description="场景分析")
    music_config: MusicConfig = Field(..., description="音乐配置")
    style_recommendations: List[StyleRecommendation] = Field(..., description="风格推荐")
    created_at: str = Field(..., description="创建时间")

class BatchMusicGenerationResponse(BaseModel):
    """批量音乐生成响应"""
    batch_status: str = Field(..., description="批量状态")
    total_chapters: int = Field(..., description="总章节数")
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    results: Dict[str, Any] = Field(..., description="详细结果")
    completed_at: str = Field(..., description="完成时间")

class MusicStylePreviewResponse(BaseModel):
    """音乐风格预览响应"""
    primary_style: str = Field(..., description="主要风格")
    confidence: float = Field(..., description="置信度", ge=0.0, le=1.0)
    intensity: float = Field(..., description="强度", ge=0.0, le=1.0)
    mood: str = Field(..., description="氛围")
    tempo_range: int = Field(..., description="节奏范围（BPM）")
    volume_suggestion: float = Field(..., description="音量建议（dB）")
    keywords: List[str] = Field(..., description="关键词")
    style_recommendations: List[StyleRecommendation] = Field(..., description="风格推荐")
    available_styles: List[str] = Field(..., description="可用风格")

class SupportedStyle(BaseModel):
    """支持的风格"""
    name: str = Field(..., description="风格名称")
    display_name: str = Field(..., description="显示名称")
    description: str = Field(..., description="描述")
    keywords: List[str] = Field(..., description="关键词")
    intensity_range: tuple = Field(..., description="强度范围")
    bpm_range: tuple = Field(..., description="BPM范围")
    volume_range: tuple = Field(..., description="音量范围")

class SupportedStylesResponse(BaseModel):
    """支持的风格列表响应"""
    styles: List[SupportedStyle] = Field(..., description="风格列表")
    total_count: int = Field(..., description="总数量")

class MusicGenerationStatusResponse(BaseModel):
    """音乐生成状态响应"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="状态", pattern="^(pending|processing|completed|failed)$")
    progress: float = Field(..., description="进度", ge=0.0, le=1.0)
    audio_url: Optional[str] = Field(None, description="音频URL")
    error_message: Optional[str] = Field(None, description="错误信息")
    generation_time: Optional[float] = Field(None, description="生成时间（秒）")

# 错误响应模型
class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误信息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    timestamp: str = Field(..., description="时间戳")

# 健康检查响应
class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="状态", pattern="^(healthy|degraded|unhealthy)$")
    services: Dict[str, str] = Field(..., description="服务状态")
    timestamp: str = Field(..., description="时间戳")

# 配置模型
class VolumeConfig(BaseModel):
    """音量配置"""
    battle: float = Field(-9.0, description="战斗场景音量")
    romance: float = Field(-15.0, description="浪漫场景音量")
    mystery: float = Field(-12.0, description="悬疑场景音量")
    peaceful: float = Field(-18.0, description="平静场景音量")
    sad: float = Field(-14.0, description="悲伤场景音量")

class DurationConfig(BaseModel):
    """时长配置"""
    battle: float = Field(1.2, description="战斗场景时长因子")
    romance: float = Field(0.9, description="浪漫场景时长因子")
    mystery: float = Field(1.1, description="悬疑场景时长因子")
    peaceful: float = Field(0.8, description="平静场景时长因子")
    sad: float = Field(1.0, description="悲伤场景时长因子")

class FadeConfig(BaseModel):
    """淡入淡出配置"""
    fade_in: float = Field(..., description="淡入时间")
    fade_out: float = Field(..., description="淡出时间")

class DefaultConfig(BaseModel):
    """默认配置"""
    volume_levels: VolumeConfig = Field(..., description="音量等级配置")
    duration_adjustments: DurationConfig = Field(..., description="时长调整配置")
    fade_settings: Dict[str, FadeConfig] = Field(..., description="淡入淡出设置")

# 统计模型
class GenerationStats(BaseModel):
    """生成统计"""
    time_range_hours: int = Field(..., description="统计时间范围（小时）")
    total_generations: int = Field(..., description="总生成数")
    successful_generations: int = Field(..., description="成功生成数")
    failed_generations: int = Field(..., description="失败生成数")
    average_generation_time: float = Field(..., description="平均生成时间（秒）")
    most_popular_styles: List[str] = Field(..., description="最受欢迎的风格")
    timestamp: str = Field(..., description="统计时间")

# 调试模型
class DebugSceneInfo(BaseModel):
    """调试场景信息"""
    scene_type: str = Field(..., description="场景类型")
    emotion_tone: str = Field(..., description="情绪")
    intensity: float = Field(..., description="强度")
    keywords: List[str] = Field(..., description="关键词")
    duration_hint: Optional[int] = Field(None, description="时长提示")
    confidence: float = Field(..., description="置信度")

class DebugInfo(BaseModel):
    """调试信息"""
    content_length: int = Field(..., description="内容长度")
    analysis_timestamp: str = Field(..., description="分析时间")

class DebugSceneAnalysisResponse(BaseModel):
    """调试场景分析响应"""
    primary_scene: DebugSceneInfo = Field(..., description="主要场景")
    secondary_scenes: List[DebugSceneInfo] = Field(..., description="次要场景")
    overall_mood: str = Field(..., description="整体氛围")
    tempo_preference: int = Field(..., description="节奏偏好")
    volume_suggestion: float = Field(..., description="音量建议")
    style_recommendations: List[StyleRecommendation] = Field(..., description="风格推荐")
    transition_points: List[Dict[str, Any]] = Field(..., description="转换点")
    debug_info: DebugInfo = Field(..., description="调试信息")

# 服务信息模型
class ServiceInfo(BaseModel):
    """服务信息"""
    service_name: str = Field(..., description="服务名称")
    version: str = Field(..., description="版本")
    supported_styles: int = Field(..., description="支持的风格数量")
    default_config: DefaultConfig = Field(..., description="默认配置")
    description: str = Field(..., description="服务描述") 