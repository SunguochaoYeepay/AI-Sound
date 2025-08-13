"""
环境音分析API端点
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.narration_environment_analyzer import NarrationEnvironmentAnalyzer
from app.services.chapter_environment_analyzer import ChapterEnvironmentAnalyzer
from app.services.environment_project_service import EnvironmentProjectService
from app.utils.logger import get_logger
from app.database import get_db
from app.models.novel_project import NovelProject
from app.models.analysis_result import AnalysisResult
from app.models.book import Book
from app.models.book_chapter import BookChapter
from .schemas import (
    EnvironmentGenerationRequest,
    ChapterEnvironmentAnalysisRequest
)

logger = get_logger(__name__)
router = APIRouter()


def get_session_id(project_id: int) -> str:
    """生成会话ID"""
    return f"env_gen_{project_id}"


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
        
        # 检查是否需要创建项目（通过analysis_options中的create_project参数控制）
        create_project = request.analysis_options.get('create_project', False)
        
        if create_project:
            # 生成项目ID（使用时间戳）
            project_id = int(datetime.now().timestamp())
            
            # 保存到数据库
            from app.models.environment_generation import EnvironmentProject
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
                "message": f"成功分析 {len(chapters)} 个章节，发现 {len(analysis_result.get('environment_tracks', []))} 个环境音轨道，已创建项目"
            }
        else:
            # 只返回分析结果，不创建项目
            logger.info(f"[ENV_GEN_API] 章节环境音分析完成，未创建项目")
            
            return {
                "success": True,
                "project_id": None,
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
    
    # 🚀 检查数据库中是否已有分析结果 - 使用独立的环境音项目
    project = db.query(NovelProject).filter(NovelProject.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 {request.project_id} 不存在")
    
    # 使用环境音项目服务检查现有分析结果
    env_service = EnvironmentProjectService(db)
    existing_env_project = env_service.get_by_novel_project_id(request.project_id)
    
    if not force_reanalyze and existing_env_project and existing_env_project.analysis_result:
        logger.info(f"[ENV_GEN_API] 发现已有分析结果，项目ID: {request.project_id}")
        return {
            'success': True,
            'project_id': request.project_id,
            'session_id': session_id,
            'analysis_result': existing_env_project.analysis_result,
            'analysis_stats': existing_env_project.matching_result.get('analysis_stats', {}) if existing_env_project.matching_result else {},
            'existing_analysis': True,
            'message': '发现已有分析结果，如需重新分析请使用重新分析功能'
        }
    
    try:
        # 🚨 验证项目状态（项目已在前面查询过）
        if project.status == 'cancelled':
            raise HTTPException(
                status_code=422, 
                detail=f"项目 {request.project_id} 已被取消，无法进行环境音分析。请重新启动项目或选择其他项目。"
            )
        
        # 🚨 验证synthesis_plan数据
        if not request.synthesis_plan:
            # 尝试从数据库获取synthesis_plan
            # 通过项目ID -> 书籍ID -> 章节 -> 分析结果的路径查找
            chapters = db.query(BookChapter).filter(BookChapter.book_id == getattr(project, 'book_id', None)).all()
            
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
        analysis_result = await analyzer.extract_and_analyze_narration(
            synthesis_plan=request.synthesis_plan
        )
        
        # 计算分析统计
        analysis_stats = {
            'total_segments': len(request.synthesis_plan),
            'environment_tracks': len(analysis_result.get('environment_tracks', [])),
            'analysis_timestamp': datetime.now().isoformat(),
            'analysis_duration': analysis_result.get('analysis_duration', 0)
        }
        
        # 🚀 保存到数据库 - 使用独立的环境音项目
        env_service = EnvironmentProjectService(db)
        env_project = env_service.create_or_update(
            novel_project_id=request.project_id,
            analysis_result=analysis_result,
            analysis_stats=analysis_stats,
            analysis_options=request.options
        )
        
        logger.info(f"[ENV_GEN_API] 环境音分析结果已保存到独立项目，项目ID: {env_project.id}")
        
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
