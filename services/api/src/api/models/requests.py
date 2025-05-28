"""
API请求模型定义
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class TTSRequest(BaseModel):
    """TTS请求模型"""
    text: str = Field(..., title="文本", description="需要转换为语音的文本")
    voice_id: str = Field("female_young", title="音色ID", description="语音音色")
    emotion_type: str = Field("neutral", title="情感类型",
                            description="情感类型: neutral, happy, sad, angry, surprised")
    emotion_intensity: float = Field(0.5, title="情感强度", 
                                  description="情感强度: 0.0-1.0", ge=0.0, le=1.0)
    speed_scale: Optional[float] = Field(None, title="语速缩放", 
                                      description="语速缩放因子: 0.5-2.0")
    pitch_scale: Optional[float] = Field(None, title="音高缩放", 
                                      description="音高缩放因子: 0.5-2.0")
    return_base64: bool = Field(False, title="返回Base64", 
                              description="是否以Base64编码返回音频")
    output_format: str = Field("wav", title="输出格式", 
                            description="输出音频格式: wav, mp3, ogg, flac")
    engine: Optional[str] = Field("auto", title="引擎选择",
                               description="引擎选择: auto, megatts3, espnet")
    formal: Optional[bool] = Field(False, title="正式场景",
                                description="是否为正式场景，影响引擎选择")

class NovelProcessRequest(BaseModel):
    """小说处理请求模型"""
    novel_path: str = Field(..., title="小说路径", description="小说文件路径")
    output_dir: Optional[str] = Field(None, title="输出目录", description="音频输出目录")
    voice_mapping: Optional[Dict[str, str]] = Field(None, title="角色音色映射",
                                                 description="角色与音色ID的映射")
    with_emotion: bool = Field(True, title="启用情感", description="是否启用情感分析")
    resume_if_exists: bool = Field(False, title="恢复处理", 
                                description="如果存在未完成的处理，是否恢复")
    auto_character_mapping: bool = Field(True, title="自动角色映射", 
                                     description="是否自动分析和映射小说角色")