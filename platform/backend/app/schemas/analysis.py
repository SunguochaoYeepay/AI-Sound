"""
智能分析相关Schema定义
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from .common import BaseResponseModel


class AnalysisSessionCreate(BaseModel):
    """创建分析会话请求"""
    project_id: int = Field(description="项目ID")
    session_name: str = Field(min_length=1, max_length=200, description="会话名称")
    description: Optional[str] = Field(default=None, description="会话描述")
    target_type: str = Field(description="分析目标类型: full_book, single_chapter, chapter_range")
    target_config: Dict[str, Any] = Field(description="目标配置")
    llm_config: Dict[str, Any] = Field(description="LLM配置")
    analysis_params: Dict[str, Any] = Field(description="分析参数")


class AnalysisSessionUpdate(BaseModel):
    """更新分析会话请求"""
    session_name: Optional[str] = Field(default=None, min_length=1, max_length=200, description="会话名称")
    description: Optional[str] = Field(default=None, description="会话描述")
    llm_config: Optional[Dict[str, Any]] = Field(default=None, description="LLM配置")
    analysis_params: Optional[Dict[str, Any]] = Field(default=None, description="分析参数")


class AnalysisSessionResponse(BaseResponseModel):
    """分析会话响应"""
    project_id: int = Field(description="项目ID")
    session_name: str = Field(description="会话名称")
    description: Optional[str] = Field(description="会话描述")
    target_type: str = Field(description="分析目标类型")
    target_config: Dict[str, Any] = Field(description="目标配置")
    llm_config: Dict[str, Any] = Field(description="LLM配置")
    analysis_params: Dict[str, Any] = Field(description="分析参数")
    status: str = Field(description="会话状态")
    progress: int = Field(description="进度百分比")
    current_step: Optional[str] = Field(description="当前步骤")
    total_chapters: int = Field(description="总章节数")
    completed_chapters: int = Field(description="已完成章节数")
    failed_chapters: int = Field(description="失败章节数")
    error_message: Optional[str] = Field(description="错误消息")
    started_at: Optional[str] = Field(description="开始时间")
    completed_at: Optional[str] = Field(description="完成时间")


class AnalysisResultResponse(BaseResponseModel):
    """分析结果响应"""
    session_id: int = Field(description="会话ID")
    chapter_id: int = Field(description="章节ID")
    detected_characters: Optional[List[Dict[str, Any]]] = Field(description="检测到的角色")
    dialogue_segments: Optional[List[Dict[str, Any]]] = Field(description="对话段落")
    emotion_analysis: Optional[Dict[str, Any]] = Field(description="情感分析")
    voice_recommendations: Optional[List[Dict[str, Any]]] = Field(description="声音推荐")
    synthesis_plan: Optional[Dict[str, Any]] = Field(description="合成计划")
    user_modifications: Optional[List[Dict[str, Any]]] = Field(description="用户修改")
    final_config: Optional[Dict[str, Any]] = Field(description="最终配置")
    is_user_confirmed: bool = Field(description="用户是否已确认")
    status: str = Field(description="处理状态")
    processing_time: Optional[int] = Field(description="处理耗时")
    confidence_score: Optional[int] = Field(description="置信度评分")
    quality_metrics: Optional[Dict[str, Any]] = Field(description="质量指标")
    error_message: Optional[str] = Field(description="错误消息")
    completed_at: Optional[str] = Field(description="完成时间")
    confirmed_at: Optional[str] = Field(description="确认时间")
    original_analysis: Optional[Dict[str, Any]] = Field(description="原始分析数据")
    llm_response_raw: Optional[str] = Field(description="LLM原始响应")


class ConfigModification(BaseModel):
    """配置修改项"""
    type: str = Field(description="修改类型: character_voice_change, synthesis_params_change, character_add, character_remove")
    data: Dict[str, Any] = Field(description="修改数据")


class AnalysisConfigUpdate(BaseModel):
    """分析结果配置更新"""
    modifications: List[ConfigModification] = Field(description="修改列表")
    user_id: Optional[str] = Field(default=None, description="用户ID")


class LLMConfig(BaseModel):
    """LLM配置"""
    provider: str = Field(description="LLM提供商: dify, openai, claude")
    model: str = Field(description="模型名称")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(default=2000, ge=1, le=8000, description="最大token数")
    workflow_id: Optional[str] = Field(default=None, description="工作流ID (Dify)")
    api_key: Optional[str] = Field(default=None, description="API密钥")
    base_url: Optional[str] = Field(default=None, description="API基础URL")


class AnalysisParams(BaseModel):
    """分析参数"""
    enable_character_detection: bool = Field(default=True, description="启用角色检测")
    enable_dialogue_analysis: bool = Field(default=True, description="启用对话分析")
    enable_emotion_analysis: bool = Field(default=True, description="启用情感分析")
    enable_voice_recommendation: bool = Field(default=True, description="启用声音推荐")
    character_merge_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="角色合并阈值")
    dialogue_confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0, description="对话置信度阈值")
    custom_prompts: Optional[Dict[str, str]] = Field(default=None, description="自定义提示词")


class AnalysisProgressUpdate(BaseModel):
    """分析进度更新"""
    session_id: int = Field(description="会话ID")
    status: str = Field(description="状态")
    progress: int = Field(ge=0, le=100, description="进度百分比")
    current_step: Optional[str] = Field(description="当前步骤")
    completed_chapters: int = Field(description="已完成章节数")
    failed_chapters: int = Field(description="失败章节数")
    error_message: Optional[str] = Field(description="错误消息") 