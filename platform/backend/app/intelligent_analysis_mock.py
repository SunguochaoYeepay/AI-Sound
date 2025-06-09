"""
智能角色分析Mock API
用于测试接口设计和数据流程
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any
import json
import logging
from datetime import datetime

from database import get_db
from models import NovelProject, VoiceProfile

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/intelligent-analysis", tags=["智能分析Mock"])

@router.post("/analyze/{project_id}")
async def mock_intelligent_analysis(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Mock智能分析接口
    返回预设的分析结果用于测试
    """
    try:
        # 验证项目是否存在
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 获取可用的声音档案
        voices = db.query(VoiceProfile).filter(VoiceProfile.status == 'active').all()
        if len(voices) < 3:
            raise HTTPException(status_code=400, detail="可用声音档案不足，至少需要3个")
        
        # Mock分析结果 - 基于真实的"数据之茧"小说内容
        mock_result = {
            "analysis_metadata": {
                "novel_type": "科幻",
                "total_characters": 12580,
                "estimated_reading_time": 45,
                "confidence_score": 0.92,
                "analysis_time": datetime.now().isoformat(),
                "ai_model": "mock-gpt-4"
            },
            
            "detected_characters": [
                {
                    "name": "李维",
                    "character_id": "char_001",
                    "gender": "male",
                    "estimated_age": 35,
                    "personality_traits": ["理性", "专业", "冷静", "好奇"],
                    "speaking_style": "逻辑清晰，语速适中，偶有专业术语",
                    "role_importance": "protagonist",
                    "first_appearance_segment": 1,
                    "total_segments": 22,
                    "sample_dialogues": [
                        "数据的流动模式确实很有趣。",
                        "我们需要更深入地分析这个现象。",
                        "这背后一定有某种我们还没发现的规律。"
                    ],
                    "recommended_voice_id": voices[0].id if len(voices) > 0 else 1,
                    "confidence_score": 0.95
                },
                {
                    "name": "艾莉",
                    "character_id": "char_002",
                    "gender": "female", 
                    "estimated_age": 28,
                    "personality_traits": ["敏锐", "直觉强", "善于观察", "有点神秘"],
                    "speaking_style": "语调轻柔，但透露着坚定",
                    "role_importance": "protagonist",
                    "first_appearance_segment": 8,
                    "total_segments": 18,
                    "sample_dialogues": [
                        "你有没有觉得这些数据像是在讲故事？",
                        "有时候直觉比逻辑更重要。",
                        "我感觉我们正在接近真相。"
                    ],
                    "recommended_voice_id": voices[1].id if len(voices) > 1 else 2,
                    "confidence_score": 0.88
                },
                {
                    "name": "系统旁白",
                    "character_id": "narrator_system",
                    "type": "narrator",
                    "style": "客观叙述，科技感",
                    "total_segments": 14,
                    "recommended_voice_id": voices[2].id if len(voices) > 2 else 3,
                    "confidence_score": 0.99
                }
            ],
            
            "intelligent_segments": [
                {
                    "segment_id": 1,
                    "text": "在数字化时代的浪潮中，数据如同蚕茧般包裹着我们的生活。",
                    "text_type": "环境描述",
                    "speaker": "系统旁白",
                    "character_id": "narrator_system",
                    "emotion": "平静",
                    "narrative_perspective": "第三人称",
                    "scene_setting": "科技背景",
                    "recommended_voice_id": voices[2].id if len(voices) > 2 else 3,
                    "confidence_score": 0.92,
                    "processing_priority": "normal"
                },
                {
                    "segment_id": 2,
                    "text": "数据的流动模式确实很有趣，我从来没有从这个角度思考过。",
                    "text_type": "对话",
                    "speaker": "李维",
                    "character_id": "char_001", 
                    "emotion": "好奇",
                    "dialogue_type": "对话",
                    "recommended_voice_id": voices[0].id if len(voices) > 0 else 1,
                    "confidence_score": 0.89,
                    "processing_priority": "high"
                },
                {
                    "segment_id": 3,
                    "text": "他停下手中的工作，开始重新审视屏幕上闪烁的数据流。",
                    "text_type": "动作描述",
                    "speaker": "系统旁白",
                    "character_id": "narrator_system",
                    "emotion": "专注",
                    "narrative_perspective": "第三人称", 
                    "scene_setting": "办公环境",
                    "recommended_voice_id": voices[2].id if len(voices) > 2 else 3,
                    "confidence_score": 0.85,
                    "processing_priority": "normal"
                },
                {
                    "segment_id": 4,
                    "text": "你有没有觉得这些数据像是在讲故事？每一个数据点都有它的情感。",
                    "text_type": "对话",
                    "speaker": "艾莉",
                    "character_id": "char_002",
                    "emotion": "思考",
                    "dialogue_type": "对话", 
                    "recommended_voice_id": voices[1].id if len(voices) > 1 else 2,
                    "confidence_score": 0.91,
                    "processing_priority": "high"
                },
                {
                    "segment_id": 5,
                    "text": "李维思考着艾莉的话，意识到数据背后可能隐藏着更深层的含义。",
                    "text_type": "心理活动",
                    "speaker": "心理旁白",
                    "character_id": "narrator_thought",
                    "emotion": "沉思",
                    "psychological_state": "深度思考",
                    "recommended_voice_id": voices[2].id if len(voices) > 2 else 3,
                    "confidence_score": 0.87,
                    "processing_priority": "normal"
                }
            ],
            
            "voice_mapping_recommendation": {
                "char_001": {
                    "character_name": "李维",
                    "primary_voice_id": voices[0].id if len(voices) > 0 else 1,
                    "alternative_voice_ids": [voices[i].id for i in range(min(3, len(voices))) if i != 0],
                    "matching_reasons": [
                        "成熟男声，适合专业角色",
                        "音色沉稳理性，符合科研人员特质",
                        "语调适合表达逻辑思维"
                    ]
                },
                "char_002": {
                    "character_name": "艾莉",
                    "primary_voice_id": voices[1].id if len(voices) > 1 else 2,
                    "alternative_voice_ids": [voices[i].id for i in range(min(3, len(voices))) if i != 1],
                    "matching_reasons": [
                        "知性女声，适合敏锐角色",
                        "音色柔和但坚定，符合直觉型人格",
                        "适合表达深层思考"
                    ]
                },
                "narrator_system": {
                    "character_name": "系统旁白",
                    "primary_voice_id": voices[2].id if len(voices) > 2 else 3,
                    "alternative_voice_ids": [],
                    "matching_reasons": ["专业旁白音色，科技感强"]
                }
            },
            
            "analysis_summary": {
                "total_segments": 54,
                "character_dialogue_segments": 28,
                "narration_segments": 20,
                "thought_segments": 6,
                "main_characters_count": 2,
                "supporting_characters_count": 0,
                "narrator_types_count": 2,
                "estimated_synthesis_time": 15,
                "quality_assessment": {
                    "character_consistency": 0.92,
                    "dialogue_clarity": 0.88,
                    "text_type_accuracy": 0.91,
                    "overall_confidence": 0.90
                },
                "potential_issues": [
                    {
                        "type": "ambiguous_speaker",
                        "segments": [25, 31],
                        "description": "部分技术讨论段落说话人可能存在歧义"
                    }
                ]
            }
        }
        
        logger.info(f"[MOCK] 为项目 {project_id} 生成Mock分析结果")
        
        return {
            "success": True,
            "message": "智能分析完成（Mock模式）",
            "data": mock_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mock分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@router.post("/apply/{project_id}")
async def apply_mock_analysis(
    project_id: int,
    analysis_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    应用Mock分析结果到项目
    """
    try:
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 提取角色映射
        voice_mapping = analysis_data.get("voice_mapping_recommendation", {})
        character_mapping = {}
        
        for char_id, mapping_info in voice_mapping.items():
            character_name = mapping_info.get("character_name", "")
            voice_id = mapping_info.get("primary_voice_id", 1)
            if character_name:
                character_mapping[character_name] = voice_id
        
        # 更新项目的角色映射
        project.set_character_mapping(character_mapping)
        
        # 这里可以进一步处理segments数据，更新数据库中的TextSegment记录
        # 但为了测试，先只更新角色映射
        
        db.commit()
        logger.info(f"[MOCK] 已应用分析结果到项目 {project_id}")
        
        return {
            "success": True,
            "message": "分析结果已应用",
            "applied_mapping": character_mapping
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"应用分析结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"应用失败: {str(e)}") 