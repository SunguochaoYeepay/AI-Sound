"""
内容准备API
提供小说章节语音合成前的智能内容准备功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging

from app.database import get_db
from app.models import BookChapter
from app.services.content_preparation_service import ContentPreparationService

router = APIRouter(prefix="/content-preparation")
logger = logging.getLogger(__name__)

# 服务实例将在每个请求中创建


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
    auto_add_narrator: bool = Query(True, description="是否自动添加旁白角色"),
    processing_mode: Optional[str] = Query("auto", description="处理模式: auto, fast, detailed"),
    db: Session = Depends(get_db)
):
    """
    智能准备章节用于语音合成
    
    核心功能：
    1. 智能文本分块（最大3000 tokens）
    2. 角色对话检测和分离
    3. 自动添加旁白角色
    4. 生成语音合成配置
    5. 输出JSON格式数据
    
    参数：
    - auto_add_narrator: 是否自动添加旁白角色
    - processing_mode: 处理模式（auto/fast/detailed）
    """
    try:
        # 获取章节
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 创建服务实例并执行智能准备
        content_prep_service = ContentPreparationService(db)
        result = await content_prep_service.prepare_chapter_for_synthesis(
            chapter_id=chapter_id,
            user_preferences={
                "auto_add_narrator": auto_add_narrator,
                "processing_mode": processing_mode
            }
        )
        
        return {
            "success": True,
            "data": result,
            "message": "章节智能准备完成"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"章节智能准备失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"章节智能准备失败: {str(e)}")


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
            
            # 构建返回数据
            result_data = {
                "synthesis_json": latest_result.synthesis_plan or {},
                "processing_info": {
                    "mode": "stored",
                    "total_segments": len(latest_result.synthesis_plan.get('synthesis_plan', [])) if latest_result.synthesis_plan else 0,
                    "characters_found": len(latest_result.detected_characters) if latest_result.detected_characters else 0,
                    "saved_to_database": True,
                    "result_id": latest_result.id,
                    "created_at": latest_result.created_at.isoformat() if latest_result.created_at else None,
                    "completed_at": latest_result.completed_at.isoformat() if latest_result.completed_at else None
                },
                "last_updated": latest_result.updated_at.isoformat() if latest_result.updated_at else latest_result.created_at.isoformat()
            }
            
            # 如果有final_config，优先使用其中的数据
            if latest_result.final_config:
                try:
                    final_config = latest_result.final_config
                    if isinstance(final_config, str):
                        import json
                        final_config = json.loads(final_config)
                    
                    if final_config.get('synthesis_json'):
                        result_data["synthesis_json"] = final_config['synthesis_json']
                    
                    if final_config.get('processing_info'):
                        result_data["processing_info"].update(final_config['processing_info'])
                        
                except Exception as e:
                    logger.warning(f"解析final_config失败: {str(e)}")
            
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