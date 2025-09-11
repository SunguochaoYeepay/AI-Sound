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
from app.models.environment_generation import (
    EnvironmentGenerationSession,
    EnvironmentTrackConfig,
    EnvironmentAudioMixingJob,
    EnvironmentGenerationLog
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
    仅创建项目，不进行任何分析
    用户需要在详情页面选择章节后手动触发分析
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
        
        # 创建新项目 - 关联书籍分析项目
        new_project = EnvironmentProject(
            name=request.name,
            description=request.description,
            status="created",  # 初始状态为created，表示项目已创建但未分析
            book_id=request.book_id,  # 设置书籍ID
            novel_project_id=request.novel_project_id,  # 关联书籍分析项目ID
            analysis_result={},  # 空的分析结果
            matching_result={},  # 空的匹配结果
            chapter_ids=[],  # 空数组，等待用户选择具体章节
            analysis_options=request.analysis_options,
            book_name=book_name,
            chapter_name="待选择章节"  # 表示需要用户选择章节
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
                "novel_project_id": getattr(new_project, 'novel_project_id', None),  # 关联的书籍分析项目ID
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
        
        # 🚀 第三阶段修改：优先从关联的书籍分析项目加载分析结果
        analysis_result = project.analysis_result or {}
        novel_project_id = getattr(project, 'novel_project_id', None)
        
        if novel_project_id and (not analysis_result or len(analysis_result) == 0):
            logger.info(f"[ENV_GEN_API] 从关联的书籍分析项目加载分析结果: {novel_project_id}")
            try:
                # 从书籍分析项目加载6卡分析结果
                from app.models.analysis_result import AnalysisResult
                book_analysis_results = db.query(AnalysisResult).filter(
                    AnalysisResult.project_id == novel_project_id
                ).all()
                
                if book_analysis_results:
                    # 构建章节分析结果字典，并转换为环境音轨道格式
                    book_analysis_dict = {}
                    for result in book_analysis_results:
                        if result.original_analysis and result.chapter_id:
                            # 检查是否有6卡分析结果
                            original_data = result.original_analysis
                            if isinstance(original_data, dict) and 'six_card_results' in original_data:
                                # 🚀 第三阶段：从6卡分析结果中提取环境音数据
                                six_card_results = original_data.get('six_card_results', [])
                                environment_sounds = []
                                
                                for six_card_result in six_card_results:
                                    # 从scene_card中提取environment_sounds
                                    scene_card = six_card_result.get('scene_card', {})
                                    if 'environment_sounds' in scene_card:
                                        chapter_environment_sounds = scene_card['environment_sounds']
                                        if isinstance(chapter_environment_sounds, list):
                                            for sound in chapter_environment_sounds:
                                                sound['chapter_id'] = result.chapter_id
                                                sound['segment_index'] = six_card_result.get('_metadata', {}).get('segment_index', 0)
                                                environment_sounds.append(sound)
                                
                                if environment_sounds:
                                    # 转换为environment_tracks格式
                                    from app.api.v1.environment_generation.generation import convert_to_frontend_format
                                    environment_tracks = convert_to_frontend_format(environment_sounds)
                                    
                                    # 构建章节分析结果
                                    chapter_analysis = {
                                        "environment_tracks": environment_tracks,
                                        "source": "book_analysis",
                                        "chapter_id": result.chapter_id,
                                        "total_sounds": len(environment_sounds)
                                    }
                                    book_analysis_dict[str(result.chapter_id)] = chapter_analysis
                                    logger.info(f"[ENV_GEN_API] 章节{result.chapter_id}提取到{len(environment_sounds)}个环境音")
                    
                    if book_analysis_dict:
                        analysis_result = book_analysis_dict
                        logger.info(f"[ENV_GEN_API] 成功从书籍分析项目加载{len(book_analysis_dict)}个章节的分析结果")
                    else:
                        logger.warning(f"[ENV_GEN_API] 书籍分析项目{novel_project_id}没有环境音数据")
                else:
                    logger.warning(f"[ENV_GEN_API] 书籍分析项目{novel_project_id}没有分析结果")
            except Exception as e:
                logger.error(f"[ENV_GEN_API] 从书籍分析项目加载分析结果失败: {str(e)}")
        
        # 构建响应数据
        project_data = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "book_id": getattr(project, 'book_id', None),  # 安全访问book_id字段
            "novel_project_id": novel_project_id,  # 关联的书籍分析项目ID
            "book_name": project.book_name,
            "chapter_ids": project.chapter_ids,
            "chapter_name": project.chapter_name,
            "status": project.status,
            "analysis_result": analysis_result,  # 使用加载的分析结果
            "matching_result": project.matching_result,
            "created_at": project.created_at,
            "updated_at": project.updated_at
        }
        
        logger.info(f"[ENV_GEN_API] 项目详情获取成功: {project_id}")
        return {
            "success": True,
            "data": {
                "project": project_data,
                "analysis_result": analysis_result  # 返回加载的分析结果
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
        book_id = project.book_id
        
        # 🚨 修复：删除项目前先清理所有相关数据
        logger.info(f"[ENV_GEN_API] 开始清理项目 {project_id} 的相关数据...")
        
        # 1. 删除相关的环境音会话
        sessions = db.query(EnvironmentGenerationSession).filter(
            EnvironmentGenerationSession.project_id == project_id
        ).all()
        session_count = len(sessions)
        for session in sessions:
            # 删除会话下的所有轨道配置
            tracks = db.query(EnvironmentTrackConfig).filter(
                EnvironmentTrackConfig.session_id == session.id
            ).all()
            for track in tracks:
                db.delete(track)
            # 删除会话
            db.delete(session)
        
        # 2. 删除相关的混合任务
        mixing_jobs = db.query(EnvironmentAudioMixingJob).filter(
            EnvironmentAudioMixingJob.project_id == project_id
        ).all()
        for job in mixing_jobs:
            db.delete(job)
        
        # 3. 删除相关的生成日志
        logs = db.query(EnvironmentGenerationLog).join(
            EnvironmentGenerationSession, EnvironmentGenerationLog.session_id == EnvironmentGenerationSession.id
        ).filter(EnvironmentGenerationSession.project_id == project_id).all()
        for log in logs:
            db.delete(log)
        
        # 4. 最后删除项目本身
        db.delete(project)
        db.commit()
        
        logger.info(f"[ENV_GEN_API] 项目删除成功: {project_name}")
        logger.info(f"[ENV_GEN_API] 清理了 {session_count} 个会话及其相关数据")
        
        return {
            "success": True,
            "data": {
                "project_id": project_id,
                "project_name": project_name,
                "cleaned_sessions": session_count,
                "book_id": book_id
            },
            "message": f"项目 '{project_name}' 删除成功，已清理所有相关数据"
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
