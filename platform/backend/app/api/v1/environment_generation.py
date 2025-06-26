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

class EnvironmentGenerationRequest(BaseModel):
    """环境音生成请求"""
    generation_plan: List[Dict[str, Any]]
    generation_options: Optional[Dict[str, Any]] = {}

class TimelineExportRequest(BaseModel):
    """时间轴导出请求"""
    timeline_data: Dict[str, Any]
    export_format: str = 'generic'  # generic, premiere_pro, davinci_resolve
    output_path: Optional[str] = None

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
    支持force_reanalyze参数强制重新分析
    """
    session_id = get_session_id(request.project_id)
    force_reanalyze = request.options.get('force_reanalyze', False)
    
    logger.info(f"[ENV_GEN_API] 开始环境音分析，项目ID: {request.project_id}，强制重新分析: {force_reanalyze}")
    
    # 检查是否已有分析结果
    if not force_reanalyze and session_id in _analysis_sessions:
        existing_session = _analysis_sessions[session_id]
        if 'analysis_result' in existing_session:
            logger.info(f"[ENV_GEN_API] 发现已有分析结果，项目ID: {request.project_id}")
            return {
                'success': True,
                'project_id': request.project_id,
                'session_id': session_id,
                'analysis_result': existing_session['analysis_result'],
                'analysis_stats': existing_session.get('analysis_stats', {}),
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
        logger.error(f"🔍 [ENV_GEN_API] 调试：检查旁白内容，synthesis_plan有{len(request.synthesis_plan)}个段落")
        for i, seg in enumerate(request.synthesis_plan):
            logger.error(f"🔍 段落{i+1}: speaker='{seg.get('speaker')}', character='{seg.get('character')}', text='{seg.get('text', '')[:30]}...'")
        
        # 支持多种旁白标识
        narration_speakers = ['旁白', 'narrator', '叙述者', 'narration']
        narration_count = len([seg for seg in request.synthesis_plan 
                              if seg.get('speaker') in narration_speakers or seg.get('character') in narration_speakers])
        
        logger.error(f"🔍 [ENV_GEN_API] 旁白检测结果：narration_count = {narration_count}")
        
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
    支持直接从分析结果生成配置（跳过校对步骤）
    """
    session_id = get_session_id(project_id)
    
    if session_id not in _analysis_sessions:
        raise HTTPException(status_code=404, detail="分析会话不存在")
        
    session_data = _analysis_sessions[session_id]
    
    # 检查是否有分析结果
    if 'analysis_result' not in session_data:
        raise HTTPException(status_code=400, detail="分析结果不存在")
        
    try:
        # 如果有校对数据，使用校对后的配置
        if 'validation_data' in session_data:
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
        else:
            # 直接从分析结果生成配置（跳过校对步骤）
            analysis_result = session_data['analysis_result']
            environment_tracks = analysis_result.get('environment_tracks', [])
            
            # 为每个轨道生成默认的TangoFlux配置
            final_tracks = []
            for i, track in enumerate(environment_tracks):
                # 生成默认的TangoFlux提示词
                keywords = track.get('environment_keywords', [])
                default_prompt = ', '.join(keywords) if keywords else 'ambient environment sound'
                
                final_track = {
                    'track_index': i,
                    'segment_id': track['segment_id'],
                    'start_time': track['start_time'],
                    'duration': track['duration'],
                    'environment_keywords': keywords,
                    'scene_description': track.get('scene_description', ''),
                    'confidence': track.get('confidence', 0.8),
                    'tangoflux_config': {
                        'prompt': default_prompt,
                        'volume': 0.6,
                        'duration': track['duration'],
                        'fade_in': 3.0,
                        'fade_out': 2.0,
                        'loop': True
                    },
                    'validation_status': 'auto_approved',
                    'auto_generated': True
                }
                final_tracks.append(final_track)
            
            # 构建持久化数据
            persistence_data = {
                'ready': True,
                'persistence_tracks': final_tracks,
                'persistence_summary': {
                    'total_tracks': len(final_tracks),
                    'approved_tracks_count': len(final_tracks),
                    'total_duration': sum(track['duration'] for track in final_tracks),
                    'inheritance_count': 0,
                    'manual_edits_count': 0,
                    'auto_generated_count': len(final_tracks)
                },
                'generation_method': 'direct_from_analysis'
            }
            
        # TODO: 实际持久化到数据库
        # 这里应该调用数据库服务保存environment_config JSON
        
        # 更新会话状态
        session_data['persistence_data'] = persistence_data
        session_data['session_stage'] = 'completed'
        
        # 生成最终配置
        final_config = {
            'environment_tracks': persistence_data['persistence_tracks'],
            'global_settings': {
                'default_volume': 0.6,
                'default_fade_in': 3.0,
                'default_fade_out': 2.0
            },
            'generation_metadata': {
                'project_id': project_id,
                'generation_method': persistence_data.get('generation_method', 'validation_based'),
                'generation_timestamp': session_data.get('analysis_result', {}).get('analysis_timestamp'),
                'total_tracks': persistence_data['persistence_summary']['total_tracks']
            }
        }
        
        # 将最终配置添加到会话数据
        session_data['final_config'] = final_config
        
        logger.info(f"[ENV_GEN_API] 环境音生成完成，项目ID: {project_id}，"
                   f"持久化{len(persistence_data['persistence_tracks'])}个轨道")
        
        return {
            'success': True,
            'project_id': project_id,
            'session_stage': 'completed',
            'config': final_config,
            'analysis_stats': session_data.get('analysis_stats', {}),
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

@router.get("/config/{project_id}")
async def get_environment_config(project_id: int) -> Dict[str, Any]:
    """
    获取项目的环境音配置（类似角色管理）
    返回已分析的环境音轨道配置，支持查看和编辑
    """
    session_id = get_session_id(project_id)
    
    if session_id not in _analysis_sessions:
        return {
            'success': False,
            'error': 'No session found',
            'message': '未找到环境音分析会话',
            'config': None
        }
        
    session_data = _analysis_sessions[session_id]
    
    # 构建配置响应
    config_response = {
        'success': True,
        'project_id': project_id,
        'session_stage': session_data.get('session_stage', 'unknown'),
        'config': {
            'environment_tracks': [],
            'global_settings': {
                'default_volume': 0.6,
                'default_fade_in': 3.0,
                'default_fade_out': 2.0
            }
        }
    }
    
    # 优先使用最终配置（如果存在）
    if 'final_config' in session_data:
        config_response['config'] = session_data['final_config']
    # 其次使用校对后的配置
    elif 'validation_data' in session_data:
        validation_tracks = session_data['validation_data'].get('validation_tracks', [])
        
        for i, val_track in enumerate(validation_tracks):
            track_config = {
                'track_index': i,
                'segment_id': val_track['segment_id'],
                'start_time': val_track['start_time'],
                'duration': val_track['duration'],
                'environment_keywords': val_track.get('environment_keywords', []),
                'scene_description': val_track.get('scene_description', ''),
                'confidence': val_track.get('confidence', 0.0),
                'tangoflux_config': val_track.get('tangoflux_config', {}),
                'validation_status': val_track.get('validation_status', 'pending'),
                'user_confirmed': val_track.get('user_confirmed', False),
                'inheritance_applied': val_track.get('inheritance_applied', False),
                'inherited_environment': val_track.get('inherited_environment')
            }
            
            config_response['config']['environment_tracks'].append(track_config)
    # 最后使用原始分析结果
    elif 'analysis_result' in session_data:
        tracks = session_data['analysis_result'].get('environment_tracks', [])
        
        for i, track in enumerate(tracks):
            # 生成默认的TangoFlux配置
            keywords = track.get('environment_keywords', [])
            default_prompt = ', '.join(keywords) if keywords else 'ambient environment sound'
            
            track_config = {
                'track_index': i,
                'segment_id': track['segment_id'],
                'start_time': track['start_time'],
                'duration': track['duration'],
                'environment_keywords': keywords,
                'scene_description': track.get('scene_description', ''),
                'confidence': track.get('confidence', 0.0),
                'tangoflux_config': {
                    'prompt': default_prompt,
                    'volume': 0.6,
                    'duration': track['duration'],
                    'fade_in': 3.0,
                    'fade_out': 2.0,
                    'loop': True
                },
                'validation_status': 'auto_generated',
                'user_confirmed': False
            }
            
            config_response['config']['environment_tracks'].append(track_config)
    

    
    # 添加统计信息
    if 'analysis_stats' in session_data:
        config_response['analysis_stats'] = session_data['analysis_stats']
    
    return config_response

@router.put("/track/{project_id}/{track_index}")
async def update_track_config(
    project_id: int, 
    track_index: int, 
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    更新环境音轨道配置（支持手动设置环境音ID）
    """
    session_id = get_session_id(project_id)
    
    if session_id not in _analysis_sessions:
        raise HTTPException(status_code=404, detail="分析会话不存在")
        
    session_data = _analysis_sessions[session_id]
    
    if 'analysis_result' not in session_data:
        raise HTTPException(status_code=400, detail="没有分析结果可以更新")
    
    tracks = session_data['analysis_result'].get('environment_tracks', [])
    
    if track_index < 0 or track_index >= len(tracks):
        raise HTTPException(status_code=400, detail=f"轨道索引 {track_index} 超出范围")
    
    try:
        track = tracks[track_index]
        
        # 更新允许的配置项
        updatable_fields = [
            'environment_keywords', 'scene_description', 'environment_sound_id',
            'tangoflux_config', 'volume', 'fade_in', 'fade_out', 'loop_enabled',
            'validation_status', 'user_confirmed'
        ]
        
        for field in updatable_fields:
            if field in config:
                track[field] = config[field]
        
        # 特殊处理环境音ID关联
        if 'environment_sound_id' in config:
            track['environment_sound_id'] = config['environment_sound_id']
            # 如果选择了环境音库中的音频，标记为库音频
            track['use_library_sound'] = config['environment_sound_id'] is not None
        
        # 更新时间戳
        track['updated_at'] = datetime.now().isoformat()
        
        logger.info(f"[ENV_GEN_API] 更新轨道配置，项目ID: {project_id}，轨道: {track_index}")
        
        return {
            'success': True,
            'project_id': project_id,
            'track_index': track_index,
            'updated_config': track,
            'message': f'轨道 {track_index + 1} 配置更新成功'
        }
        
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 更新轨道配置失败，项目ID: {project_id}，错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新轨道配置失败: {str(e)}")

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

# === 新流程API端点 ===

@router.post("/chapters/analyze")
async def analyze_chapters_environment(
    request: ChapterEnvironmentAnalysisRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    章节级环境音智能分析 - 新流程第2步
    支持多章节批量分析，生成精确时间轴和强度配置
    """
    logger.info(f"[CHAPTER_ENV_API] 开始章节环境音分析，章节数: {len(request.chapter_ids)}")
    
    try:
        # 验证章节是否存在且有智能准备结果
        analysis_results = []
        chapter_contents = {}
        
        for chapter_id in request.chapter_ids:
            # 获取章节信息
            chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
            if not chapter:
                raise HTTPException(status_code=404, detail=f"章节 {chapter_id} 不存在")
            
            # 获取章节的智能准备结果
            analysis_result = db.query(AnalysisResult).filter(
                AnalysisResult.chapter_id == chapter_id,
                AnalysisResult.status == 'completed',
                AnalysisResult.synthesis_plan.isnot(None)
            ).order_by(AnalysisResult.created_at.desc()).first()
            
            if not analysis_result or not analysis_result.synthesis_plan:
                raise HTTPException(
                    status_code=422, 
                    detail=f"章节 {chapter_id} ({chapter.chapter_title}) 没有完成智能准备，请先执行智能准备步骤"
                )
            
            # 提取synthesis_plan
            synthesis_plan = []
            if isinstance(analysis_result.synthesis_plan, dict) and 'synthesis_plan' in analysis_result.synthesis_plan:
                synthesis_plan = analysis_result.synthesis_plan['synthesis_plan']
            elif isinstance(analysis_result.synthesis_plan, list):
                synthesis_plan = analysis_result.synthesis_plan
            
            if not synthesis_plan:
                raise HTTPException(
                    status_code=422,
                    detail=f"章节 {chapter_id} 的合成计划格式不正确"
                )
            
            analysis_results.append({
                'chapter_id': chapter_id,
                'chapter_title': chapter.chapter_title,
                'chapter_number': chapter.chapter_number,
                'synthesis_plan': synthesis_plan,
                'word_count': chapter.word_count
            })
            
            chapter_contents[chapter_id] = chapter.content or ""
        
        logger.info(f"[CHAPTER_ENV_API] 验证通过，开始分析{len(analysis_results)}个章节")
        
        # 初始化增强分析器
        analyzer = ChapterEnvironmentAnalyzer()
        
        # 逐章节分析
        chapter_analysis_results = []
        total_tracks = 0
        total_duration = 0.0
        
        for chapter_data in analysis_results:
            chapter_id = chapter_data['chapter_id']
            chapter_content = chapter_contents[chapter_id]
            synthesis_plan = chapter_data['synthesis_plan']
            
            logger.info(f"[CHAPTER_ENV_API] 分析章节 {chapter_id}: {chapter_data['chapter_title']}")
            
            # 执行章节级分析
            chapter_result = await analyzer.analyze_chapter_environment(
                chapter_content=chapter_content,
                synthesis_plan=synthesis_plan,
                options=request.analysis_options
            )
            
            if chapter_result['success']:
                # 添加章节信息
                chapter_result['chapter_info'] = {
                    'chapter_id': chapter_id,
                    'chapter_title': chapter_data['chapter_title'],
                    'chapter_number': chapter_data['chapter_number'],
                    'word_count': chapter_data['word_count']
                }
                
                chapter_analysis_results.append(chapter_result)
                
                # 统计信息
                tracks_count = len(chapter_result['analysis_result']['environment_tracks'])
                duration = chapter_result['analysis_result']['analysis_metadata']['total_duration']
                total_tracks += tracks_count
                total_duration += duration
                
                logger.info(f"[CHAPTER_ENV_API] 章节 {chapter_id} 分析完成: {tracks_count}个轨道, {duration:.1f}秒")
            else:
                logger.error(f"[CHAPTER_ENV_API] 章节 {chapter_id} 分析失败")
                raise HTTPException(status_code=500, detail=f"章节 {chapter_id} 分析失败")
        
        # 生成综合结果
        combined_result = {
            'success': True,
            'analysis_timestamp': datetime.now().isoformat(),
            'chapters_analyzed': len(chapter_analysis_results),
            'total_tracks': total_tracks,
            'total_duration': round(total_duration, 1),
            'avg_tracks_per_chapter': round(total_tracks / len(chapter_analysis_results), 1) if chapter_analysis_results else 0,
            'chapters': chapter_analysis_results,
            'analysis_summary': {
                'analyzer_version': '2.0_enhanced',
                'features_enabled': [
                    'precise_timing',
                    'intensity_analysis', 
                    'continuity_analysis',
                    'video_timeline_generation'
                ],
                'ready_for_matching': True
            }
        }
        
        logger.info(f"[CHAPTER_ENV_API] 章节环境音分析完成: {len(chapter_analysis_results)}个章节, "
                   f"总计{total_tracks}个轨道, {total_duration:.1f}秒")
        
        return combined_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CHAPTER_ENV_API] 章节环境音分析失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"章节环境音分析失败: {str(e)}")

