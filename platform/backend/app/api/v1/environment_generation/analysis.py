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
from app.models.environment_generation import EnvironmentProject
from .schemas import (
    EnvironmentGenerationRequest,
    ChapterEnvironmentAnalysisRequest,
    BookEnvironmentAnalysisRequest
)

logger = get_logger(__name__)
router = APIRouter()


def get_session_id(project_id: int) -> str:
    """生成会话ID"""
    return f"env_gen_{project_id}"


@router.post("/books/analyze")
async def analyze_book_environment(
    request: BookEnvironmentAnalysisRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    分析整本书的环境音需求
    基于书籍的环境音分析，自动分析所有章节
    """
    try:
        book_id = request.book_id
        analysis_options = request.analysis_options or {}
        project_id = request.project_id  # 可选：指定现有项目ID
        
        logger.info(f"[ENV_GEN_API] 开始书籍环境音分析，书籍ID: {book_id}，项目ID: {project_id}")
        
        if not book_id:
            raise HTTPException(status_code=400, detail="请指定要分析的书籍ID")
        
        # 获取书籍信息
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="未找到指定的书籍")
        
        # 获取书籍的所有章节
        chapters = db.query(BookChapter).filter(BookChapter.book_id == book_id).order_by(BookChapter.chapter_number).all()
        if not chapters:
            raise HTTPException(status_code=404, detail="书籍没有章节内容")
        
        logger.info(f"[ENV_GEN_API] 找到 {len(chapters)} 个章节")
        
        # 检查是否跳过分析，只保存结果
        skip_analysis = analysis_options.get('skip_analysis', False)
        provided_analysis_result = analysis_options.get('analysis_result', None)
        
        if skip_analysis and provided_analysis_result:
            # 跳过分析，直接使用提供的结果
            logger.info(f"[ENV_GEN_API] 跳过分析，使用提供的结果")
            multi_chapter_result = provided_analysis_result
            
            # 计算总轨道数
            total_tracks = 0
            for chapter_id, chapter_result in multi_chapter_result.items():
                tracks = chapter_result.get('environment_tracks', [])
                total_tracks += len(tracks)
            
            # 构建分析统计
            analysis_stats = {
                'total_chapters': len(multi_chapter_result),
                'total_tracks': total_tracks,
                'analysis_time': datetime.now().isoformat(),
                'skip_analysis': True
            }
        else:
            # 正常分析所有章节的环境音
            analyzer = ChapterEnvironmentAnalyzer()
            
            # 为每个章节单独分析，然后合并结果
            multi_chapter_result = {}
            total_tracks = 0
            
            for chapter in chapters:
                logger.info(f"[ENV_GEN_API] 分析章节 {chapter.id}: {chapter.chapter_title}")
                
                # 单独分析每个章节
                chapter_result = await analyzer.analyze_chapters([chapter], analysis_options)
                
                # 将结果存储到多章节格式中
                multi_chapter_result[chapter.id] = chapter_result
                total_tracks += len(chapter_result.get('environment_tracks', []))
                
                logger.info(f"[ENV_GEN_API] 章节 {chapter.id} 分析完成，发现 {len(chapter_result.get('environment_tracks', []))} 个轨道")
            
            # 构建分析统计
            analysis_stats = {
                'total_chapters': len(chapters),
                'total_tracks': total_tracks,
                'analysis_time': datetime.now().isoformat()
            }
        
        # 确定项目ID和保存策略
        if project_id:
            # 使用指定的项目ID，更新现有项目
            logger.info(f"[ENV_GEN_API] 使用指定项目ID: {project_id}")
            
            # 查找现有项目并更新
            existing_project = db.query(EnvironmentProject).filter(EnvironmentProject.id == project_id).first()
            if existing_project:
                # 直接更新现有项目的分析结果
                existing_project.analysis_result = multi_chapter_result
                existing_project.matching_result = {
                    'analysis_stats': analysis_stats,
                    'session_stage': 'analyzed'
                }
                existing_project.analysis_options = analysis_options
                existing_project.status = 'analyzed'
                existing_project.updated_at = datetime.now()
                
                # 更新统计信息
                existing_project.analysis_tracks = total_tracks
                
                db.commit()
                logger.info(f"[ENV_GEN_API] 更新指定项目: {project_id}")
            else:
                logger.warning(f"[ENV_GEN_API] 指定的项目ID {project_id} 不存在")
        else:
            # 查找或创建环境音项目
            env_service = EnvironmentProjectService(db)
            
            # 查找现有项目（通过书籍ID）
            existing_env_project = db.query(EnvironmentProject).filter(EnvironmentProject.book_id == book_id).first()
            
            if existing_env_project:
                # 更新现有项目
                env_service.create_or_update(
                    novel_project_id=book_id,  # 使用书籍ID作为novel_project_id
                    analysis_result=multi_chapter_result, # 保存多章节结果
                    analysis_stats=analysis_stats,
                    analysis_options=analysis_options
                )
                project_id = existing_env_project.id
                logger.info(f"[ENV_GEN_API] 更新现有环境音项目: {project_id}")
            else:
                # 创建新项目
                env_project = env_service.create_or_update(
                    novel_project_id=book_id,  # 使用书籍ID作为novel_project_id
                    analysis_result=multi_chapter_result, # 保存多章节结果
                    analysis_stats=analysis_stats,
                    analysis_options=analysis_options
                )
                project_id = env_project.id
                logger.info(f"[ENV_GEN_API] 创建新环境音项目: {project_id}")
        
        logger.info(f"[ENV_GEN_API] 书籍环境音分析完成，项目ID: {project_id}")
        
        return {
            "success": True,
            "project_id": project_id,
            "analysis_result": multi_chapter_result,
            "analysis_stats": analysis_stats,
            "message": f"成功分析 {len(chapters)} 个章节，发现 {total_tracks} 个环境音轨道"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 书籍环境音分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"书籍环境音分析失败: {str(e)}")


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
        analyzer = ChapterEnvironmentAnalyzer()
        analysis_result = await analyzer.analyze_chapters(chapters, analysis_options)
        
        # 构建分析统计
        analysis_stats = {
            'total_chapters': len(chapters),
            'total_tracks': len(analysis_result.get('environment_tracks', [])),
            'analysis_time': datetime.now().isoformat()
        }
        
        # 确定项目ID和保存策略
        project_id = None
        create_project = analysis_options.get('create_project', False)
        
        # 通过书籍ID找到对应的合成项目
        novel_project = db.query(NovelProject).filter(NovelProject.book_id == book.id).first()
        if not novel_project:
            logger.warning(f"[ENV_GEN_API] 书籍 {book.id} 没有对应的合成项目")
            # 如果没有合成项目，使用书籍ID作为后备
            novel_project_id = book.id
        else:
            novel_project_id = novel_project.id
        
        if existing_project_id:
            # 使用指定的现有项目ID
            project_id = existing_project_id
            create_project = True  # 强制保存到现有项目
            logger.info(f"[ENV_GEN_API] 使用现有项目ID: {project_id}")
        elif create_project:
            # 创建新项目
            env_service = EnvironmentProjectService(db)
            env_project = env_service.create_or_update(
                novel_project_id=novel_project_id,  # 使用合成项目ID
                analysis_result=analysis_result,
                analysis_stats=analysis_stats,
                analysis_options=analysis_options
            )
            project_id = env_project.id
            logger.info(f"[ENV_GEN_API] 创建新环境音项目: {project_id}")
        else:
            # 查找现有项目（通过合成项目ID）
            env_service = EnvironmentProjectService(db)
            existing_env_project = env_service.get_by_novel_project_id(novel_project_id)
            
            if existing_env_project:
                # 更新现有项目
                env_service.create_or_update(
                    novel_project_id=novel_project_id,
                    analysis_result=analysis_result,
                    analysis_stats=analysis_stats,
                    analysis_options=analysis_options
                )
                project_id = existing_env_project.id
                logger.info(f"[ENV_GEN_API] 更新现有环境音项目: {project_id}")
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
            "analysis_result": analysis_result,
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
