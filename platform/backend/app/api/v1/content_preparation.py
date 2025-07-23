"""
内容准备API
提供小说章节语音合成前的智能内容准备功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from app.database import get_db
from app.models import BookChapter, Book, AnalysisResult
from app.services.content_preparation_service import ContentPreparationService
from app.services.intelligent_detection_service import IntelligentDetectionService

router = APIRouter(prefix="/content-preparation")
logger = logging.getLogger(__name__)

# 服务实例将在每个请求中创建

class PreparationRequest(BaseModel):
    """智能准备请求模型"""
    auto_add_narrator: bool = True
    processing_mode: str = "auto"
    tts_optimization: str = "balanced"  # fast, balanced, quality


@router.get("/content-stats/{chapter_id}")
async def get_content_stats(
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """
    获取章节内容统计信息
    用于快速了解章节基本信息和处理建议
    """
    try:
        # 获取章节
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 创建服务实例并获取统计信息
        content_prep_service = ContentPreparationService(db)
        stats = await content_prep_service.get_content_stats(chapter_id, db)
        
        return {
            "success": True,
            "data": stats,
            "message": "内容统计获取成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取内容统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取内容统计失败: {str(e)}")


@router.get("/synthesis-preview/{chapter_id}")
async def get_synthesis_preview(
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """
    获取章节语音合成预览
    快速分析章节内容，提供角色检测和分段预览
    """
    try:
        # 获取章节
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 创建服务实例并获取预览信息
        content_prep_service = ContentPreparationService(db)
        preview = await content_prep_service.get_synthesis_preview(chapter_id, db)
        
        return {
            "success": True,
            "data": preview,
            "message": "合成预览获取成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取合成预览失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取合成预览失败: {str(e)}")


@router.post("/prepare-synthesis/{chapter_id}")
async def prepare_chapter_for_synthesis(
    chapter_id: int,
    request: PreparationRequest = Body(default=PreparationRequest()),
    db: Session = Depends(get_db)
):
    """
    智能准备章节用于语音合成（优化版）
    
    核心功能：
    1. 智能文本分块（最大3000 tokens）
    2. 角色对话检测和分离
    3. 自动添加旁白角色
    4. 生成语音合成配置（支持TTS优化模式）
    5. 输出JSON格式数据
    
    参数：
    - auto_add_narrator: 是否自动添加旁白角色
    - processing_mode: 处理模式（auto/single/distributed）
      * auto: 自动选择最佳模式
      * single: 单块分析模式（适合较短章节）
      * distributed: 分布式分析模式（适合长章节）
    - tts_optimization: TTS优化模式（fast/balanced/quality）
      * fast: 快速模式，优化性能
      * balanced: 平衡模式，性能与质量兼顾
      * quality: 质量模式，最高质量分析
    """
    try:
        # 获取章节
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 创建服务实例并执行智能准备
        content_prep_service = ContentPreparationService(db)
        
        # 🔧 优化：构建用户偏好配置，包含TTS优化模式
        user_preferences = {
            "auto_add_narrator": request.auto_add_narrator,
            "processing_mode": request.processing_mode,
            "tts_optimization": request.tts_optimization
        }
        
        logger.info(f"📋 章节{chapter_id}智能准备请求: {user_preferences}")
        
        result = await content_prep_service.prepare_chapter_for_synthesis(
            chapter_id=chapter_id,
            user_preferences=user_preferences
        )
        
        return {
            "success": True,
            "data": result,
            "message": "章节智能准备完成"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"章节智能准备失败: {error_msg}")
        
        # 提供用户友好的错误消息
        user_friendly_msg = "章节智能准备失败"
        
        if "timeout" in error_msg.lower() or "超时" in error_msg:
            user_friendly_msg = "智能准备超时，该章节内容可能较长，请稍后重试"
        elif "ollama" in error_msg.lower():
            user_friendly_msg = "AI分析服务暂时不可用，请稍后重试"
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            user_friendly_msg = "网络连接错误，请检查网络后重试"
        elif "analysis" in error_msg.lower():
            user_friendly_msg = "文本分析失败，请检查章节内容格式"
        elif "character" in error_msg.lower():
            user_friendly_msg = "角色识别失败，请确保章节包含对话内容"
        else:
            user_friendly_msg = f"智能准备过程中发生错误：{error_msg}"
        
        raise HTTPException(status_code=500, detail=user_friendly_msg)


@router.get("/preparation-status/{chapter_id}")
async def get_preparation_status(
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """
    获取章节准备状态
    检查章节是否已经完成智能准备
    """
    try:
        # 获取章节
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 创建服务实例并检查准备状态
        content_prep_service = ContentPreparationService(db)
        status = await content_prep_service.get_preparation_status(chapter_id, db)
        
        return {
            "success": True,
            "data": status,
            "message": "准备状态获取成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取准备状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取准备状态失败: {str(e)}")


@router.get("/result/{chapter_id}")
async def get_preparation_result(
    chapter_id: int,
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    db: Session = Depends(get_db)
):
    """
    获取章节的已有智能准备结果
    不重新执行智能准备，只返回已存储的结果
    
    Args:
        chapter_id: 章节ID
        force_refresh: 强制刷新缓存，忽略final_config
    """
    try:
        # 获取章节
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 检查是否有智能准备结果
        try:
            
            # 查找最新的智能准备结果
            latest_result = db.query(AnalysisResult).filter(
                AnalysisResult.chapter_id == chapter_id,
                AnalysisResult.status == 'completed'
            ).order_by(AnalysisResult.created_at.desc()).first()
            
            if not latest_result:
                raise HTTPException(status_code=404, detail="该章节尚未完成智能准备")
            
            # 直接使用存储的智能准备结果，不再进行动态缓存同步
            synthesis_plan = latest_result.synthesis_plan or {}
            logger.info("📋 [结果获取] 使用存储的智能准备结果，已包含正确的角色配置")
            
            # 构建返回数据
            result_data = {
                "synthesis_json": synthesis_plan,
                "processing_info": {
                    "mode": "stored",
                    "total_segments": len(synthesis_plan.get('synthesis_plan', [])) if synthesis_plan else 0,
                    "characters_found": len(latest_result.detected_characters) if latest_result.detected_characters else 0,
                    "saved_to_database": True,
                    "result_id": latest_result.id,
                    "created_at": latest_result.created_at.isoformat() if latest_result.created_at else None,
                    "completed_at": latest_result.completed_at.isoformat() if latest_result.completed_at else None,
                    "voice_sync_applied": False,  # 不再进行动态语音同步
                    "cache_status": "fresh" if force_refresh else "cached",  # 🔥 新增：缓存状态
                    "data_source": "synthesis_plan"  # 🔥 新增：数据来源
                },
                "last_updated": latest_result.updated_at.isoformat() if latest_result.updated_at else latest_result.created_at.isoformat()
            }
            
            # 🔥 智能缓存处理：根据force_refresh参数决定是否使用final_config
            if not force_refresh and latest_result.final_config:
                try:
                    final_config = latest_result.final_config
                    if isinstance(final_config, str):
                        import json
                        final_config = json.loads(final_config)
                    
                    # 🔥 简化逻辑：只有final_config包含明确的更新时间戳时才使用
                    # 否则优先使用synthesis_plan（角色同步后的最新数据）
                    if (final_config.get('synthesis_json') and 
                        final_config.get('last_updated')):
                        
                        # 有明确更新时间的final_config，认为是用户手动编辑的最新数据
                        result_data["synthesis_json"] = final_config['synthesis_json']
                        result_data["processing_info"]["data_source"] = "final_config"
                        result_data["processing_info"]["user_edited"] = True
                        logger.info(f"使用final_config数据 (手动编辑于: {final_config.get('last_updated')})")
                    else:
                        # 没有时间戳的final_config认为是过期数据，使用synthesis_plan
                        result_data["processing_info"]["data_source"] = "synthesis_plan"
                        result_data["processing_info"]["user_edited"] = False
                        logger.info("final_config缺少时间戳，使用synthesis_plan数据（角色同步后的最新数据）")
                    
                    if final_config.get('processing_info'):
                        result_data["processing_info"].update(final_config['processing_info'])
                    
                except Exception as e:
                    logger.warning(f"解析final_config失败，使用synthesis_plan: {str(e)}")
                    result_data["processing_info"]["data_source"] = "synthesis_plan"
                    result_data["processing_info"]["user_edited"] = False
            else:
                if force_refresh:
                    logger.info("🔄 [强制刷新] 忽略final_config缓存，使用最新synthesis_plan数据")
                result_data["processing_info"]["data_source"] = "synthesis_plan"
                result_data["processing_info"]["user_edited"] = False
            
            return {
                "success": True,
                "data": result_data,
                "message": "智能准备结果获取成功"
            }
            
        except Exception as e:
            # 兼容旧版本：如果没有AnalysisResult模型，尝试从章节字段获取
            analysis_result = chapter.analysis_results[0].original_analysis if chapter.analysis_results else None
            if not analysis_result:
                raise HTTPException(status_code=404, detail="该章节尚未完成智能准备")
            
            try:
                import json
                if isinstance(analysis_result, str):
                    result_data = json.loads(analysis_result)
                else:
                    result_data = analysis_result
                
                return {
                    "success": True,
                    "data": result_data,
                    "message": "智能准备结果获取成功"
                }
            except Exception as e:
                logger.error(f"解析章节分析结果失败: {str(e)}")
                raise HTTPException(status_code=500, detail="智能准备结果数据格式错误")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取智能准备结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取智能准备结果失败: {str(e)}")


# 🔥 新增：缓存管理API
@router.delete("/cache/{chapter_id}")
async def clear_preparation_cache(
    chapter_id: int,
    cache_type: str = Query("final_config", description="缓存类型: final_config | all"),
    db: Session = Depends(get_db)
):
    """
    清除章节的缓存数据
    
    Args:
        chapter_id: 章节ID
        cache_type: 缓存类型
            - final_config: 只清除用户编辑缓存
            - all: 清除所有缓存（将重新智能准备）
    """
    try:
        from sqlalchemy.orm.attributes import flag_modified
        
        # 查找最新的智能准备结果
        result = db.query(AnalysisResult).filter(
            AnalysisResult.chapter_id == chapter_id,
            AnalysisResult.status == 'completed'
        ).order_by(AnalysisResult.created_at.desc()).first()
        
        if not result:
            raise HTTPException(status_code=404, detail="未找到智能准备结果")
        
        if cache_type == "final_config":
            # 只清除final_config缓存
            result.final_config = None
            flag_modified(result, 'final_config')
            message = "已清除用户编辑缓存，将显示最新的智能准备结果"
        elif cache_type == "all":
            # 清除所有缓存，标记为需要重新分析
            result.status = 'pending'
            result.final_config = None
            result.synthesis_plan = None
            flag_modified(result, 'final_config')
            flag_modified(result, 'synthesis_plan')
            message = "已清除所有缓存，需要重新进行智能准备"
        else:
            raise HTTPException(status_code=400, detail="不支持的缓存类型")
        
        db.commit()
        
        logger.info(f"🗑️ [缓存清理] 章节{chapter_id}的{cache_type}缓存已清除")
        
        return {
            "success": True,
            "data": {
                "chapter_id": chapter_id,
                "cache_type": cache_type,
                "cleared_at": result.updated_at.isoformat()
            },
            "message": message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清除缓存失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")


@router.put("/result/{chapter_id}")
async def update_preparation_result(
    chapter_id: int,
    update_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    更新章节的智能准备结果
    允许用户编辑和修正AI分析的结果
    """
    try:
        # 获取章节
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 🔥 新增：获取书籍ID用于后续角色语音同步
        book_id = chapter.book_id
        
        # 尝试找到现有的分析结果
        try:
            
            # 查找最新的智能准备结果
            latest_result = db.query(AnalysisResult).filter(
                AnalysisResult.chapter_id == chapter_id,
                AnalysisResult.status == 'completed'
            ).order_by(AnalysisResult.created_at.desc()).first()
            
            if not latest_result:
                raise HTTPException(status_code=404, detail="该章节尚未完成智能准备，无法更新")
            
            # 更新结果数据
            if 'synthesis_json' in update_data:
                latest_result.synthesis_plan = update_data['synthesis_json']
            
            # 更新final_config以保存完整的编辑后数据
            import json
            from sqlalchemy import func
            from datetime import datetime
            
            # 🔥 添加时间戳，确保API能够正确识别手动编辑的数据
            update_data['last_updated'] = datetime.utcnow().isoformat()
            
            latest_result.final_config = json.dumps(update_data, ensure_ascii=False)
            latest_result.updated_at = func.now()
            
            # 如果有角色数据，更新detected_characters
            updated_characters = []
            if 'synthesis_json' in update_data and 'characters' in update_data['synthesis_json']:
                characters = update_data['synthesis_json']['characters']
                character_names = [char.get('name', '') for char in characters if char.get('name')]
                latest_result.detected_characters = character_names
                updated_characters = characters
            
            db.commit()
            
            # 🔥 关键修复：更新书籍角色汇总
            # 当用户手动编辑章节分析数据时，需要同步更新书籍的角色汇总
            try:
                if updated_characters:
                    logger.info(f"🔄 [更新书籍角色汇总] 章节 {chapter_id} 的角色数据已更新，同步到书籍汇总")
                    
                    # 更新书籍角色汇总
                    book = db.query(Book).filter(Book.id == book_id).first()
                    if book:
                        book.update_character_summary(updated_characters, chapter_id)
                        db.commit()
                        logger.info(f"✅ [更新书籍角色汇总] 成功更新书籍 {book_id} 的角色汇总")
                    else:
                        logger.warning(f"⚠️ [更新书籍角色汇总] 未找到书籍 {book_id}")
                        
            except Exception as summary_error:
                logger.warning(f"⚠️ [更新书籍角色汇总] 更新失败: {str(summary_error)}")
                # 汇总更新失败不影响主要的保存功能
            
            # 🔥 新增：自动触发角色语音配置同步
            # 提取角色语音映射并同步到所有相关章节的synthesis_plan
            updated_chapters_count = 0
            try:
                if updated_characters:
                    # 构建角色语音映射
                    character_voice_mappings = {}
                    for char in updated_characters:
                        if char.get('voice_id') and char.get('name'):
                            character_voice_mappings[char['name']] = str(char['voice_id'])
                    
                    logger.info(f"🔄 [自动同步] 从编辑结果中提取到角色映射: {character_voice_mappings}")
                    
                    if character_voice_mappings:
                        # 导入同步函数
                        from ..books import _sync_character_voice_to_synthesis_plans
                        
                        # 同步角色语音配置到相关章节
                        updated_chapters_count = await _sync_character_voice_to_synthesis_plans(
                            book_id, character_voice_mappings, db
                        )
                        
                        logger.info(f"✅ [自动同步] 成功同步角色配置到 {updated_chapters_count} 个章节")
                        
            except Exception as sync_error:
                logger.warning(f"⚠️ [自动同步] 角色语音配置同步失败: {str(sync_error)}")
                # 同步失败不影响主要的保存功能
                updated_chapters_count = 0
            
            logger.info(f"已更新章节 {chapter_id} 的智能准备结果，同步了 {updated_chapters_count} 个章节")
            
            return {
                "success": True,
                "data": {
                    "result_id": latest_result.id,
                    "updated_at": latest_result.updated_at.isoformat(),
                    "characters_count": len(latest_result.detected_characters) if latest_result.detected_characters else 0,
                    "segments_count": len(update_data.get('synthesis_json', {}).get('synthesis_plan', [])),
                    "synced_chapters": updated_chapters_count  # 🔥 新增：返回同步的章节数量
                },
                "message": f"智能准备结果更新成功，已自动同步 {updated_chapters_count} 个章节的角色配置"
            }
            
        except Exception as e:
            # 如果没有AnalysisResult模型，尝试更新章节字段
            try:
                import json
                chapter.analysis_results[0].original_analysis = json.dumps(update_data, ensure_ascii=False)
                db.commit()
                
                from datetime import datetime
                return {
                    "success": True,
                    "data": {
                        "chapter_id": chapter_id,
                        "updated_at": datetime.now().isoformat()
                    },
                    "message": "智能准备结果更新成功"
                }
            except Exception as e:
                logger.error(f"更新章节分析结果失败: {str(e)}")
                raise HTTPException(status_code=500, detail="更新智能准备结果失败")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新智能准备结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新智能准备结果失败: {str(e)}")


