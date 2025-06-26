"""
环境音时间轴生成与管理服务
支持视频编辑兼容格式，提供精确的时间控制和轨道管理
为新的环境音优化流程提供时间轴集成能力
"""

import logging
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from app.models.environment_sound import EnvironmentSound
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class TimelineTrack:
    """时间轴轨道"""
    def __init__(self, track_id: str, sound_id: int, sound_name: str, 
                 start_time: float, duration: float, volume: float = 1.0):
        self.track_id = track_id
        self.sound_id = sound_id
        self.sound_name = sound_name
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.volume = volume
        self.fade_in = 1.0
        self.fade_out = 1.0
        self.loop_enabled = True
        self.audio_file_path = None
        self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'track_id': self.track_id,
            'sound_id': self.sound_id,
            'sound_name': self.sound_name,
            'start_time': self.start_time,
            'duration': self.duration,
            'end_time': self.end_time,
            'volume': self.volume,
            'fade_in': self.fade_in,
            'fade_out': self.fade_out,
            'loop_enabled': self.loop_enabled,
            'audio_file_path': self.audio_file_path,
            'metadata': self.metadata
        }

class VideoEditingTimeline:
    """视频编辑时间轴格式"""
    def __init__(self, project_name: str, total_duration: float):
        self.project_name = project_name
        self.total_duration = total_duration
        self.timeline_version = "2.0"
        self.frame_rate = 30  # FPS
        self.sample_rate = 44100  # 音频采样率
        self.tracks: List[TimelineTrack] = []
        self.metadata = {
            'created_at': datetime.now().isoformat(),
            'creator': 'AI-Sound Environment Generator',
            'format': 'video_editing_compatible'
        }
    
    def add_track(self, track: TimelineTrack):
        """添加轨道"""
        self.tracks.append(track)
        # 更新总时长
        max_end_time = max([t.end_time for t in self.tracks], default=0)
        self.total_duration = max(self.total_duration, max_end_time)
    
    def to_premiere_pro_format(self) -> Dict[str, Any]:
        """导出为Adobe Premiere Pro兼容格式"""
        return {
            'project': {
                'name': self.project_name,
                'format': 'adobe_premiere_pro',
                'version': self.timeline_version,
                'settings': {
                    'frame_rate': self.frame_rate,
                    'sample_rate': self.sample_rate,
                    'total_duration': self.total_duration
                }
            },
            'sequences': [{
                'name': f"{self.project_name}_环境音轨道",
                'duration': self.total_duration,
                'audio_tracks': [
                    {
                        'track_number': i + 1,
                        'track_name': f"环境音轨道_{i+1}",
                        'clips': [{
                            'clip_id': track.track_id,
                            'name': track.sound_name,
                            'media_source': track.audio_file_path,
                            'in_point': 0,
                            'out_point': track.duration,
                            'timeline_in': track.start_time,
                            'timeline_out': track.end_time,
                            'volume': track.volume * 100,  # 转换为百分比
                            'fade_in_duration': track.fade_in,
                            'fade_out_duration': track.fade_out,
                            'loop_enabled': track.loop_enabled,
                            'audio_effects': []
                        }]
                    } for i, track in enumerate(self.tracks)
                ]
            }],
            'metadata': self.metadata
        }
    
    def to_davinci_resolve_format(self) -> Dict[str, Any]:
        """导出为DaVinci Resolve兼容格式"""
        return {
            'resolve_project': {
                'name': self.project_name,
                'format': 'davinci_resolve',
                'version': self.timeline_version,
                'timeline_settings': {
                    'frame_rate': f"{self.frame_rate}fps",
                    'resolution': "1920x1080",
                    'audio_sample_rate': self.sample_rate
                }
            },
            'timeline': {
                'name': f"{self.project_name}_Timeline",
                'duration_frames': int(self.total_duration * self.frame_rate),
                'audio_tracks': [
                    {
                        'track_index': i + 1,
                        'track_type': "audio",
                        'clips': [{
                            'clip_name': track.sound_name,
                            'media_pool_item': track.audio_file_path,
                            'start_frame': int(track.start_time * self.frame_rate),
                            'end_frame': int(track.end_time * self.frame_rate),
                            'duration_frames': int(track.duration * self.frame_rate),
                            'volume_db': 20 * (track.volume - 1),  # 转换为dB
                            'fade_in_frames': int(track.fade_in * self.frame_rate),
                            'fade_out_frames': int(track.fade_out * self.frame_rate),
                            'loop_enabled': track.loop_enabled
                        }]
                    } for i, track in enumerate(self.tracks)
                ]
            },
            'metadata': self.metadata
        }
    
    def to_generic_json_format(self) -> Dict[str, Any]:
        """导出为通用JSON格式"""
        return {
            'timeline': {
                'project_name': self.project_name,
                'version': self.timeline_version,
                'total_duration': self.total_duration,
                'frame_rate': self.frame_rate,
                'sample_rate': self.sample_rate,
                'tracks': [track.to_dict() for track in self.tracks],
                'metadata': self.metadata
            }
        }

