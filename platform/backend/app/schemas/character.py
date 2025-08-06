from typing import Optional, List
from pydantic import BaseModel

class CharacterBase(BaseModel):
    name: str
    description: Optional[str] = None
    voice_profile: Optional[str] = None
    voice_config: Optional[str] = None
    book_id: Optional[int] = None
    chapter_id: Optional[int] = None

class CharacterCreate(CharacterBase):
    pass

class CharacterUpdate(CharacterBase):
    name: Optional[str] = None
    description: Optional[str] = None
    voice_profile: Optional[str] = None
    voice_config: Optional[str] = None
    book_id: Optional[int] = None
    chapter_id: Optional[int] = None
    
    # 声音配置字段
    voice_type: Optional[str] = None
    color: Optional[str] = None
    
    # 外貌特征字段
    age_range: Optional[str] = None
    build_type: Optional[str] = None
    clothing_style: Optional[str] = None
    distinctive_features: Optional[str] = None
    appearance_description: Optional[str] = None
    avatar_prompt: Optional[str] = None
    consistency_tag: Optional[str] = None
    
    # 参数配置
    voice_parameters: Optional[dict] = None
    tags: Optional[list] = None
    
    # 状态信息
    status: Optional[str] = None
    quality_score: Optional[float] = None
    usage_count: Optional[int] = None

class CharacterInDB(CharacterBase):
    id: int
    
    class Config:
        from_attributes = True

class CharacterResponse(CharacterInDB):
    # 声音配置字段
    voice_type: Optional[str] = None
    color: Optional[str] = None
    
    # 外貌特征字段
    age_range: Optional[str] = None
    build_type: Optional[str] = None
    clothing_style: Optional[str] = None
    distinctive_features: Optional[str] = None
    appearance_description: Optional[str] = None
    avatar_prompt: Optional[str] = None
    consistency_tag: Optional[str] = None
    
    # 文件路径
    avatar_path: Optional[str] = None
    reference_audio_path: Optional[str] = None
    latent_file_path: Optional[str] = None
    
    # 参数配置
    voice_parameters: Optional[dict] = None
    tags: Optional[list] = None
    
    # 状态信息
    status: Optional[str] = None
    quality_score: Optional[float] = None
    usage_count: Optional[int] = None
    
    # 计算属性
    is_voice_configured: Optional[bool] = None
    has_avatar: Optional[bool] = None
    has_latent: Optional[bool] = None
    
    # 文件URL
    avatarUrl: Optional[str] = None
    referenceAudioUrl: Optional[str] = None
    latentFileUrl: Optional[str] = None

class CharacterListResponse(BaseModel):
    characters: List[CharacterResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_prev: bool

class CharacterBatchConfig(BaseModel):
    """批量操作配置"""
    operation_type: str  # create, update, delete
    characters: List[dict]
    options: Optional[dict] = None

class CharacterBatchResult(BaseModel):
    """批量操作结果"""
    success_count: int
    failed_count: int
    total_count: int
    errors: List[str] = []
    results: List[dict] = []

class CharacterBatchResponse(BaseModel):
    """批量操作响应"""
    success: bool
    message: str
    data: CharacterBatchResult

# AI相关模型
class VoiceTestRequest(BaseModel):
    """语音测试请求"""
    text: str
    voice_config: Optional[dict] = None

class VoiceTestResponse(BaseModel):
    """语音测试响应"""
    success: bool
    audio_url: Optional[str] = None
    message: str

class VoiceQualityRequest(BaseModel):
    """语音质量评估请求"""
    audio_url: str
    reference_text: str

class VoiceQualityResponse(BaseModel):
    """语音质量评估响应"""
    quality_score: float
    details: dict

class AvatarGenerateRequest(BaseModel):
    """头像生成请求"""
    character_name: Optional[str] = None
    description: Optional[str] = None
    style: Optional[str] = "default"

class AvatarGenerateResponse(BaseModel):
    """头像生成响应"""
    success: bool
    avatar_url: Optional[str] = None
    task_id: Optional[str] = None
    message: str

# 别名以保持兼容性
AvatarGenerationRequest = AvatarGenerateRequest
AvatarGenerationResponse = AvatarGenerateResponse

# 相似角色相关模型
class SimilarCharacterResponse(BaseModel):
    """相似角色响应"""
    characters: List[CharacterResponse]
    similarity_scores: List[float]

class PopularTagsResponse(BaseModel):
    """热门标签响应"""
    tags: List[str]
    counts: List[int]

class VoiceModelResponse(BaseModel):
    """语音模型响应"""
    models: List[dict]
    total: int

# 匹配相关模型
class CharacterMatchRequest(BaseModel):
    """角色匹配请求"""
    chapter_id: int
    text_content: Optional[str] = None
    auto_apply: bool = False

class CharacterMatchResponse(BaseModel):
    """角色匹配响应"""
    success: bool
    matched_characters: List[dict]
    total_matches: int
    message: str

class ApplyMatchesRequest(BaseModel):
    """应用匹配请求"""
    chapter_id: int
    matches: List[dict]

class CharacterSyncRequest(BaseModel):
    """角色同步请求"""
    source_book_id: int
    target_book_id: int
    sync_options: Optional[dict] = None

class CharacterMatchResult(BaseModel):
    matched: bool
    character: Optional[CharacterResponse] = None
    current_config: Optional[str] = None  # 当前配置
    matched_config: Optional[str] = None  # 匹配到的配置