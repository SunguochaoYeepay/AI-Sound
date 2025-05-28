"""
API响应模型定义
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class TTSResponse(BaseModel):
    """TTS响应模型"""
    success: bool = Field(..., title="成功标志", description="是否成功")
    message: str = Field("", title="消息", description="处理结果消息")
    engine: Optional[str] = Field(None, title="引擎", description="使用的TTS引擎")
    audio_base64: Optional[str] = Field(None, title="音频Base64", 
                                    description="Base64编码的音频数据")
    audio_url: Optional[str] = Field(None, title="音频URL", 
                                description="音频文件URL")
    duration: float = Field(0.0, title="音频时长", description="音频时长(秒)")

class NovelProcessResponse(BaseModel):
    """小说处理响应模型"""
    success: bool = Field(..., title="成功标志", description="是否成功")
    message: str = Field("", title="消息", description="处理结果消息")
    task_id: str = Field(..., title="任务ID", description="后台处理任务ID")
    status_url: str = Field(..., title="状态URL", description="任务状态查询URL")

class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
    success: bool = Field(..., title="成功标志", description="是否成功")
    task_id: str = Field(..., title="任务ID", description="任务ID")
    status: str = Field(..., title="任务状态", 
                      description="任务状态: pending, processing, completed, failed")
    progress: float = Field(0.0, title="处理进度", description="处理进度: 0.0-1.0")
    message: str = Field("", title="消息", description="状态消息")
    result: Optional[Dict[str, Any]] = Field(None, title="处理结果", description="处理完成后的结果")
    error: Optional[str] = Field(None, title="错误信息", description="处理失败时的错误信息")
    created_at: Optional[float] = Field(None, title="创建时间", description="任务创建时间戳")
    updated_at: Optional[float] = Field(None, title="更新时间", description="任务最后更新时间戳")

class SystemInfoResponse(BaseModel):
    """系统信息响应模型"""
    success: bool = Field(..., title="成功标志", description="是否成功")
    system: Dict[str, Any] = Field(..., title="系统信息", description="系统信息")
    services: Dict[str, Any] = Field(..., title="服务信息", description="服务信息")
    dependencies: Dict[str, Any] = Field(..., title="依赖信息", description="依赖信息")
    config: Dict[str, Any] = Field(..., title="配置信息", description="配置信息")

class StatsResponse(BaseModel):
    """统计信息响应模型"""
    success: bool = Field(..., title="成功标志", description="是否成功")
    server: Dict[str, Any] = Field(..., title="服务器信息", description="服务器运行信息")
    api: Dict[str, Any] = Field(..., title="API信息", description="API使用统计")
    files: Dict[str, Any] = Field(..., title="文件信息", description="文件统计信息")

# 新增：声纹特征相关响应模型
class VoiceFeatureMetadata(BaseModel):
    """声纹特征元数据"""
    description: str = Field("", title="描述", description="声音描述")
    tags: List[str] = Field([], title="标签", description="声音标签")
    attributes: Dict[str, Any] = Field({}, title="属性", description="声音属性（如性别、年龄等）")
    feature_shape: List[int] = Field(None, title="特征形状", description="特征数组形状")
    created_at: str = Field(..., title="创建时间", description="创建时间")
    file_size: Optional[int] = Field(None, title="文件大小", description="特征文件大小(字节)")

class VoiceFeature(BaseModel):
    """声纹特征信息"""
    id: str = Field(..., title="ID", description="声音ID")
    name: str = Field(..., title="名称", description="声音名称")
    description: str = Field("", title="描述", description="声音描述")
    tags: List[str] = Field([], title="标签", description="声音标签")
    attributes: Dict[str, Any] = Field({}, title="属性", description="声音属性")
    preview_url: str = Field(..., title="预览URL", description="声音预览URL")
    feature_url: str = Field(..., title="特征URL", description="声音特征下载URL")
    created_at: str = Field(..., title="创建时间", description="创建时间")
    feature_shape: Optional[List[int]] = Field(None, title="特征形状", description="特征数组形状")
    file_size: Optional[int] = Field(None, title="文件大小", description="特征文件大小(字节)")

class VoiceFeatureExtractResponse(BaseModel):
    """声纹特征提取响应"""
    success: bool = Field(..., title="成功标志", description="是否成功")
    message: str = Field(..., title="消息", description="处理结果消息")
    voice_id: str = Field(..., title="声音ID", description="声音唯一标识")
    name: str = Field(..., title="名称", description="声音名称")
    preview_url: str = Field(..., title="预览URL", description="声音预览URL")
    feature_url: str = Field(..., title="特征URL", description="声音特征下载URL")
    metadata: VoiceFeatureMetadata = Field(..., title="元数据", description="声音元数据")

class VoiceFeatureListResponse(BaseModel):
    """声纹特征列表响应"""
    success: bool = Field(..., title="成功标志", description="是否成功")
    count: int = Field(..., title="总数", description="声音总数")
    voices: List[VoiceFeature] = Field(..., title="声音列表", description="声音列表")

class VoiceFeatureDetailResponse(BaseModel):
    """声纹特征详情响应"""
    success: bool = Field(..., title="成功标志", description="是否成功")
    voice: VoiceFeature = Field(..., title="声音信息", description="声音详细信息")

class VoiceTagsResponse(BaseModel):
    """声音标签统计响应"""
    success: bool = Field(..., title="成功标志", description="是否成功")
    tags: Dict[str, int] = Field(..., title="标签统计", description="标签使用频率统计")
    attributes: Dict[str, Dict[str, int]] = Field(..., title="属性统计", description="属性值使用频率统计")

class CharacterVoiceMapping(BaseModel):
    """角色声音映射"""
    name: str = Field(..., title="角色名称", description="角色名称")
    voice_id: str = Field(..., title="声音ID", description="映射的声音ID")
    voice_name: str = Field(..., title="声音名称", description="映射的声音名称")
    attributes: Dict[str, Any] = Field({}, title="属性", description="角色属性")
    mapped_at: str = Field(..., title="映射时间", description="映射创建时间")

class CharacterListResponse(BaseModel):
    """角色列表响应"""
    success: bool = Field(..., title="成功标志", description="是否成功")
    count: int = Field(..., title="总数", description="角色总数")
    characters: List[CharacterVoiceMapping] = Field(..., title="角色列表", description="角色映射列表")

class CharacterDetailResponse(BaseModel):
    """角色详情响应"""
    success: bool = Field(..., title="成功标志", description="是否成功")
    character: CharacterVoiceMapping = Field(..., title="角色信息", description="角色详细信息")
    voice: Optional[VoiceFeature] = Field(None, title="声音信息", description="映射的声音详细信息")

class CharacterAnalysisResponse(BaseModel):
    """小说角色分析响应"""
    success: bool = Field(..., title="成功标志", description="是否成功")
    characters: Dict[str, int] = Field(..., title="角色频率", description="角色出现频率")
    suggestions: Dict[str, List[str]] = Field(..., title="映射建议", description="角色-声音映射建议")