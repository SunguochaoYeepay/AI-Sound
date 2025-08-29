"""
故事板分析数据模式
基于6类卡片方案的API数据模式定义
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class StoryboardSessionCreate(BaseModel):
    """创建故事板分析会话请求"""
    book_id: int = Field(..., description="书籍ID")
    session_name: str = Field(..., description="会话名称", max_length=200)
    description: Optional[str] = Field(None, description="会话描述")
    analysis_type: str = Field("standard", description="分析类型", pattern="^(standard|enhanced|custom)$")
    llm_config: Optional[Dict[str, Any]] = Field(None, description="LLM配置")
    analysis_params: Optional[Dict[str, Any]] = Field(None, description="分析参数")


class StoryboardSessionResponse(BaseModel):
    """故事板分析会话响应"""
    id: int
    book_id: int
    session_name: str
    description: Optional[str]
    analysis_type: str
    llm_config: Optional[Dict[str, Any]]
    analysis_params: Optional[Dict[str, Any]]
    status: str
    progress: int
    current_step: Optional[str]
    total_chapters: int
    analyzed_chapters: int
    failed_chapters: int
    book_confirmed: bool
    storyboard_confirmed: bool
    error_message: Optional[str]
    created_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    updated_at: Optional[str]


class StoryboardSessionList(BaseModel):
    """故事板分析会话列表响应"""
    sessions: List[StoryboardSessionResponse]
    total: int
    skip: int
    limit: int


class StoryboardCardResponse(BaseModel):
    """故事板卡片响应"""
    id: int
    session_id: int
    card_type: str
    chapter_id: Optional[int]
    scene_id: Optional[int]
    content: Dict[str, Any]
    relationships: Optional[Dict[str, Any]]
    confirmation_status: str
    confirmed_at: Optional[str]
    confirmed_by: Optional[str]
    reanalysis_count: int
    last_reanalysis_at: Optional[str]
    reanalysis_reason: Optional[str]
    confidence_score: float
    quality_metrics: Optional[Dict[str, Any]]
    created_at: Optional[str]
    updated_at: Optional[str]


class StoryboardCardUpdate(BaseModel):
    """更新故事板卡片请求"""
    content: Dict[str, Any] = Field(..., description="卡片内容")


class StoryboardConfirmation(BaseModel):
    """确认请求"""
    confirmed_by: Optional[str] = Field(None, description="确认人")
    confirmation_type: Optional[str] = Field("storyboard", description="确认类型", pattern="^(book|storyboard)$")


class ChapterStatus(BaseModel):
    """章节状态"""
    chapter_id: int
    chapter_title: str
    chapter_number: int
    word_count: int
    analysis_status: str
    analysis_progress: int
    card_count: int
    story_card: bool
    character_cards: List[Dict[str, Any]]
    scene_cards: List[Dict[str, Any]]
    event_cards: List[Dict[str, Any]]
    emotion_cards: List[Dict[str, Any]]
    storyboard_card: bool


class SessionChaptersResponse(BaseModel):
    """会话章节列表响应"""
    session_id: int
    chapters: List[ChapterStatus]


class StoryboardReviewData(BaseModel):
    """分镜确认页面数据"""
    session: StoryboardSessionResponse
    chapter: Dict[str, Any]
    cards: Dict[str, List[Dict[str, Any]]]
    book_cards: Dict[str, List[Dict[str, Any]]]


# 具体的卡片类型模式
class StoryCardContent(BaseModel):
    """故事卡内容"""
    story_summary: str
    main_plot: List[Dict[str, Any]]
    themes: List[str]
    genre: str
    target_audience: str


class CharacterCardContent(BaseModel):
    """角色卡内容"""
    character_name: str
    character_type: str
    personality: List[str]
    background: str
    voice_characteristics: Dict[str, Any]
    emotional_range: List[str]


class SceneCardContent(BaseModel):
    """场景卡内容"""
    scene_name: str
    scene_type: str
    location: Dict[str, Any]
    atmosphere: Dict[str, Any]
    time_period: str
    environmental_sounds: List[str]


class EventCardContent(BaseModel):
    """事件卡内容"""
    event_name: str
    event_type: str
    participants: List[str]
    action_description: str
    dialogue_content: List[Dict[str, str]]
    emotional_context: Dict[str, Any]


class EmotionCardContent(BaseModel):
    """情绪卡内容"""
    emotion_type: str
    intensity: float
    duration: Dict[str, Any]
    triggers: List[str]
    expression: List[str]
    voice_impact: Dict[str, Any]


class AudioStoryboardContent(BaseModel):
    """音频分镜卡内容"""
    timeline: List[Dict[str, Any]]
    audio_tracks: Dict[str, Dict[str, Any]]
    voice_assignments: Dict[str, str]
    sound_effects: List[Dict[str, Any]]
    background_music: Dict[str, Any]


# 分析配置模式
class LLMConfig(BaseModel):
    """LLM配置"""
    provider: str = Field("openai", description="LLM提供商")
    model: str = Field("gpt-4", description="模型名称")
    temperature: float = Field(0.7, description="温度参数", ge=0.0, le=2.0)
    max_tokens: int = Field(4000, description="最大token数", ge=1, le=8000)
    system_prompt: Optional[str] = Field(None, description="系统提示词")


class AnalysisParams(BaseModel):
    """分析参数"""
    enable_scene_analysis: bool = Field(True, description="启用场景分析")
    enable_emotion_analysis: bool = Field(True, description="启用情绪分析")
    enable_character_analysis: bool = Field(True, description="启用角色分析")
    enable_storyboard_generation: bool = Field(True, description="启用分镜生成")
    confidence_threshold: float = Field(0.7, description="置信度阈值", ge=0.0, le=1.0)
    max_scenes_per_chapter: int = Field(5, description="每章最大场景数", ge=1, le=20)
    max_events_per_scene: int = Field(10, description="每场景最大事件数", ge=1, le=50)


# 进度更新模式
class ProgressUpdate(BaseModel):
    """进度更新"""
    type: str = "progress_update"
    session_id: int
    progress: int
    current_step: str
    analyzed_chapters: int
    total_chapters: int


class CompletionNotification(BaseModel):
    """完成通知"""
    type: str = "analysis_completed"
    session_id: int
    status: str


# 错误响应模式
class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
