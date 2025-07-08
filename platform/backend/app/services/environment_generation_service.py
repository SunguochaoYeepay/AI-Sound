"""
环境音生成服务 - 整合分析、校对、持久化的完整流程
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .narration_environment_analyzer import NarrationEnvironmentAnalyzer
from .environment_config_validator import EnvironmentConfigValidator
from ..models.environment_generation import (
    EnvironmentGenerationSession,
    EnvironmentTrackConfig,
    EnvironmentGenerationLog
)

logger = logging.getLogger(__name__)


class EnvironmentGenerationService:
    """环境音生成服务 - 方案A完整实现"""
    
    def __init__(self, db: Session):
        self.db = db
        self.analyzer = NarrationEnvironmentAnalyzer(db=db)  # 传递数据库会话
        self.validator = EnvironmentConfigValidator()
        
    def log_operation(self, session_id: int, level: str, message: str, 
                     operation: str = None, details: Dict = None):
        """记录操作日志"""
        try:
            log_entry = EnvironmentGenerationLog(
                session_id=session_id,
                log_level=level,
                log_message=message,
                log_details=details,
                operation=operation
            )
            self.db.add(log_entry)
            self.db.commit()
        except Exception as e:
            logger.error(f"记录日志失败: {e}")
    
    def create_or_get_session(self, project_id: int, chapter_id: str) -> EnvironmentGenerationSession:
        """创建或获取环境音生成会话"""
        # 查找现有的活跃会话
        existing_session = self.db.query(EnvironmentGenerationSession).filter(
            EnvironmentGenerationSession.project_id == project_id,
            EnvironmentGenerationSession.chapter_id == chapter_id,
            EnvironmentGenerationSession.session_status == 'active'
        ).first()
        
        if existing_session:
            logger.info(f"找到现有会话: {existing_session.id}")
            return existing_session
        
        # 创建新会话
        new_session = EnvironmentGenerationSession(
            project_id=project_id,
            chapter_id=chapter_id,
            session_status='active'
        )
        self.db.add(new_session)
        self.db.commit()
        self.db.refresh(new_session)
        
        self.log_operation(
            new_session.id, 
            'INFO', 
            f'创建新的环境音生成会话 - 项目: {project_id}, 章节: {chapter_id}',
            'create_session'
        )
        
        logger.info(f"创建新会话: {new_session.id}")
        return new_session
    
    def step1_analyze_environment(self, project_id: int, synthesis_plan: Dict[str, Any], 
                                 options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        第一步：环境音需求分析
        从synthesis_plan中提取旁白内容，分析环境关键词
        """
        try:
            # 从synthesis_plan中提取章节ID
            chapter_id = synthesis_plan.get('chapter_id', 'unknown')
            
            # 创建或获取会话
            session = self.create_or_get_session(project_id, chapter_id)
            
            self.log_operation(
                session.id, 
                'INFO', 
                '开始环境音需求分析',
                'analyze',
                {'synthesis_plan_segments': len(synthesis_plan.get('segments', []))}
            )
            
            # 使用分析器处理 - 调用正确的方法名
            # 注意：此方法需要synthesis_plan中包含segments列表
            segments = synthesis_plan.get('segments', [])
            if not segments:
                # 如果没有segments，尝试直接使用synthesis_plan作为segments
                segments = synthesis_plan if isinstance(synthesis_plan, list) else []
            
            # 由于分析器方法是异步的，这里需要同步调用
            import asyncio
            
            try:
                # 在新的事件循环中运行异步方法
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                raw_result = loop.run_until_complete(
                    self.analyzer.extract_and_analyze_narration(segments)
                )
                loop.close()
                
                # 转换结果格式以匹配期望的结构
                analysis_result = {
                    'analysis_result': raw_result,
                    'analysis_stats': raw_result.get('analysis_summary', {})
                }
                
            except Exception as analyzer_error:
                logger.error(f"分析器执行失败: {analyzer_error}")
                # 提供一个默认的空结果
                analysis_result = {
                    'analysis_result': {
                        'environment_tracks': [],
                        'analysis_summary': {
                            'total_duration': 0.0,
                            'narration_segments': 0,
                            'environment_tracks_detected': 0,
                            'analysis_timestamp': datetime.utcnow().isoformat(),
                            'error': str(analyzer_error)
                        }
                    },
                    'analysis_stats': {
                        'total_duration': 0.0,
                        'avg_confidence': 0.0,
                        'error': str(analyzer_error)
                    }
                }
            
            # 保存分析结果到数据库
            session.analysis_result = analysis_result['analysis_result']
            session.analysis_stats = analysis_result['analysis_stats']
            session.analysis_timestamp = datetime.utcnow()
            
            # 创建轨道配置记录
            environment_tracks = analysis_result['analysis_result'].get('environment_tracks', [])
            for i, track in enumerate(environment_tracks):
                track_config = EnvironmentTrackConfig(
                    session_id=session.id,
                    segment_id=track['segment_id'],
                    track_index=i,
                    start_time=track['start_time'],
                    duration=track['duration'],
                    scene_description=track.get('scene_description'),
                    environment_keywords=track.get('environment_keywords', []),
                    confidence=track.get('confidence', 0.0),
                    validation_status='pending'
                )
                self.db.add(track_config)
            
            self.db.commit()
            self.db.refresh(session)
            
            self.log_operation(
                session.id, 
                'INFO', 
                f'环境音分析完成 - 检测到 {len(environment_tracks)} 个轨道',
                'analyze',
                {
                    'total_tracks': len(environment_tracks),
                    'total_duration': analysis_result['analysis_stats'].get('total_duration', 0),
                    'avg_confidence': analysis_result['analysis_stats'].get('avg_confidence', 0)
                }
            )
            
            return {
                'success': True,
                'session_id': session.id,
                'analysis_result': analysis_result['analysis_result'],
                'analysis_stats': analysis_result['analysis_stats'],
                'message': f'环境音分析完成，检测到 {len(environment_tracks)} 个环境音轨道'
            }
            
        except Exception as e:
            logger.error(f"环境音分析失败: {e}")
            if 'session' in locals():
                self.log_operation(
                    session.id, 
                    'ERROR', 
                    f'环境音分析失败: {str(e)}',
                    'analyze',
                    {'error': str(e)}
                )
            return {
                'success': False,
                'error': str(e),
                'message': '环境音分析失败'
            }
    
    def step2_prepare_validation(self, project_id: int) -> Dict[str, Any]:
        """
        第二步：准备人工校对
        应用场景继承逻辑，生成TangoFlux配置建议
        """
        try:
            # 获取最新的活跃会话
            session = self.db.query(EnvironmentGenerationSession).filter(
                EnvironmentGenerationSession.project_id == project_id,
                EnvironmentGenerationSession.session_status == 'active'
            ).order_by(EnvironmentGenerationSession.created_at.desc()).first()
            
            if not session:
                return {
                    'success': False,
                    'error': 'No active session found',
                    'message': '未找到活跃的环境音生成会话'
                }
            
            self.log_operation(
                session.id, 
                'INFO', 
                '开始准备人工校对',
                'prepare_validation'
            )
            
            # 获取轨道配置
            tracks = self.db.query(EnvironmentTrackConfig).filter(
                EnvironmentTrackConfig.session_id == session.id
            ).order_by(EnvironmentTrackConfig.track_index).all()
            
            if not tracks:
                return {
                    'success': False,
                    'error': 'No tracks found',
                    'message': '未找到环境音轨道数据'
                }
            
            # 转换为校对器需要的格式
            tracks_data = []
            for track in tracks:
                track_data = {
                    'segment_id': track.segment_id,
                    'start_time': track.start_time,
                    'duration': track.duration,
                    'scene_description': track.scene_description,
                    'environment_keywords': track.environment_keywords or [],
                    'confidence': track.confidence or 0.0
                }
                tracks_data.append(track_data)
            
            # 使用校对器处理
            validation_result = self.validator.prepare_validation({
                'environment_tracks': tracks_data
            })
            
            # 保存校对数据到数据库
            session.validation_data = validation_result['validation_data']
            session.validation_summary = validation_result['validation_summary']
            session.validation_timestamp = datetime.utcnow()
            
            # 更新轨道配置的校对信息
            validation_tracks = validation_result['validation_data'].get('validation_tracks', [])
            for i, validation_track in enumerate(validation_tracks):
                if i < len(tracks):
                    db_track = tracks[i]
                    db_track.inheritance_applied = validation_track.get('inheritance_applied', False)
                    db_track.inherited_environment = validation_track.get('inherited_environment')
                    db_track.matching_suggestions = validation_track.get('matching_suggestions', [])
                    
                    # 设置前一个轨道的关联
                    if i > 0 and db_track.inheritance_applied:
                        db_track.previous_track_id = tracks[i-1].id
            
            self.db.commit()
            self.db.refresh(session)
            
            self.log_operation(
                session.id, 
                'INFO', 
                f'人工校对准备完成 - {len(validation_tracks)} 个轨道待校对',
                'prepare_validation',
                {
                    'total_tracks': len(validation_tracks),
                    'inheritance_applied': validation_result['validation_summary'].get('inheritance_applied_count', 0)
                }
            )
            
            return {
                'success': True,
                'session_id': session.id,
                'validation_data': validation_result['validation_data'],
                'validation_summary': validation_result['validation_summary'],
                'message': f'校对数据准备完成，{len(validation_tracks)} 个轨道待校对'
            }
            
        except Exception as e:
            logger.error(f"校对准备失败: {e}")
            if 'session' in locals():
                self.log_operation(
                    session.id, 
                    'ERROR', 
                    f'校对准备失败: {str(e)}',
                    'prepare_validation',
                    {'error': str(e)}
                )
            return {
                'success': False,
                'error': str(e),
                'message': '校对准备失败'
            }
    
    def step3_edit_validation(self, project_id: int, track_index: int, 
                             manual_edits: Dict[str, Any]) -> Dict[str, Any]:
        """
        第三步：应用人工编辑
        """
        try:
            # 获取会话和轨道
            session = self.db.query(EnvironmentGenerationSession).filter(
                EnvironmentGenerationSession.project_id == project_id,
                EnvironmentGenerationSession.session_status == 'active'
            ).order_by(EnvironmentGenerationSession.created_at.desc()).first()
            
            if not session:
                return {
                    'success': False,
                    'error': 'No active session found',
                    'message': '未找到活跃的环境音生成会话'
                }
            
            track = self.db.query(EnvironmentTrackConfig).filter(
                EnvironmentTrackConfig.session_id == session.id,
                EnvironmentTrackConfig.track_index == track_index
            ).first()
            
            if not track:
                return {
                    'success': False,
                    'error': 'Track not found',
                    'message': f'未找到轨道 {track_index}'
                }
            
            self.log_operation(
                session.id, 
                'INFO', 
                f'开始编辑轨道 {track_index}',
                'edit_validation',
                {'track_index': track_index}
            )
            
            # 应用手动编辑
            track.manual_edits = manual_edits
            track.validation_status = 'edited'
            
            # 更新环境关键词
            if 'environment_keywords' in manual_edits:
                track.environment_keywords = manual_edits['environment_keywords']
            
            # 更新场景描述
            if 'scene_description' in manual_edits:
                track.scene_description = manual_edits['scene_description']
            
            # 更新TangoFlux配置
            if 'selected_tangoflux_config' in manual_edits:
                track.selected_tangoflux_config = manual_edits['selected_tangoflux_config']
                track.final_prompt = manual_edits['selected_tangoflux_config'].get('prompt')
                track.volume = manual_edits['selected_tangoflux_config'].get('volume', 0.6)
                track.fade_in = manual_edits['selected_tangoflux_config'].get('fade_in', 3.0)
                track.fade_out = manual_edits['selected_tangoflux_config'].get('fade_out', 2.0)
                track.loop_enabled = manual_edits['selected_tangoflux_config'].get('loop', True)
            
            self.db.commit()
            self.db.refresh(track)
            
            # 构造返回的轨道数据
            updated_track = {
                'segment_id': track.segment_id,
                'track_index': track.track_index,
                'start_time': track.start_time,
                'duration': track.duration,
                'scene_description': track.scene_description,
                'environment_keywords': track.environment_keywords,
                'confidence': track.confidence,
                'inheritance_applied': track.inheritance_applied,
                'inherited_environment': track.inherited_environment,
                'manual_edits': track.manual_edits,
                'validation_status': track.validation_status,
                'matching_suggestions': track.matching_suggestions,
                'selected_tangoflux_config': track.selected_tangoflux_config
            }
            
            self.log_operation(
                session.id, 
                'INFO', 
                f'轨道 {track_index} 编辑完成',
                'edit_validation',
                {'track_index': track_index, 'validation_status': 'edited'}
            )
            
            return {
                'success': True,
                'session_id': session.id,
                'updated_track': updated_track,
                'message': f'轨道 {track_index} 编辑保存成功'
            }
            
        except Exception as e:
            logger.error(f"轨道编辑失败: {e}")
            if 'session' in locals():
                self.log_operation(
                    session.id, 
                    'ERROR', 
                    f'轨道编辑失败: {str(e)}',
                    'edit_validation',
                    {'error': str(e), 'track_index': track_index}
                )
            return {
                'success': False,
                'error': str(e),
                'message': '轨道编辑失败'
            }
    
    def step4_approve_validation(self, project_id: int, track_index: int, 
                                validation_result: str, notes: str = None) -> Dict[str, Any]:
        """
        第四步：校对审批
        """
        try:
            # 获取会话和轨道
            session = self.db.query(EnvironmentGenerationSession).filter(
                EnvironmentGenerationSession.project_id == project_id,
                EnvironmentGenerationSession.session_status == 'active'
            ).order_by(EnvironmentGenerationSession.created_at.desc()).first()
            
            if not session:
                return {
                    'success': False,
                    'error': 'No active session found',
                    'message': '未找到活跃的环境音生成会话'
                }
            
            track = self.db.query(EnvironmentTrackConfig).filter(
                EnvironmentTrackConfig.session_id == session.id,
                EnvironmentTrackConfig.track_index == track_index
            ).first()
            
            if not track:
                return {
                    'success': False,
                    'error': 'Track not found',
                    'message': f'未找到轨道 {track_index}'
                }
            
            self.log_operation(
                session.id, 
                'INFO', 
                f'轨道 {track_index} 校对审批: {validation_result}',
                'approve_validation',
                {'track_index': track_index, 'validation_result': validation_result}
            )
            
            # 更新校对状态
            track.validation_status = validation_result
            track.validation_notes = notes
            track.validation_timestamp = datetime.utcnow()
            
            self.db.commit()
            
            return {
                'success': True,
                'session_id': session.id,
                'track_index': track_index,
                'validation_status': validation_result,
                'message': f'轨道 {track_index} 校对审批完成'
            }
            
        except Exception as e:
            logger.error(f"校对审批失败: {e}")
            if 'session' in locals():
                self.log_operation(
                    session.id, 
                    'ERROR', 
                    f'校对审批失败: {str(e)}',
                    'approve_validation',
                    {'error': str(e), 'track_index': track_index}
                )
            return {
                'success': False,
                'error': str(e),
                'message': '校对审批失败'
            }
    
    def step5_finalize_generation(self, project_id: int) -> Dict[str, Any]:
        """
        第五步：完成环境音生成流程
        持久化最终配置JSON
        """
        try:
            # 获取会话
            session = self.db.query(EnvironmentGenerationSession).filter(
                EnvironmentGenerationSession.project_id == project_id,
                EnvironmentGenerationSession.session_status == 'active'
            ).order_by(EnvironmentGenerationSession.created_at.desc()).first()
            
            if not session:
                return {
                    'success': False,
                    'error': 'No active session found',
                    'message': '未找到活跃的环境音生成会话'
                }
            
            # 获取所有已通过的轨道
            approved_tracks = self.db.query(EnvironmentTrackConfig).filter(
                EnvironmentTrackConfig.session_id == session.id,
                EnvironmentTrackConfig.validation_status == 'approved'
            ).order_by(EnvironmentTrackConfig.track_index).all()
            
            if not approved_tracks:
                return {
                    'success': False,
                    'error': 'No approved tracks found',
                    'message': '未找到已通过校对的轨道'
                }
            
            self.log_operation(
                session.id, 
                'INFO', 
                f'开始完成环境音生成 - {len(approved_tracks)} 个已通过轨道',
                'finalize'
            )
            
            # 构建最终的环境音配置JSON
            final_environment_config = {
                'project_id': project_id,
                'chapter_id': session.chapter_id,
                'session_id': session.id,
                'generation_timestamp': datetime.utcnow().isoformat(),
                'environment_tracks': [],
                'global_settings': {
                    'default_volume': 0.6,
                    'default_fade_in': 3.0,
                    'default_fade_out': 2.0,
                    'overlap_duration': 1.0
                }
            }
            
            total_duration = 0.0
            inheritance_count = 0
            manual_edits_count = 0
            
            for track in approved_tracks:
                track_config = {
                    'segment_id': track.segment_id,
                    'track_index': track.track_index,
                    'start_time': track.start_time,
                    'duration': track.duration,
                    'environment_keywords': track.environment_keywords or [],
                    'scene_description': track.scene_description,
                    'confidence': track.confidence,
                    'tangoflux_config': track.selected_tangoflux_config or {},
                    'final_prompt': track.final_prompt,
                    'volume': track.volume,
                    'fade_in': track.fade_in,
                    'fade_out': track.fade_out,
                    'loop_enabled': track.loop_enabled,
                    'inheritance_applied': track.inheritance_applied,
                    'inherited_environment': track.inherited_environment,
                    'validation_timestamp': track.validation_timestamp.isoformat() if track.validation_timestamp else None
                }
                
                final_environment_config['environment_tracks'].append(track_config)
                total_duration += track.duration
                
                if track.inheritance_applied:
                    inheritance_count += 1
                
                if track.manual_edits:
                    manual_edits_count += 1
            
            # 生成持久化摘要
            persistence_summary = {
                'approved_tracks_count': len(approved_tracks),
                'total_duration': round(total_duration, 2),
                'inheritance_count': inheritance_count,
                'manual_edits_count': manual_edits_count,
                'avg_confidence': sum(track.confidence or 0 for track in approved_tracks) / len(approved_tracks),
                'finalized_timestamp': datetime.utcnow().isoformat()
            }
            
            # 保存持久化数据
            session.persistence_data = final_environment_config
            session.persistence_summary = persistence_summary
            session.persistence_timestamp = datetime.utcnow()
            session.session_status = 'completed'
            
            self.db.commit()
            self.db.refresh(session)
            
            self.log_operation(
                session.id, 
                'INFO', 
                f'环境音生成完成 - {len(approved_tracks)} 个轨道已持久化',
                'finalize',
                persistence_summary
            )
            
            return {
                'success': True,
                'session_id': session.id,
                'persistence_data': final_environment_config,
                'persistence_summary': persistence_summary,
                'message': f'环境音生成完成，{len(approved_tracks)} 个轨道配置已保存'
            }
            
        except Exception as e:
            logger.error(f"完成环境音生成失败: {e}")
            if 'session' in locals():
                self.log_operation(
                    session.id, 
                    'ERROR', 
                    f'完成环境音生成失败: {str(e)}',
                    'finalize',
                    {'error': str(e)}
                )
            return {
                'success': False,
                'error': str(e),
                'message': '完成环境音生成失败'
            }
    
    def get_generation_status(self, project_id: int) -> Dict[str, Any]:
        """获取环境音生成状态"""
        try:
            session = self.db.query(EnvironmentGenerationSession).filter(
                EnvironmentGenerationSession.project_id == project_id,
                EnvironmentGenerationSession.session_status.in_(['active', 'completed'])
            ).order_by(EnvironmentGenerationSession.created_at.desc()).first()
            
            if not session:
                return {
                    'success': False,
                    'error': 'No session found',
                    'message': '未找到环境音生成会话'
                }
            
            # 获取轨道统计
            tracks = self.db.query(EnvironmentTrackConfig).filter(
                EnvironmentTrackConfig.session_id == session.id
            ).all()
            
            track_stats = {
                'total': len(tracks),
                'pending': len([t for t in tracks if t.validation_status == 'pending']),
                'edited': len([t for t in tracks if t.validation_status == 'edited']),
                'approved': len([t for t in tracks if t.validation_status == 'approved']),
                'rejected': len([t for t in tracks if t.validation_status == 'rejected'])
            }
            
            return {
                'success': True,
                'session_id': session.id,
                'session_status': session.session_status,
                'project_id': session.project_id,
                'chapter_id': session.chapter_id,
                'track_stats': track_stats,
                'analysis_completed': session.analysis_timestamp is not None,
                'validation_prepared': session.validation_timestamp is not None,
                'finalized': session.persistence_timestamp is not None,
                'created_at': session.created_at.isoformat(),
                'updated_at': session.updated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取生成状态失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '获取生成状态失败'
            }
    
    def clear_generation_session(self, project_id: int) -> Dict[str, Any]:
        """清除环境音生成会话"""
        try:
            sessions = self.db.query(EnvironmentGenerationSession).filter(
                EnvironmentGenerationSession.project_id == project_id,
                EnvironmentGenerationSession.session_status == 'active'
            ).all()
            
            cleared_count = 0
            for session in sessions:
                session.session_status = 'cancelled'
                cleared_count += 1
                
                self.log_operation(
                    session.id, 
                    'INFO', 
                    '会话已清除',
                    'clear_session'
                )
            
            self.db.commit()
            
            return {
                'success': True,
                'cleared_sessions': cleared_count,
                'message': f'已清除 {cleared_count} 个活跃会话'
            }
            
        except Exception as e:
            logger.error(f"清除会话失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '清除会话失败'
            } 