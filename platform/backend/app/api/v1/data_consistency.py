"""
数据一致性检查和修复API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from ...database import get_db
from ...services.auto_recovery_service import AutoRecoveryService
from ...schemas.segment_data import ConsistencyChecker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/consistency", tags=["数据一致性"])

@router.get("/check/{project_id}")
async def check_project_consistency(
    project_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    检查项目数据一致性
    """
    try:
        result = ConsistencyChecker.check_chapter_segment_consistency(db, project_id)
        
        return {
            "success": True,
            "data": result,
            "message": "一致性检查完成" if result["success"] else f"发现 {len(result['issues'])} 个问题"
        }
        
    except Exception as e:
        logger.error(f"检查项目 {project_id} 一致性失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"检查失败: {str(e)}")

@router.post("/fix/{project_id}")
async def fix_project_consistency(
    project_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    自动修复项目数据一致性问题
    """
    try:
        recovery_service = AutoRecoveryService(db)
        result = await recovery_service.check_and_fix_project_consistency(project_id)
        
        return {
            "success": result["success"],
            "data": result,
            "message": result["message"]
        }
        
    except Exception as e:
        logger.error(f"修复项目 {project_id} 一致性失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"修复失败: {str(e)}")

@router.post("/daily-check")
async def run_daily_consistency_check(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    运行每日数据一致性检查
    """
    try:
        recovery_service = AutoRecoveryService(db)
        result = await recovery_service.run_daily_consistency_check()
        
        return {
            "success": result["success"],
            "data": result,
            "message": "每日检查完成"
        }
        
    except Exception as e:
        logger.error(f"每日一致性检查失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"每日检查失败: {str(e)}")

@router.get("/health")
async def consistency_health_check(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    数据一致性健康检查
    """
    try:
        from ...models import NovelProject
        
        # 快速检查几个最近的项目
        recent_projects = db.query(NovelProject).order_by(
            NovelProject.updated_at.desc()
        ).limit(5).all()
        
        healthy_projects = 0
        total_projects = len(recent_projects)
        
        for project in recent_projects:
            try:
                result = ConsistencyChecker.check_chapter_segment_consistency(db, project.id)
                if result["success"]:
                    healthy_projects += 1
            except Exception:
                # 检查失败的项目不计入健康项目
                pass
        
        health_score = (healthy_projects / total_projects * 100) if total_projects > 0 else 100
        
        return {
            "success": True,
            "data": {
                "health_score": round(health_score, 2),
                "healthy_projects": healthy_projects,
                "total_checked": total_projects,
                "status": "良好" if health_score >= 80 else "需要关注" if health_score >= 60 else "严重"
            },
            "message": f"数据一致性健康度: {health_score:.1f}%"
        }
        
    except Exception as e:
        logger.error(f"数据一致性健康检查失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "健康检查失败"
        } 