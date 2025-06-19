"""
顺序生成协调器
协调 TTS3 → TangoFlux → 混合 的完整环境音混合流程
"""

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import numpy as np

from sqlalchemy.orm import Session
from app.database import get_db
from app.models import NovelProject, AudioFile
from app.novel_reader import process_audio_generation_from_synthesis_plan
from app.services.sequential_timeline_generator import timeline_generator
from app.services.audio_enhancement import AudioEnhancementService
from app.clients.tangoflux_client import TangoFluxClient
from app.utils import get_audio_duration
from pydub import AudioSegment
import io

logger = logging.getLogger(__name__)

class SequentialSynthesisCoordinator:
    """顺序生成协调器 - 管理完整的环境音混合流程"""
    
    def __init__(self):
        self.audio_enhancement = AudioEnhancementService()
        self.tangoflux_client = TangoFluxClient()
        
    async def synthesize_with_environment(
        self, 
        project_id: int,
        synthesis_data: List[Dict],
        enable_environment: bool = True,
        environment_volume: float = 0.3,
        parallel_tasks: int = 1,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        完整的环境音混合合成流程
        
        Args:
            project_id: 项目ID
            synthesis_data: 合成计划数据
            enable_environment: 是否启用环境音
            environment_volume: 环境音音量 (0.0-1.0)
            parallel_tasks: TTS并发任务数
            progress_callback: 进度回调函数
            
        Returns:
            合成结果信息
        """
        try:
            logger.info(f"[COORDINATOR] 开始环境音混合合成 - 项目 {project_id}")
            
            # 获取数据库连接
            db = next(get_db())
            project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
            
            if not project:
                raise ValueError(f"项目 {project_id} 不存在")
            
            # 更新项目状态
            project.status = 'processing'
            project.updated_at = datetime.utcnow()
            db.commit()
            
            result = {
                "project_id": project_id,
                "enable_environment": enable_environment,
                "stages_completed": [],
                "total_duration": 0.0,
                "files_generated": [],
                "error": None
            }
            
            try:
                # 阶段1: TTS语音合成
                await self._update_progress(progress_callback, "stage_1_tts", 0, "开始TTS语音合成...")
                dialogue_files = await self._stage_1_tts_synthesis(
                    project_id, synthesis_data, parallel_tasks, progress_callback
                )
                result["stages_completed"].append("tts_synthesis")
                result["dialogue_files_count"] = len(dialogue_files)
                
                if not enable_environment:
                    # 如果不启用环境音，直接返回TTS结果
                    logger.info(f"[COORDINATOR] 项目 {project_id} TTS合成完成，跳过环境音混合")
                    project.status = 'completed'
                    db.commit()
                    return result
                
                # 阶段2: 时间轴生成
                await self._update_progress(progress_callback, "stage_2_timeline", 25, "分析音频，生成时间轴...")
                timeline = await self._stage_2_timeline_generation(dialogue_files)
                result["stages_completed"].append("timeline_generation")
                result["total_duration"] = timeline.total_duration
                
                # 阶段3: 环境音生成
                await self._update_progress(progress_callback, "stage_3_environment", 50, "生成环境音效...")
                environment_files = await self._stage_3_environment_generation(
                    timeline, project_id, progress_callback
                )
                result["stages_completed"].append("environment_generation")
                result["environment_files_count"] = len(environment_files)
                
                # 阶段4: 音频混合
                await self._update_progress(progress_callback, "stage_4_mixing", 75, "混合音频，生成最终文件...")
                final_audio_path = await self._stage_4_audio_mixing(
                    dialogue_files, environment_files, environment_volume, project_id
                )
                result["stages_completed"].append("audio_mixing")
                result["final_audio_path"] = final_audio_path
                
                # 完成
                await self._update_progress(progress_callback, "completed", 100, "环境音混合完成！")
                project.status = 'completed'
                db.commit()
                
                logger.info(f"[COORDINATOR] 项目 {project_id} 环境音混合合成完成")
                return result
                
            except Exception as e:
                logger.error(f"[COORDINATOR] 项目 {project_id} 合成失败: {str(e)}")
                project.status = 'failed'
                project.error_message = str(e)
                result["error"] = str(e)
                db.commit()
                raise
                
        except Exception as e:
            logger.error(f"[COORDINATOR] 协调器执行失败: {str(e)}")
            raise
    
    async def _stage_1_tts_synthesis(
        self, 
        project_id: int, 
        synthesis_data: List[Dict],
        parallel_tasks: int,
        progress_callback=None
    ) -> List[Dict]:
        """
        阶段1: TTS语音合成
        利用现有的 novel_reader 进行语音合成
        """
        logger.info(f"[COORDINATOR] 阶段1: 开始TTS语音合成")
        
        # 调用现有的合成流程
        await process_audio_generation_from_synthesis_plan(
            project_id, synthesis_data, parallel_tasks
        )
        
        # 获取生成的音频文件信息
        db = next(get_db())
        audio_files = db.query(AudioFile).filter(
            AudioFile.project_id == project_id,
            AudioFile.audio_type == 'segment',
            AudioFile.status == 'active'
        ).order_by(AudioFile.paragraph_index).all()
        
        dialogue_files = []
        for audio_file in audio_files:
            dialogue_files.append({
                "file_path": audio_file.file_path,
                "text_content": audio_file.text_content,
                "speaker": audio_file.speaker,
                "duration": audio_file.duration,
                "paragraph_index": audio_file.paragraph_index
            })
        
        logger.info(f"[COORDINATOR] 阶段1完成: 生成 {len(dialogue_files)} 个音频文件")
        return dialogue_files
    
    async def _stage_2_timeline_generation(self, dialogue_files: List[Dict]) -> Any:
        """
        阶段2: 时间轴生成
        分析音频文件，生成精确的时间轴
        """
        logger.info(f"[COORDINATOR] 阶段2: 开始时间轴生成")
        
        # 准备时间轴生成器需要的数据格式
        audio_files_data = []
        for file_info in dialogue_files:
            audio_files_data.append({
                "file_path": file_info["file_path"],
                "text_content": file_info["text_content"],
                "speaker": file_info["speaker"]
            })
        
        # 生成时间轴
        timeline = timeline_generator.generate_timeline(audio_files_data)
        
        logger.info(f"[COORDINATOR] 阶段2完成: 时间轴总时长 {timeline.total_duration:.2f}s, "
                   f"环境音轨道 {len(timeline.environment_tracks)}个")
        return timeline
    
    async def _stage_3_environment_generation(
        self, 
        timeline: Any, 
        project_id: int,
        progress_callback=None
    ) -> List[Dict]:
        """
        阶段3: 环境音生成
        基于时间轴生成相应的环境音
        """
        logger.info(f"[COORDINATOR] 阶段3: 开始环境音生成")
        
        environment_files = []
        project_output_dir = f"outputs/projects/{project_id}"
        
        # 为每个环境音轨道生成音频
        for i, track in enumerate(timeline.environment_tracks):
            try:
                logger.info(f"[COORDINATOR] 生成环境音 {i+1}/{len(timeline.environment_tracks)}: {track.scene_prompt}")
                
                # 更新进度
                progress = 50 + (i / len(timeline.environment_tracks)) * 20  # 50%-70%
                await self._update_progress(
                    progress_callback, "stage_3_environment", progress,
                    f"生成环境音 {i+1}/{len(timeline.environment_tracks)}: {track.scene_prompt}"
                )
                
                # 生成环境音音频
                audio_data = await self._generate_single_environment_audio(
                    track.tango_prompt, track.duration
                )
                
                if audio_data:
                    # 保存环境音文件
                    env_filename = f"environment_{i+1:03d}_{track.scene_prompt.replace(' ', '_')}.wav"
                    env_path = os.path.join(project_output_dir, env_filename)
                    
                    with open(env_path, 'wb') as f:
                        f.write(audio_data)
                    
                    environment_files.append({
                        "file_path": env_path,
                        "start_time": track.start_time,
                        "end_time": track.end_time,
                        "duration": track.duration,
                        "scene_prompt": track.scene_prompt,
                        "volume_level": track.volume_level
                    })
                    
                    logger.info(f"[COORDINATOR] 环境音生成成功: {env_filename}")
                else:
                    logger.warning(f"[COORDINATOR] 环境音生成失败: {track.scene_prompt}")
                    
            except Exception as e:
                logger.error(f"[COORDINATOR] 环境音轨道 {i} 生成失败: {str(e)}")
                continue
        
        logger.info(f"[COORDINATOR] 阶段3完成: 生成 {len(environment_files)} 个环境音文件")
        return environment_files
    
    async def _stage_4_audio_mixing(
        self, 
        dialogue_files: List[Dict], 
        environment_files: List[Dict],
        environment_volume: float,
        project_id: int
    ) -> str:
        """
        阶段4: 音频混合
        将对话音频和环境音进行智能混合
        """
        logger.info(f"[COORDINATOR] 阶段4: 开始音频混合")
        
        try:
            # 加载所有对话音频并按时间顺序拼接
            dialogue_audio = self._load_and_concatenate_dialogue(dialogue_files)
            
            # 创建环境音轨道
            environment_audio = self._create_environment_track(
                environment_files, dialogue_audio.duration_seconds, environment_volume
            )
            
            # 混合音频
            mixed_audio = dialogue_audio.overlay(environment_audio)
            
            # 保存最终音频文件
            project_output_dir = f"outputs/projects/{project_id}"
            final_filename = f"final_mixed_audio_{project_id}_{int(datetime.now().timestamp())}.wav"
            final_path = os.path.join(project_output_dir, final_filename)
            
            mixed_audio.export(final_path, format="wav")
            
            logger.info(f"[COORDINATOR] 阶段4完成: 最终音频已保存 {final_path}")
            return final_path
            
        except Exception as e:
            logger.error(f"[COORDINATOR] 音频混合失败: {str(e)}")
            raise
    
    async def _generate_single_environment_audio(self, prompt: str, duration: float) -> Optional[bytes]:
        """
        生成单个环境音音频
        """
        try:
            # 限制时长在合理范围内
            duration = max(1.0, min(duration, 60.0))
            
            # 调用TangoFlux生成音频
            audio_data = await self.audio_enhancement.generate_scene_audio(
                prompt, int(duration)
            )
            
            return audio_data
            
        except Exception as e:
            logger.error(f"[COORDINATOR] 环境音生成失败 '{prompt}': {str(e)}")
            return None
    
    def _load_and_concatenate_dialogue(self, dialogue_files: List[Dict]) -> AudioSegment:
        """
        加载并拼接所有对话音频
        """
        concatenated = AudioSegment.empty()
        
        for file_info in dialogue_files:
            try:
                audio = AudioSegment.from_wav(file_info["file_path"])
                concatenated += audio
            except Exception as e:
                logger.error(f"[COORDINATOR] 加载音频文件失败 {file_info['file_path']}: {str(e)}")
                # 添加静音作为占位符
                placeholder = AudioSegment.silent(duration=3000)  # 3秒静音
                concatenated += placeholder
        
        return concatenated
    
    def _create_environment_track(
        self, 
        environment_files: List[Dict], 
        target_duration: float,
        volume_level: float
    ) -> AudioSegment:
        """
        创建环境音轨道，匹配目标时长
        """
        if not environment_files:
            # 如果没有环境音文件，创建静音轨道
            return AudioSegment.silent(duration=int(target_duration * 1000))
        
        # 创建环境音轨道
        environment_track = AudioSegment.silent(duration=int(target_duration * 1000))
        
        for env_file in environment_files:
            try:
                # 加载环境音文件
                env_audio = AudioSegment.from_wav(env_file["file_path"])
                
                # 调整音量
                file_volume = env_file.get("volume_level", volume_level)
                env_audio = env_audio + (20 * np.log10(file_volume)) if file_volume > 0 else env_audio - 60
                
                # 计算在时间轴上的位置
                start_ms = int(env_file["start_time"] * 1000)
                end_ms = int(env_file["end_time"] * 1000)
                
                # 确保不超出目标时长
                if start_ms < len(environment_track):
                    # 裁剪环境音以匹配时间段
                    target_length = min(end_ms - start_ms, len(env_audio))
                    env_audio = env_audio[:target_length]
                    
                    # 叠加到环境音轨道
                    environment_track = environment_track.overlay(env_audio, position=start_ms)
                
            except Exception as e:
                logger.error(f"[COORDINATOR] 处理环境音文件失败 {env_file['file_path']}: {str(e)}")
                continue
        
        return environment_track
    
    async def _update_progress(self, progress_callback, stage: str, percent: int, message: str):
        """
        更新进度信息
        """
        if progress_callback:
            try:
                await progress_callback({
                    "stage": stage,
                    "percent": percent,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"[COORDINATOR] 进度更新失败: {str(e)}")
    
    def get_stage_info(self) -> Dict[str, str]:
        """
        获取各阶段信息
        """
        return {
            "stage_1_tts": "TTS语音合成",
            "stage_2_timeline": "时间轴生成",
            "stage_3_environment": "环境音生成",
            "stage_4_mixing": "音频混合",
            "completed": "合成完成"
        }


# 全局实例
synthesis_coordinator = SequentialSynthesisCoordinator()