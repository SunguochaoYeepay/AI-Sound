"""角色批量操作路由"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.schemas.character import (
    CharacterUpdate,
    CharacterBatchConfig,
    CharacterBatchResponse
)
from app.services.character_batch_service import CharacterBatchService
from app.utils.character_utils import (
    validate_character_name,
    validate_voice_type,
    validate_quality_score,
    validate_tags
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/characters/batch", tags=["角色管理-批量操作"])

@router.put("/update")
async def batch_update_characters(
    character_ids: List[int],
    update_data: CharacterUpdate,
    db: Session = Depends(get_db)
):
    """批量更新角色"""
    try:
        if not character_ids:
            raise HTTPException(status_code=400, detail="角色ID列表不能为空")
        
        if len(character_ids) > 100:
            raise HTTPException(status_code=400, detail="单次最多更新100个角色")
        
        # 验证更新数据
        if update_data.name:
            is_valid, error_msg = validate_character_name(update_data.name)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
        
        if update_data.voice_type:
            is_valid, error_msg = validate_voice_type(update_data.voice_type)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
        
        if update_data.quality_score is not None:
            is_valid, error_msg = validate_quality_score(update_data.quality_score)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
        
        if update_data.tags:
            is_valid, error_msg = validate_tags(update_data.tags)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
        
        service = CharacterBatchService(db)
        return service.batch_update_characters(character_ids, update_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量更新角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete")
async def batch_delete_characters(
    character_ids: List[int],
    force: bool = Query(False, description="是否强制删除（包括关联文件）"),
    db: Session = Depends(get_db)
):
    """批量删除角色"""
    try:
        if not character_ids:
            raise HTTPException(status_code=400, detail="角色ID列表不能为空")
        
        if len(character_ids) > 100:
            raise HTTPException(status_code=400, detail="单次最多删除100个角色")
        
        service = CharacterBatchService(db)
        return service.batch_delete_characters(character_ids, force)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量删除角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/configure")
async def batch_configure_characters(
    character_ids: List[int],
    config: CharacterBatchConfig,
    db: Session = Depends(get_db)
):
    """批量配置角色"""
    try:
        if not character_ids:
            raise HTTPException(status_code=400, detail="角色ID列表不能为空")
        
        if len(character_ids) > 100:
            raise HTTPException(status_code=400, detail="单次最多配置100个角色")
        
        service = CharacterBatchService(db)
        return service.batch_configure_characters(character_ids, config)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量配置角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export")
async def export_characters_list(
    format: str = Query("csv", regex="^(csv|json)$", description="导出格式"),
    character_ids: Optional[List[int]] = Query(None, description="指定角色ID列表"),
    search: str = Query("", description="搜索关键词"),
    voice_type: str = Query("", description="声音类型"),
    quality_min: float = Query(0, ge=0, le=100, description="最低质量分"),
    tags: str = Query("", description="标签过滤（逗号分隔）"),
    status: str = Query("", description="状态过滤"),
    book_id: Optional[int] = Query(None, description="书籍ID"),
    chapter_id: Optional[int] = Query(None, description="章节ID"),
    db: Session = Depends(get_db)
):
    """导出角色列表"""
    try:
        service = CharacterBatchService(db)
        
        # 构建过滤条件
        filters = {
            "search": search,
            "voice_type": voice_type,
            "quality_min": quality_min,
            "tags": tags,
            "status": status,
            "book_id": book_id,
            "chapter_id": chapter_id
        }
        
        result = service.export_characters_list(
            format=format,
            character_ids=character_ids,
            filters=filters
        )
        
        # 设置响应头
        filename = f"characters_export.{format}"
        content_type = "text/csv" if format == "csv" else "application/json"
        
        return Response(
            content=result["content"],
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出角色列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync-with-analysis")
async def sync_characters_with_analysis(
    book_id: Optional[int] = Query(None, description="书籍ID"),
    chapter_id: Optional[int] = Query(None, description="章节ID"),
    force_update: bool = Query(False, description="是否强制更新已存在的角色"),
    db: Session = Depends(get_db)
):
    """同步角色与分析结果"""
    try:
        service = CharacterBatchService(db)
        return service.sync_characters_with_analysis(
            book_id=book_id,
            chapter_id=chapter_id,
            force_update=force_update
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"同步角色与分析结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate")
async def validate_batch_operation(
    operation_type: str = Query(..., regex="^(update|delete|configure)$", description="操作类型"),
    character_ids: List[int] = Query(..., description="角色ID列表"),
    db: Session = Depends(get_db)
):
    """验证批量操作的可行性"""
    try:
        if not character_ids:
            raise HTTPException(status_code=400, detail="角色ID列表不能为空")
        
        if len(character_ids) > 100:
            raise HTTPException(status_code=400, detail="单次最多操作100个角色")
        
        service = CharacterBatchService(db)
        
        # 检查角色是否存在
        from app.services.character_management_service import CharacterManagementService
        management_service = CharacterManagementService(db)
        
        validation_results = []
        for char_id in character_ids:
            character = management_service.get_character_by_id(char_id)
            if not character:
                validation_results.append({
                    "character_id": char_id,
                    "valid": False,
                    "reason": "角色不存在"
                })
            else:
                # 根据操作类型进行特定验证
                valid = True
                reason = ""
                
                if operation_type == "delete":
                    # 检查是否有关联的生成任务
                    # 这里可以添加更多的删除前检查逻辑
                    pass
                elif operation_type == "update":
                    # 检查是否可以更新
                    pass
                elif operation_type == "configure":
                    # 检查是否可以配置
                    pass
                
                validation_results.append({
                    "character_id": char_id,
                    "valid": valid,
                    "reason": reason,
                    "character_name": character.name
                })
        
        valid_count = sum(1 for r in validation_results if r["valid"])
        invalid_count = len(validation_results) - valid_count
        
        return {
            "success": True,
            "data": {
                "total_count": len(character_ids),
                "valid_count": valid_count,
                "invalid_count": invalid_count,
                "validation_results": validation_results,
                "can_proceed": invalid_count == 0
            },
            "message": f"验证完成，{valid_count}个角色可以执行{operation_type}操作"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证批量操作失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/operation-history")
async def get_batch_operation_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    operation_type: Optional[str] = Query(None, description="操作类型过滤"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
):
    """获取批量操作历史记录"""
    try:
        # 这里可以实现批量操作历史记录的查询逻辑
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
            "message": "获取批量操作历史记录成功"
        }
    except Exception as e:
        logger.error(f"获取批量操作历史记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))