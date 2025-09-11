"""
章节分析API
提供章节智能分段和6卡分析功能
从原chapters.py中拆分出来的分析相关路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.database import get_db
from app.models import BookChapter, Book, AnalysisResult
from app.utils import log_system_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chapters", tags=["Chapter Analysis"])

@router.post("/{chapter_id}/smart-segmentation")
async def smart_segmentation(
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """智能分段章节内容"""
    try:
        # 获取章节
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")

        # 检查章节是否有内容
        if not chapter.content or len(chapter.content.strip()) == 0:
            raise HTTPException(status_code=400, detail="章节内容为空，无法进行分段")

        # 导入智能分段服务
        from app.services.smart_segmentation_service import SmartSegmentationService

        # 创建分段服务实例
        segmentation_service = SmartSegmentationService()

        # 执行智能分段
        logger.info(f"开始对章节 {chapter_id} 进行智能分段")
        segmentation_result = await segmentation_service.segment_and_save(
            chapter.content,
            chapter_id,
            db
        )

        if segmentation_result["success"]:
            logger.info(f"章节 {chapter_id} 智能分段成功，共生成 {segmentation_result['segmentation_data']['segment_count']} 个段落")
            return {
                "success": True,
                "message": "智能分段完成",
                "data": segmentation_result
            }
        else:
            raise HTTPException(status_code=500, detail=segmentation_result.get("error", "分段失败"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"章节 {chapter_id} 智能分段失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"智能分段失败: {str(e)}")

@router.get("/{chapter_id}/segmentation-result")
async def get_segmentation_result(
    chapter_id: int,
    project_id: int = Query(..., description="分析项目ID"),
    db: Session = Depends(get_db)
):
    """获取章节的分段结果"""
    try:
        # 获取章节
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")

        # 导入智能分段服务
        from app.services.smart_segmentation_service import SmartSegmentationService

        # 创建分段服务实例
        segmentation_service = SmartSegmentationService()

        # 获取缓存的分段结果
        segments = await segmentation_service.get_cached_segments(project_id, chapter_id, db)

        if segments:
            return {
                "success": True,
                "message": "获取分段结果成功",
                "data": {
                    "chapter_id": chapter_id,
                    "chapter_title": chapter.chapter_title,
                    "segments": segments,
                    "segment_count": len(segments)
                }
            }
        else:
            return {
                "success": False,
                "message": "未找到分段结果，请先执行智能分段",
                "data": None
            }

    except Exception as e:
        logger.error(f"获取章节 {chapter_id} 分段结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取分段结果失败: {str(e)}")

@router.post("/{chapter_id}/six-card-analysis")
async def six_card_analysis(
    chapter_id: int,
    request_data: Dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db)
):
    # 从请求体中提取段落索引和session_id
    segment_indices = request_data.get("segment_indices")
    project_id = request_data.get("project_id")
    """对章节的指定段落进行6卡分析"""
    try:
        # 获取章节
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")

        # 导入智能分段服务
        from app.services.smart_segmentation_service import SmartSegmentationService

        # 创建分段服务实例
        segmentation_service = SmartSegmentationService()

        # 获取分段结果
        segments = await segmentation_service.get_cached_segments(project_id, chapter_id, db)
        if not segments:
            raise HTTPException(status_code=400, detail="未找到分段结果，请先执行智能分段")

        # 确定要分析的段落
        if segment_indices is None:
            # 分析所有段落
            target_segments = [(i, segment) for i, segment in enumerate(segments)]
            analysis_type = "all"
        else:
            # 分析指定段落
            target_segments = []
            for idx in segment_indices:
                if 0 <= idx < len(segments):
                    target_segments.append((idx, segments[idx]))
            analysis_type = "selected"

        if not target_segments:
            raise HTTPException(status_code=400, detail="没有有效的段落索引")

        # 导入6卡分析器
        from app.services.six_card_analyzer import SixCardAnalyzer
        from app.detectors.ollama_character_detector import OllamaCharacterDetector

        # 创建分析器实例
        character_detector = OllamaCharacterDetector()
        six_card_analyzer = SixCardAnalyzer()

        # 执行段落分析：先对话分析，再6卡分析
        logger.info(f"开始对章节 {chapter_id} 的 {len(target_segments)} 个段落进行分析")

        analysis_results = []
        for segment_index, segment_text in target_segments:
            try:
                logger.info(f"分析段落 {segment_index + 1}/{len(segments)}")
                
                # 第一步：对话分析和角色识别
                logger.info(f"第一步：对段落 {segment_index + 1} 进行对话分析...")
                chapter_info = {
                    "chapter_id": chapter_id,
                    "chapter_title": f"段落_{segment_index + 1}",
                    "chapter_number": segment_index + 1,
                    "processing_mode": "single"
                }
                dialogue_analysis = await character_detector.analyze_text(segment_text, chapter_info)
                
                # 第二步：6卡分析
                logger.info(f"第二步：对段落 {segment_index + 1} 进行6卡分析...")
                six_card_result = await six_card_analyzer.analyze_segment(segment_text, segment_index, chapter_id)
                
                # 第三步：整合结果
                combined_result = {
                    **six_card_result,
                    "dialogue_analysis": dialogue_analysis,
                    "_metadata": {
                        **six_card_result.get("_metadata", {}),
                        "dialogue_analysis_time": datetime.utcnow().isoformat()
                    }
                }
                
                analysis_results.append(combined_result)
                logger.info(f"段落 {segment_index + 1} 分析完成")
                
            except Exception as e:
                logger.error(f"段落 {segment_index + 1} 分析失败: {str(e)}")
                # 创建失败时的默认结果
                fallback_result = six_card_analyzer._create_fallback_cards(segment_text, segment_index)
                analysis_results.append(fallback_result)

        # 保存分析结果到数据库
        analysis_summary = await save_six_card_analysis_results(
            chapter_id, project_id, analysis_results, analysis_type, db
        )

        logger.info(f"章节 {chapter_id} 6卡分析完成，共分析 {len(analysis_results)} 个段落")

        return {
            "success": True,
            "message": f"6卡分析完成，共分析 {len(analysis_results)} 个段落",
            "data": {
                "chapter_id": chapter_id,
                "chapter_title": chapter.chapter_title,
                "analysis_type": analysis_type,
                "total_segments": len(segments),
                "analyzed_segments": len(analysis_results),
                "results": analysis_results,
                "summary": analysis_summary
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"章节 {chapter_id} 6卡分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"6卡分析失败: {str(e)}")

@router.get("/{chapter_id}/six-card-results")
async def get_six_card_results(
    chapter_id: int,
    project_id: int = Query(..., description="分析项目ID"),
    db: Session = Depends(get_db)
):
    """获取章节的6卡分析结果"""
    try:
        # 获取章节
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")

        # 从数据库获取6卡分析结果
        # 查找包含6卡分析数据的记录
        analysis_result = db.query(AnalysisResult).filter(
            AnalysisResult.project_id == project_id,
            AnalysisResult.chapter_id == chapter_id
        ).first()
        
        # 检查是否有6卡分析数据
        has_six_card_data = False
        if analysis_result and analysis_result.original_analysis:
            # 检查original_analysis中是否包含6卡分析结果
            original_data = analysis_result.original_analysis
            if isinstance(original_data, dict) and 'six_card_results' in original_data:
                has_six_card_data = True
        
        if not has_six_card_data:
            return {
                "success": True,
                "message": "暂无6卡分析结果",
                "data": {
                    "chapter_id": chapter_id,
                    "chapter_title": chapter.chapter_title,
                    "results": [],
                    "analysis_count": 0,
                    "has_results": False
                }
            }
        
        # 返回已保存的分析结果
        analysis_data = analysis_result.original_analysis
        six_card_results = analysis_data.get("six_card_results", [])
        
        # 按段落序号排序
        if six_card_results:
            six_card_results = sorted(
                six_card_results, 
                key=lambda x: x.get("_metadata", {}).get("segment_index", 0)
            )
        
        # 转换数据格式为前端期望的格式
        script_segments = []
        timeline_details = []
        
        for result in six_card_results:
            # 提取synthesis_json作为剧本段落 - 每个段落只创建一个条目
            if "synthesis_json" in result:
                synthesis_data = result["synthesis_json"]
                if "synthesis_plan" in synthesis_data and synthesis_data["synthesis_plan"]:
                    # 只取第一个segment作为代表，避免重复
                    first_segment = synthesis_data["synthesis_plan"][0]
                    script_segments.append({
                        "segment_index": result.get("_metadata", {}).get("segment_index", 0),
                        "text": first_segment.get("text", ""),
                        "speaker": first_segment.get("speaker", ""),
                        "audio_type": first_segment.get("audio_type", "dialogue"),
                        "synthesis_json": synthesis_data
                    })
            
            # 提取audio_storyboard_card作为时间线详情
            if "audio_storyboard_card" in result:
                timeline_details.append({
                    "segment_index": result.get("_metadata", {}).get("segment_index", 0),
                    "audio_storyboard": result["audio_storyboard_card"],
                    "story_card": result.get("story_card", {}),
                    "character_card": result.get("character_card", {}),
                    "scene_card": result.get("scene_card", {}),
                    "event_card": result.get("event_card", {}),
                    "emotion_card": result.get("emotion_card", {}),
                    "audio_script_card": result.get("audio_script_card", {})
                })
        
        return {
            "success": True,
            "message": "获取6卡分析结果成功",
            "data": {
                "chapter_id": chapter_id,
                "chapter_title": chapter.chapter_title,
                "results": six_card_results,
                "script_segments": script_segments,
                "timeline_details": timeline_details,
                "analysis_count": analysis_data.get("six_card_total_results", 0),
                "analysis_type": analysis_data.get("six_card_analysis_type", "unknown"),
                "saved_at": analysis_data.get("six_card_saved_at"),
                "has_results": True
            }
        }

    except Exception as e:
        logger.error(f"获取章节 {chapter_id} 6卡分析结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取6卡分析结果失败: {str(e)}")


def _validate_paragraph_uniqueness(results: List[Dict]) -> bool:
    """验证段落分析结果的唯一性"""
    unique_keys = set()
    for result in results:
        segment_index = result.get("_metadata", {}).get("segment_index")
        chapter_id = result.get("_metadata", {}).get("chapter_id")
        if segment_index is not None and chapter_id is not None:
            # 使用章节ID+段落索引作为唯一标识
            unique_key = f"{chapter_id}_{segment_index}"
            if unique_key in unique_keys:
                logger.error(f"发现重复的段落: 章节 {chapter_id} 段落 {segment_index}")
                return False
            unique_keys.add(unique_key)
        else:
            logger.warning(f"分析结果缺少segment_index或chapter_id元数据: {result}")
    return True


async def save_six_card_analysis_results(chapter_id: int, project_id: int, results: List[Dict], analysis_type: str, db: Session) -> Dict[str, Any]:
    """保存6卡分析结果到数据库"""
    try:
        # 验证段落分析结果的唯一性
        if not _validate_paragraph_uniqueness(results):
            raise ValueError("段落分析结果包含重复的段落索引")
        
        # 检查是否已有分析结果记录
        existing_result = db.query(AnalysisResult).filter(
            AnalysisResult.project_id == project_id,
            AnalysisResult.chapter_id == chapter_id
        ).first()
        
        if existing_result:
            # 更新现有记录，保留已有的智能分段数据
            current_analysis = existing_result.original_analysis or {}
            
            # 获取现有的6卡分析结果
            existing_six_card_results = current_analysis.get("six_card_results", [])
            
            # 建立章节+段落索引到分析结果的映射，确保一个段落只有一个分析结果
            segment_result_map = {}
            
            # 先处理已存在的分析结果
            for result in existing_six_card_results:
                segment_index = result.get("_metadata", {}).get("segment_index")
                result_chapter_id = result.get("_metadata", {}).get("chapter_id")
                if segment_index is not None and result_chapter_id is not None:
                    # 使用章节ID+段落索引作为唯一标识
                    unique_key = f"{result_chapter_id}_{segment_index}"
                    segment_result_map[unique_key] = result
            
            # 用新的分析结果覆盖相同段落的旧结果
            for result in results:
                segment_index = result.get("_metadata", {}).get("segment_index")
                result_chapter_id = result.get("_metadata", {}).get("chapter_id")
                if segment_index is not None and result_chapter_id is not None:
                    # 使用章节ID+段落索引作为唯一标识
                    unique_key = f"{result_chapter_id}_{segment_index}"
                    segment_result_map[unique_key] = result
                    logger.info(f"更新章节 {result_chapter_id} 段落 {segment_index} 的分析结果")
                else:
                    logger.warning(f"分析结果缺少segment_index或chapter_id元数据: {result}")
            
            # 将映射转换回列表
            final_results = list(segment_result_map.values())
            
            # 合并数据，使用去重后的结果
            updated_analysis = {
                **current_analysis,  # 保留现有数据（包括智能分段）
                "six_card_results": final_results,  # 使用去重后的结果
                "six_card_analysis_type": analysis_type,
                "six_card_total_results": len(final_results),
                "six_card_saved_at": datetime.utcnow().isoformat()
            }
            
            existing_result.project_id = project_id  # 确保project_id被正确设置
            existing_result.original_analysis = updated_analysis
            existing_result.updated_at = datetime.utcnow()
            existing_result.status = 'completed'
        else:
            # 创建新记录
            new_result = AnalysisResult(
                project_id=project_id,
                chapter_id=chapter_id,
                original_analysis={
                    "six_card_results": results,
                    "six_card_analysis_type": analysis_type,
                    "six_card_total_results": len(results),
                    "six_card_saved_at": datetime.utcnow().isoformat()
                },
                status='completed',
                processing_time=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(new_result)
        
        # 检查章节分析状态 - 只有当所有段落都分析完成时才设置为completed
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if chapter:
            # 获取该章节的所有段落数量
            from app.services.smart_segmentation_service import SmartSegmentationService
            segmentation_service = SmartSegmentationService()
            segments = await segmentation_service.get_cached_segments(project_id, chapter_id, db)
            total_segments = len(segments) if segments else 0
            
            # 获取已分析的段落数量
            analyzed_count = db.query(AnalysisResult).filter(
                AnalysisResult.chapter_id == chapter_id,
                AnalysisResult.status == 'completed'
            ).count()
            
            # 只有当所有段落都分析完成时，才设置为completed
            if total_segments > 0 and analyzed_count >= total_segments:
                chapter.analysis_status = 'completed'
                logger.info(f"章节 {chapter_id} 所有段落分析完成，状态更新为 completed ({analyzed_count}/{total_segments})")
            else:
                chapter.analysis_status = 'analyzing'
                logger.info(f"章节 {chapter_id} 部分段落分析完成，状态更新为 analyzing ({analyzed_count}/{total_segments})")
            
            chapter.updated_at = datetime.utcnow()
        
        # 提交到数据库
        db.commit()
        
        return {
            "total_results": len(final_results) if existing_result else len(results),
            "analysis_type": analysis_type,
            "saved_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"保存6卡分析结果失败: {str(e)}")
        db.rollback()
        return {
            "total_results": len(results),
            "analysis_type": analysis_type,
            "saved_at": datetime.utcnow().isoformat(),
            "save_error": str(e)
        }
