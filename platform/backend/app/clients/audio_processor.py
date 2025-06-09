"""
音频处理器
提供音频文件的后处理功能
"""

import os
import logging
from typing import List, Optional, Dict, Any
import wave
import tempfile
from pydub import AudioSegment
from pydub.effects import normalize
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class AudioProcessor:
    """音频处理器"""
    
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def merge_audio_files(
        self,
        audio_files: List[str],
        output_path: str,
        fade_duration: float = 0.1,
        gap_duration: float = 0.5
    ) -> bool:
        """
        合并多个音频文件
        
        Args:
            audio_files: 音频文件路径列表
            output_path: 输出文件路径
            fade_duration: 淡入淡出时长（秒）
            gap_duration: 文件间隔时长（秒）
        
        Returns:
            是否合并成功
        """
        try:
            def _merge():
                merged_audio = AudioSegment.empty()
                gap = AudioSegment.silent(duration=int(gap_duration * 1000))
                
                for i, file_path in enumerate(audio_files):
                    if not os.path.exists(file_path):
                        logger.warning(f"音频文件不存在: {file_path}")
                        continue
                    
                    try:
                        # 加载音频文件
                        audio = AudioSegment.from_file(file_path)
                        
                        # 添加淡入淡出效果
                        if fade_duration > 0:
                            fade_ms = int(fade_duration * 1000)
                            audio = audio.fade_in(fade_ms).fade_out(fade_ms)
                        
                        # 合并音频
                        if i == 0:
                            merged_audio = audio
                        else:
                            merged_audio = merged_audio + gap + audio
                        
                        logger.debug(f"已添加音频文件: {file_path}")
                        
                    except Exception as e:
                        logger.error(f"处理音频文件失败 {file_path}: {e}")
                        continue
                
                if len(merged_audio) > 0:
                    # 导出合并后的音频
                    merged_audio.export(output_path, format="wav")
                    logger.info(f"音频合并完成: {output_path}")
                    return True
                else:
                    logger.error("没有有效的音频文件进行合并")
                    return False
            
            # 在线程池中执行音频处理
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor, _merge
            )
            return result
            
        except Exception as e:
            logger.error(f"音频合并失败: {e}")
            return False
    
    async def normalize_audio(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        target_dbfs: float = -20.0
    ) -> Optional[str]:
        """
        音频标准化
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径，如果为None则覆盖原文件
            target_dbfs: 目标音量（dBFS）
        
        Returns:
            处理后的文件路径
        """
        try:
            if output_path is None:
                output_path = input_path
            
            def _normalize():
                audio = AudioSegment.from_file(input_path)
                
                # 标准化音频
                normalized_audio = normalize(audio)
                
                # 调整到目标音量
                change_in_dbfs = target_dbfs - normalized_audio.dBFS
                normalized_audio = normalized_audio.apply_gain(change_in_dbfs)
                
                # 导出处理后的音频
                normalized_audio.export(output_path, format="wav")
                return output_path
            
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor, _normalize
            )
            
            logger.info(f"音频标准化完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"音频标准化失败: {e}")
            return None
    
    async def convert_format(
        self,
        input_path: str,
        output_path: str,
        output_format: str = "wav",
        **kwargs
    ) -> bool:
        """
        音频格式转换
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            output_format: 输出格式
            **kwargs: 额外的转换参数
        
        Returns:
            是否转换成功
        """
        try:
            def _convert():
                audio = AudioSegment.from_file(input_path)
                
                # 应用转换参数
                if 'sample_rate' in kwargs:
                    audio = audio.set_frame_rate(kwargs['sample_rate'])
                
                if 'channels' in kwargs:
                    audio = audio.set_channels(kwargs['channels'])
                
                if 'bit_depth' in kwargs:
                    audio = audio.set_sample_width(kwargs['bit_depth'] // 8)
                
                # 导出指定格式
                audio.export(output_path, format=output_format)
                return True
            
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor, _convert
            )
            
            if result:
                logger.info(f"音频格式转换完成: {input_path} -> {output_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"音频格式转换失败: {e}")
            return False
    
    async def trim_silence(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        silence_threshold: int = -40,
        min_silence_len: int = 300
    ) -> Optional[str]:
        """
        裁剪音频中的静音部分
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            silence_threshold: 静音阈值（dBFS）
            min_silence_len: 最小静音长度（毫秒）
        
        Returns:
            处理后的文件路径
        """
        try:
            if output_path is None:
                name, ext = os.path.splitext(input_path)
                output_path = f"{name}_trimmed{ext}"
            
            def _trim():
                from pydub.silence import strip_silence
                
                audio = AudioSegment.from_file(input_path)
                
                # 裁剪静音
                trimmed_audio = strip_silence(
                    audio,
                    silence_len=min_silence_len,
                    silence_thresh=silence_threshold,
                    padding=100  # 保留100ms的静音作为缓冲
                )
                
                # 导出处理后的音频
                trimmed_audio.export(output_path, format="wav")
                return output_path
            
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor, _trim
            )
            
            logger.info(f"静音裁剪完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"静音裁剪失败: {e}")
            return None
    
    async def apply_effects(
        self,
        input_path: str,
        output_path: str,
        effects: Dict[str, Any]
    ) -> bool:
        """
        应用音频效果
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            effects: 效果配置字典
        
        Returns:
            是否处理成功
        """
        try:
            def _apply_effects():
                audio = AudioSegment.from_file(input_path)
                
                # 应用音量调整
                if 'volume' in effects:
                    volume_change = effects['volume']
                    audio = audio.apply_gain(volume_change)
                
                # 应用速度调整
                if 'speed' in effects:
                    speed_factor = effects['speed']
                    # 改变播放速度（同时影响音调）
                    new_sample_rate = int(audio.frame_rate * speed_factor)
                    audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_sample_rate})
                    audio = audio.set_frame_rate(audio.frame_rate)
                
                # 应用淡入淡出
                if 'fade_in' in effects:
                    fade_in_ms = int(effects['fade_in'] * 1000)
                    audio = audio.fade_in(fade_in_ms)
                
                if 'fade_out' in effects:
                    fade_out_ms = int(effects['fade_out'] * 1000)
                    audio = audio.fade_out(fade_out_ms)
                
                # 应用高通/低通滤波器
                if 'high_pass_filter' in effects:
                    freq = effects['high_pass_filter']
                    audio = audio.high_pass_filter(freq)
                
                if 'low_pass_filter' in effects:
                    freq = effects['low_pass_filter']
                    audio = audio.low_pass_filter(freq)
                
                # 导出处理后的音频
                audio.export(output_path, format="wav")
                return True
            
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor, _apply_effects
            )
            
            if result:
                logger.info(f"音频效果处理完成: {output_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"音频效果处理失败: {e}")
            return False
    
    def get_audio_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        获取音频文件信息
        
        Args:
            file_path: 音频文件路径
        
        Returns:
            音频信息字典
        """
        try:
            audio = AudioSegment.from_file(file_path)
            
            return {
                "duration": len(audio) / 1000.0,  # 转换为秒
                "frame_rate": audio.frame_rate,
                "channels": audio.channels,
                "sample_width": audio.sample_width,
                "frame_count": audio.frame_count(),
                "max_dBFS": audio.max_dBFS,
                "dBFS": audio.dBFS,
                "file_size": os.path.getsize(file_path)
            }
            
        except Exception as e:
            logger.error(f"获取音频信息失败: {e}")
            return None
    
    async def close(self):
        """关闭音频处理器"""
        self.executor.shutdown(wait=True)
        logger.info("音频处理器已关闭")


# 全局音频处理器实例
audio_processor = AudioProcessor() 