"""
音频处理工具包
"""

import os
import numpy as np
import logging
import soundfile as sf
from scipy.io import wavfile
from typing import Optional, Union, List, Tuple
import base64
import tempfile
from pydub import AudioSegment
import shutil
import platform

# 配置日志
logger = logging.getLogger("utils.audio")

# 设置ffmpeg路径 - 使用跨平台方式
try:
    # 先尝试从PATH环境变量中找ffmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        ffmpeg_dir = os.path.dirname(ffmpeg_path)
        AudioSegment.converter = ffmpeg_path
        AudioSegment.ffmpeg = ffmpeg_path
        ffprobe_path = shutil.which("ffprobe")
        if ffprobe_path:
            AudioSegment.ffprobe = ffprobe_path
        logger.info(f"已从PATH找到ffmpeg: {ffmpeg_path}")
        print(f"已从PATH找到ffmpeg: {ffmpeg_path}")
    else:
        # 检查是否在Docker环境
        in_docker = os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER", False)
        if in_docker:
            # Docker中常见的ffmpeg路径
            docker_ffmpeg_paths = [
                "/usr/bin/ffmpeg",
                "/usr/local/bin/ffmpeg"
            ]
            for path in docker_ffmpeg_paths:
                if os.path.exists(path):
                    ffmpeg_dir = os.path.dirname(path)
                    AudioSegment.converter = path
                    AudioSegment.ffmpeg = path
                    ffprobe_path = os.path.join(ffmpeg_dir, "ffprobe")
                    if os.path.exists(ffprobe_path):
                        AudioSegment.ffprobe = ffprobe_path
                    logger.info(f"Docker环境中找到ffmpeg: {path}")
                    print(f"Docker环境中找到ffmpeg: {path}")
                    break
        else:
            # Windows环境下的常见路径检查
            if platform.system() == "Windows":
                potential_ffmpeg_paths = [
                    "C:/ffmpeg/bin/ffmpeg.exe",
                    "C:/ffmpeg-bin/ffmpeg.exe",
                    "C:/Program Files/ffmpeg/bin/ffmpeg.exe",
                    os.path.expanduser("~/ffmpeg/bin/ffmpeg.exe")
                ]
                for path in potential_ffmpeg_paths:
                    if os.path.exists(path):
                        ffmpeg_dir = os.path.dirname(path)
                        AudioSegment.converter = path
                        AudioSegment.ffmpeg = path
                        ffprobe_path = os.path.join(ffmpeg_dir, "ffprobe.exe")
                        if os.path.exists(ffprobe_path):
                            AudioSegment.ffprobe = ffprobe_path
                        logger.info(f"已从常见位置找到ffmpeg: {path}")
                        print(f"已从常见位置找到ffmpeg: {path}")
                        break
            
    # 如果仍然找不到，记录警告
    if not hasattr(AudioSegment, "ffmpeg") or not AudioSegment.ffmpeg:
        logger.warning("无法找到ffmpeg可执行文件，音频处理功能可能受限")
        print("警告: 无法找到ffmpeg可执行文件，音频处理功能可能受限")
        
except Exception as e:
    logger.error(f"设置ffmpeg路径时出错: {e}")
    print(f"设置ffmpeg路径时出错: {e}")

