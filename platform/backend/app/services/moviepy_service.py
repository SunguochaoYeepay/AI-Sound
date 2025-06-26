"""
MoviePy音频编辑服务
提供音频混合、章节拼接、效果处理等功能
"""

import os
import asyncio
import logging
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import tempfile
import json

from moviepy.editor import (
    AudioFileClip, 
    CompositeAudioClip, 
    concatenate_audioclips,
    afx
)
from moviepy.audio.fx.all import audio_fadein, audio_fadeout
import numpy as np
from pydantic import BaseModel

from ..config.environment import get_environment_config

logger = logging.getLogger(__name__)
env_config = get_environment_config()

class AudioMixConfig(BaseModel):
    """音频混合配置"""
    dialogue_volume: float = 1.0
    environment_volume: float = 0.3
    fadein_duration: float = 0.5
    fadeout_duration: float = 0.5
    normalize_audio: bool = True

class AudioEffectConfig(BaseModel):
    """音频效果配置"""
    volume: float = 1.0
    fadein: Optional[float] = None
    fadeout: Optional[float] = None
    normalize: bool = False
    noise_reduction: bool = False

class ChapterAudioConfig(BaseModel):
    """章节音频配置"""
    silence_duration: float = 1.0  # 片段间静音时长
    normalize_volume: bool = True
    apply_fade: bool = True
    fade_duration: float = 0.3

