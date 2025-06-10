"""
智能分析API
基于Dify工作流的文本分析和角色识别
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
import json
import logging
from datetime import datetime

from app.database import get_db
from app.models import NovelProject, VoiceProfile, Book, TextSegment
from app.services.dify_client import get_dify_client, DifyAPIException
from app.exceptions import ServiceException
from app.config import settings
from app.novel_reader import update_segments_voice_mapping_no_commit

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/intelligent-analysis", tags=["智能分析"])

@router.post("/analyze/{project_id}")
async def analyze_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    调用Dify工作流分析项目
    返回直接可用的合成计划
    """
    try:
        # 1. 验证项目是否存在
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 2. 获取项目关联的书籍内容
        book_content = ""
        if project.book_id:
            book = db.query(Book).filter(Book.id == project.book_id).first()
            if book and book.content:
                book_content = book.content
            else:
                raise HTTPException(status_code=400, detail="项目关联的书籍没有内容")
        else:
            # 如果没有关联书籍，使用项目自身的original_text
            if hasattr(project, 'original_text') and project.original_text:
                book_content = project.original_text
            else:
                raise HTTPException(status_code=400, detail="项目没有可分析的文本内容")
        
        # 3. 获取可用的声音档案
        voices = db.query(VoiceProfile).filter(VoiceProfile.status == 'active').all()
        if len(voices) < 2:
            logger.warning(f"项目 {project_id} 可用声音档案不足，将使用Mock模式")
            return await _fallback_to_mock_analysis(project_id, voices, db)
        
        # 4. 准备Dify工作流输入数据
        available_voices = [
            {
                "id": voice.id,
                "name": voice.name,
                "type": voice.type,
                "description": voice.description or ""
            }
            for voice in voices
        ]
        
        # 5. 调用Dify工作流进行分析
        try:
            dify_client = await get_dify_client()
            
            # 构建工作流输入参数
            workflow_input = {
                "text": book_content,
                "available_voices": available_voices,
                "analysis_config": {
                    "max_segments": 500,
                    "include_narration": True,
                    "detect_emotions": True
                }
            }
            
            # 获取Dify工作流ID
            workflow_id = getattr(settings, 'DIFY_NOVEL_WORKFLOW_ID', None)
            if not workflow_id:
                logger.warning("未配置DIFY_NOVEL_WORKFLOW_ID，使用Mock模式")
                return await _fallback_to_mock_analysis(project_id, voices, db)
            
            # 调用Dify分析
            analysis_result = await dify_client.analyze_text(
                text=book_content,
                workflow_id=workflow_id,
                additional_params=workflow_input
            )
            
            # 6. 验证和处理Dify返回结果
            if analysis_result and analysis_result.data:
                processed_result = _process_dify_result(analysis_result.data, voices)
                
                logger.info(f"[DIFY] 为项目 {project_id} 完成智能分析")
                
                return {
                    "success": True,
                    "message": "智能分析完成",
                    "data": processed_result,
                    "source": "dify",
                    "execution_time": analysis_result.execution_time
                }
            else:
                logger.warning("Dify返回结果为空，使用Mock模式")
                return await _fallback_to_mock_analysis(project_id, voices, db)
                
        except DifyAPIException as e:
            logger.error(f"Dify API调用失败: {str(e)}，使用Mock模式")
            return await _fallback_to_mock_analysis(project_id, voices, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"智能分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@router.post("/apply/{project_id}")
async def apply_analysis(
    project_id: int,
    analysis_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    应用分析结果到项目
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
        logger.info(f"[DEBUG] 准备设置角色映射: {character_mapping}")
        
        if hasattr(project, 'set_character_mapping'):
            logger.info(f"[DEBUG] 使用set_character_mapping方法")
            project.set_character_mapping(character_mapping)
            logger.info(f"[DEBUG] 设置完成，当前config: {project.config}")
        else:
            logger.info(f"[DEBUG] 直接设置character_mapping字段")
            # 如果模型没有该方法，直接设置JSON字段
            project.character_mapping = json.dumps(character_mapping) if character_mapping else None
        
        # 标记项目为已配置状态
        project.status = 'configured'
        
        logger.info(f"[DEBUG] 提交前项目config: {project.config}")
        db.commit()
        logger.info(f"[DEBUG] 提交后重新查询项目配置")
        
        # 重新查询验证
        db.refresh(project)
        logger.info(f"[DEBUG] 重新查询后的config: {project.config}")
        logger.info(f"[DEBUG] 获取的character_mapping: {project.get_character_mapping()}")
        
        # 重要：更新段落的声音映射
        mapping_result = await update_segments_voice_mapping_no_commit(project_id, character_mapping, db)
        db.commit()
        
        logger.info(f"已应用分析结果到项目 {project_id}")
        logger.info(f"段落映射更新结果: {mapping_result}")
        
        return {
            "success": True,
            "message": "分析结果已应用",
            "applied_mapping": character_mapping,
            "segments_updated": mapping_result.get("updated_count", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"应用分析结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"应用失败: {str(e)}")

def _process_dify_result(dify_data: Dict[str, Any], available_voices: List[VoiceProfile]) -> Dict[str, Any]:
    """
    处理Dify返回的结果，确保格式正确
    """
    try:
        # 如果Dify直接返回了标准格式，直接使用
        if "synthesis_plan" in dify_data and "characters" in dify_data:
            return dify_data
        
        # 否则尝试从Dify结果中提取和转换数据
        processed = {
            "project_info": {
                "novel_type": dify_data.get("novel_type", "未知"),
                "analysis_time": datetime.now().isoformat(),
                "total_segments": len(dify_data.get("segments", [])),
                "ai_model": "dify-intelligent-analysis"
            },
            "synthesis_plan": _extract_synthesis_plan(dify_data),
            "characters": _extract_characters(dify_data, available_voices)
        }
        
        return processed
        
    except Exception as e:
        logger.error(f"处理Dify结果失败: {str(e)}")
        raise ServiceException(f"处理AI分析结果失败: {str(e)}")

def _extract_synthesis_plan(dify_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    从Dify结果中提取合成计划
    """
    segments = dify_data.get("segments", [])
    synthesis_plan = []
    
    for i, segment in enumerate(segments):
        plan_item = {
            "segment_id": i + 1,
            "text": segment.get("text", ""),
            "speaker": segment.get("speaker", "旁白"),
            "voice_id": segment.get("voice_id"),
            "voice_name": segment.get("voice_name", ""),
            "parameters": segment.get("parameters", {
                "timeStep": 20,
                "pWeight": 1.0,
                "tWeight": 1.0
            })
        }
        synthesis_plan.append(plan_item)
    
    return synthesis_plan

def _extract_characters(dify_data: Dict[str, Any], available_voices: List[VoiceProfile]) -> List[Dict[str, Any]]:
    """
    从Dify结果中提取角色信息
    """
    characters_data = dify_data.get("characters", [])
    characters = []
    
    # 创建voice_id到voice的映射
    voice_map = {voice.id: voice for voice in available_voices}
    
    for char_data in characters_data:
        character = {
            "name": char_data.get("name", ""),
            "voice_id": char_data.get("voice_id"),
            "voice_name": char_data.get("voice_name", "")
        }
        
        # 如果没有voice_name但有voice_id，从可用声音中查找
        if character["voice_id"] and not character["voice_name"]:
            voice = voice_map.get(character["voice_id"])
            if voice:
                character["voice_name"] = voice.name
        
        characters.append(character)
    
    return characters

async def _fallback_to_mock_analysis(project_id: int, voices: List[VoiceProfile], db: Session) -> Dict[str, Any]:
    """
    Dify调用失败时的Mock分析回退逻辑
    """
    try:
        # 获取项目的实际段落数据，分析真实的角色
        segments = db.query(TextSegment).filter(TextSegment.project_id == project_id).all()
        
        # 提取所有唯一的speaker名称
        unique_speakers = list(set([seg.speaker for seg in segments if seg.speaker and seg.speaker.strip()]))
        
        # 按性别分类声音
        male_voices = [v for v in voices if v.type == 'male']
        female_voices = [v for v in voices if v.type == 'female']
        neutral_voices = [v for v in voices if v.type in ['child', 'neutral', 'narrator']]
        
        # 确保有足够的声音选择
        all_voices = male_voices + female_voices + neutral_voices
        if not all_voices:
            all_voices = voices
        
        # 为每个角色分配声音（简单的轮询分配）
        characters = []
        synthesis_plan = []
        
        for i, speaker in enumerate(unique_speakers):
            # 根据角色名称智能分配声音类型
            if any(keyword in speaker.lower() for keyword in ['章', 'chapter', '旁白', 'narrator']):
                # 章节标题和旁白使用中性声音
                assigned_voice = neutral_voices[i % len(neutral_voices)] if neutral_voices else all_voices[i % len(all_voices)]
            elif any(keyword in speaker.lower() for keyword in ['女', 'female', '温柔']):
                # 女性角色使用女声
                assigned_voice = female_voices[i % len(female_voices)] if female_voices else all_voices[i % len(all_voices)]
            else:
                # 其他角色使用男声
                assigned_voice = male_voices[i % len(male_voices)] if male_voices else all_voices[i % len(all_voices)]
            
            characters.append({
                "name": speaker,
                "voice_id": assigned_voice.id,
                "voice_name": assigned_voice.name
            })
        
        # 生成合成计划（基于实际段落）
        for i, segment in enumerate(segments[:5]):  # 只显示前5个段落作为示例
            synthesis_plan.append({
                "segment_id": i + 1,
                "text": segment.content[:50] + "..." if len(segment.content) > 50 else segment.content,
                "speaker": segment.speaker or "未知",
                "voice_id": next((char["voice_id"] for char in characters if char["name"] == segment.speaker), all_voices[0].id),
                "voice_name": next((char["voice_name"] for char in characters if char["name"] == segment.speaker), all_voices[0].name),
                "parameters": {"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}
            })
        
        # 生成Mock分析结果
        mock_result = {
            "project_info": {
                "novel_type": "智能检测",
                "analysis_time": datetime.now().isoformat(),
                "total_segments": len(segments),
                "ai_model": "mock-smart-analysis",
                "detected_characters": len(unique_speakers)
            },
            
            "synthesis_plan": synthesis_plan,
            "characters": characters
        }
        
        logger.info(f"[MOCK FALLBACK] 为项目 {project_id} 生成基于实际数据的Mock分析结果")
        logger.info(f"[MOCK FALLBACK] 检测到 {len(unique_speakers)} 个角色: {unique_speakers}")
        
        return {
            "success": True,
            "message": "智能分析完成（Mock模式）",
            "data": mock_result,
            "source": "mock_fallback"
        }
        
    except Exception as e:
        logger.error(f"Mock回退分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}") 