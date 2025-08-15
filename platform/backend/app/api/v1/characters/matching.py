"""角色匹配相关功能路由"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.schemas.character import (
    CharacterMatchRequest,
    CharacterMatchResponse,
    CharacterMatchResult
)
from app.services.character_service import CharacterService
from app.services.character_management_service import CharacterManagementService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/characters/matching", tags=["角色管理-匹配功能"])

@router.post("/match-by-chapter", response_model=List[CharacterMatchResult])
async def match_characters_by_chapter(
    chapter_id: int,
    match_request: CharacterMatchRequest,
    db: Session = Depends(get_db)
):
    """根据章节匹配角色"""
    try:
        # 验证章节是否存在
        from app.models import BookChapter
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 验证匹配参数
        if match_request.similarity_threshold < 0 or match_request.similarity_threshold > 1:
            raise HTTPException(status_code=400, detail="相似度阈值必须在0-1之间")
        
        if match_request.max_matches < 1 or match_request.max_matches > 50:
            raise HTTPException(status_code=400, detail="最大匹配数量必须在1-50之间")
        
        service = CharacterService(db)
        return service.match_characters_by_chapter(chapter_id, match_request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"根据章节匹配角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/apply-matches")
async def apply_character_matches(
    matches: List[CharacterMatchResult],
    auto_create_missing: bool = Body(False, description="是否自动创建缺失的角色"),
    db: Session = Depends(get_db)
):
    """应用角色匹配结果"""
    try:
        if not matches:
            raise HTTPException(status_code=400, detail="匹配结果不能为空")
        
        if len(matches) > 100:
            raise HTTPException(status_code=400, detail="单次最多应用100个匹配结果")
        
        # 验证匹配结果
        for i, match in enumerate(matches):
            if not match.character_name:
                raise HTTPException(
                    status_code=400, 
                    detail=f"第{i+1}个匹配结果的角色名称不能为空"
                )
            
            if match.confidence_score < 0 or match.confidence_score > 1:
                raise HTTPException(
                    status_code=400, 
                    detail=f"第{i+1}个匹配结果的置信度必须在0-1之间"
                )
        
        service = CharacterService(db)
        return service.apply_character_matches(matches, auto_create_missing)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"应用角色匹配结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/match-history")
async def get_character_match_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    chapter_id: Optional[int] = Query(None, description="章节ID过滤"),
    book_id: Optional[int] = Query(None, description="书籍ID过滤"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
):
    """获取角色匹配历史记录"""
    try:
        # 这里可以实现匹配历史记录的查询逻辑
        # 目前返回一个示例响应
        return {
            "success": True,
            "data": {
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            },
            "message": "获取角色匹配历史记录成功"
        }
    except Exception as e:
        logger.error(f"获取角色匹配历史记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-matches")
async def validate_character_matches(
    matches: List[CharacterMatchResult],
    db: Session = Depends(get_db)
):
    """验证角色匹配结果"""
    try:
        if not matches:
            raise HTTPException(status_code=400, detail="匹配结果不能为空")
        
        if len(matches) > 100:
            raise HTTPException(status_code=400, detail="单次最多验证100个匹配结果")
        
        management_service = CharacterManagementService(db)
        validation_results = []
        
        for match in matches:
            result = {
                "character_name": match.character_name,
                "valid": True,
                "issues": [],
                "suggestions": []
            }
            
            # 检查角色名称
            if not match.character_name or len(match.character_name.strip()) == 0:
                result["valid"] = False
                result["issues"].append("角色名称不能为空")
            elif len(match.character_name) > 50:
                result["valid"] = False
                result["issues"].append("角色名称长度不能超过50字符")
            
            # 检查置信度
            if match.confidence_score < 0 or match.confidence_score > 1:
                result["valid"] = False
                result["issues"].append("置信度必须在0-1之间")
            elif match.confidence_score < 0.5:
                result["suggestions"].append("置信度较低，建议人工确认")
            
            # 检查角色是否已存在
            existing_character = management_service.check_character_exists(match.character_name)
            if existing_character["exists"]:
                result["suggestions"].append("角色已存在，将使用现有角色")
            else:
                result["suggestions"].append("角色不存在，将创建新角色")
            
            # 检查匹配类型
            if hasattr(match, 'match_type') and match.match_type not in [
                "exact", "fuzzy", "semantic", "manual"
            ]:
                result["valid"] = False
                result["issues"].append("不支持的匹配类型")
            
            validation_results.append(result)
        
        valid_count = sum(1 for r in validation_results if r["valid"])
        invalid_count = len(validation_results) - valid_count
        
        return {
            "success": True,
            "data": {
                "total_count": len(matches),
                "valid_count": valid_count,
                "invalid_count": invalid_count,
                "validation_results": validation_results,
                "can_apply": invalid_count == 0
            },
            "message": f"验证完成，{valid_count}个匹配结果有效"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证角色匹配结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auto-match")
async def auto_match_characters(
    book_id: Optional[int] = Query(None, description="书籍ID"),
    chapter_id: Optional[int] = Query(None, description="章节ID"),
    similarity_threshold: float = Query(0.8, ge=0.0, le=1.0, description="相似度阈值"),
    max_matches_per_character: int = Query(5, ge=1, le=20, description="每个角色最大匹配数"),
    auto_apply: bool = Query(False, description="是否自动应用高置信度匹配"),
    db: Session = Depends(get_db)
):
    """自动匹配角色"""
    try:
        if book_id:
            # 验证书籍是否存在
            from app.models.book import Book
            book = db.query(Book).filter(Book.id == book_id).first()
            if not book:
                raise HTTPException(status_code=404, detail="书籍不存在")
        
        if chapter_id:
            # 验证章节是否存在
            from app.models import BookChapter
            chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
            if not chapter:
                raise HTTPException(status_code=404, detail="章节不存在")
        
        # 这里可以实现自动匹配逻辑
        # 目前返回一个示例响应
        return {
            "success": True,
            "data": {
                "total_characters_analyzed": 0,
                "matches_found": 0,
                "auto_applied_matches": 0,
                "pending_review_matches": 0,
                "match_results": [],
                "processing_time": "0.5s"
            },
            "message": "自动匹配完成"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"自动匹配角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/match-statistics")
async def get_match_statistics(
    book_id: Optional[int] = Query(None, description="书籍ID过滤"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
):
    """获取匹配统计信息"""
    try:
        # 这里可以实现匹配统计信息的查询逻辑
        # 目前返回一个示例响应
        return {
            "success": True,
            "data": {
                "total_matches": 0,
                "successful_matches": 0,
                "failed_matches": 0,
                "auto_applied_matches": 0,
                "manual_review_matches": 0,
                "average_confidence_score": 0.0,
                "match_accuracy": 0.0,
                "most_matched_characters": [],
                "match_trends": []
            },
            "message": "获取匹配统计信息成功"
        }
    except Exception as e:
        logger.error(f"获取匹配统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export-matches")
async def export_match_results(
    book_id: Optional[int] = Query(None, description="书籍ID过滤"),
    chapter_id: Optional[int] = Query(None, description="章节ID过滤"),
    format: str = Query("csv", regex="^(csv|json|xlsx)$", description="导出格式"),
    include_confidence: bool = Query(True, description="是否包含置信度信息"),
    db: Session = Depends(get_db)
):
    """导出匹配结果"""
    try:
        # 这里可以实现匹配结果导出逻辑
        # 目前返回一个示例响应
        from fastapi import Response
        
        content = "character_name,chapter_id,confidence_score,match_type\n"
        filename = f"character_matches.{format}"
        content_type = {
            "csv": "text/csv",
            "json": "application/json",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }.get(format, "text/csv")
        
        return Response(
            content=content,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"导出匹配结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))