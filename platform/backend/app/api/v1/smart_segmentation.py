"""
智能分段API - 独立服务
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.book_chapter import BookChapter
from app.models.smart_segmentation import SmartSegmentation
from app.services.smart_segmentation_service import SmartSegmentationService

logger = logging.getLogger(__name__)
router = APIRouter()


class SegmentationRequest(BaseModel):
    """智能分段请求"""
    project_id: int
    chapter_id: int


class SegmentationResponse(BaseModel):
    """智能分段响应"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


@router.post("/segment", response_model=SegmentationResponse)
async def create_smart_segmentation(
    request: SegmentationRequest,
    db: Session = Depends(get_db)
):
    """创建智能分段"""
    try:
        # 获取章节
        chapter = db.query(BookChapter).filter(BookChapter.id == request.chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")

        # 检查章节是否有内容
        if not chapter.content or len(chapter.content.strip()) == 0:
            raise HTTPException(status_code=400, detail="章节内容为空，无法进行分段")

        # 创建智能分段服务实例
        segmentation_service = SmartSegmentationService()

        # 执行智能分段
        logger.debug(f"开始对分析项目 {request.project_id} 章节 {request.chapter_id} 进行智能分段")
        segmentation_result = await segmentation_service.segment_and_save(
            chapter.content,
            request.project_id,
            request.chapter_id,
            db
        )

        if segmentation_result["success"]:
            logger.debug(f"章节 {request.chapter_id} 智能分段成功，共生成 {segmentation_result['segmentation_data']['segment_count']} 个段落")
            return SegmentationResponse(
                success=True,
                message="智能分段完成",
                data=segmentation_result
            )
        else:
            raise HTTPException(status_code=500, detail=segmentation_result.get("error", "分段失败"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"章节 {request.chapter_id} 智能分段失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"智能分段失败: {str(e)}")


@router.get("/{project_id}/{chapter_id}/segments", response_model=SegmentationResponse)
async def get_smart_segments(
    project_id: int,
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """获取智能分段结果"""
    try:
        # 获取章节
        chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")

        # 查询智能分段结果
        segmentation_result = db.query(SmartSegmentation).filter(
            SmartSegmentation.project_id == project_id,
            SmartSegmentation.chapter_id == chapter_id
        ).first()

        if segmentation_result:
            return SegmentationResponse(
                success=True,
                message="获取智能分段结果成功",
                data=segmentation_result.to_dict()
            )
        else:
            return SegmentationResponse(
                success=False,
                message="未找到智能分段结果，请先执行智能分段",
                data=None
            )

    except Exception as e:
        logger.error(f"获取分析项目 {project_id} 章节 {chapter_id} 智能分段结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取智能分段结果失败: {str(e)}")


@router.delete("/{project_id}/{chapter_id}/segments")
async def delete_smart_segments(
    project_id: int,
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """删除智能分段结果"""
    try:
        # 查询智能分段结果
        segmentation_result = db.query(SmartSegmentation).filter(
            SmartSegmentation.project_id == project_id,
            SmartSegmentation.chapter_id == chapter_id
        ).first()

        if segmentation_result:
            db.delete(segmentation_result)
            db.commit()
            logger.info(f"删除分析项目 {project_id} 章节 {chapter_id} 的智能分段结果成功")
            return {"success": True, "message": "智能分段结果已删除"}
        else:
            return {"success": False, "message": "未找到智能分段结果"}

    except Exception as e:
        logger.error(f"删除分析项目 {project_id} 章节 {chapter_id} 智能分段结果失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除智能分段结果失败: {str(e)}")


@router.get("/{project_id}/{chapter_id}/segments/count")
async def get_segments_count(
    project_id: int,
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """获取智能分段数量"""
    try:
        # 查询智能分段结果
        segmentation_result = db.query(SmartSegmentation).filter(
            SmartSegmentation.project_id == project_id,
            SmartSegmentation.chapter_id == chapter_id
        ).first()

        if segmentation_result:
            return {
                "success": True,
                "project_id": project_id,
                "chapter_id": chapter_id,
                "segment_count": segmentation_result.segment_count,
                "segments": segmentation_result.segments
            }
        else:
            return {
                "success": False,
                "project_id": project_id,
                "chapter_id": chapter_id,
                "segment_count": 0,
                "message": "未找到智能分段结果"
            }

    except Exception as e:
        logger.error(f"获取分析项目 {project_id} 章节 {chapter_id} 智能分段数量失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取智能分段数量失败: {str(e)}")
