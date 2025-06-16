"""
智能分析API
基于章节分析的文本分析和角色识别
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
import json
import logging
from datetime import datetime

from app.database import get_db
from app.models import NovelProject, VoiceProfile, Book, TextSegment
from app.exceptions import ServiceException
from app.config import settings
from app.novel_reader import update_segments_voice_mapping_no_commit
from app.services.chapter_analysis_service import ChapterAnalysisService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/intelligent-analysis", tags=["智能分析"])

@router.post("/analyze/{project_id}")
async def analyze_project(
    project_id: int,
    request_data: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """
    基于章节分析结果进行项目智能分析
    返回直接可用的合成计划
    """
    try:
        # 1. 验证项目是否存在
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 基于章节分析的智能分析逻辑
        try:
            # 创建章节分析服务
            chapter_analysis_service = ChapterAnalysisService(db)
            
            # 获取选中的章节ID列表（如果有的话）
            selected_chapter_ids = None
            if request_data and 'chapter_ids' in request_data:
                selected_chapter_ids = request_data['chapter_ids']
                logger.info(f"智能分析将基于选中的章节: {selected_chapter_ids}")
            else:
                logger.info("智能分析将基于项目的所有章节")
            
            # 1. 获取项目关联的章节并检查分析状态
            chapters, status_summary = chapter_analysis_service.get_project_chapters_with_status(project_id, selected_chapter_ids)
            
            # 2. 检查是否所有章节都已完成分析
            if status_summary['pending_chapters'] > 0:
                # 构建详细的错误信息
                pending_chapters = [ch for ch in chapters if not ch['has_analysis']]
                pending_info = []
                for ch in pending_chapters[:5]:  # 最多显示5个
                    pending_info.append(f"第{ch['chapter_number']}章: {ch['chapter_title']}")
                
                error_message = (
                    f"项目还有 {status_summary['pending_chapters']} 个章节未完成智能准备，"
                    f"请先在书籍管理中对以下章节执行'智能准备'：\n" + 
                    "\n".join(pending_info)
                )
                
                if len(pending_chapters) > 5:
                    error_message += f"\n... 等其他 {len(pending_chapters) - 5} 个章节"
                
                return {
                    "success": False,
                    "message": error_message,
                    "data": {
                        "status": "pending_analysis",
                        "total_chapters": status_summary['total_chapters'],
                        "analyzed_chapters": status_summary['analyzed_chapters'],
                        "pending_chapters": status_summary['pending_chapters'],
                        "pending_chapter_list": pending_chapters
                    },
                    "source": "chapter_analysis_validation"
                }
            
            # 3. 聚合选中章节的分析结果
            logger.info(f"开始聚合项目 {project_id} 的章节分析结果")
            aggregated_data = chapter_analysis_service.aggregate_chapter_results(project_id, selected_chapter_ids)
            
            # 4. 转换为合成格式并分配声音
            logger.info(f"开始为项目 {project_id} 分配声音")
            synthesis_result = chapter_analysis_service.convert_to_synthesis_format(aggregated_data)
            
            # 5. 记录成功信息
            logger.info(f"项目 {project_id} 智能分析完成: {synthesis_result['voice_assignment_summary']['total_characters']} 个角色, {len(synthesis_result['synthesis_plan'])} 个段落")
            
            return {
                "success": True,
                "message": "智能分析完成",
                "data": synthesis_result,
                "source": "chapter_analysis"
            }
            
        except ServiceException as e:
            # 业务逻辑异常，返回用户友好的错误信息
            return {
                "success": False,
                "message": str(e),
                "data": {
                    "status": "analysis_error",
                    "error_type": "service_exception"
                },
                "source": "chapter_analysis_error"
            }
        
        except Exception as e:
            # 系统异常，记录详细错误并返回通用错误信息
            logger.error(f"项目 {project_id} 智能分析失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"智能分析失败: {str(e)}")
        
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