def save_audio(file_path: str, audio_data: np.ndarray, sample_rate: int = 22050, format: str = "wav") -> bool:
    """
    保存音频数据到文件
    
    Args:
        file_path: 输出文件路径
        audio_data: 音频数据数组
        sample_rate: 采样率
        format: 输出格式 (wav, mp3, ogg, flac)
        
    Returns:
        bool: 是否成功
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # 确保音频数据是float32类型，范围在[-1, 1]之间
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        
        # 将float32音频转换为16位整型
        if np.abs(audio_data).max() > 1.0:
            audio_data = audio_data / np.abs(audio_data).max()
        
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        # 根据格式保存
        if format.lower() == "wav":
            # 使用临时文件名避免冲突
            temp_path = f"{file_path}.tmp"
            try:
                # 使用scipy的wavfile写入方式，不容易发生锁定
                wavfile.write(temp_path, sample_rate, audio_int16)
                # 确保文件完全写入并关闭
                import gc
                gc.collect()  # 强制垃圾回收
                # 使用os.replace原子操作重命名文件，避免文件锁定问题
                if os.path.exists(file_path):
                    try:
                        os.unlink(file_path)  # 先尝试删除目标文件
                    except:
                        pass
                os.replace(temp_path, file_path)
            except Exception as e:
                logger.error(f"保存WAV文件失败: {e}")
                raise
            finally:
                # 清理临时文件
                if os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
        else:
            # 对于非wav格式，先保存为临时wav文件，然后转换
            temp_wav = f"{file_path}.temp.wav"
            try:
                wavfile.write(temp_wav, sample_rate, audio_int16)
                import gc
                gc.collect()  # 强制垃圾回收
                convert_audio_format(temp_wav, file_path, format)
            finally:
                # 删除临时文件
                if os.path.exists(temp_wav):
                    try:
                        os.unlink(temp_wav)
                    except:
                        pass
                
        return True
    except Exception as e:
        logger.error(f"保存音频失败: {e}")
        return False

def convert_audio_format(input_path: str, output_path: str, format: str) -> bool:
    """
    转换音频格式
    
    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径
        format: 目标格式
        
    Returns:
        bool: 是否成功转换
    """
    try:
        # 首先尝试使用FFmpeg
        try:
            import subprocess
            import shutil
            
            # 检查ffmpeg是否存在
            ffmpeg_path = shutil.which("ffmpeg")
            if ffmpeg_path is None:
                logger.warning("未找到ffmpeg，将使用内置的音频转换功能")
                raise FileNotFoundError("FFmpeg not found")
            
            # 构建FFmpeg命令
            command = [
                ffmpeg_path,
                "-y",  # 覆盖输出文件
                "-i", input_path,  # 输入文件
                "-ar", "44100",  # 输出采样率
                "-ac", "1",  # 单声道
                "-b:a", "192k",  # 比特率
            ]
            
            # 根据格式选择编码器
            if format.lower() == "mp3":
                command.extend(["-codec:a", "libmp3lame"])
            elif format.lower() == "ogg":
                command.extend(["-codec:a", "libvorbis"])
            elif format.lower() == "flac":
                command.extend(["-codec:a", "flac"])
                
            # 添加输出文件
            command.append(output_path)
            
            # 执行转换
            process = subprocess.Popen(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                logger.warning(f"FFmpeg转换失败: {stderr}")
                raise RuntimeError(f"FFmpeg转换失败: {stderr}")
                
            logger.info(f"成功使用FFmpeg转换音频: {output_path}")
            return True
            
        except (FileNotFoundError, RuntimeError) as e:
            logger.warning(f"使用FFmpeg转换失败: {str(e)}，尝试使用内置转换")
            
            # 使用soundfile和scipy进行内部转换
            import soundfile as sf
            from scipy.io import wavfile
            import numpy as np
            
            # 加载音频
            audio_data, sample_rate = sf.read(input_path)
            
            # 确保音频数据是float32类型，范围在[-1, 1]之间
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            if np.abs(audio_data).max() > 1.0:
                audio_data = audio_data / np.abs(audio_data).max()
                
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # 尝试直接用soundfile保存
            if format.lower() in ["wav", "ogg", "flac"]:
                sf.write(output_path, audio_data, sample_rate, format=format.upper())
                logger.info(f"成功使用soundfile转换音频: {output_path}")
                return True
            elif format.lower() == "mp3":
                # MP3需要特殊处理，先保存为WAV，然后提示用户
                fallback_path = output_path.rsplit(".", 1)[0] + ".wav"
                sf.write(fallback_path, audio_data, sample_rate)
                # 尝试复制WAV文件到目标路径，以确保总是有一个文件返回
                try:
                    import shutil
                    shutil.copy2(fallback_path, output_path)
                    logger.warning(f"无法转换为MP3格式，使用WAV格式代替: {output_path}")
                except Exception as e:
                    logger.warning(f"复制WAV文件失败: {str(e)}")
                    logger.warning(f"无法转换为MP3格式，已保存为WAV格式: {fallback_path}")
                logger.warning("要启用MP3转换，请安装FFmpeg并确保它在系统PATH中")
                return True  # 返回True以便流程继续
            else:
                # 其他格式，保存为WAV
                fallback_path = output_path.rsplit(".", 1)[0] + ".wav"
                sf.write(fallback_path, audio_data, sample_rate)
                logger.warning(f"不支持的格式 '{format}'，已保存为WAV格式: {fallback_path}")
                return False
                
    except Exception as e:
        logger.error(f"转换音频格式失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def load_audio(
    file_path: str, 
    normalize: bool = True
) -> Tuple[np.ndarray, int]:
    """
    加载音频文件
    
    Args:
        file_path: 音频文件路径
        normalize: 是否归一化到[-1, 1]范围
        
    Returns:
        Tuple[np.ndarray, int]: (音频数据, 采样率)
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"音频文件不存在: {file_path}")
            raise FileNotFoundError(f"音频文件不存在: {file_path}")
        
        # 加载音频
        audio_data, sample_rate = sf.read(file_path)
        
        # 归一化
        if normalize and audio_data.dtype != np.float32 and audio_data.dtype != np.float64:
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0
            elif audio_data.dtype == np.int32:
                audio_data = audio_data.astype(np.float32) / 2147483648.0
        
        return audio_data, sample_rate
        
    except Exception as e:
        logger.error(f"加载音频失败: {str(e)}")
        raise

