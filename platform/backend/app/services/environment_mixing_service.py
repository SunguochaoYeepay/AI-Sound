"""
环境混音服务
提供环境音混音功能
"""

import os
import logging
from typing import List, Tuple, Dict, Any
from datetime import datetime
from pydub import AudioSegment
import numpy as np

from app.utils.logger import get_logger
from app.services.environment_project_service import EnvironmentProjectService
from app.database import get_db

logger = get_logger(__name__)


class EnvironmentMixingService:
    """环境混音服务类"""
    
    def __init__(self):
        self.logger = logger
    
    async def mix_project_environment_sounds(
        self,
        project_id: int,
        tracks_to_mix: List[Tuple[int, Dict[str, Any]]],
        task_id: str
    ):
        """
        混音项目环境音
        
        Args:
            project_id: 项目ID
            tracks_to_mix: 要混音的轨道列表 [(index, track_data), ...]
            task_id: 任务ID
        """
        try:
            self.logger.info(f"[ENV_MIXING] 开始混音项目 {project_id}，任务ID: {task_id}")
            
            # 获取数据库会话
            from app.database import SessionLocal
            db = SessionLocal()
            
            try:
                # 获取环境音项目
                env_service = EnvironmentProjectService(db)
                env_project = env_service.get_by_novel_project_id(project_id)
                
                if not env_project:
                    self.logger.error(f"[ENV_MIXING] 未找到项目 {project_id}")
                    return
                
                # 收集音频文件
                audio_segments = []
                for index, track in tracks_to_mix:
                    file_path = track.get('generated_file_path')
                    if file_path and os.path.exists(file_path):
                        try:
                            audio = AudioSegment.from_wav(file_path)
                            audio_segments.append(audio)
                            self.logger.info(f"[ENV_MIXING] 加载轨道 {index}: {file_path}")
                        except Exception as e:
                            self.logger.error(f"[ENV_MIXING] 加载轨道 {index} 失败: {str(e)}")
                
                if not audio_segments:
                    self.logger.error(f"[ENV_MIXING] 没有有效的音频文件可混音")
                    return
                
                # 混音处理
                mixed_audio = self._mix_audio_segments(audio_segments)
                
                # 保存混音文件
                output_dir = os.path.join("data", "outputs", "projects", str(project_id), "environment")
                os.makedirs(output_dir, exist_ok=True)
                
                mixed_file_path = os.path.join(output_dir, f"mixed_environment_{project_id}.wav")
                mixed_audio.export(mixed_file_path, format="wav")
                
                self.logger.info(f"[ENV_MIXING] 混音完成，保存到: {mixed_file_path}")
                
                # 更新项目匹配结果
                matching_result = env_project.matching_result or {}
                matching_result['mixed_file_path'] = mixed_file_path
                matching_result['mixed_at'] = datetime.now().isoformat()
                matching_result['mixed_tracks_count'] = len(audio_segments)
                
                env_project.matching_result = matching_result
                db.commit()
                
                self.logger.info(f"[ENV_MIXING] 项目 {project_id} 混音任务完成")
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"[ENV_MIXING] 混音失败: {str(e)}")
            raise
    
    def _mix_audio_segments(self, audio_segments: List[AudioSegment]) -> AudioSegment:
        """
        混音音频片段
        
        Args:
            audio_segments: 音频片段列表
            
        Returns:
            混音后的音频片段
        """
        if not audio_segments:
            return AudioSegment.empty()
        
        if len(audio_segments) == 1:
            return audio_segments[0]
        
        # 找到最长的音频长度
        max_length = max(len(segment) for segment in audio_segments)
        
        # 将所有音频扩展到相同长度
        normalized_segments = []
        for segment in audio_segments:
            if len(segment) < max_length:
                # 用静音填充到相同长度
                silence = AudioSegment.silent(duration=max_length - len(segment))
                segment = segment + silence
            normalized_segments.append(segment)
        
        # 混音所有音频
        mixed = normalized_segments[0]
        for segment in normalized_segments[1:]:
            mixed = mixed.overlay(segment)
        
        return mixed