class MoviePyService:
    """MoviePy音频编辑服务"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.temp_dir = Path(tempfile.gettempdir()) / "ai_sound_moviepy"
        self.temp_dir.mkdir(exist_ok=True)
        
    async def mix_dialogue_with_environment(
        self,
        dialogue_path: str,
        environment_path: str,
        output_path: str,
        config: AudioMixConfig = AudioMixConfig()
    ) -> Dict[str, Any]:
        """
        混合对话音频与环境音
        
        Args:
            dialogue_path: 对话音频文件路径
            environment_path: 环境音频文件路径  
            output_path: 输出文件路径
            config: 混合配置
            
        Returns:
            混合结果信息
        """
        try:
            logger.info(f"开始混合音频: {dialogue_path} + {environment_path}")
            
            # 在线程池中执行CPU密集型操作
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._mix_audio_sync,
                dialogue_path,
                environment_path, 
                output_path,
                config
            )
            
            logger.info(f"音频混合完成: {output_path}")
            return result
            
        except Exception as e:
            logger.error(f"音频混合失败: {str(e)}")
            raise Exception(f"音频混合失败: {str(e)}")
    
    def _mix_audio_sync(
        self,
        dialogue_path: str,
        environment_path: str,
        output_path: str,
        config: AudioMixConfig
    ) -> Dict[str, Any]:
        """同步执行音频混合"""
        
        # 加载音频文件
        dialogue_clip = AudioFileClip(dialogue_path)
        environment_clip = AudioFileClip(environment_path)
        
        # 调整音量
        dialogue_clip = dialogue_clip.volumex(config.dialogue_volume)
        environment_clip = environment_clip.volumex(config.environment_volume)
        
        # 环境音循环播放以匹配对话长度
        if environment_clip.duration < dialogue_clip.duration:
            # 计算需要循环的次数
            loop_count = int(np.ceil(dialogue_clip.duration / environment_clip.duration))
            environment_clips = [environment_clip] * loop_count
            environment_clip = concatenate_audioclips(environment_clips)
        
        # 裁剪环境音到对话长度
        environment_clip = environment_clip.subclip(0, dialogue_clip.duration)
        
        # 添加淡入淡出效果
        if config.fadein_duration > 0:
            dialogue_clip = audio_fadein(dialogue_clip, config.fadein_duration)
            environment_clip = audio_fadein(environment_clip, config.fadein_duration)
            
        if config.fadeout_duration > 0:
            dialogue_clip = audio_fadeout(dialogue_clip, config.fadeout_duration)
            environment_clip = audio_fadeout(environment_clip, config.fadeout_duration)
        
        # 混合音频
        mixed_clip = CompositeAudioClip([dialogue_clip, environment_clip])
        
        # 音频标准化
        if config.normalize_audio:
            mixed_clip = mixed_clip.volumex(0.8)  # 防止过载
        
        # 导出音频
        mixed_clip.write_audiofile(
            output_path,
            codec='libmp3lame',
            bitrate='192k',
            verbose=False,
            logger=None
        )
        
        # 清理资源
        dialogue_clip.close()
        environment_clip.close()
        mixed_clip.close()
        
        # 返回结果信息
        return {
            "success": True,
            "output_path": output_path,
            "duration": dialogue_clip.duration,
            "file_size": os.path.getsize(output_path),
            "format": "mp3",
            "bitrate": "192k"
        }
    
    async def create_chapter_audio(
        self,
        audio_files: List[str],
        output_path: str,
        config: ChapterAudioConfig = ChapterAudioConfig()
    ) -> Dict[str, Any]:
        """
        创建章节音频（拼接多个音频文件）
        
        Args:
            audio_files: 音频文件路径列表
            output_path: 输出文件路径
            config: 章节音频配置
            
        Returns:
            拼接结果信息
        """
        try:
            logger.info(f"开始创建章节音频，共{len(audio_files)}个片段")
            
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._create_chapter_sync,
                audio_files,
                output_path,
                config
            )
            
            logger.info(f"章节音频创建完成: {output_path}")
            return result
            
        except Exception as e:
            logger.error(f"章节音频创建失败: {str(e)}")
            raise Exception(f"章节音频创建失败: {str(e)}")
    
    def _create_chapter_sync(
        self,
        audio_files: List[str],
        output_path: str,
        config: ChapterAudioConfig
    ) -> Dict[str, Any]:
        """同步执行章节音频创建"""
        
        clips = []
        total_duration = 0
        
        for i, audio_file in enumerate(audio_files):
            if not os.path.exists(audio_file):
                logger.warning(f"音频文件不存在: {audio_file}")
                continue
                
            # 加载音频片段
            clip = AudioFileClip(audio_file)
            
            # 应用淡入淡出效果
            if config.apply_fade and config.fade_duration > 0:
                clip = audio_fadein(clip, config.fade_duration)
                clip = audio_fadeout(clip, config.fade_duration)
            
            clips.append(clip)
            total_duration += clip.duration
            
            # 在片段间添加静音（除了最后一个片段）
            if i < len(audio_files) - 1 and config.silence_duration > 0:
                from moviepy.editor import AudioClip
                silence = AudioClip(
                    lambda t: np.zeros((int(44100 * config.silence_duration), 2)),
                    duration=config.silence_duration
                )
                clips.append(silence)
                total_duration += config.silence_duration
        
        if not clips:
            raise Exception("没有有效的音频文件")
        
        # 拼接所有音频片段
        final_clip = concatenate_audioclips(clips)
        
        # 音量标准化
        if config.normalize_volume:
            final_clip = final_clip.volumex(0.8)
        
        # 导出音频
        final_clip.write_audiofile(
            output_path,
            codec='libmp3lame',
            bitrate='192k',
            verbose=False,
            logger=None
        )
        
        # 清理资源
        for clip in clips:
            clip.close()
        final_clip.close()
        
        return {
            "success": True,
            "output_path": output_path,
            "duration": total_duration,
            "segments_count": len([f for f in audio_files if os.path.exists(f)]),
            "file_size": os.path.getsize(output_path),
            "format": "mp3",
            "bitrate": "192k"
        }
    
    async def apply_audio_effects(
        self,
        input_path: str,
        output_path: str,
        effects: AudioEffectConfig
    ) -> Dict[str, Any]:
        """
        应用音频效果
        
        Args:
            input_path: 输入音频文件路径
            output_path: 输出音频文件路径
            effects: 音频效果配置
            
        Returns:
            处理结果信息
        """
        try:
            logger.info(f"开始应用音频效果: {input_path}")
            
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._apply_effects_sync,
                input_path,
                output_path,
                effects
            )
            
            logger.info(f"音频效果应用完成: {output_path}")
            return result
            
        except Exception as e:
            logger.error(f"音频效果应用失败: {str(e)}")
            raise Exception(f"音频效果应用失败: {str(e)}")
    
    def _apply_effects_sync(
        self,
        input_path: str,
        output_path: str,
        effects: AudioEffectConfig
    ) -> Dict[str, Any]:
        """同步执行音频效果应用"""
        
        clip = AudioFileClip(input_path)
        
        # 调整音量
        if effects.volume != 1.0:
            clip = clip.volumex(effects.volume)
        
        # 添加淡入效果
        if effects.fadein is not None and effects.fadein > 0:
            clip = audio_fadein(clip, effects.fadein)
        
        # 添加淡出效果
        if effects.fadeout is not None and effects.fadeout > 0:
            clip = audio_fadeout(clip, effects.fadeout)
        
        # 音频标准化
        if effects.normalize:
            clip = clip.volumex(0.8)
        
        # 导出处理后的音频
        clip.write_audiofile(
            output_path,
            codec='libmp3lame',
            bitrate='192k',
            verbose=False,
            logger=None
        )
        
        # 清理资源
        original_duration = clip.duration
        clip.close()
        
        return {
            "success": True,
            "output_path": output_path,
            "duration": original_duration,
            "file_size": os.path.getsize(output_path),
            "effects_applied": {
                "volume": effects.volume,
                "fadein": effects.fadein,
                "fadeout": effects.fadeout,
                "normalize": effects.normalize
            }
        }
    
    async def get_audio_info(self, audio_path: str) -> Dict[str, Any]:
        """
        获取音频文件信息
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            音频文件信息
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._get_audio_info_sync,
                audio_path
            )
            return result
            
        except Exception as e:
            logger.error(f"获取音频信息失败: {str(e)}")
            raise Exception(f"获取音频信息失败: {str(e)}")
    
    def _get_audio_info_sync(self, audio_path: str) -> Dict[str, Any]:
        """同步获取音频信息"""
        
        if not os.path.exists(audio_path):
            raise Exception(f"音频文件不存在: {audio_path}")
        
        clip = AudioFileClip(audio_path)
        
        info = {
            "file_path": audio_path,
            "duration": clip.duration,
            "fps": clip.fps,
            "channels": clip.nchannels if hasattr(clip, 'nchannels') else 2,
            "file_size": os.path.getsize(audio_path),
            "format": os.path.splitext(audio_path)[1].lower()
        }
        
        clip.close()
        return info
    
    async def mix_multiple_audio_tracks(
        self, 
        track_data: List[Dict], 
        output_path: str
    ) -> str:
        """
        混合多个音频轨道
        
        Args:
            track_data: 轨道数据列表，每个包含 file_path, start_time, end_time, volume 等
            output_path: 输出文件路径
            
        Returns:
            输出文件路径
        """
        try:
            logger.info(f"开始混合多轨道音频，共{len(track_data)}个片段")
            
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._mix_multiple_tracks_sync,
                track_data,
                output_path
            )
            
            logger.info(f"多轨道音频混合完成: {output_path}")
            return result
            
        except Exception as e:
            logger.error(f"多轨道音频混合失败: {str(e)}")
            raise Exception(f"多轨道音频混合失败: {str(e)}")

    def _mix_multiple_tracks_sync(
        self,
        track_data: List[Dict],
        output_path: str
    ) -> str:
        """同步执行多轨道音频混合"""
        
        audio_clips = []
        max_end_time = 0.0
        
        try:
            # 处理每个音频片段
            for clip_data in track_data:
                # 加载音频文件
                audio = AudioFileClip(clip_data["file_path"])
                
                # 应用裁剪（如果需要）
                if "source_start" in clip_data and clip_data["source_start"] > 0:
                    audio = audio.subclip(clip_data["source_start"])
                if "source_end" in clip_data and clip_data["source_end"]:
                    duration = clip_data["source_end"] - clip_data.get("source_start", 0)
                    audio = audio.subclip(0, duration)
                
                # 设置音频在时间轴上的位置
                audio = audio.set_start(clip_data["start_time"])
                
                # 应用音量调节
                if "volume" in clip_data and clip_data["volume"] != 1.0:
                    audio = audio.volumex(clip_data["volume"])
                
                # 应用淡入淡出效果
                if "fade_in" in clip_data and clip_data["fade_in"] > 0:
                    audio = audio_fadein(audio, clip_data["fade_in"])
                if "fade_out" in clip_data and clip_data["fade_out"] > 0:
                    audio = audio_fadeout(audio, clip_data["fade_out"])
                
                audio_clips.append(audio)
                
                # 计算最大结束时间
                end_time = clip_data["start_time"] + audio.duration
                max_end_time = max(max_end_time, end_time)
            
            if not audio_clips:
                raise Exception("没有有效的音频片段")
            
            # 混合所有音频片段
            final_audio = CompositeAudioClip(audio_clips)
            
            # 设置总时长
            final_audio = final_audio.set_duration(max_end_time)
            
            # 导出混合后的音频
            final_audio.write_audiofile(
                output_path,
                codec='pcm_s16le',
                verbose=False,
                logger=None
            )
            
            return output_path
            
        except Exception as e:
            raise Exception(f"多轨道音频混合失败: {str(e)}")
        finally:
            # 清理资源
            for clip in audio_clips:
                try:
                    clip.close()
                except:
                    pass
            try:
                if 'final_audio' in locals():
                    final_audio.close()
            except:
                pass

    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            for file in self.temp_dir.glob("*"):
                if file.is_file():
                    file.unlink()
            logger.info("临时文件清理完成")
        except Exception as e:
            logger.error(f"临时文件清理失败: {str(e)}")
    
    def __del__(self):
        """析构函数，清理资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)

class VideoGenerationService:
    """视频生成服务（未来功能）"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    async def create_slideshow_video(
        self,
        images: List[str],
        audio_path: str,
        output_path: str,
        duration_per_image: float = 3.0
    ) -> Dict[str, Any]:
        """
        创建图片轮播视频（未来功能预留）
        
        Args:
            images: 图片文件路径列表
            audio_path: 背景音频路径
            output_path: 输出视频路径
            duration_per_image: 每张图片显示时长
            
        Returns:
            视频创建结果
        """
        # TODO: 实现图片轮播视频功能
        logger.info("VideoGenerationService.create_slideshow_video - 功能开发中")
        return {
            "success": False,
            "message": "视频生成功能正在开发中"
        }
    
    def __del__(self):
        """析构函数，清理资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)

# 服务实例
moviepy_service = MoviePyService()
video_service = VideoGenerationService() 