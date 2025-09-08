"""
整合分析API
提供结合书籍智能准备和6卡分析的整合分析功能
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from app.database import get_db
from app.services.integrated_analysis_service import IntegratedAnalysisService

router = APIRouter(prefix="/integrated-analysis")
logger = logging.getLogger(__name__)


class IntegratedAnalysisRequest(BaseModel):
    """整合分析请求模型"""
    dialogue_unit_text: str
    dialogue_unit_index: int
    book_id: Optional[int] = None
    chapter_number: Optional[int] = None
    project_name: Optional[str] = None


@router.post("/analyze-paragraph")
async def analyze_paragraph(
    request: IntegratedAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    整合分析段落
    
    结合书籍智能准备的对话分析优势和6卡分析的内容丰富化
    """
    try:
        # 创建正确的整合分析服务
        analysis_service = IntegratedAnalysisService()
        
        # 执行整合分析
        result = await analysis_service.analyze_paragraph(
            paragraph_text=request.dialogue_unit_text,
            paragraph_index=request.dialogue_unit_index,
            chapter_id=request.book_id  # 使用book_id作为chapter_id
        )
        
        # 保存到数据库（兼容现有字段结构）
        try:
            from app.models.analysis_result import AnalysisResult
            from datetime import datetime
            
            logger.info(f"开始保存分析结果到数据库...")
            logger.info(f"数据库会话类型: {type(db)}")
            logger.info(f"分析结果类型: {type(result)}")
            logger.info(f"six_card_analysis: {type(result.get('six_card_analysis', {}))}")
            logger.info(f"characters: {type(result.get('characters', []))}")
            logger.info(f"synthesis_plan: {type(result.get('synthesis_plan', []))}")
            
            # 根据book_id和chapter_number查找chapter_id
            from app.models.book_chapter import BookChapter
            chapter = db.query(BookChapter).filter(
                BookChapter.book_id == request.book_id,
                BookChapter.chapter_number == request.chapter_number
            ).first()
            
            if not chapter:
                raise ValueError(f"找不到书籍{request.book_id}的第{request.chapter_number}章")
            
            analysis_record = AnalysisResult(
                chapter_id=chapter.id,
                original_analysis=result.get("six_card_analysis", {}),
                detected_characters=result.get("characters", []),
                synthesis_plan=result.get("synthesis_plan", []),
                status="completed",
                created_at=datetime.now(),
                completed_at=datetime.now()
            )
            
            logger.info(f"创建分析记录对象: {analysis_record}")
            
            db.add(analysis_record)
            logger.info(f"添加到数据库会话")
            
            db.commit()
            logger.info(f"提交数据库事务")
            
            db.refresh(analysis_record)
            logger.info(f"刷新记录，ID: {analysis_record.id}")
            
            return {
                "success": True,
                "message": f"对话单元 {request.dialogue_unit_index} 整合分析完成",
                "synthesis_json": result,
                "analysis_id": analysis_record.id
            }
            
        except Exception as db_error:
            logger.error(f"数据库保存失败: {str(db_error)}")
            logger.error(f"错误类型: {type(db_error)}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            # 即使数据库保存失败，也返回分析结果
            return {
                "success": True,
                "message": f"对话单元 {request.dialogue_unit_index} 整合分析完成（数据库保存失败）",
                "synthesis_json": result,
                "analysis_id": None,
                "db_error": str(db_error)
            }
        
    except Exception as e:
        logger.error(f"整合分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"整合分析失败: {str(e)}")


@router.post("/analyze-multiple-paragraphs")
async def analyze_multiple_paragraphs(
    paragraphs: list[IntegratedAnalysisRequest],
    db: Session = Depends(get_db)
):
    """
    批量整合分析多个段落
    """
    try:
        # 创建正确的整合分析服务
        analysis_service = IntegratedAnalysisService()
        
        results = []
        for request in paragraphs:
            try:
                result = await analysis_service.analyze_paragraph(
                    paragraph_text=request.dialogue_unit_text,
                    paragraph_index=request.dialogue_unit_index,
                    chapter_id=request.book_id  # 使用book_id作为chapter_id
                )
                results.append({
                    "dialogue_unit_index": request.dialogue_unit_index,
                    "success": True,
                    "synthesis_json": result
                })
            except Exception as e:
                logger.error(f"对话单元 {request.dialogue_unit_index} 分析失败: {str(e)}")
                results.append({
                    "dialogue_unit_index": request.dialogue_unit_index,
                    "success": False,
                    "error": str(e)
                })
        
        success_count = sum(1 for r in results if r["success"])
        
        return {
            "success": True,
            "message": f"批量分析完成，成功 {success_count}/{len(paragraphs)} 个对话单元",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"批量整合分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量整合分析失败: {str(e)}")