@router.get("/chapters/{chapter_id}/timeline")
async def get_chapter_timeline(
    chapter_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取章节环境音时间轴 - 用于预览和编辑
    """
    try:
        # 这里应该从缓存或数据库中获取已分析的时间轴
        # 暂时返回示例数据
        return {
            'success': True,
            'chapter_id': chapter_id,
            'timeline': {
                'timeline_version': '1.0',
                'total_duration': 300.0,
                'tracks': []
            },
            'message': '时间轴获取功能正在开发中'
        }
        
    except Exception as e:
        logger.error(f"[CHAPTER_ENV_API] 获取章节时间轴失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取时间轴失败: {str(e)}")

@router.post("/match-sounds")
async def match_environment_sounds(
    request: EnvironmentMatchingRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    环境音智能匹配 - 新流程第3步
    为分析结果中的环境音需求匹配已有环境音
    """
    logger.info("[MATCHING_API] 开始环境音智能匹配")
    
    try:
        # 初始化匹配引擎
        matching_engine = SoundMatchingEngine()
        
        # 执行批量匹配
        enhanced_result = await matching_engine.batch_match_analysis_result(
            request.analysis_result,
            db
        )
        
        # 生成环境音生成计划
        generation_plan = matching_engine.get_generation_plan(enhanced_result)
        
        # 构建响应
        matching_response = {
            'success': True,
            'matching_timestamp': datetime.now().isoformat(),
            'enhanced_analysis_result': enhanced_result,
            'generation_plan': generation_plan,
            'matching_summary': enhanced_result.get('matching_summary', {}),
            'ready_for_generation': len(generation_plan['need_generation']) > 0
        }
        
        # 安全地获取匹配汇总信息
        matching_summary = enhanced_result.get('matching_summary', {})
        matched_tracks = matching_summary.get('matched_tracks', 0)
        need_generation_tracks = matching_summary.get('need_generation_tracks', 0)
        
        logger.info(f"[MATCHING_API] 匹配完成: "
                   f"{matched_tracks}个已匹配, "
                   f"{need_generation_tracks}个需生成")
        
        return matching_response
        
    except Exception as e:
        logger.error(f"[MATCHING_API] 环境音匹配失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"环境音匹配失败: {str(e)}")

@router.get("/sounds/search")
async def search_environment_sounds(
    keywords: str,
    max_results: int = 10,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    搜索环境音 - 支持关键词匹配
    """
    try:
        matching_engine = SoundMatchingEngine()
        keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
        
        matches = await matching_engine.find_matching_sounds(keyword_list, db, max_results)
        
        return {
            'success': True,
            'keywords': keyword_list,
            'total_matches': len(matches),
            'matches': [match.to_dict() for match in matches]
        }
        
    except Exception as e:
        logger.error(f"[MATCHING_API] 环境音搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"环境音搜索失败: {str(e)}")

@router.post("/generate-sounds")
async def generate_environment_sounds(
    request: EnvironmentGenerationRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    环境音批量生成 - 新流程第4步
    使用TangoFlux AI生成需要的环境音
    """
    logger.info("[GENERATION_API] 开始环境音批量生成")
    
    try:
        # 初始化生成器
        generator = TangoFluxEnvironmentGenerator()
        
        # 检查TangoFlux服务健康状态
        if not await generator.check_service_health():
            raise HTTPException(status_code=503, detail="TangoFlux服务不可用")
        
        # 准备生成请求
        generation_requests = []
        for item in request.generation_plan:
            generation_request = {
                'keyword': item.get('keyword', ''),
                'description': item.get('example_scene', ''),
                'duration': item.get('suggested_duration', 30.0),
                'intensity': item.get('intensity_level', 'medium')
            }
            generation_requests.append(generation_request)
        
        # 执行批量生成
        generation_tasks = await generator.batch_generate_environment_sounds(
            generation_requests,
            max_concurrent=request.generation_options.get('max_concurrent', 3)
        )
        
        # 保存生成结果到数据库
        saved_sounds = await generator.save_generated_sounds_to_database(
            generation_tasks, db
        )
        
        # 构建响应
        response = {
            'success': True,
            'generation_timestamp': datetime.now().isoformat(),
            'total_requested': len(generation_requests),
            'total_completed': len([task for task in generation_tasks if task.status == 'completed']),
            'total_failed': len([task for task in generation_tasks if task.status == 'failed']),
            'generation_tasks': [task.to_dict() for task in generation_tasks],
            'saved_sounds': [
                {
                    'id': sound.id,
                    'name': sound.name,
                    'file_path': sound.file_path,
                    'duration': sound.duration,
                    'tags': sound.tags
                } for sound in saved_sounds
            ]
        }
        
        logger.info(f"[GENERATION_API] 批量生成完成: {len(saved_sounds)}个成功保存")
        
        return response
        
    except Exception as e:
        logger.error(f"[GENERATION_API] 环境音生成失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"环境音生成失败: {str(e)}")

@router.post("/create-timeline")
async def create_environment_timeline(
    analysis_result: Dict[str, Any],
    matching_result: Dict[str, Any],
    project_name: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    创建环境音时间轴 - 集成分析和匹配结果
    """
    logger.info("[TIMELINE_API] 开始创建环境音时间轴")
    
    try:
        # 初始化时间轴生成器
        timeline_generator = EnvironmentTimelineGenerator()
        
        # 创建时间轴
        timeline = timeline_generator.create_timeline_from_analysis(
            analysis_result, matching_result, project_name
        )
        
        # 验证时间轴
        validation_result = timeline_generator.validate_timeline(timeline)
        
        # 导出通用格式
        timeline_data = timeline_generator.export_timeline(timeline, 'generic')
        
        response = {
            'success': True,
            'timeline_created': True,
            'project_name': timeline.project_name,
            'total_duration': timeline.total_duration,
            'total_tracks': len(timeline.tracks),
            'timeline_data': timeline_data,
            'validation_result': validation_result,
            'created_at': datetime.now().isoformat()
        }
        
        logger.info(f"[TIMELINE_API] 时间轴创建完成: {timeline.project_name}")
        
        return response
        
    except Exception as e:
        logger.error(f"[TIMELINE_API] 时间轴创建失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"时间轴创建失败: {str(e)}")

@router.post("/export-timeline")
async def export_timeline(
    request: TimelineExportRequest
) -> Dict[str, Any]:
    """
    导出时间轴为视频编辑软件兼容格式
    """
    logger.info(f"[TIMELINE_API] 开始导出时间轴: {request.export_format}")
    
    try:
        # 初始化时间轴生成器
        timeline_generator = EnvironmentTimelineGenerator()
        
        # 从请求数据重建时间轴对象
        timeline_data = request.timeline_data.get('timeline', {})
        
        # 这里需要一个helper方法来从JSON数据重建TimelineObject
        # 简化实现，直接处理数据
        if request.export_format == 'premiere_pro':
            exported_data = {
                'project': {
                    'name': timeline_data.get('project_name', 'Environment_Project'),
                    'format': 'adobe_premiere_pro',
                    'version': '2.0',
                    'settings': {
                        'frame_rate': timeline_data.get('frame_rate', 30),
                        'sample_rate': timeline_data.get('sample_rate', 44100),
                        'total_duration': timeline_data.get('total_duration', 300.0)
                    }
                },
                'sequences': [{
                    'name': f"{timeline_data.get('project_name', 'Environment')}_环境音轨道",
                    'duration': timeline_data.get('total_duration', 300.0),
                    'audio_tracks': [
                        {
                            'track_number': i + 1,
                            'track_name': f"环境音轨道_{i+1}",
                            'clips': [{
                                'clip_id': track.get('track_id'),
                                'name': track.get('sound_name'),
                                'media_source': track.get('audio_file_path'),
                                'in_point': 0,
                                'out_point': track.get('duration', 30.0),
                                'timeline_in': track.get('start_time', 0.0),
                                'timeline_out': track.get('end_time', 30.0),
                                'volume': track.get('volume', 0.7) * 100,
                                'fade_in_duration': track.get('fade_in', 1.0),
                                'fade_out_duration': track.get('fade_out', 1.0),
                                'loop_enabled': track.get('loop_enabled', True),
                                'audio_effects': []
                            }]
                        } for i, track in enumerate(timeline_data.get('tracks', []))
                    ]
                }],
                'metadata': timeline_data.get('metadata', {})
            }
        elif request.export_format == 'davinci_resolve':
            exported_data = {
                'resolve_project': {
                    'name': timeline_data.get('project_name', 'Environment_Project'),
                    'format': 'davinci_resolve',
                    'version': '2.0',
                    'timeline_settings': {
                        'frame_rate': f"{timeline_data.get('frame_rate', 30)}fps",
                        'resolution': "1920x1080",
                        'audio_sample_rate': timeline_data.get('sample_rate', 44100)
                    }
                },
                'timeline': {
                    'name': f"{timeline_data.get('project_name', 'Environment')}_Timeline",
                    'duration_frames': int(timeline_data.get('total_duration', 300.0) * timeline_data.get('frame_rate', 30)),
                    'audio_tracks': [
                        {
                            'track_index': i + 1,
                            'track_type': "audio",
                            'clips': [{
                                'clip_name': track.get('sound_name'),
                                'media_pool_item': track.get('audio_file_path'),
                                'start_frame': int(track.get('start_time', 0.0) * timeline_data.get('frame_rate', 30)),
                                'end_frame': int(track.get('end_time', 30.0) * timeline_data.get('frame_rate', 30)),
                                'duration_frames': int(track.get('duration', 30.0) * timeline_data.get('frame_rate', 30)),
                                'volume_db': 20 * (track.get('volume', 0.7) - 1),
                                'fade_in_frames': int(track.get('fade_in', 1.0) * timeline_data.get('frame_rate', 30)),
                                'fade_out_frames': int(track.get('fade_out', 1.0) * timeline_data.get('frame_rate', 30)),
                                'loop_enabled': track.get('loop_enabled', True)
                            }]
                        } for i, track in enumerate(timeline_data.get('tracks', []))
                    ]
                },
                'metadata': timeline_data.get('metadata', {})
            }
        else:
            # 通用格式
            exported_data = request.timeline_data
        
        # 如果指定了输出路径，保存文件
        if request.output_path:
            output_file = Path(request.output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(exported_data, f, indent=2, ensure_ascii=False)
        
        response = {
            'success': True,
            'export_format': request.export_format,
            'exported_data': exported_data,
            'output_path': request.output_path,
            'exported_at': datetime.now().isoformat()
        }
        
        logger.info(f"[TIMELINE_API] 时间轴导出完成: {request.export_format}")
        
        return response
        
    except Exception as e:
        logger.error(f"[TIMELINE_API] 时间轴导出失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"时间轴导出失败: {str(e)}")

@router.get("/generation/status/{task_id}")
async def get_generation_task_status(task_id: str) -> Dict[str, Any]:
    """
    获取生成任务状态
    """
    try:
        generator = TangoFluxEnvironmentGenerator()
        task_status = generator.get_task_status(task_id)
        
        if task_status:
            return {
                'success': True,
                'task_status': task_status
            }
        else:
            raise HTTPException(status_code=404, detail="任务不存在")
            
    except Exception as e:
        logger.error(f"[GENERATION_API] 获取任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")

@router.get("/generation/tasks")
async def get_all_generation_tasks() -> Dict[str, Any]:
    """
    获取所有活动生成任务状态
    """
    try:
        generator = TangoFluxEnvironmentGenerator()
        all_tasks = generator.get_all_active_tasks()
        
        return {
            'success': True,
            'total_tasks': len(all_tasks),
            'tasks': all_tasks
        }
        
    except Exception as e:
        logger.error(f"[GENERATION_API] 获取所有任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取所有任务失败: {str(e)}") 