class EnvironmentTimelineGenerator:
    """环境音时间轴生成器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_timeline_from_analysis(self, 
                                    analysis_result: Dict[str, Any],
                                    matching_result: Dict[str, Any],
                                    project_name: str = None) -> VideoEditingTimeline:
        """
        从分析结果和匹配结果创建时间轴
        
        Args:
            analysis_result: 章节环境音分析结果
            matching_result: 环境音匹配结果
            project_name: 项目名称
            
        Returns:
            视频编辑时间轴对象
        """
        if not project_name:
            project_name = f"Environment_Timeline_{int(time.time())}"
        
        logger.info(f"[TIMELINE_GEN] 开始创建时间轴: {project_name}")
        
        # 获取增强的分析结果
        enhanced_result = matching_result.get('enhanced_analysis_result', analysis_result)
        environment_tracks = enhanced_result.get('environment_tracks', [])
        
        # 计算总时长
        total_duration = max([
            track.get('start_time', 0) + track.get('duration', 30.0)
            for track in environment_tracks
        ], default=300.0)
        
        # 创建时间轴
        timeline = VideoEditingTimeline(project_name, total_duration)
        
        # 添加环境音轨道
        for track_data in environment_tracks:
            if track_data.get('has_match') and track_data.get('best_match'):
                # 使用匹配的环境音
                sound_info = track_data['best_match']
                track = self._create_timeline_track_from_match(track_data, sound_info)
                timeline.add_track(track)
            else:
                # 创建占位轨道（等待生成）
                track = self._create_placeholder_track(track_data)
                timeline.add_track(track)
        
        logger.info(f"[TIMELINE_GEN] 时间轴创建完成: {len(timeline.tracks)}个轨道, 总时长{total_duration:.1f}秒")
        
        return timeline
    
    def _create_timeline_track_from_match(self, track_data: Dict[str, Any], sound_info: Dict[str, Any]) -> TimelineTrack:
        """从匹配结果创建时间轴轨道"""
        track_id = f"track_{track_data.get('segment_id', int(time.time()))}"
        
        track = TimelineTrack(
            track_id=track_id,
            sound_id=sound_info.get('sound_id', 0),
            sound_name=sound_info.get('sound_name', '未知环境音'),
            start_time=track_data.get('start_time', 0.0),
            duration=track_data.get('duration', 30.0),
            volume=self._calculate_volume_from_intensity(track_data.get('intensity_level', 'medium'))
        )
        
        # 设置其他属性
        track.fade_in = track_data.get('fade_in_duration', 1.0)
        track.fade_out = track_data.get('fade_out_duration', 1.0)
        track.loop_enabled = track_data.get('environment_type') in ['ambient', 'continuous']
        
        # 添加元数据
        track.metadata = {
            'segment_id': track_data.get('segment_id'),
            'environment_keywords': track_data.get('environment_keywords', []),
            'scene_description': track_data.get('scene_description', ''),
            'match_confidence': sound_info.get('confidence', 0.0),
            'match_type': sound_info.get('match_type', 'unknown'),
            'intensity_level': track_data.get('intensity_level', 'medium')
        }
        
        return track
    
    def _create_placeholder_track(self, track_data: Dict[str, Any]) -> TimelineTrack:
        """创建占位轨道（等待生成环境音）"""
        track_id = f"placeholder_{track_data.get('segment_id', int(time.time()))}"
        keywords = track_data.get('environment_keywords', [])
        sound_name = f"待生成_{keywords[0] if keywords else '环境音'}"
        
        track = TimelineTrack(
            track_id=track_id,
            sound_id=0,  # 占位ID
            sound_name=sound_name,
            start_time=track_data.get('start_time', 0.0),
            duration=track_data.get('duration', 30.0),
            volume=self._calculate_volume_from_intensity(track_data.get('intensity_level', 'medium'))
        )
        
        # 设置占位属性
        track.audio_file_path = "PLACEHOLDER_TO_BE_GENERATED"
        track.metadata = {
            'is_placeholder': True,
            'generation_needed': True,
            'segment_id': track_data.get('segment_id'),
            'environment_keywords': track_data.get('environment_keywords', []),
            'scene_description': track_data.get('scene_description', ''),
            'intensity_level': track_data.get('intensity_level', 'medium')
        }
        
        return track
    
    def _calculate_volume_from_intensity(self, intensity: str) -> float:
        """根据强度计算音量"""
        intensity_volumes = {
            'low': 0.4,
            'medium': 0.7,
            'high': 1.0
        }
        return intensity_volumes.get(intensity, 0.7)
    
    def update_timeline_with_generated_sounds(self, 
                                            timeline: VideoEditingTimeline,
                                            generated_sounds: List[EnvironmentSound],
                                            db: Session) -> VideoEditingTimeline:
        """
        用生成的环境音更新时间轴
        
        Args:
            timeline: 原始时间轴
            generated_sounds: 生成的环境音列表
            db: 数据库会话
            
        Returns:
            更新后的时间轴
        """
        logger.info(f"[TIMELINE_GEN] 开始更新时间轴，使用{len(generated_sounds)}个生成的环境音")
        
        # 创建关键词到环境音的映射
        keyword_to_sound = {}
        for sound in generated_sounds:
            if sound.tags and isinstance(sound.tags, list):
                for tag in sound.tags:
                    if tag != "AI生成" and not tag.startswith("强度_"):
                        keyword_to_sound[tag] = sound
        
        # 更新占位轨道
        updated_tracks = []
        for track in timeline.tracks:
            if track.metadata.get('is_placeholder'):
                # 尝试匹配生成的环境音
                keywords = track.metadata.get('environment_keywords', [])
                matched_sound = None
                
                for keyword in keywords:
                    if keyword in keyword_to_sound:
                        matched_sound = keyword_to_sound[keyword]
                        break
                
                if matched_sound:
                    # 更新轨道信息
                    track.sound_id = matched_sound.id
                    track.sound_name = matched_sound.name
                    track.audio_file_path = matched_sound.file_path
                    track.metadata['is_placeholder'] = False
                    track.metadata['generation_needed'] = False
                    track.metadata['generated_sound_id'] = matched_sound.id
                    
                    logger.info(f"[TIMELINE_GEN] 轨道已更新: {track.track_id} -> {matched_sound.name}")
                else:
                    logger.warning(f"[TIMELINE_GEN] 未找到匹配的生成环境音: {keywords}")
            
            updated_tracks.append(track)
        
        timeline.tracks = updated_tracks
        timeline.metadata['last_updated'] = datetime.now().isoformat()
        
        logger.info(f"[TIMELINE_GEN] 时间轴更新完成")
        return timeline
    
    def export_timeline(self, 
                       timeline: VideoEditingTimeline, 
                       export_format: str = 'generic',
                       output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        导出时间轴
        
        Args:
            timeline: 时间轴对象
            export_format: 导出格式 (generic, premiere_pro, davinci_resolve)
            output_path: 输出文件路径
            
        Returns:
            导出的时间轴数据
        """
        logger.info(f"[TIMELINE_GEN] 开始导出时间轴: {export_format}")
        
        # 根据格式选择导出方法
        if export_format == 'premiere_pro':
            timeline_data = timeline.to_premiere_pro_format()
        elif export_format == 'davinci_resolve':
            timeline_data = timeline.to_davinci_resolve_format()
        else:
            timeline_data = timeline.to_generic_json_format()
        
        # 如果指定了输出路径，保存到文件
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(timeline_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"[TIMELINE_GEN] 时间轴已保存到: {output_path}")
        
        return timeline_data
    
    def validate_timeline(self, timeline: VideoEditingTimeline) -> Dict[str, Any]:
        """
        验证时间轴完整性
        
        Returns:
            验证结果
        """
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'statistics': {
                'total_tracks': len(timeline.tracks),
                'placeholder_tracks': 0,
                'completed_tracks': 0,
                'total_duration': timeline.total_duration
            }
        }
        
        for track in timeline.tracks:
            if track.metadata.get('is_placeholder'):
                validation_result['statistics']['placeholder_tracks'] += 1
                validation_result['warnings'].append(
                    f"轨道 {track.track_id} 仍为占位状态，需要生成环境音"
                )
            else:
                validation_result['statistics']['completed_tracks'] += 1
            
            # 检查时间重叠
            for other_track in timeline.tracks:
                if (track != other_track and 
                    track.start_time < other_track.end_time and 
                    track.end_time > other_track.start_time):
                    validation_result['warnings'].append(
                        f"轨道 {track.track_id} 与 {other_track.track_id} 存在时间重叠"
                    )
        
        # 如果有占位轨道，标记为不完整
        if validation_result['statistics']['placeholder_tracks'] > 0:
            validation_result['is_valid'] = False
            validation_result['errors'].append("存在未生成的环境音轨道")
        
        logger.info(f"[TIMELINE_GEN] 时间轴验证完成: {validation_result}")
        return validation_result 