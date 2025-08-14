"""
环境音项目管理API端点
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.environment_generation import EnvironmentProject
from app.models.book import Book
from app.models.book_chapter import BookChapter
from app.utils.logger import get_logger
from app.database import get_db
from .schemas import (
    EnvironmentProjectCreateRequest,
    EnvironmentProjectUpdateRequest
)

logger = get_logger(__name__)
router = APIRouter()


@router.post("/projects")
async def create_environment_project(
    request: EnvironmentProjectCreateRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    创建环境音分析项目
    基于书籍的环境音分析，自动分析整本书的所有章节
    """
    try:
        logger.info(f"[ENV_GEN_API] 创建环境音项目: {request.name}")
        
        # 获取书籍信息
        book_name = "未知书籍"
        
        if request.book_id:
            # 通过book_id获取书籍名称
            book = db.query(Book).filter(Book.id == request.book_id).first()
            if book:
                book_name = book.title
                logger.info(f"[ENV_GEN_API] 关联书籍: {book_name} (ID: {request.book_id})")
            else:
                logger.warning(f"[ENV_GEN_API] 未找到书籍: {request.book_id}")
        
        # 创建新项目 - 基于书籍，不指定具体章节
        new_project = EnvironmentProject(
            name=request.name,
            description=request.description,
            status="pending",  # 初始状态为pending，等待分析
            book_id=request.book_id,  # 设置书籍ID
            analysis_result={},  # 空的分析结果
            matching_result={},  # 空的匹配结果
            chapter_ids=[],  # 空数组表示分析整本书的所有章节
            analysis_options=request.analysis_options,
            book_name=book_name,
            chapter_name="整本书"  # 表示分析整本书
        )
        
        # 保存到数据库
        db.add(new_project)
        db.commit()
        db.refresh(new_project)
        
        logger.info(f"[ENV_GEN_API] 项目创建成功，ID: {new_project.id}")
        
        return {
            "success": True,
            "data": {
                "id": new_project.id,
                "name": new_project.name,
                "description": new_project.description,
                "status": new_project.status,
                "book_id": getattr(new_project, 'book_id', None),  # 安全访问book_id字段
                "chapter_ids": new_project.chapter_ids,
                "analysis_options": new_project.analysis_options,
                "analysis_tracks": new_project.analysis_tracks,
                "generation_count": new_project.generation_count,
                "matched_count": new_project.matched_count,
                "book_name": new_project.book_name,
                "chapter_name": new_project.chapter_name,
                "created_at": new_project.created_at.isoformat() if new_project.created_at else None
            },
            "message": "项目创建成功"
        }
        
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 创建项目失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建项目失败: {str(e)}")


@router.get("/projects/{project_id}")
async def get_environment_project(
    project_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取环境音项目详情"""
    try:
        logger.info(f"[ENV_GEN_API] 获取项目详情: {project_id}")
        
        # 查找项目
        project = db.query(EnvironmentProject).filter(EnvironmentProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 构建响应数据
        project_data = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "book_id": getattr(project, 'book_id', None),  # 安全访问book_id字段
            "book_name": project.book_name,
            "chapter_ids": project.chapter_ids,
            "chapter_name": project.chapter_name,
            "status": project.status,
            "analysis_result": project.analysis_result,
            "matching_result": project.matching_result,
            "created_at": project.created_at,
            "updated_at": project.updated_at
        }
        
        logger.info(f"[ENV_GEN_API] 项目详情获取成功: {project_id}")
        return {
            "success": True,
            "data": {
                "project": project_data,
                "analysis_result": project.analysis_result  # 单独返回分析结果
            },
            "message": "获取项目详情成功"
        }
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 获取项目详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目详情失败: {str(e)}")


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    删除环境音分析项目
    """
    try:
        logger.info(f"[ENV_GEN_API] 删除项目: {project_id}")
        
        # 从数据库查询项目
        project = db.query(EnvironmentProject).filter(EnvironmentProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        project_name = project.name or "未命名项目"
        
        # 从数据库中删除项目
        db.delete(project)
        db.commit()
        
        logger.info(f"[ENV_GEN_API] 项目删除成功: {project_name}")
        
        return {
            "success": True,
            "data": {
                "project_id": project_id,
                "project_name": project_name
            },
            "message": f"项目 '{project_name}' 删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 删除项目失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")


@router.get("/projects")
async def get_projects(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取环境音分析项目列表
    """
    try:
        # 从数据库查询项目列表
        projects = db.query(EnvironmentProject).order_by(EnvironmentProject.created_at.desc()).offset(skip).limit(limit).all()
        
        project_list = []
        for project in projects:
            # 手动构建项目数据，确保编码正确
            project_data = {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "book_id": project.book_id,  # 添加book_id字段
                "chapter_ids": project.chapter_ids,
                "analysis_options": project.analysis_options,
                "analysis_tracks": project.analysis_tracks,
                "generation_count": project.generation_count,
                "matched_count": project.matched_count,
                "book_name": project.book_name,
                "chapter_name": project.chapter_name,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None
            }
            project_list.append(project_data)
        
        return {
            "success": True,
            "data": {
                "data": {
                    "projects": project_list,
                    "total": len(project_list),
                    "skip": skip,
                    "limit": limit
                }
            }
        }
        
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 获取项目列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")


@router.put("/projects/{project_id}/analysis")
async def update_project_analysis(
    project_id: int,
    request: EnvironmentProjectUpdateRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """更新项目分析结果"""
    try:
        logger.info(f"[ENV_GEN_API] 更新项目分析结果: {project_id}")
        
        # 查找项目
        project = db.query(EnvironmentProject).filter(EnvironmentProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 更新分析结果 - 支持多章节分析结果存储
        if request.analysis_result is not None:
            # 如果analysis_result是字典格式，说明是单个章节的分析结果
            if isinstance(request.analysis_result, dict):
                # 获取章节ID（从请求中获取）
                chapter_id = request.chapter_id
                
                if chapter_id:
                    # 初始化多章节分析结果存储
                    if not project.analysis_result or not isinstance(project.analysis_result, dict):
                        project.analysis_result = {}
                    
                    # 存储到对应章节
                    project.analysis_result[str(chapter_id)] = request.analysis_result
                    logger.info(f"[ENV_GEN_API] 保存章节 {chapter_id} 的分析结果")
                else:
                    # 兼容旧格式，直接覆盖
                    project.analysis_result = request.analysis_result
            else:
                # 兼容旧格式，直接覆盖
                project.analysis_result = request.analysis_result
        
        if request.status is not None:
            project.status = request.status
        
        db.commit()
        db.refresh(project)
        
        logger.info(f"[ENV_GEN_API] 项目分析结果更新成功: {project_id}")
        return {
            "success": True,
            "data": {
                "id": project.id,
                "analysis_result": project.analysis_result,
                "status": project.status
            },
            "message": "分析结果更新成功"
        }
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 更新项目分析结果失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新分析结果失败: {str(e)}")
