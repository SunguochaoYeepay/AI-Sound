"""
环境音生成API接口
整合旁白环境分析器和环境配置校对器为完整的API服务
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from app.services.narration_environment_analyzer import NarrationEnvironmentAnalyzer
from app.services.environment_config_validator import EnvironmentConfigValidator
from app.utils.logger import get_logger
from app.database import get_db
from app.models.novel_project import NovelProject
from app.models.analysis_result import AnalysisResult
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

# === Global Storage (Session-based) ===
# 在实际应用中，这应该存储在Redis或数据库中
_analysis_sessions: Dict[str, Dict] = {}

def get_session_id(project_id: int) -> str:
    """生成会话ID"""
    return f"env_gen_{project_id}"

# === API Endpoints ===

@router.post("/analyze")
async def analyze_environment_from_synthesis_plan(
    request: EnvironmentGenerationRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    从synthesis_plan分析环境音需求
    第一步：旁白提取分析
    """
    session_id = get_session_id(request.project_id)
    logger.info(f"[ENV_GEN_API] 开始环境音分析，项目ID: {request.project_id}")
    
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
        narration_count = len([seg for seg in request.synthesis_plan 
                              if seg.get('speaker') == '旁白' or seg.get('character') == '旁白'])
        
        if narration_count == 0:
            logger.warning(f"[ENV_GEN_API] 项目 {request.project_id} 没有旁白内容，无法分析环境音")
            return {
                'success': True,
                'project_id': request.project_id,
                'session_id': session_id,
                'analysis_result': {'environment_tracks': []},
                'analysis_stats': {'total_tracks': 0, 'total_duration': 0.0},
                'message': '该项目没有旁白内容，无需环境音分析'
            }
        
        logger.info(f"[ENV_GEN_API] 检测到{narration_count}个旁白段落，开始分析")
        
        # 初始化分析器
        analyzer = NarrationEnvironmentAnalyzer()
        
        # 分析synthesis_plan
        analysis_result = await analyzer.extract_and_analyze_narration(
            request.synthesis_plan
        )
        
        # 生成分析统计
        analysis_stats = analyzer.get_analysis_stats(analysis_result)
        
        # 保存会话数据
        _analysis_sessions[session_id] = {
            'project_id': request.project_id,
            'analysis_result': analysis_result,
            'analysis_stats': analysis_stats,
            'session_stage': 'analyzed',
            'options': request.options
        }
        
        logger.info(f"[ENV_GEN_API] 分析完成，项目ID: {request.project_id}，"
                   f"检测到{len(analysis_result.get('environment_tracks', []))}个环境轨道")
        
        return {
            'success': True,
            'project_id': request.project_id,
            'session_id': session_id,
            'analysis_result': analysis_result,
            'analysis_stats': analysis_stats
        }
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 分析失败，项目ID: {request.project_id}，错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"环境音分析失败: {str(e)}")

@router.post("/prepare-validation/{project_id}")
async def prepare_validation(project_id: int) -> Dict[str, Any]:
    """
    准备人工校对
    第二步：应用场景继承逻辑，生成校对数据
    """
    session_id = get_session_id(project_id)
    
    if session_id not in _analysis_sessions:
        raise HTTPException(status_code=404, detail="分析会话不存在，请先执行分析步骤")
        
    session_data = _analysis_sessions[session_id]
    if session_data['session_stage'] != 'analyzed':
        raise HTTPException(status_code=400, detail=f"会话状态错误: {session_data['session_stage']}")
        
    try:
        # 初始化校对器
        validator = EnvironmentConfigValidator()
        
        # 准备校对数据
        environment_tracks = session_data['analysis_result'].get('environment_tracks', [])
        validation_data = validator.prepare_validation_data(environment_tracks)
        
        # 更新会话数据
        session_data['validation_data'] = validation_data
        session_data['session_stage'] = 'validation_prepared'
        
        logger.info(f"[ENV_GEN_API] 校对数据准备完成，项目ID: {project_id}，"
                   f"待校对轨道: {validation_data['validation_summary']['total_tracks']}个")
        
        return {
            'success': True,
            'project_id': project_id,
            'validation_data': validation_data,
            'validation_summary': validator.get_validation_summary(validation_data)
        }
        
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 校对准备失败，项目ID: {project_id}，错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"校对准备失败: {str(e)}")

@router.post("/edit-validation/{project_id}")
async def edit_validation(
    project_id: int,
    request: ValidationEditRequest
) -> Dict[str, Any]:
    """
    应用人工编辑
    校对步骤的子项：环境音ID匹配
    """
    session_id = get_session_id(project_id)
    
    if session_id not in _analysis_sessions:
        raise HTTPException(status_code=404, detail="分析会话不存在")
        
    session_data = _analysis_sessions[session_id]
    if 'validation_data' not in session_data:
        raise HTTPException(status_code=400, detail="校对数据不存在，请先执行校对准备")
        
    try:
        # 初始化校对器
        validator = EnvironmentConfigValidator()
        
        # 应用人工编辑
        updated_validation_data = validator.apply_manual_edits(
            request.track_index,
            request.manual_edits,
            session_data['validation_data']
        )
        
        # 更新会话数据
        session_data['validation_data'] = updated_validation_data
        
        logger.info(f"[ENV_GEN_API] 人工编辑已应用，项目ID: {project_id}，"
                   f"轨道索引: {request.track_index}")
        
        return {
            'success': True,
            'project_id': project_id,
            'track_index': request.track_index,
            'updated_track': updated_validation_data['validation_tracks'][request.track_index],
            'validation_summary': validator.get_validation_summary(updated_validation_data)
        }
        
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 人工编辑失败，项目ID: {project_id}，错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"人工编辑失败: {str(e)}")

