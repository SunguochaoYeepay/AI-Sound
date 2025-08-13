"""
环境音生成API接口
整合旁白环境分析器和环境配置校对器为完整的API服务
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
from datetime import datetime

from app.services.narration_environment_analyzer import NarrationEnvironmentAnalyzer
from app.services.chapter_environment_analyzer import ChapterEnvironmentAnalyzer
from app.services.sound_matching_engine import SoundMatchingEngine
from app.services.tangoflux_environment_generator import TangoFluxEnvironmentGenerator
from app.services.timeline_generator import EnvironmentTimelineGenerator
from app.services.environment_config_validator import EnvironmentConfigValidator
from app.utils.logger import get_logger
from app.database import get_db
from app.models.novel_project import NovelProject
from app.models.analysis_result import AnalysisResult
from app.models.environment_generation import EnvironmentProject
from app.models.book import Book
from app.models.book_chapter import BookChapter
from sqlalchemy.orm import Session

logger = get_logger(__name__)
router = APIRouter(prefix="/environment-generation", tags=["环境音生成"])


# === Request/Response Models ===
class EnvironmentGenerationRequest(BaseModel):
    """环境音生成请求"""
    project_id: int
    synthesis_plan: List[Dict[str, Any]]
    options: Optional[Dict[str, Any]] = {}

class ValidationEditRequest(BaseModel):
    """校对编辑请求"""
    track_index: int
    manual_edits: Dict[str, Any]

class ValidationApprovalRequest(BaseModel):
    """校对审批请求"""
    track_index: int
    validation_result: str  # approved/rejected/needs_revision
    notes: Optional[str] = None

class ChapterEnvironmentAnalysisRequest(BaseModel):
    """章节环境音分析请求 - 新流程"""
    chapter_ids: List[int]
    analysis_options: Optional[Dict[str, Any]] = {}

class EnvironmentMatchingRequest(BaseModel):
    """环境音匹配请求"""
    analysis_result: Dict[str, Any]
    matching_options: Optional[Dict[str, Any]] = {}

class EnvironmentProjectCreateRequest(BaseModel):
    """环境音项目创建请求"""
    name: str
    description: Optional[str] = ""
    book_id: Optional[int] = None
    chapter_ids: Optional[List[int]] = []
    analysis_options: Optional[Dict[str, Any]] = {}

class TimelineExportRequest(BaseModel):
    """时间轴导出请求"""
    timeline_data: Dict[str, Any]
    export_format: str = 'generic'  # generic, premiere_pro, davinci_resolve
    output_path: Optional[str] = None

class BatchGenerationRequest(BaseModel):
    """批量生成环境音请求"""
    tracks: List[Dict[str, Any]]
    options: Optional[Dict[str, Any]] = {}

class EnvironmentProjectUpdateRequest(BaseModel):
    """环境音项目更新请求"""
    analysis_result: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


def get_session_id(project_id: int) -> str:
    """生成会话ID"""
    return f"env_gen_{project_id}"

# === API Endpoints ===

@router.post("/chapters/analyze")
async def analyze_chapters_environment(
    request: ChapterEnvironmentAnalysisRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    章节环境音智能分析 - 新流程第2步
    基于章节ID进行环境音需求分析
    """
    logger.info(f"[ENV_GEN_API] 开始章节环境音分析，章节IDs: {request.chapter_ids}")
    
    try:
        # 获取章节信息
        chapters = db.query(BookChapter).filter(BookChapter.id.in_(request.chapter_ids)).all()
        if not chapters:
            raise HTTPException(status_code=404, detail="未找到指定的章节")
        
        # 获取项目信息
        project = None
        if chapters:
            project = db.query(NovelProject).filter(NovelProject.id == chapters[0].book_id).first()
        
        # 创建分析器实例
        analyzer = ChapterEnvironmentAnalyzer()
        
        # 执行分析
        analysis_result = await analyzer.analyze_chapters(
            chapters=chapters,
            options=request.analysis_options or {}
        )
        
        # 生成项目ID（使用时间戳）
        project_id = int(datetime.now().timestamp())
        
        # 保存到数据库
        new_project = EnvironmentProject(
            id=project_id,
            name=f"环境音分析_{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}",
            description=f"基于{len(chapters)}个章节的智能环境音分析",
            status="analyzed",
            analysis_result=analysis_result,
            matching_result={
                'analysis_stats': {
                    'total_chapters': len(chapters),
                    'total_tracks': len(analysis_result.get('environment_tracks', [])),
                    'analysis_time': datetime.now().isoformat()
                },
                'session_stage': 'analyzed'
            },
            chapter_ids=request.chapter_ids,
            analysis_options=request.analysis_options or {},
            book_name=project.name if project else "未知书籍",
            chapter_name=f"第{len(chapters)}章"
        )
        
        db.add(new_project)
        db.commit()
        db.refresh(new_project)
        
        logger.info(f"[ENV_GEN_API] 章节环境音分析完成，项目ID: {project_id}")
        
        return {
            "success": True,
            "project_id": project_id,
            "analysis_result": analysis_result,
            "analysis_stats": {
                'total_chapters': len(chapters),
                'total_tracks': len(analysis_result.get('environment_tracks', [])),
                'analysis_time': datetime.now().isoformat()
            },
            "message": f"成功分析 {len(chapters)} 个章节，发现 {len(analysis_result.get('environment_tracks', []))} 个环境音轨道"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 章节环境音分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"章节环境音分析失败: {str(e)}")

