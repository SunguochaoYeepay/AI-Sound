"""角色AI相关功能路由"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.schemas.character import (
    VoiceTestRequest,
    VoiceTestResponse,
    VoiceQualityResponse,
    AvatarGenerationRequest,
    AvatarGenerationResponse,
    SimilarCharacterResponse
)
from app.services.character_ai_service import CharacterAIService
from app.services.character_management_service import CharacterManagementService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/characters/ai", tags=["角色管理-AI功能"])

@router.post("/test-voice/{character_id}", response_model=VoiceTestResponse)
async def test_voice_synthesis(
    character_id: int,
    test_request: VoiceTestRequest,
    db: Session = Depends(get_db)
):
    """测试语音合成"""
    try:
        # 验证角色是否存在
        management_service = CharacterManagementService(db)
        character = management_service.get_character_by_id(character_id)
        if not character:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        # 验证测试文本
        if not test_request.text or len(test_request.text.strip()) == 0:
            raise HTTPException(status_code=400, detail="测试文本不能为空")
        
        if len(test_request.text) > 500:
            raise HTTPException(status_code=400, detail="测试文本长度不能超过500字符")
        
        service = CharacterAIService(db)
        return service.test_voice_synthesis(character_id, test_request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试语音合成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate-voice/{character_id}", response_model=VoiceQualityResponse)
async def evaluate_voice_quality(
    character_id: int,
    audio_file_path: str = Body(..., description="音频文件路径"),
    db: Session = Depends(get_db)
):
    """评估语音质量"""
    try:
        # 验证角色是否存在
        management_service = CharacterManagementService(db)
        character = management_service.get_character_by_id(character_id)
        if not character:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        # 验证音频文件路径
        if not audio_file_path or len(audio_file_path.strip()) == 0:
            raise HTTPException(status_code=400, detail="音频文件路径不能为空")
        
        service = CharacterAIService(db)
        return service.evaluate_voice_quality(character_id, audio_file_path)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"评估语音质量失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-avatar/{character_id}", response_model=AvatarGenerationResponse)
async def generate_character_avatar(
    character_id: int,
    generation_request: AvatarGenerationRequest,
    db: Session = Depends(get_db)
):
    """生成角色头像"""
    try:
        # 验证角色是否存在
        management_service = CharacterManagementService(db)
        character = management_service.get_character_by_id(character_id)
        if not character:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        # 🔧 修复：自动设置角色名称，不需要前端提供
        # 创建一个新的请求对象，包含角色名称
        from app.schemas.character import AvatarGenerateRequest
        updated_request = AvatarGenerateRequest(
            character_name=character.name,
            description=generation_request.description or character.description,
            style=generation_request.style
        )
        
        # 验证生成参数
        if updated_request.style and updated_request.style not in [
            "realistic", "anime", "cartoon", "oil_painting", "watercolor"
        ]:
            raise HTTPException(status_code=400, detail="不支持的头像风格")
        
        # 注意：AvatarGenerateRequest 模型中没有 size 字段，已移除相关检查
        
        service = CharacterAIService(db)
        return await service.generate_character_avatar(character_id, updated_request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成角色头像失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/avatar-generation-status/{task_id}")
async def get_avatar_generation_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """获取头像生成状态"""
    try:
        service = CharacterAIService(db)
        # 这里可以实现头像生成任务状态查询逻辑
        # 目前返回一个示例响应
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "status": "completed",  # pending, processing, completed, failed
                "progress": 100,
                "result_url": None,
                "error_message": None,
                "created_at": "2024-01-01T00:00:00Z",
                "completed_at": "2024-01-01T00:01:00Z"
            },
            "message": "获取头像生成状态成功"
        }
    except Exception as e:
        logger.error(f"获取头像生成状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/popular-tags")
async def get_popular_tags(
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """获取热门标签"""
    try:
        service = CharacterAIService(db)
        return service.get_popular_tags(limit)
    except Exception as e:
        logger.error(f"获取热门标签失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-similar/{character_id}", response_model=List[SimilarCharacterResponse])
async def search_similar_characters(
    character_id: int,
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0, description="相似度阈值"),
    db: Session = Depends(get_db)
):
    """搜索相似角色"""
    try:
        # 验证角色是否存在
        management_service = CharacterManagementService(db)
        character = management_service.get_character_by_id(character_id)
        if not character:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        service = CharacterAIService(db)
        return service.search_similar_characters(
            character_id, 
            limit, 
            similarity_threshold
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索相似角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-character-traits/{character_id}")
async def analyze_character_traits(
    character_id: int,
    analysis_text: str = Body(..., description="用于分析的文本内容"),
    db: Session = Depends(get_db)
):
    """分析角色特征"""
    try:
        # 验证角色是否存在
        management_service = CharacterManagementService(db)
        character = management_service.get_character_by_id(character_id)
        if not character:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        # 验证分析文本
        if not analysis_text or len(analysis_text.strip()) == 0:
            raise HTTPException(status_code=400, detail="分析文本不能为空")
        
        if len(analysis_text) > 10000:
            raise HTTPException(status_code=400, detail="分析文本长度不能超过10000字符")
        
        # 这里可以实现角色特征分析逻辑
        # 目前返回一个示例响应
        return {
            "success": True,
            "data": {
                "character_id": character_id,
                "traits": {
                    "personality": ["勇敢", "善良", "聪明"],
                    "speaking_style": "正式",
                    "emotional_tendency": "积极",
                    "age_group": "青年",
                    "gender_tendency": "中性"
                },
                "confidence_score": 0.85,
                "suggestions": [
                    "建议使用温和的语调",
                    "可以添加一些正能量的语气词"
                ]
            },
            "message": "角色特征分析完成"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析角色特征失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recommend-voice-settings/{character_id}")
async def recommend_voice_settings(
    character_id: int,
    context: str = Body("", description="上下文信息"),
    db: Session = Depends(get_db)
):
    """推荐语音设置"""
    try:
        # 验证角色是否存在
        management_service = CharacterManagementService(db)
        character = management_service.get_character_by_id(character_id)
        if not character:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        # 这里可以实现语音设置推荐逻辑
        # 目前返回一个示例响应
        return {
            "success": True,
            "data": {
                "character_id": character_id,
                "recommended_settings": {
                    "voice_type": "female_young",
                    "speed": 1.0,
                    "pitch": 0.0,
                    "volume": 0.8,
                    "emotion": "neutral",
                    "style": "natural"
                },
                "confidence_score": 0.9,
                "reasoning": "基于角色特征和上下文分析，推荐使用年轻女性声音，语速正常，情感中性"
            },
            "message": "语音设置推荐完成"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"推荐语音设置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voice-models")
async def get_available_voice_models(
    voice_type: Optional[str] = Query(None, description="声音类型过滤"),
    language: Optional[str] = Query(None, description="语言过滤"),
    db: Session = Depends(get_db)
):
    """获取可用的语音模型"""
    try:
        # 这里可以实现获取可用语音模型的逻辑
        # 目前返回一个示例响应
        models = [
            {
                "id": "model_1",
                "name": "标准女声",
                "voice_type": "female",
                "language": "zh-CN",
                "quality": "high",
                "description": "清晰自然的女性声音",
                "sample_url": "/samples/model_1.mp3"
            },
            {
                "id": "model_2",
                "name": "标准男声",
                "voice_type": "male",
                "language": "zh-CN",
                "quality": "high",
                "description": "沉稳有力的男性声音",
                "sample_url": "/samples/model_2.mp3"
            }
        ]
        
        # 应用过滤条件
        if voice_type:
            models = [m for m in models if m["voice_type"] == voice_type]
        if language:
            models = [m for m in models if m["language"] == language]
        
        return {
            "success": True,
            "data": {
                "models": models,
                "total": len(models)
            },
            "message": "获取可用语音模型成功"
        }
    except Exception as e:
        logger.error(f"获取可用语音模型失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))