def merge_audio_files(
    file_paths: List[str], 
    output_path: str,
    crossfade_duration: float = 0.2
) -> bool:
    """
    合并多个音频文件
    
    Args:
        file_paths: 音频文件路径列表
        output_path: 输出文件路径
        crossfade_duration: 交叉淡入淡出时长(秒)
        
    Returns:
        bool: 是否成功合并
    """
    if not file_paths:
        logger.error("没有提供音频文件")
        return False
    
    try:
        # 收集所有音频文件
        audio_segments = []
        sample_rate = None
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                logger.warning(f"音频文件不存在，跳过: {file_path}")
                continue
                
            # 加载音频
            audio_data, sr = load_audio(file_path)
            
            # 确保所有文件采样率一致
            if sample_rate is None:
                sample_rate = sr
            elif sample_rate != sr:
                logger.warning(f"音频文件采样率不一致: {file_path} ({sr} != {sample_rate})")
                # 这里可以添加重采样逻辑，现在暂时跳过不匹配的文件
                continue
                
            audio_segments.append(audio_data)
        
        if not audio_segments:
            logger.error("没有有效的音频文件")
            return False
            
        # 计算交叉淡入淡出的样本数
        crossfade_samples = int(crossfade_duration * sample_rate)
        
        # 合并音频片段
        merged_audio = audio_segments[0]
        for i in range(1, len(audio_segments)):
            next_segment = audio_segments[i]
            
            # 如果两个片段都足够长，应用交叉淡入淡出
            if len(merged_audio) > crossfade_samples and len(next_segment) > crossfade_samples:
                # 创建淡出淡入曲线
                fade_out = np.linspace(1.0, 0.0, crossfade_samples)
                fade_in = np.linspace(0.0, 1.0, crossfade_samples)
                
                # 应用交叉淡变
                merged_end = merged_audio[-crossfade_samples:] * fade_out
                next_start = next_segment[:crossfade_samples] * fade_in
                crossfade = merged_end + next_start
                
                # 合并音频
                merged_audio = np.concatenate([
                    merged_audio[:-crossfade_samples],
                    crossfade,
                    next_segment[crossfade_samples:]
                ])
            else:
                # 如果片段太短，直接连接
                merged_audio = np.concatenate([merged_audio, next_segment])
        
        # 保存合并后的音频
        format = os.path.splitext(output_path)[1][1:].lower()
        if format not in ["wav", "mp3", "ogg", "flac"]:
            format = "mp3"  # 默认使用MP3格式
            
        save_audio(output_path, merged_audio, sample_rate, format)
        
        logger.info(f"音频合并完成: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"合并音频失败: {str(e)}")
        return False