@router.post("/analyze")
async def analyze_environment_from_synthesis_plan(
    request: EnvironmentGenerationRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    从synthesis_plan分析环境音需求
    第一步：旁白提取分析
    支持force_reanalyze参数强制重新分析
    """
    session_id = get_session_id(request.project_id)
    force_reanalyze = request.options.get('force_reanalyze', False)
    
    logger.info(f"[ENV_GEN_API] 开始环境音分析，项目ID: {request.project_id}，强制重新分析: {force_reanalyze}")
    
    # 🚀 检查数据库中是否已有分析结果
    existing_project = db.query(EnvironmentProject).filter(EnvironmentProject.id == request.project_id).first()
    if not force_reanalyze and existing_project and existing_project.analysis_result:
        logger.info(f"[ENV_GEN_API] 发现已有分析结果，项目ID: {request.project_id}")
        return {
            'success': True,
            'project_id': request.project_id,
            'session_id': session_id,
            'analysis_result': existing_project.analysis_result,
            'analysis_stats': existing_project.matching_result.get('analysis_stats', {}) if existing_project.matching_result else {},
            'existing_analysis': True,
            'message': '发现已有分析结果，如需重新分析请使用重新分析功能'
        }
    
    try:
        # 🚨 验证项目状态
        project = db.query(NovelProject).filter(NovelProject.id == request.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"项目 {request.project_id} 不存在")
        
        if project.status == 'cancelled':
            raise HTTPException(
                status_code=422, 
                detail=f"项目 {request.project_id} 已被取消，无法进行环境音分析。请重新启动项目或选择其他项目。"
            )
        
        # 🚨 验证synthesis_plan数据
        if not request.synthesis_plan:
            # 尝试从数据库获取synthesis_plan
            # 通过项目ID -> 书籍ID -> 章节 -> 分析结果的路径查找
            chapters = db.query(BookChapter).filter(BookChapter.book_id == project.book_id).all()
            
            analysis_result = None
            for chapter in chapters:
                chapter_analysis = db.query(AnalysisResult).filter(
                    AnalysisResult.chapter_id == chapter.id
                ).order_by(AnalysisResult.id.desc()).first()
                
                if chapter_analysis and chapter_analysis.synthesis_plan:
                    analysis_result = chapter_analysis
                    logger.info(f"[ENV_GEN_API] 找到章节{chapter.chapter_number}的分析结果")
                    break
            
            if not analysis_result or not analysis_result.synthesis_plan:
                raise HTTPException(
                    status_code=422, 
                    detail=f"项目 {request.project_id} 没有可用的合成计划数据。请先完成智能准备步骤。"
                )
            
            # 从数据库中提取synthesis_plan
            if isinstance(analysis_result.synthesis_plan, dict) and 'synthesis_plan' in analysis_result.synthesis_plan:
                request.synthesis_plan = analysis_result.synthesis_plan['synthesis_plan']
                logger.info(f"[ENV_GEN_API] 从数据库获取到synthesis_plan，共{len(request.synthesis_plan)}个段落")
            else:
                raise HTTPException(
                    status_code=422, 
                    detail=f"项目 {request.project_id} 的合成计划数据格式不正确"
                )
        
        # 验证synthesis_plan格式
        if not isinstance(request.synthesis_plan, list) or len(request.synthesis_plan) == 0:
            raise HTTPException(
                status_code=422, 
                detail=f"synthesis_plan必须是非空的列表格式，当前类型: {type(request.synthesis_plan)}"
            )
        
        # 检查是否有旁白内容
        logger.info(f"🔍 [ENV_GEN_API] 检查旁白内容，synthesis_plan有{len(request.synthesis_plan)}个段落")
        for i, seg in enumerate(request.synthesis_plan):
            logger.debug(f"🔍 段落{i+1}: speaker='{seg.get('speaker')}', character='{seg.get('character')}', text='{seg.get('text', '')[:30]}...'")
        
        # 初始化分析器
        analyzer = NarrationEnvironmentAnalyzer()
        
        # 执行环境音分析
        analysis_result = analyzer.analyze_narration_environment(
            synthesis_plan=request.synthesis_plan,
            analysis_options=request.options
        )
        
        # 计算分析统计
        analysis_stats = {
            'total_segments': len(request.synthesis_plan),
            'environment_tracks': len(analysis_result.get('environment_tracks', [])),
            'analysis_timestamp': datetime.now().isoformat(),
            'analysis_duration': analysis_result.get('analysis_duration', 0)
        }
        
        # 🚀 保存到数据库
        if existing_project:
            # 更新现有项目
            existing_project.analysis_result = analysis_result
            existing_project.matching_result = {
                'analysis_stats': analysis_stats,
                'session_stage': 'analyzed'
            }
            existing_project.updated_at = datetime.now()
            db.commit()
            db.refresh(existing_project)
        else:
            # 创建新项目
            new_project = EnvironmentProject(
                id=request.project_id,
                name=f"环境音分析_{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}",
                description=f"基于{len(request.synthesis_plan)}个段落的智能环境音分析",
                status="analyzed",
                analysis_result=analysis_result,
                matching_result={
                    'analysis_stats': analysis_stats,
                    'session_stage': 'analyzed'
                },
                chapter_ids=[project.book_id],
                analysis_options=request.options,
                book_name=project.name if hasattr(project, 'name') else "未知书籍",
                chapter_name="第1章"  # 默认值
            )
            db.add(new_project)
            db.commit()
            db.refresh(new_project)
        
        # 🚀 同时保存到内存数据库（用于快速访问）
        # _analysis_sessions[session_id] = {
        #     'analysis_result': analysis_result,
        #     'analysis_stats': analysis_stats,
        #     'session_stage': 'analyzed',
        #     'created_at': datetime.now().isoformat()
        # }
        
        logger.info(f"[ENV_GEN_API] 分析完成，项目ID: {request.project_id}，"
                   f"发现环境音轨道: {analysis_stats['environment_tracks']}个")
        
        return {
            'success': True,
            'project_id': request.project_id,
            'session_id': session_id,
            'analysis_result': analysis_result,
            'analysis_stats': analysis_stats,
            'message': f"环境音分析完成，发现 {analysis_stats['environment_tracks']} 个环境音轨道"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 环境音分析失败，项目ID: {request.project_id}，错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"环境音分析失败: {str(e)}")

@router.post("/projects")
async def create_environment_project(
    request: EnvironmentProjectCreateRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    创建环境音分析项目
    """
    try:
        logger.info(f"[ENV_GEN_API] 创建环境音项目: {request.name}")
        
        # 获取书籍和章节信息
        book_name = "未知书籍"
        chapter_name = "未知章节"
        
        if request.book_id:
            # 通过book_id获取书籍名称
            book = db.query(Book).filter(Book.id == request.book_id).first()
            if book:
                book_name = book.title
                
                # 如果有章节ID，获取章节名称
                if request.chapter_ids and len(request.chapter_ids) > 0:
                    chapter = db.query(BookChapter).filter(BookChapter.id == request.chapter_ids[0]).first()
                    if chapter:
                        chapter_name = f"第{chapter.chapter_number}章 {chapter.chapter_title}"
                else:
                    # 如果没有指定章节，获取书籍的第一个章节
                    first_chapter = db.query(BookChapter).filter(BookChapter.book_id == request.book_id).order_by(BookChapter.chapter_number).first()
                    if first_chapter:
                        chapter_name = f"第{first_chapter.chapter_number}章 {first_chapter.chapter_title}"
        
        # 创建新项目
        new_project = EnvironmentProject(
            name=request.name,
            description=request.description,
            status="pending",  # 初始状态为pending，等待分析
            analysis_result={},  # 空的分析结果
            matching_result={},  # 空的匹配结果
            chapter_ids=request.chapter_ids,
            analysis_options=request.analysis_options,
            book_name=book_name,
            chapter_name=chapter_name
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
                "chapter_ids": new_project.chapter_ids,
                "analysis_options": new_project.analysis_options,
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
            "book_id": project.book_id,
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
        
        # 从内存数据库删除
        # session_id = get_session_id(project_id)
        # if session_id in _analysis_sessions:
        #     del _analysis_sessions[session_id]
        #     logger.info(f"[ENV_GEN_API] 从内存数据库删除项目: {project_id}")
        
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
        
        # 更新分析结果
        if request.analysis_result is not None:
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

@router.post("/batch-generate")
async def batch_generate_environment_sounds(
    request: BatchGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    批量生成环境音
    """
    try:
        logger.info(f"[ENV_GEN_API] 开始批量生成环境音，轨道数量: {len(request.tracks)}")
        
        if not request.tracks:
            raise HTTPException(status_code=400, detail="没有需要生成的轨道")
        
        # 转换前端数据格式为后端期望的格式
        generation_requests = []
        for track in request.tracks:
            # 从environment_keywords中获取主要关键词
            keyword = track.get('environment_keywords', [''])[0] if track.get('environment_keywords') else ''
            if not keyword and track.get('scene_description'):
                keyword = track.get('scene_description')
            
            generation_request = {
                'keyword': keyword,
                'description': track.get('scene_description', ''),
                'duration': track.get('duration', 30.0),
                'intensity': track.get('intensity_level', 'medium')
            }
            generation_requests.append(generation_request)
        
        # 创建生成器实例
        generator = TangoFluxEnvironmentGenerator()
        
        # 生成任务ID
        task_id = f"batch_gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(generation_requests)}"
        
        # 记录生成任务
        generation_stats = {
            "task_id": task_id,
            "total_tracks": len(generation_requests),
            "generated_tracks": 0,
            "failed_tracks": 0,
            "status": "processing",
            "start_time": datetime.now().isoformat(),
            "tracks": []
        }
        
        # 在后台任务中执行生成
        background_tasks.add_task(
            generator.batch_generate_environment_sounds,
            generation_requests=generation_requests,
            max_concurrent=request.options.get('max_concurrent', 3)
        )
        
        logger.info(f"[ENV_GEN_API] 批量生成任务已启动: {task_id}")
        
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "total_tracks": len(request.tracks),
                "status": "processing",
                "message": f"批量生成任务已启动，共 {len(request.tracks)} 个环境音"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 批量生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量生成失败: {str(e)}")