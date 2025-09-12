"""
环境音分析API端点
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

# ChapterEnvironmentAnalyzer已删除，功能由EnvironmentDataService替代
from app.services.environment_project_service import EnvironmentProjectService
from app.utils.logger import get_logger
from app.database import get_db
from app.models.novel_project import NovelProject
from app.models.analysis_result import AnalysisResult
from app.models.book import Book
from app.models.book_chapter import BookChapter
from app.models.environment_generation import EnvironmentProject
from .schemas import (
    EnvironmentGenerationRequest,
    ChapterEnvironmentAnalysisRequest
)

logger = get_logger(__name__)
router = APIRouter()


def get_session_id(project_id: int) -> str:
    """生成会话ID"""
    return f"env_gen_{project_id}"


# 删除整本书环境音分析功能 - 因为整本书分析不现实，几千张内容无法一次性处理
# 保留章节级别的环境音分析功能


@router.post("/chapters/analyze")
async def analyze_chapters_environment(
    request: ChapterEnvironmentAnalysisRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    分析指定章节的环境音需求
    支持指定现有项目ID，合并分析结果
    """
    try:
        chapter_ids = request.chapter_ids
        analysis_options = request.analysis_options or {}
        existing_project_id = analysis_options.get('existing_project_id')  # 新增：支持指定现有项目ID
        
        logger.info(f"[ENV_GEN_API] 开始章节环境音分析，章节IDs: {chapter_ids}，现有项目ID: {existing_project_id}")
        
        if not chapter_ids:
            raise HTTPException(status_code=400, detail="请指定要分析的章节ID")
        
        # 获取章节信息
        chapters = db.query(BookChapter).filter(BookChapter.id.in_(chapter_ids)).all()
        if not chapters:
            raise HTTPException(status_code=404, detail="未找到指定的章节")
        
        # 获取第一个章节的书籍信息（假设所有章节来自同一本书）
        book = db.query(Book).filter(Book.id == chapters[0].book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="未找到章节对应的书籍")
        
        # 分析章节环境音
        analyzer = ChapterEnvironmentAnalyzer(db_session=db)
        raw_result = await analyzer.analyze_chapters(chapters, analysis_options)
        # 🚨 修复：正确扁平化结构，直接提取environment_tracks到顶层
        if isinstance(raw_result, dict) and 'analysis_result' in raw_result:
            inner_result = raw_result['analysis_result']
            # 构建扁平结构：environment_tracks直接在analysis_result下
            analysis_result = {
                'environment_tracks': inner_result.get('environment_tracks', []),
                'video_timeline': inner_result.get('video_timeline', {}),
                'analysis_metadata': inner_result.get('analysis_metadata', {}),
                'chapter_info': inner_result.get('chapter_info', []),
                'total_chapters': inner_result.get('total_chapters', 0)
            }
        else:
            analysis_result = raw_result if isinstance(raw_result, dict) else {}
        
        # 检查分析结果是否有错误
        if 'analysis_metadata' in analysis_result and analysis_result['analysis_metadata'].get('error'):
            error_info = analysis_result['analysis_metadata']
            error_msg = error_info['error']
            suggestion = error_info.get('suggestion', '请检查数据完整性')
            
            # 🔥 修复：正确处理章节ID信息
            chapter_id = '未知'
            if 'chapter_id' in error_info:
                chapter_id = error_info['chapter_id']
            elif 'chapter_ids' in error_info:
                # 如果有多个章节ID，取第一个
                chapter_ids = error_info['chapter_ids']
                if isinstance(chapter_ids, list) and chapter_ids:
                    chapter_id = str(chapter_ids[0])
                else:
                    chapter_id = str(chapter_ids)
            
            logger.error(f"[ENV_GEN_API] 环境音分析失败: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "suggestion": suggestion,
                "chapter_id": chapter_id,
                "message": error_msg  # 🔥 优化：避免重复前缀
            }
        
        # 构建分析统计（基于扁平结构）
        analysis_stats = {
            'total_chapters': len(chapters),
            'total_tracks': len(analysis_result.get('environment_tracks', [])),
            'analysis_time': datetime.now().isoformat()
        }
        
        # 确定项目ID和保存策略
        project_id = None
        create_project = analysis_options.get('create_project', False)
        force_reanalyze = analysis_options.get('force_reanalyze', False)
        
        # 🚨 修复：新增环境音项目时强制重新分析，避免使用旧数据
        if not existing_project_id and not create_project:
            # 新增项目时，强制重新分析
            force_reanalyze = True
            logger.info(f"[ENV_GEN_API] 新增环境音项目，强制重新分析以避免使用旧数据")
        
        if existing_project_id:
            # 使用指定的现有项目ID，直接更新项目
            project_id = existing_project_id
            logger.info(f"[ENV_GEN_API] 使用现有项目ID: {project_id}")
            
            # 直接更新现有项目
            env_service = EnvironmentProjectService(db)
            updated_project = env_service.create_or_update(
                book_id=book.id,
                analysis_result=analysis_result,
                analysis_stats=analysis_stats,
                analysis_options=analysis_options
            )
            project_id = updated_project.id  # 确保返回正确的项目ID
            logger.info(f"[ENV_GEN_API] 更新现有项目: {project_id}")
        elif create_project:
            # 创建新项目
            env_service = EnvironmentProjectService(db)
            env_project = env_service.create_or_update(
                book_id=book.id,
                analysis_result=analysis_result,
                analysis_stats=analysis_stats,
                analysis_options=analysis_options
            )
            project_id = env_project.id
            logger.info(f"[ENV_GEN_API] 创建新环境音项目: {project_id}")
        else:
            # 查找现有项目（通过书籍ID）
            env_service = EnvironmentProjectService(db)
            existing_env_project = db.query(EnvironmentProject).filter(EnvironmentProject.book_id == book.id).first()
            
            if existing_env_project:
                # 🚨 修复：更新现有项目时，如果强制重新分析，则清理旧数据
                if force_reanalyze:
                    logger.info(f"[ENV_GEN_API] 强制重新分析：清理现有项目 {existing_env_project.id} 的旧数据")
                    analysis_options['force_reanalyze'] = True
                
                # 🚨 修复：强制重新分析后，项目ID保持不变
                updated_project = env_service.create_or_update(
                    book_id=book.id,
                    analysis_result=analysis_result,
                    analysis_stats=analysis_stats,
                    analysis_options=analysis_options
                )
                project_id = updated_project.id  # 项目ID保持不变
                logger.info(f"[ENV_GEN_API] 更新环境音项目: {project_id}")
            else:
                # 没有现有项目，但不创建新项目
                logger.info(f"[ENV_GEN_API] 章节环境音分析完成，未创建项目")
                
                return {
                    "success": True,
                    "project_id": None,
                    "analysis_result": analysis_result,
                    "analysis_stats": analysis_stats,
                    "message": f"成功分析 {len(chapters)} 个章节，发现 {len(analysis_result.get('environment_tracks', []))} 个环境音轨道"
                }
        
        logger.info(f"[ENV_GEN_API] 章节环境音分析完成，项目ID: {project_id}")
        
        return {
            "success": True,
            "project_id": project_id,
            "analysis_result": analysis_result,  # 扁平结构
            "analysis_stats": analysis_stats,
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
    
    # 🚀 检查数据库中是否已有分析结果 - 支持环境音项目ID和小说项目ID
    project = None
    book_id = None
    existing_env_project = None
    
    # 首先尝试查找环境音项目
    env_project = db.query(EnvironmentProject).filter(EnvironmentProject.id == request.project_id).first()
    if env_project:
        # 这是环境音项目ID
        project = env_project
        book_id = env_project.book_id
        existing_env_project = env_project
        logger.info(f"[ENV_GEN_API] 使用环境音项目ID: {request.project_id}")
    else:
        # 尝试查找小说项目
        novel_project = db.query(NovelProject).filter(NovelProject.id == request.project_id).first()
        if novel_project:
            # 这是小说项目ID
            project = novel_project
            book_id = novel_project.book_id
            logger.info(f"[ENV_GEN_API] 使用小说项目ID: {request.project_id}")
            
            # 通过书籍ID查找环境音项目
            env_service = EnvironmentProjectService(db)
            existing_env_project = db.query(EnvironmentProject).filter(EnvironmentProject.book_id == book_id).first()
        else:
            raise HTTPException(status_code=404, detail=f"项目 {request.project_id} 不存在（既不是环境音项目也不是小说项目）")
    
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
        if hasattr(project, 'status') and project.status == 'cancelled':
            raise HTTPException(
                status_code=422, 
                detail=f"项目 {request.project_id} 已被取消，无法进行环境音分析。请重新启动项目或选择其他项目。"
            )
        
        # 🚨 验证synthesis_plan数据
        if not request.synthesis_plan:
            # 尝试从数据库获取synthesis_plan
            # 通过书籍ID -> 章节 -> 分析结果的路径查找
            chapters = db.query(BookChapter).filter(BookChapter.book_id == book_id).all()
            
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
        
        # 🚨 旧的ChapterEnvironmentAnalyzer已删除，这个API端点已废弃
        # 现在环境音分析通过书籍分析结果 + 同步API完成
        raise HTTPException(
            status_code=410,
            detail="此API端点已废弃。请使用书籍分析结果配合同步环境音API完成环境音分析。"
        )
        
        # 以下代码保留作为参考，但不会执行
        analysis_stats = {
            'total_segments': len(request.synthesis_plan),
            'environment_tracks': 0,
            'analysis_timestamp': datetime.now().isoformat(),
            'analysis_duration': 0,
            'status': 'deprecated'
        }
        
        # 🚀 保存到数据库 - 使用独立的环境音项目
        env_service = EnvironmentProjectService(db)
        env_project = env_service.create_or_update(
            book_id=book_id,
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
