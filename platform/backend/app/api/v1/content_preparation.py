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
from app.models import BookChapter, Book
from app.services.content_preparation_service import ContentPreparationService

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
    db: Session = Depends(get_db)
):
    """
    获取章节的已有智能准备结果
    不重新执行智能准备，只返回已存储的结果
    """
    try:
        # 获取章节
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 检查是否有智能准备结果
        try:
            from app.models import AnalysisResult
            
            # 查找最新的智能准备结果
            latest_result = db.query(AnalysisResult).filter(
                AnalysisResult.chapter_id == chapter_id,
                AnalysisResult.status == 'completed'
            ).order_by(AnalysisResult.created_at.desc()).first()
            
            if not latest_result:
                raise HTTPException(status_code=404, detail="该章节尚未完成智能准备")
            
            # 🔥 关键修复：强制应用最新的角色语音配置
            synthesis_plan = latest_result.synthesis_plan or {}
            
            # 获取书籍的最新角色语音配置
            try:
                from app.models import Book
                book = db.query(Book).join(BookChapter).filter(BookChapter.id == chapter_id).first()
                if book:
                    character_summary = book.get_character_summary()
                    if isinstance(character_summary, dict) and 'voice_mappings' in character_summary:
                        voice_mappings = character_summary['voice_mappings']
                        logger.info(f"📋 [缓存结果] 应用最新角色配置: {voice_mappings}")
                        
                        # 强制同步角色配置到synthesis_plan
                        if 'synthesis_plan' in synthesis_plan and voice_mappings:
                            # 🔥 修复：优先从角色配音库获取voice_name，然后才从VoiceProfile获取
                            voice_id_to_name = {}
                            
                            # 1. 先从角色配音库获取映射
                            try:
                                from app.models import Character
                                characters = db.query(Character).filter(Character.book_id == book.id).all()
                                for char in characters:
                                    voice_id_to_name[str(char.id)] = char.name
                                logger.info(f"📚 [缓存同步] 从角色配音库获取映射: {voice_id_to_name}")
                            except Exception as e:
                                logger.warning(f"获取角色配音库映射失败: {str(e)}")
                            
                            # 2. 再从VoiceProfile获取剩余的映射
                            try:
                                from app.models import VoiceProfile
                                voices = db.query(VoiceProfile).filter(VoiceProfile.status == 'active').all()
                                for v in voices:
                                    if str(v.id) not in voice_id_to_name:  # 只添加角色配音库中没有的
                                        voice_id_to_name[str(v.id)] = v.name
                                logger.info(f"🎙️ [缓存同步] 添加VoiceProfile映射，总映射数: {len(voice_id_to_name)}")
                            except Exception as e:
                                logger.warning(f"获取VoiceProfile映射失败: {str(e)}")
                            
                            # 更新每个segment的voice配置（使用智能匹配）
                            segments = synthesis_plan['synthesis_plan']
                            for segment in segments:
                                speaker = segment.get('speaker', '')
                                
                                # 🔥 智能角色匹配：支持精确匹配和模糊匹配
                                matched_voice_id = None
                                matched_character_name = None
                                
                                # 1. 精确匹配
                                if speaker in voice_mappings:
                                    matched_voice_id = voice_mappings[speaker]
                                    matched_character_name = speaker
                                
                                # 2. 模糊匹配（如果精确匹配失败）
                                elif speaker:
                                    for config_name, voice_id in voice_mappings.items():
                                        # 检查是否为相似角色名（如"太监"和"太监假"）
                                        if (speaker in config_name) or (config_name in speaker):
                                            matched_voice_id = voice_id
                                            matched_character_name = config_name
                                            logger.info(f"🔍 [API模糊匹配] 角色 '{speaker}' 匹配到配置角色 '{config_name}': voice_id={voice_id}")
                                            break
                                        
                                        # 检查去除常见后缀后是否匹配
                                        clean_speaker = speaker.rstrip('假临时备用')
                                        clean_config = config_name.rstrip('假临时备用')
                                        if clean_speaker == clean_config and len(clean_speaker) > 1:
                                            matched_voice_id = voice_id
                                            matched_character_name = config_name
                                            logger.info(f"🧹 [API后缀匹配] 角色 '{speaker}' 通过去除后缀匹配到 '{config_name}': voice_id={voice_id}")
                                            break
                                
                                if matched_voice_id:
                                    new_voice_name = voice_id_to_name.get(str(matched_voice_id), f"Voice_{matched_voice_id}")
                                    segment['voice_id'] = matched_voice_id
                                    segment['voice_name'] = new_voice_name
                                    logger.info(f"✅ [缓存同步] {speaker} (通过{matched_character_name}配置): voice_id={matched_voice_id}, voice_name={new_voice_name}")
                        
                        # 更新characters配置
                        if 'characters' in synthesis_plan and voice_mappings:
                            for character in synthesis_plan['characters']:
                                char_name = character.get('name', '')
                                if char_name in voice_mappings:
                                    new_voice_id = voice_mappings[char_name]
                                    new_voice_name = voice_id_to_name.get(str(new_voice_id), char_name)  # 🔥 修复：如果找不到映射，使用角色名本身
                                    character['voice_id'] = new_voice_id
                                    character['voice_name'] = new_voice_name
                                    logger.info(f"✅ [角色同步] {char_name}: voice_id={new_voice_id}, voice_name={new_voice_name}")
                        
                        logger.info("🔄 [缓存结果] 已应用最新角色语音配置")
                    else:
                        logger.info("📋 [缓存结果] 书籍暂无角色配置，使用原始数据")
                else:
                    logger.warning("📋 [缓存结果] 无法找到对应书籍，使用原始数据")
            except Exception as e:
                logger.warning(f"应用最新角色配置失败: {str(e)}，使用原始数据")
            
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
                    "voice_sync_applied": True  # 标记已应用语音同步
                },
                "last_updated": latest_result.updated_at.isoformat() if latest_result.updated_at else latest_result.created_at.isoformat()
            }
            
            # 🔥 CRITICAL FIX: 智能处理final_config，优先返回最新数据
            if latest_result.final_config:
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
                        logger.info(f"使用final_config数据 (手动编辑于: {final_config.get('last_updated')})")
                    else:
                        # 没有时间戳的final_config认为是过期数据，使用synthesis_plan
                        logger.info("final_config缺少时间戳，使用synthesis_plan数据（角色同步后的最新数据）")
                    
                    if final_config.get('processing_info'):
                        result_data["processing_info"].update(final_config['processing_info'])
                        
                except Exception as e:
                    logger.warning(f"解析final_config失败，使用synthesis_plan数据: {str(e)}")
            
            return {
                "success": True,
                "data": result_data,
                "message": "智能准备结果获取成功"
            }
            
        except ImportError:
            # 如果没有AnalysisResult模型，尝试从章节字段获取
            analysis_result = getattr(chapter, 'character_analysis_result', None)
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
            from app.models import AnalysisResult
            
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
            
        except ImportError:
            # 如果没有AnalysisResult模型，尝试更新章节字段
            try:
                import json
                chapter.character_analysis_result = json.dumps(update_data, ensure_ascii=False)
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