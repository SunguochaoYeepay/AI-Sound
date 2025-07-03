"""
环境音配置到音频编辑器格式转换器
将环境音JSON配置转换为编辑器可用的多轨项目格式
"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class EnvironmentToEditorConverter:
    """环境音配置到音频编辑器格式转换器"""
    
    def __init__(self):
        pass
    
    def convert_environment_config_to_editor_project(self, 
                                                   environment_data: Dict[str, Any],
                                                   project_name: str = "环境音项目") -> Dict[str, Any]:
        """
        将环境音JSON配置转换为编辑器多轨项目格式
        
        Args:
            environment_data: 环境音配置数据
            project_name: 项目名称
            
        Returns:
            转换结果
        """
        try:
            # 生成项目ID和时间戳
            project_id = f"env_project_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            timestamp = datetime.now().isoformat()
            
            # 提取环境音轨道数据
            environment_tracks = environment_data.get('environment_tracks', [])
            if not environment_tracks:
                return {
                    'success': False,
                    'error': '环境音配置中没有轨道数据'
                }
            
            # 计算总时长
            total_duration = max(
                track.get('start_time', 0) + track.get('duration', 0) 
                for track in environment_tracks
            ) if environment_tracks else 0
            
            # 构建项目基本信息
            project_info = {
                "id": project_id,
                "title": project_name,
                "description": f"从环境音配置转换的项目",
                "author": "AI-Sound",
                "totalDuration": total_duration,
                "sampleRate": 44100,
                "channels": 2,
                "bitDepth": 16,
                "exportFormat": "wav",
                "createdAt": timestamp,
                "version": "1.0"
            }
            
            # 构建环境音轨道
            environment_track = {
                "id": "track_environment_converted",
                "name": "环境音效",
                "type": "environment",
                "volume": 0.8,
                "muted": False,
                "solo": False,
                "color": "#27ae60",
                "order": 1,
                "clips": []
            }
            
            # 转换环境音轨道为编辑器片段
            markers = []
            for i, track in enumerate(environment_tracks):
                track_name = track.get('name', f'环境音_{i+1}')
                start_time = track.get('start_time', 0)
                duration = track.get('duration', 0)
                file_path = track.get('file_path', '')
                
                # 创建音频片段
                clip = {
                    "id": f"clip_env_{i}_{uuid.uuid4().hex[:8]}",
                    "fileId": f"env_file_{i}",
                    "filename": track_name,
                    "startTime": start_time,
                    "duration": duration,
                    "volume": track.get('volume', 0.8),
                    "offset": 0.0,
                    "fadeIn": track.get('fade_in', 0.5),
                    "fadeOut": track.get('fade_out', 0.5),
                    "audioFilePath": file_path,
                    "_environmentInfo": {
                        "category": track.get('category', 'unknown'),
                        "mood": track.get('mood', ''),
                        "scene_type": track.get('scene_type', ''),
                        "volume_level": track.get('volume_level', 0.8)
                    }
                }
                environment_track["clips"].append(clip)
                
                # 添加标记点
                if track_name and track_name != f'环境音_{i+1}':
                    markers.append({
                        "id": f"marker_env_{i}",
                        "time": start_time,
                        "label": track_name,
                        "description": f"环境音: {track.get('category', 'unknown')}",
                        "color": "#2ecc71"
                    })
            
            # 构建完整项目数据
            editor_project = {
                "project": project_info,
                "tracks": [environment_track],
                "markers": markers
            }
            
            logger.info(f"环境音配置转换完成: {len(environment_tracks)} 个轨道 -> {project_name}")
            
            return {
                'success': True,
                'editor_project': editor_project,
                'conversion_summary': {
                    'original_tracks_count': len(environment_tracks),
                    'converted_clips_count': len(environment_track["clips"]),
                    'total_duration': total_duration,
                    'markers_count': len(markers)
                }
            }
            
        except Exception as e:
            logger.error(f"环境音配置转换失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def merge_environment_projects(self, 
                                 projects: List[Dict[str, Any]], 
                                 merged_project_name: str = "合并环境音项目") -> Dict[str, Any]:
        """
        合并多个环境音项目
        
        Args:
            projects: 项目列表
            merged_project_name: 合并后的项目名称
            
        Returns:
            合并结果
        """
        try:
            if not projects:
                return {
                    'success': False,
                    'error': '没有项目可以合并'
                }
            
            # 生成合并项目ID
            merged_project_id = f"merged_env_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            timestamp = datetime.now().isoformat()
            
            # 合并所有轨道和标记
            all_clips = []
            all_markers = []
            max_duration = 0
            
            current_offset = 0  # 时间偏移量，确保项目不重叠
            
            for i, project in enumerate(projects):
                project_data = project.get('editor_project', {})
                tracks = project_data.get('tracks', [])
                markers = project_data.get('markers', [])
                
                # 处理轨道中的片段
                for track in tracks:
                    for clip in track.get('clips', []):
                        merged_clip = clip.copy()
                        # 应用时间偏移
                        merged_clip['startTime'] += current_offset
                        merged_clip['id'] = f"merged_clip_{i}_{clip['id']}"
                        all_clips.append(merged_clip)
                
                # 处理标记点
                for marker in markers:
                    merged_marker = marker.copy()
                    # 应用时间偏移
                    merged_marker['time'] += current_offset
                    merged_marker['id'] = f"merged_marker_{i}_{marker['id']}"
                    merged_marker['label'] = f"P{i+1}: {marker['label']}"
                    all_markers.append(merged_marker)
                
                # 计算当前项目的持续时间
                project_duration = project_data.get('project', {}).get('totalDuration', 0)
                current_offset += project_duration
                max_duration = current_offset
            
            # 构建合并后的项目
            merged_project_info = {
                "id": merged_project_id,
                "title": merged_project_name,
                "description": f"合并了 {len(projects)} 个环境音项目",
                "author": "AI-Sound",
                "totalDuration": max_duration,
                "sampleRate": 44100,
                "channels": 2,
                "bitDepth": 16,
                "exportFormat": "wav",
                "createdAt": timestamp,
                "version": "1.0"
            }
            
            # 构建合并后的轨道
            merged_track = {
                "id": "track_merged_environment",
                "name": "合并环境音效",
                "type": "environment",
                "volume": 0.8,
                "muted": False,
                "solo": False,
                "color": "#27ae60",
                "order": 1,
                "clips": all_clips
            }
            
            merged_editor_project = {
                "project": merged_project_info,
                "tracks": [merged_track],
                "markers": all_markers
            }
            
            logger.info(f"环境音项目合并完成: {len(projects)} 个项目 -> {merged_project_name}")
            
            return {
                'success': True,
                'editor_project': merged_editor_project,
                'merge_summary': {
                    'source_projects_count': len(projects),
                    'total_clips_count': len(all_clips),
                    'total_markers_count': len(all_markers),
                    'total_duration': max_duration
                }
            }
            
        except Exception as e:
            logger.error(f"环境音项目合并失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }