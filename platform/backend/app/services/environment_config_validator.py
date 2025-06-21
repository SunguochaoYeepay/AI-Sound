"""
环境配置校对器
支持人工校对并包含环境音ID匹配功能
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class EnvironmentConfigValidator:
    """环境配置校对器 - 人工校对器，含环境音ID匹配功能"""
    
    def __init__(self):
        # 场景继承逻辑 (新旁白无环境描述时继承上一个环境设置)
        self.SCENE_INHERITANCE_ENABLED = True
        
        # 环境音优先级 (多个环境元素时，最新出现的优先级最高)
        self.LATEST_ENVIRONMENT_PRIORITY = True
        
        # 渐变过渡配置
        self.FADE_CONFIG = {
            'fade_in_duration': 3.0,    # 3秒渐入
            'fade_out_duration': 2.0,   # 2秒渐出
            'overlap_duration': 1.0     # 1秒重叠
        }
        
    def prepare_validation_data(self, environment_tracks: List[Dict]) -> Dict:
        """准备校对数据，应用场景继承逻辑"""
        logger.info(f"[CONFIG_VALIDATOR] 准备校对数据，共{len(environment_tracks)}个环境轨道")
        
        validation_tracks = []
        current_environment = None  # 当前环境状态
        
        for i, track in enumerate(environment_tracks):
            # 创建校对轨道副本
            validation_track = track.copy()
            validation_track['track_index'] = i
            validation_track['validation_status'] = 'pending'  # 待校对
            validation_track['manual_edits'] = {}  # 人工编辑记录
            
            # 场景继承逻辑
            if self.SCENE_INHERITANCE_ENABLED:
                environment_keywords = track.get('environment_keywords', [])
                
                if not environment_keywords and current_environment:
                    # 无环境描述时继承上一个环境
                    validation_track['inherited_environment'] = current_environment.copy()
                    validation_track['inheritance_applied'] = True
                    logger.info(f"[CONFIG_VALIDATOR] 轨道{i}继承环境: {current_environment.get('primary_keyword', '未知')}")
                else:
                    # 有环境描述时更新当前环境
                    if environment_keywords:
                        # 环境音优先级 (最新出现的优先级最高)
                        primary_keyword = environment_keywords[-1] if self.LATEST_ENVIRONMENT_PRIORITY else environment_keywords[0]
                        current_environment = {
                            'primary_keyword': primary_keyword,
                            'all_keywords': environment_keywords,
                            'scene_description': track.get('scene_description', ''),
                            'source_track_index': i
                        }
                        validation_track['primary_environment'] = current_environment.copy()
                        validation_track['inheritance_applied'] = False
                        logger.info(f"[CONFIG_VALIDATOR] 轨道{i}新环境: {primary_keyword}")
                    else:
                        validation_track['inheritance_applied'] = False
                        
            # 初始化匹配建议
            validation_track['matching_suggestions'] = self._generate_matching_suggestions(validation_track)
            
            validation_tracks.append(validation_track)
            
        logger.info(f"[CONFIG_VALIDATOR] 校对数据准备完成，场景继承: {self.SCENE_INHERITANCE_ENABLED}")
        
        return {
            'validation_tracks': validation_tracks,
            'validation_config': {
                'scene_inheritance_enabled': self.SCENE_INHERITANCE_ENABLED,
                'latest_environment_priority': self.LATEST_ENVIRONMENT_PRIORITY,
                'fade_config': self.FADE_CONFIG
            },
            'validation_summary': {
                'total_tracks': len(validation_tracks),
                'inheritance_applied_count': len([t for t in validation_tracks if t.get('inheritance_applied', False)]),
                'pending_validation_count': len(validation_tracks),
                'preparation_timestamp': datetime.now().isoformat()
            }
        }
        
    def _generate_matching_suggestions(self, track: Dict) -> List[Dict]:
        """生成环境音ID匹配建议"""
        suggestions = []
        
        # 获取环境关键词 (包括继承的)
        keywords = []
        if track.get('inheritance_applied') and track.get('inherited_environment'):
            keywords = track['inherited_environment'].get('all_keywords', [])
        else:
            keywords = track.get('environment_keywords', [])
            
        if not keywords:
            return suggestions
            
        # 为每个关键词生成匹配建议
        for keyword in keywords:
            suggestion = {
                'keyword': keyword,
                'suggested_tangoflux_config': self._generate_tangoflux_config(keyword),
                'confidence': 0.8,  # 初始置信度
                'match_type': 'tangoflux_generation'
            }
            suggestions.append(suggestion)
            
        return suggestions
        
    def _generate_tangoflux_config(self, keyword: str) -> Dict:
        """生成TangoFlux配置建议"""
        # 基于关键词生成TangoFlux配置
        return {
            'prompt': f"{keyword}环境音，自然真实，高质量",
            'duration': 30.0,  # 默认30秒
            'fade_in': self.FADE_CONFIG['fade_in_duration'],
            'fade_out': self.FADE_CONFIG['fade_out_duration'],
            'volume': 0.6,  # 默认音量
            'loop': True,   # 是否循环
            'generation_params': {
                'keyword': keyword,
                'style': 'natural',
                'quality': 'high'
            }
        }
        
    def apply_manual_edits(self, track_index: int, manual_edits: Dict, validation_data: Dict) -> Dict:
        """应用人工编辑"""
        validation_tracks = validation_data.get('validation_tracks', [])
        
        if track_index < 0 or track_index >= len(validation_tracks):
            raise ValueError(f"Invalid track_index: {track_index}")
            
        track = validation_tracks[track_index]
        logger.info(f"[CONFIG_VALIDATOR] 应用人工编辑到轨道{track_index}: {list(manual_edits.keys())}")
        
        # 记录原始值
        if 'manual_edits' not in track:
            track['manual_edits'] = {}
            
        # 应用编辑
        for field, new_value in manual_edits.items():
            original_value = track.get(field)
            track['manual_edits'][field] = {
                'original_value': original_value,
                'new_value': new_value,
                'edit_timestamp': datetime.now().isoformat()
            }
            track[field] = new_value
            
        # 如果编辑了环境音ID匹配，更新相关配置
        if 'selected_tangoflux_config' in manual_edits:
            track['environment_audio_id'] = manual_edits['selected_tangoflux_config'].get('id')
            track['tangoflux_config'] = manual_edits['selected_tangoflux_config']
            
        # 更新校对状态
        track['validation_status'] = 'edited'
        track['last_edit_timestamp'] = datetime.now().isoformat()
        
        return validation_data
        
    def validate_track(self, track_index: int, validation_result: str, validation_data: Dict, 
                      notes: Optional[str] = None) -> Dict:
        """校对轨道 (通过/拒绝/需要修改)"""
        validation_tracks = validation_data.get('validation_tracks', [])
        
        if track_index < 0 or track_index >= len(validation_tracks):
            raise ValueError(f"Invalid track_index: {track_index}")
            
        if validation_result not in ['approved', 'rejected', 'needs_revision']:
            raise ValueError(f"Invalid validation_result: {validation_result}")
            
        track = validation_tracks[track_index]
        logger.info(f"[CONFIG_VALIDATOR] 校对轨道{track_index}: {validation_result}")
        
        track['validation_status'] = validation_result
        track['validation_timestamp'] = datetime.now().isoformat()
        if notes:
            track['validation_notes'] = notes
            
        return validation_data
        
    def get_validation_summary(self, validation_data: Dict) -> Dict:
        """获取校对总结"""
        validation_tracks = validation_data.get('validation_tracks', [])
        
        status_count = {}
        for track in validation_tracks:
            status = track.get('validation_status', 'pending')
            status_count[status] = status_count.get(status, 0) + 1
            
        total_tracks = len(validation_tracks)
        approved_tracks = status_count.get('approved', 0)
        
        return {
            'total_tracks': total_tracks,
            'status_distribution': status_count,
            'approval_rate': round(approved_tracks / total_tracks * 100, 1) if total_tracks > 0 else 0.0,
            'ready_for_persistence': approved_tracks == total_tracks,
            'inheritance_stats': {
                'inheritance_applied_count': len([t for t in validation_tracks if t.get('inheritance_applied', False)]),
                'new_environment_count': len([t for t in validation_tracks if not t.get('inheritance_applied', False) and t.get('environment_keywords')])
            },
            'manual_edits_count': len([t for t in validation_tracks if t.get('manual_edits')]),
            'summary_timestamp': datetime.now().isoformat()
        }
        
    def prepare_for_persistence(self, validation_data: Dict) -> Dict:
        """准备持久化数据 (仅校对通过的轨道)"""
        validation_tracks = validation_data.get('validation_tracks', [])
        
        # 筛选已校对通过的轨道
        approved_tracks = [
            track for track in validation_tracks 
            if track.get('validation_status') == 'approved'
        ]
        
        if not approved_tracks:
            logger.warning("[CONFIG_VALIDATOR] 没有校对通过的轨道，无法持久化")
            return {'persistence_tracks': [], 'ready': False}
            
        # 生成持久化配置
        persistence_tracks = []
        for track in approved_tracks:
            persistence_track = {
                'segment_id': track.get('segment_id'),
                'start_time': track.get('start_time'),
                'duration': track.get('duration'),
                'environment_config': {
                    'keywords': track.get('environment_keywords', []) or track.get('inherited_environment', {}).get('all_keywords', []),
                    'scene_description': track.get('scene_description', '') or track.get('inherited_environment', {}).get('scene_description', ''),
                    'tangoflux_config': track.get('tangoflux_config', {}),
                    'fade_config': self.FADE_CONFIG,
                    'inheritance_applied': track.get('inheritance_applied', False)
                },
                'validation_metadata': {
                    'validation_timestamp': track.get('validation_timestamp'),
                    'manual_edits_applied': bool(track.get('manual_edits')),
                    'validation_notes': track.get('validation_notes', '')
                }
            }
            persistence_tracks.append(persistence_track)
            
        logger.info(f"[CONFIG_VALIDATOR] 准备持久化{len(persistence_tracks)}个已校对轨道")
        
        return {
            'persistence_tracks': persistence_tracks,
            'ready': True,
            'persistence_summary': {
                'approved_tracks_count': len(persistence_tracks),
                'total_duration': sum(track['duration'] for track in persistence_tracks),
                'inheritance_count': len([t for t in persistence_tracks if t['environment_config']['inheritance_applied']]),
                'manual_edits_count': len([t for t in persistence_tracks if t['validation_metadata']['manual_edits_applied']]),
                'preparation_timestamp': datetime.now().isoformat()
            }
        } 