@router.post("/ai-resegment")
async def ai_resegment_text(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    使用AI大模型重新分段文本
    正确分离对话和旁白，解决"某某说"的分段问题
    """
    try:
        text = request_data.get("text", "")
        characters = request_data.get("characters", [])
        chapter_id = request_data.get("chapter_id")
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="文本内容不能为空")
        
        # 构建AI提示词
        prompt = f"""请将以下小说文本重新分段，正确分离对话和旁白。

规则：
1. "某某说："这种描述性文字应该归为【旁白】
2. 引号""内的内容才是该角色的【对话】
3. 其他描述性文字都归为【旁白】

已知角色：{', '.join(characters)}

请将文本分段，每段标明说话人，格式如下：
[说话人]：文本内容

原文：
{text}

重新分段结果："""

        logger.info(f"AI重新分段请求，文本长度: {len(text)}")
        
        # 这里应该调用AI服务，暂时用模拟结果
        # TODO: 集成实际的AI模型调用
        
        # 模拟AI分段结果 - 正确处理对话分离
        segments = []
        
        # 简单的规则处理，先作为占位符
        import re
        
        # 按句子分割
        sentences = re.split(r'[。！？]', text)
        segment_id = 1
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            # 检查是否包含对话
            if '：' in sentence and '"' in sentence:
                # 分离描述和对话
                parts = sentence.split('：', 1)
                if len(parts) == 2:
                    desc_part = parts[0].strip() + '：'
                    dialog_part = parts[1].strip()
                    
                    # 添加描述部分（旁白）
                    segments.append({
                        "segment_id": segment_id,
                        "speaker": "旁白",
                        "text": desc_part,
                        "voice_name": "系统旁白",
                        "parameters": {"timeStep": 0.5, "pWeight": 0.5, "tWeight": 0.5}
                    })
                    segment_id += 1
                    
                    # 提取引号内的内容
                    dialog_match = re.search(r'"([^"]*)"', dialog_part)
                    if dialog_match:
                        dialog_text = dialog_match.group(1)
                        
                        # 尝试从描述中提取角色名
                        speaker_name = "旁白"
                        for char in characters:
                            if char in desc_part:
                                speaker_name = char
                                break
                        
                        segments.append({
                            "segment_id": segment_id,
                            "speaker": speaker_name,
                            "text": f'"{dialog_text}"',
                            "voice_name": speaker_name,
                            "parameters": {"timeStep": 0.5, "pWeight": 0.5, "tWeight": 0.5}
                        })
                        segment_id += 1
                    
                    # 处理引号后的其他内容
                    remaining = re.sub(r'"[^"]*"', '', dialog_part).strip()
                    if remaining:
                        segments.append({
                            "segment_id": segment_id,
                            "speaker": "旁白",
                            "text": remaining,
                            "voice_name": "系统旁白",
                            "parameters": {"timeStep": 0.5, "pWeight": 0.5, "tWeight": 0.5}
                        })
                        segment_id += 1
            else:
                # 普通描述性文字，归为旁白
                segments.append({
                    "segment_id": segment_id,
                    "speaker": "旁白",
                    "text": sentence.strip() + "。",
                    "voice_name": "系统旁白",
                    "parameters": {"timeStep": 0.5, "pWeight": 0.5, "tWeight": 0.5}
                })
                segment_id += 1
        
        logger.info(f"AI重新分段完成，生成 {len(segments)} 个片段")
        
        return {
            "success": True,
            "data": {
                "segments": segments,
                "total_segments": len(segments),
                "processing_info": {
                    "method": "ai_resegment",
                    "original_length": len(text),
                    "characters_found": len(characters)
                }
            },
            "message": f"AI重新分段完成，生成 {len(segments)} 个片段"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI重新分段失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI重新分段失败: {str(e)}")


# ==================== 智能检测相关API ====================

class DetectionRequest(BaseModel):
    """智能检测请求模型"""
    use_ai: bool = True
    auto_fix: bool = False

class SingleSegmentDetectionRequest(BaseModel):
    """单段落检测请求模型"""
    segment_text: str
    segment_index: Optional[int] = 0


@router.post("/detect/segment")
async def detect_single_segment(
    request: SingleSegmentDetectionRequest,
    db: Session = Depends(get_db)
):
    """
    🔥 新增：单段落智能检测
    专门用于检测单个段落是否需要拆分（如"太监假尖着嗓子喊道：陛下！楚军已逼近函谷关！"）
    
    Args:
        request: 单段落检测请求
            - segment_text: 要检测的段落文本
            - segment_index: 段落索引（可选）
    
    Returns:
        检测结果，包含拆分建议
    """
    try:
        # 创建检测服务
        detection_service = IntelligentDetectionService()
        
        # 执行单段落检测
        issues = await detection_service.detect_single_segment_issues(
            request.segment_text, 
            request.segment_index
        )
        
        return {
            "success": True,
            "segment_text": request.segment_text,
            "issues": [
                {
                    "issue_type": issue.issue_type,
                    "severity": issue.severity,
                    "segment_index": issue.segment_index,
                    "description": issue.description,
                    "suggestion": issue.suggestion,
                    "context": issue.context,
                    "fixable": issue.fixable,
                    "fix_data": issue.fix_data
                } for issue in issues
            ],
            "total_issues": len(issues),
            "split_needed": len(issues) > 0
        }
        
    except Exception as e:
        logger.error(f"单段落检测失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"单段落检测失败: {str(e)}")


@router.post("/detect/{chapter_id}")
async def detect_chapter_issues(
    chapter_id: int,
    request: DetectionRequest = Body(default=DetectionRequest()),
    db: Session = Depends(get_db)
):
    """
    执行章节内容智能检测
    检测智能准备后可能存在的问题
    
    Args:
        chapter_id: 章节ID
        request: 检测请求参数
            - use_ai: 是否使用AI检测
            - auto_fix: 是否自动修复可修复的问题
    
    Returns:
        检测结果，包含问题列表和统计信息
    """
    try:
        # 获取章节
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 检查是否已完成智能准备
        if not chapter.analysis_results:
            raise HTTPException(status_code=400, detail="章节尚未完成智能准备，无法进行检测")
        
        # 创建检测服务
        detection_service = IntelligentDetectionService()
        
        # 执行检测
        detection_result = await detection_service.detect_chapter_issues(
            chapter_id=chapter_id,
            enable_ai_detection=request.use_ai
        )
        
        # 如果启用自动修复
        fixed_segments = None
        fix_logs = []
        if request.auto_fix and detection_result.issues:
            # 这里可以添加自动修复逻辑，目前先跳过
            pass
        
        # 计算统计信息
        critical_count = sum(1 for issue in detection_result.issues if issue.severity == 'critical')
        warning_count = sum(1 for issue in detection_result.issues if issue.severity == 'warning')
        info_count = sum(1 for issue in detection_result.issues if issue.severity == 'info')
        fixable_count = sum(1 for issue in detection_result.issues if issue.fixable)
        
        # 转换DetectionResult对象为字典格式
        result_dict = {
            "chapter_id": detection_result.chapter_id,
            "total_issues": detection_result.total_issues,
            "issues_by_severity": detection_result.issues_by_severity,
            "fixable_issues": detection_result.fixable_issues,
            "fixable_count": fixable_count,
            "stats": {
                "critical_count": critical_count,
                "warning_count": warning_count,
                "info_count": info_count,
                "total_count": len(detection_result.issues)
            },
            "issues": [{
                "issue_type": issue.issue_type,
                "severity": issue.severity,
                "segment_index": issue.segment_index,
                "description": issue.description,
                "suggestion": issue.suggestion,
                "context": issue.context,
                "fixable": issue.fixable,
                "fix_data": issue.fix_data
            } for issue in detection_result.issues],
            "detection_time": detection_result.detection_time
        }
        
        return {
            "success": True,
            "detection_result": result_dict,
            "auto_fix_applied": request.auto_fix and len(fix_logs) > 0,
            "fix_logs": fix_logs,
            "fixed_segments": fixed_segments,
            "message": f"检测完成，发现 {detection_result.total_issues} 个问题"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"智能检测失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"智能检测失败: {str(e)}")


@router.get("/detect/result/{chapter_id}")
async def get_detection_result(
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """
    获取章节的最新检测结果
    
    Args:
        chapter_id: 章节ID
    
    Returns:
        最新的检测结果
    """
    try:
        # 获取章节
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 检查是否有检测结果（这里可以扩展为从数据库存储的检测结果中获取）
        # 目前先返回基本信息，后续可以添加检测结果的持久化存储
        
        return {
            "success": True,
            "chapter_id": chapter_id,
            "has_detection_result": False,
            "message": "暂无检测结果，请先执行检测"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取检测结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取检测结果失败: {str(e)}")


@router.post("/detect/fix/{chapter_id}")
async def apply_detection_fixes(
    chapter_id: int,
    fix_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    应用检测问题的修复
    
    Args:
        chapter_id: 章节ID
        fix_data: 修复数据
            - issues: 要修复的问题列表（单个问题修复）
            - fixed_segments: 修复后的片段数据（批量修复）
    
    Returns:
        修复结果
    """
    try:
        # 获取章节
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 支持两种修复模式：单个问题修复和批量修复
        issues_to_fix = fix_data.get('issues', [])
        fixed_segments = fix_data.get('fixed_segments', [])
        
        # 如果是单个问题修复模式
        if issues_to_fix and not fixed_segments:
            logger.info(f"开始单个问题修复，章节ID: {chapter_id}, 问题数量: {len(issues_to_fix)}")
            
            # 获取当前章节的分析结果
            analysis_result = db.query(AnalysisResult).filter(
                AnalysisResult.chapter_id == chapter_id
            ).order_by(AnalysisResult.created_at.desc()).first()
            
            if not analysis_result:
                logger.error(f"未找到章节 {chapter_id} 的分析结果")
                raise HTTPException(status_code=400, detail="未找到章节的分析结果")
            
            if not analysis_result.synthesis_plan:
                logger.error(f"章节 {chapter_id} 的分析结果中没有合成计划")
                raise HTTPException(status_code=400, detail="未找到章节的合成计划")
            
            # 确保synthesis_plan是字典类型
            if not isinstance(analysis_result.synthesis_plan, dict):
                logger.error(f"章节 {chapter_id} 的合成计划不是字典类型: {type(analysis_result.synthesis_plan)}")
                raise HTTPException(status_code=400, detail="合成计划格式错误")
            
            # 应用单个问题的修复
            # 🔧 修复：正确获取segments数据，支持两种数据结构
            current_segments = analysis_result.synthesis_plan.get('synthesis_plan', [])
            if not current_segments:
                # 兼容旧的数据结构
                current_segments = analysis_result.synthesis_plan.get('segments', [])
            logger.info(f"当前片段数量: {len(current_segments)}")

            # 如果没有片段数据，则无需尝试修复任何问题
            if not current_segments:
                error_detail = f"章节 {chapter_id} 的合成计划中没有片段数据，无法应用修复。请先执行章节分析以生成片段数据。"
                logger.warning(error_detail)
                raise HTTPException(status_code=400, detail=error_detail)
            
            # 检查是否有可修复的问题
            if not issues_to_fix:
                logger.warning(f"章节 {chapter_id} 没有提供可修复的问题")
                return {
                    "success": False,
                    "message": "没有提供可修复的问题",
                        "details": "请检查修复数据"
                    }

            fixed_count = 0
            
            for i, issue in enumerate(issues_to_fix):
                logger.info(f"处理问题 {i+1}: {issue}")
                
                if issue.get('fixable') and issue.get('fix_data'):
                    segment_index = issue.get('segment_index')
                    logger.info(f"问题的片段索引: {segment_index}")
                    if segment_index is None:
                        logger.warning(f"问题 {i+1} 缺少片段索引")
                        continue
                    
                    if 0 <= segment_index < len(current_segments):
                        # 应用修复数据
                        fix_data_content = issue.get('fix_data', {})
                        if fix_data_content:
                            logger.info(f"应用修复数据到片段 {segment_index}: {fix_data_content}")
                            
                            # 🔥 关键修复：根据action类型正确应用修复
                            action = fix_data_content.get('action')
                            success = False
                            
                            # 🔥 移除assign_voice_type：不再检测语音类型问题
                            if action == 'assign_voice_type':
                                # 已移除：voice_type不影响核心合成功能
                                success = True
                                logger.info(f"跳过语音类型设置（已移除检测）")
                            
                            elif action == 'clean_special_chars':
                                # 清理特殊字符
                                text = current_segments[segment_index]['text']
                                chars_to_clean = fix_data_content.get('chars', [])
                                for char in chars_to_clean:
                                    text = text.replace(char, '')
                                current_segments[segment_index]['text'] = text.strip()
                                success = True
                                logger.info(f"清理特殊字符: {chars_to_clean}")
                            
                            elif action == 'set_character':
                                # 设置角色
                                character = fix_data_content.get('character', '')
                                text_type = fix_data_content.get('text_type', 'dialogue')
                                current_segments[segment_index]['speaker'] = character
                                current_segments[segment_index]['character'] = character  # 兼容性
                                current_segments[segment_index]['text_type'] = text_type
                                if text_type == 'dialogue' and character:
                                    if not current_segments[segment_index].get('voice_type'):
                                        current_segments[segment_index]['voice_type'] = 'default'
                                success = True
                                logger.info(f"设置角色: '{character}', 文本类型: {text_type}")
                            
                            elif action == 'set_narration':
                                # 设置为旁白
                                current_segments[segment_index]['text_type'] = 'narration'
                                current_segments[segment_index]['speaker'] = ''
                                current_segments[segment_index]['character'] = ''
                                current_segments[segment_index]['voice_type'] = ''
                                success = True
                                logger.info("设置为旁白")
                            
                            else:
                                logger.warning(f"未知的修复动作: {action}")
                                success = False
                            
                            if success:
                                fixed_count += 1
                        else:
                            logger.warning(f"问题 {i+1} 的修复数据为空")
                    else:
                        logger.warning(f"问题 {i+1} 的片段索引 {segment_index} 超出范围 [0, {len(current_segments)-1}]")
                else:
                    logger.warning(f"问题 {i+1} 不可修复或缺少修复数据")
            
            if fixed_count == 0:
                error_detail = "没有成功修复任何问题。请检查提供的修复数据（如 segment_index 是否正确，fixable 是否为 True，fix_data 是否有效）。"
                logger.error(error_detail)
                raise HTTPException(status_code=400, detail=error_detail)
            
            # 更新分析结果
            import json
            from datetime import datetime
            
            # 🔧 修复：正确更新synthesis_plan数据结构
            synthesis_plan_copy = analysis_result.synthesis_plan.copy() if analysis_result.synthesis_plan else {}
            
            # 更新synthesis_plan中的segments数据
            if 'synthesis_plan' in synthesis_plan_copy:
                synthesis_plan_copy['synthesis_plan'] = current_segments
            else:
                # 兼容旧的数据结构
                synthesis_plan_copy['segments'] = current_segments
            
            # 更新synthesis_plan本身
            analysis_result.synthesis_plan = synthesis_plan_copy
            
            # 🔥 关键修复：正确更新final_config，保持与检测逻辑一致的数据结构和格式
            if analysis_result.final_config:
                try:
                    # 如果已有final_config，解析并更新
                    if isinstance(analysis_result.final_config, str):
                        final_config_data = json.loads(analysis_result.final_config)
                    else:
                        final_config_data = analysis_result.final_config
                    
                    # 确保有正确的数据结构
                    if 'synthesis_json' not in final_config_data:
                        final_config_data['synthesis_json'] = {}
                    
                    # 更新synthesis_plan数据
                    final_config_data['synthesis_json']['synthesis_plan'] = current_segments
                    final_config_data['synthesis_json']['total_segments'] = len(current_segments)
                    final_config_data['last_updated'] = datetime.now().isoformat()
                    final_config_data['updated_by'] = 'detection_fix'
                    
                    # 保存为JSON字符串
                    analysis_result.final_config = json.dumps(final_config_data, ensure_ascii=False)
                    logger.info(f"[修复同步] 已更新final_config数据结构，段落数: {len(current_segments)}")
                    
                except Exception as e:
                    logger.error(f"[修复同步] 更新final_config失败: {str(e)}，回退到创建新结构")
                    # 创建新的final_config结构
                    final_config_data = {
                        'synthesis_json': {
                            'synthesis_plan': current_segments,
                            'total_segments': len(current_segments)
                        },
                        'last_updated': datetime.now().isoformat(),
                        'updated_by': 'detection_fix'
                    }
                    analysis_result.final_config = json.dumps(final_config_data, ensure_ascii=False)
            else:
                # 如果没有final_config，创建新的结构
                final_config_data = {
                    'synthesis_json': {
                        'synthesis_plan': current_segments,
                        'total_segments': len(current_segments)
                    },
                    'last_updated': datetime.now().isoformat(),
                    'updated_by': 'detection_fix'
                }
                analysis_result.final_config = json.dumps(final_config_data, ensure_ascii=False)
                logger.info(f"[修复同步] 创建新final_config数据结构，段落数: {len(current_segments)}")
            db.commit()
            
            logger.info(f"单个问题修复成功，修复了 {fixed_count} 个问题")
            
            return {
                "success": True,
                "message": f"成功修复 {fixed_count} 个问题",
                "data": {
                    "fixed_count": fixed_count,
                    "fixed_issues": fixed_count
                }
            }
        
        # 批量修复模式
        elif fixed_segments:
            try:
                # 获取AnalysisResult
                analysis_result = db.query(AnalysisResult).filter(
                    AnalysisResult.chapter_id == chapter_id
                ).order_by(AnalysisResult.created_at.desc()).first()
                
                if not analysis_result:
                    logger.error(f"未找到章节 {chapter_id} 的分析结果")
                    raise HTTPException(status_code=404, detail="未找到分析结果")
                
                # 更新final_config以标记为用户编辑
                import json
                from datetime import datetime
                
                final_config = analysis_result.synthesis_plan.copy() if analysis_result.synthesis_plan else {}
                final_config.update({
                    'synthesis_plan': fixed_segments,
                    'total_segments': len(fixed_segments),
                    'last_updated': datetime.now().isoformat(),
                    'updated_by': 'detection_fix'
                })
                
                analysis_result.final_config = final_config
                db.commit()
                
                logger.info(f"批量修复成功，更新了 {len(fixed_segments)} 个片段")
                
                return {
                    "success": True,
                    "message": f"成功应用修复，更新了 {len(fixed_segments)} 个片段",
                    "data": {
                        "fixed_count": len(fixed_segments),
                        "updated_segments": len(fixed_segments)
                    }
                }
            except HTTPException:
                db.rollback()
                raise
            except Exception as e:
                db.rollback()
                logger.error(f"批量修复处理失败: {str(e)}")
                raise HTTPException(status_code=500, detail=f"批量修复处理失败: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail="请提供要修复的问题列表或修复后的片段数据")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"应用修复失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"应用修复失败: {str(e)}")