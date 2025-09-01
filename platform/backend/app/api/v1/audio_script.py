"""
音频剧本API
基于7类卡片方案的音频剧本生成和管理API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging

from app.database import get_db
from app.services.storyboard_analysis_service_v2 import StoryboardAnalysisServiceV2
from app.models.storyboard_cards import AudioScriptCard, BaseStoryboardCard
from app.models import BookChapter
from app.utils.exceptions import ServiceException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audio-script")


@router.post("/generate/{session_id}")
async def generate_audio_script(
    session_id: int,
    chapter_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    为指定会话生成音频剧本
    """
    service = StoryboardAnalysisServiceV2(db)
    
    try:
        # 获取会话
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="分析会话不存在")
        
        # 获取现有卡片
        cards = service.get_session_cards(session_id, chapter_id)
        
        # 按类型分组
        scene_cards = [card for card in cards if card.card_type == 'scene']
        event_cards = [card for card in cards if card.card_type == 'event']
        emotion_cards = [card for card in cards if card.card_type == 'emotion']
        
        if not scene_cards or not event_cards or not emotion_cards:
            raise HTTPException(status_code=400, detail="缺少必要的分析卡片，请先完成6卡分析")
        
        # 获取章节内容
        original_content = ""
        if chapter_id:
            chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
            if chapter:
                original_content = chapter.content
                logger.info(f"获取到章节 {chapter_id} 的内容，长度: {len(original_content)}")
            else:
                logger.warning(f"章节 {chapter_id} 不存在")
        else:
            logger.warning("未指定章节ID，无法获取原文内容")
        
        # 生成音频剧本
        logger.info(f"准备调用音频剧本生成器，原文内容长度: {len(original_content)}")
        script_data = await service.script_generator.generate_script(
            scene_data=[card.content for card in scene_cards],
            event_data=[card.content for card in event_cards],
            emotion_data=[card.content for card in emotion_cards],
            original_content=original_content
        )
        
        # 创建音频剧本卡
        script_card = AudioScriptCard(
            session_id=session_id,
            chapter_id=chapter_id,
            content=script_data,
            confidence_score=script_data.get('quality_score', 0.85),
            card_type='audio_script'
        )
        
        db.add(script_card)
        db.commit()
        db.refresh(script_card)
        
        return {
            "success": True,
            "message": "音频剧本生成成功",
            "script_card": script_card.to_dict()
        }
        
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成音频剧本失败: {str(e)}")


@router.get("/{script_id}")
def get_audio_script(script_id: int, db: Session = Depends(get_db)):
    """
    获取音频剧本详情
    """
    try:
        script_card = db.query(AudioScriptCard).filter(AudioScriptCard.id == script_id).first()
        if not script_card:
            raise HTTPException(status_code=404, detail="音频剧本不存在")
        
        return script_card.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取音频剧本失败: {str(e)}")


@router.get("/session/{session_id}")
def get_session_audio_scripts(
    session_id: int,
    chapter_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    获取会话的所有音频剧本
    """
    try:
        query = db.query(AudioScriptCard).filter(AudioScriptCard.session_id == session_id)
        
        if chapter_id:
            query = query.filter(AudioScriptCard.chapter_id == chapter_id)
        
        script_cards = query.all()
        
        return {
            "script_cards": [card.to_dict() for card in script_cards],
            "total": len(script_cards)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取音频剧本列表失败: {str(e)}")


@router.put("/{script_id}")
def update_audio_script(
    script_id: int,
    script_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    更新音频剧本
    """
    try:
        script_card = db.query(AudioScriptCard).filter(AudioScriptCard.id == script_id).first()
        if not script_card:
            raise HTTPException(status_code=404, detail="音频剧本不存在")
        
        # 更新内容
        script_card.content.update(script_data)
        db.commit()
        db.refresh(script_card)
        
        return {
            "success": True,
            "message": "音频剧本更新成功",
            "script_card": script_card.to_dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新音频剧本失败: {str(e)}")


@router.delete("/{script_id}")
def delete_audio_script(script_id: int, db: Session = Depends(get_db)):
    """
    删除音频剧本
    """
    try:
        script_card = db.query(AudioScriptCard).filter(AudioScriptCard.id == script_id).first()
        if not script_card:
            raise HTTPException(status_code=404, detail="音频剧本不存在")
        
        db.delete(script_card)
        db.commit()
        
        return {
            "success": True,
            "message": "音频剧本删除成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除音频剧本失败: {str(e)}")


@router.post("/{script_id}/validate")
def validate_audio_script(script_id: int, db: Session = Depends(get_db)):
    """
    验证音频剧本质量
    """
    try:
        script_card = db.query(AudioScriptCard).filter(AudioScriptCard.id == script_id).first()
        if not script_card:
            raise HTTPException(status_code=404, detail="音频剧本不存在")
        
        # 简单的质量验证逻辑
        content = script_card.content
        script_segments = content.get('script_segments', [])
        
        validation_results = {
            "total_segments": len(script_segments),
            "quality_score": content.get('quality_score', 0.0),
            "issues": [],
            "recommendations": []
        }
        
        # 检查每个段落
        for i, segment in enumerate(script_segments):
            if not segment.get('dialogue', {}).get('content'):
                validation_results["issues"].append(f"段落 {i+1}: 缺少对话内容")
            
            if not segment.get('production_notes', {}).get('voice_direction'):
                validation_results["issues"].append(f"段落 {i+1}: 缺少制作指导")
        
        # 生成建议
        if validation_results["quality_score"] < 0.8:
            validation_results["recommendations"].append("建议提高剧本质量，增加更多制作细节")
        
        if len(validation_results["issues"]) > 0:
            validation_results["recommendations"].append("请修复上述问题以提高剧本质量")
        
        return validation_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证音频剧本失败: {str(e)}")
