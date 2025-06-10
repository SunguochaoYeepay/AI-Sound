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

from app.database import get_db
from app.models import NovelProject, VoiceProfile

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/intelligent-analysis", tags=["智能分析Mock"])

@router.post("/analyze/{project_id}")
async def mock_intelligent_analysis(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Mock智能分析接口
    返回直接可用的合成计划
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
        
        # 按性别分类声音
        male_voices = [v for v in voices if v.type == 'male']
        female_voices = [v for v in voices if v.type == 'female']
        neutral_voices = [v for v in voices if v.type in ['child', 'neutral', 'narrator']]
        
        # 确保有足够的声音选择
        all_voices = male_voices + female_voices + neutral_voices
        if len(all_voices) < 4:
            # 如果声音不够，补充使用所有可用声音
            all_voices = voices
        
        # 智能分析结果 - 直接可用的合成计划
        mock_result = {
            "project_info": {
                "novel_type": "科幻",
                "analysis_time": datetime.now().isoformat(),
                "total_segments": 5,
                "ai_model": "mock-intelligent-analysis"
            },
            
            "synthesis_plan": [
                {
                    "segment_id": 1,
                    "text": "在数字化时代的浪潮中，数据如同蚕茧般包裹着我们的生活。",
                    "speaker": "系统旁白",
                    "voice_id": neutral_voices[0].id if neutral_voices else None,
                    "voice_name": neutral_voices[0].name if neutral_voices else "未配置",
                    "parameters": {
                        "timeStep": 20,
                        "pWeight": 1.0,
                        "tWeight": 1.0
                    }
                },
                {
                    "segment_id": 2,
                    "text": "数据的流动模式确实很有趣，我从来没有从这个角度思考过。",
                    "speaker": "李维",
                    "voice_id": male_voices[0].id if male_voices else None,
                    "voice_name": male_voices[0].name if male_voices else "未配置",
                    "parameters": {
                        "timeStep": 15,
                        "pWeight": 1.2,
                        "tWeight": 0.8
                    }
                },
                {
                    "segment_id": 3,
                    "text": "他停下手中的工作，开始重新审视屏幕上闪烁的数据流。",
                    "speaker": "系统旁白",
                    "voice_id": neutral_voices[0].id if neutral_voices else None,
                    "voice_name": neutral_voices[0].name if neutral_voices else "未配置",
                    "parameters": {
                        "timeStep": 18,
                        "pWeight": 1.0,
                        "tWeight": 1.0
                    }
                },
                {
                    "segment_id": 4,
                    "text": "你有没有觉得这些数据像是在讲故事？每一个数据点都有它的情感。",
                    "speaker": "艾莉",
                    "voice_id": female_voices[0].id if female_voices else None,
                    "voice_name": female_voices[0].name if female_voices else "未配置",
                    "parameters": {
                        "timeStep": 16,
                        "pWeight": 1.1,
                        "tWeight": 0.9
                    }
                },
                {
                    "segment_id": 5,
                    "text": "李维思考着艾莉的话，意识到数据背后可能隐藏着更深层的含义。",
                    "speaker": "心理旁白",
                    "voice_id": neutral_voices[1].id if len(neutral_voices) > 1 else (all_voices[3].id if len(all_voices) > 3 else None),
                    "voice_name": neutral_voices[1].name if len(neutral_voices) > 1 else (all_voices[3].name if len(all_voices) > 3 else "未配置"),
                    "parameters": {
                        "timeStep": 22,
                        "pWeight": 0.9,
                        "tWeight": 1.1
                    }
                }
            ],
            
            "characters": [
                {
                    "name": "李维",
                    "voice_id": male_voices[0].id if male_voices else None,
                    "voice_name": male_voices[0].name if male_voices else "未配置"
                },
                {
                    "name": "艾莉", 
                    "voice_id": female_voices[0].id if female_voices else None,
                    "voice_name": female_voices[0].name if female_voices else "未配置"
                },
                {
                    "name": "系统旁白",
                    "voice_id": neutral_voices[0].id if neutral_voices else None,
                    "voice_name": neutral_voices[0].name if neutral_voices else "未配置"
                },
                {
                    "name": "心理旁白",
                    "voice_id": neutral_voices[1].id if len(neutral_voices) > 1 else (all_voices[3].id if len(all_voices) > 3 else None),
                    "voice_name": neutral_voices[1].name if len(neutral_voices) > 1 else (all_voices[3].name if len(all_voices) > 3 else "未配置")
                }
            ]
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
        characters = analysis_data.get("characters", [])
        character_mapping = {}
        
        for char in characters:
            character_name = char.get("name", "")
            voice_id = char.get("voice_id")
            if character_name and voice_id:
                character_mapping[character_name] = voice_id
        
        # 更新项目的角色映射
        project.set_character_mapping(character_mapping)
        
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