@router.post("/approve-validation/{project_id}")
async def approve_validation(
    project_id: int,
    request: ValidationApprovalRequest
) -> Dict[str, Any]:
    """
    校对审批 (通过/拒绝/需要修改)
    """
    session_id = get_session_id(project_id)
    
    if session_id not in _analysis_sessions:
        raise HTTPException(status_code=404, detail="分析会话不存在")
        
    session_data = _analysis_sessions[session_id]
    if 'validation_data' not in session_data:
        raise HTTPException(status_code=400, detail="校对数据不存在")
        
    try:
        # 初始化校对器
        validator = EnvironmentConfigValidator()
        
        # 执行校对审批
        updated_validation_data = validator.validate_track(
            request.track_index,
            request.validation_result,
            session_data['validation_data'],
            request.notes
        )
        
        # 更新会话数据
        session_data['validation_data'] = updated_validation_data
        
        # 获取校对总结
        validation_summary = validator.get_validation_summary(updated_validation_data)
        
        logger.info(f"[ENV_GEN_API] 校对审批完成，项目ID: {project_id}，"
                   f"轨道索引: {request.track_index}，结果: {request.validation_result}")
        
        return {
            'success': True,
            'project_id': project_id,
            'track_index': request.track_index,
            'validation_result': request.validation_result,
            'validation_summary': validation_summary,
            'ready_for_persistence': validation_summary['ready_for_persistence']
        }
        
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 校对审批失败，项目ID: {project_id}，错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"校对审批失败: {str(e)}")

@router.post("/finalize/{project_id}")
async def finalize_environment_generation(project_id: int) -> Dict[str, Any]:
    """
    完成环境音生成流程
    第三步：持久化JSON配置
    """
    session_id = get_session_id(project_id)
    
    if session_id not in _analysis_sessions:
        raise HTTPException(status_code=404, detail="分析会话不存在")
        
    session_data = _analysis_sessions[session_id]
    if 'validation_data' not in session_data:
        raise HTTPException(status_code=400, detail="校对数据不存在")
        
    try:
        # 初始化校对器
        validator = EnvironmentConfigValidator()
        
        # 检查是否可以持久化
        validation_summary = validator.get_validation_summary(session_data['validation_data'])
        if not validation_summary['ready_for_persistence']:
            raise HTTPException(
                status_code=400, 
                detail=f"校对未完成，无法持久化。已审批: {validation_summary['status_distribution'].get('approved', 0)}/"
                      f"{validation_summary['total_tracks']}"
            )
            
        # 准备持久化数据
        persistence_data = validator.prepare_for_persistence(session_data['validation_data'])
        
        if not persistence_data['ready']:
            raise HTTPException(status_code=400, detail="没有校对通过的轨道，无法持久化")
            
        # TODO: 实际持久化到数据库
        # 这里应该调用数据库服务保存environment_config JSON
        
        # 更新会话状态
        session_data['persistence_data'] = persistence_data
        session_data['session_stage'] = 'completed'
        
        logger.info(f"[ENV_GEN_API] 环境音生成完成，项目ID: {project_id}，"
                   f"持久化{len(persistence_data['persistence_tracks'])}个轨道")
        
        return {
            'success': True,
            'project_id': project_id,
            'session_stage': 'completed',
            'persistence_data': persistence_data,
            'next_steps': {
                'description': '环境音配置已生成，可以进行音频混合',
                'suggested_action': '在合成中心执行音频混合流程'
            }
        }
        
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 环境音生成完成失败，项目ID: {project_id}，错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"环境音生成完成失败: {str(e)}")

@router.get("/status/{project_id}")
async def get_generation_status(project_id: int) -> Dict[str, Any]:
    """
    获取环境音生成状态
    """
    session_id = get_session_id(project_id)
    
    if session_id not in _analysis_sessions:
        return {
            'exists': False,
            'project_id': project_id,
            'session_stage': 'not_started'
        }
        
    session_data = _analysis_sessions[session_id]
    
    # 构建状态响应
    status_response = {
        'exists': True,
        'project_id': project_id,
        'session_stage': session_data.get('session_stage', 'unknown')
    }
    
    # 根据阶段添加相应数据
    if 'analysis_stats' in session_data:
        status_response['analysis_stats'] = session_data['analysis_stats']
        
    if 'validation_data' in session_data:
        validator = EnvironmentConfigValidator()
        status_response['validation_summary'] = validator.get_validation_summary(
            session_data['validation_data']
        )
        
    if 'persistence_data' in session_data:
        status_response['persistence_summary'] = session_data['persistence_data']['persistence_summary']
        
    return status_response

@router.delete("/session/{project_id}")
async def clear_generation_session(project_id: int) -> Dict[str, Any]:
    """
    清除环境音生成会话
    """
    session_id = get_session_id(project_id)
    
    if session_id in _analysis_sessions:
        del _analysis_sessions[session_id]
        logger.info(f"[ENV_GEN_API] 会话已清除，项目ID: {project_id}")
        return {
            'success': True,
            'project_id': project_id,
            'message': '会话已清除'
        }
    else:
        return {
            'success': False,
            'project_id': project_id,
            'message': '会话不存在'
        } 