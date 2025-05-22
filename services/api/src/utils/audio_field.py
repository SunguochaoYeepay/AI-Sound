"""
声场处理模块
提供基础声场构建和音频空间处理功能
"""

import numpy as np
import librosa
import soundfile as sf
from typing import Tuple, List, Dict, Any, Optional


class SoundField:
    """声场处理类，提供基础的立体声空间定位和混响效果"""
    
    def __init__(self, sample_rate: int = 22050):
        """
        初始化声场处理器
        
        Args:
            sample_rate: 音频采样率
        """
        self.sample_rate = sample_rate
        self.reverb_buffer = None
        self.reverb_size = int(sample_rate * 1.5)  # 1.5秒的混响缓冲区
        self._initialize_reverb()
    
    def _initialize_reverb(self):
        """初始化混响效果"""
        # 创建指数衰减的混响滤波器
        decay = np.exp(np.linspace(0, -8, self.reverb_size))
        noise = np.random.normal(0, 0.001, self.reverb_size)
        self.reverb_buffer = decay * noise
    
    def apply_stereo_panning(self, audio: np.ndarray, position_x: float) -> np.ndarray:
        """
        应用立体声左右声道平衡
        
        Args:
            audio: 单声道音频数据
            position_x: 位置参数，范围-1.0(左)到1.0(右)
            
        Returns:
            np.ndarray: 立体声音频数据
        """
        # 确保音频是单声道
        if len(audio.shape) > 1 and audio.shape[1] > 1:
            audio = np.mean(audio, axis=1)
        
        # 确保位置在合法范围内
        position_x = max(-1.0, min(1.0, position_x))
        
        # 计算左右声道增益
        left_gain = np.sqrt(0.5 - position_x/2)
        right_gain = np.sqrt(0.5 + position_x/2)
        
        # 创建立体声音频
        stereo_audio = np.vstack([audio * left_gain, audio * right_gain]).T
        return stereo_audio
    
    def apply_reverb(self, audio: np.ndarray, amount: float = 0.3) -> np.ndarray:
        """
        应用混响效果
        
        Args:
            audio: 音频数据
            amount: 混响强度，范围0.0-1.0
            
        Returns:
            np.ndarray: 添加混响后的音频
        """
        # 确保声音是单声道用于处理
        if len(audio.shape) > 1:
            # 对于立体声，分别处理两个声道
            processed = np.zeros_like(audio)
            for i in range(audio.shape[1]):
                processed[:, i] = self._apply_reverb_mono(audio[:, i], amount)
            return processed
        else:
            # 单声道处理
            return self._apply_reverb_mono(audio, amount)
    
    def _apply_reverb_mono(self, audio: np.ndarray, amount: float) -> np.ndarray:
        """给单声道音频添加混响"""
        # 计算卷积（效率较低但简单实现）
        reverb_audio = np.zeros(len(audio) + self.reverb_size - 1)
        for i in range(len(audio)):
            reverb_audio[i:i+self.reverb_size] += audio[i] * self.reverb_buffer
        
        # 混合原始音频和混响
        # 截取与原始音频相同长度
        reverb_audio = reverb_audio[:len(audio)]
        return audio * (1.0 - amount) + reverb_audio * amount
    
    def place_audio_source(self, audio: np.ndarray, position_x: float, 
                          reverb_amount: float = 0.2) -> np.ndarray:
        """
        在声场中放置音频源
        
        Args:
            audio: 音频数据
            position_x: 位置参数，范围-1.0(左)到1.0(右)
            reverb_amount: 混响强度，范围0.0-1.0
            
        Returns:
            np.ndarray: 处理后的立体声音频
        """
        # 应用立体声左右平衡
        stereo_audio = self.apply_stereo_panning(audio, position_x)
        
        # 应用混响
        if reverb_amount > 0:
            stereo_audio = self.apply_reverb(stereo_audio, reverb_amount)
        
        return stereo_audio
    
    def create_sound_scene(self, sources: List[Dict[str, Any]]) -> np.ndarray:
        """
        创建完整的声场场景
        
        Args:
            sources: 音频源列表，每个源包含:
                    {
                        'audio': 音频数据,
                        'position_x': 位置(-1.0到1.0),
                        'reverb': 混响强度(0.0到1.0)
                    }
                    
        Returns:
            np.ndarray: 混合后的场景音频
        """
        if not sources:
            return np.array([])
        
        # 确定最长的音频
        max_length = max(source['audio'].shape[0] for source in sources)
        
        # 初始化场景声音（立体声）
        scene_audio = np.zeros((max_length, 2))
        
        # 添加每个音频源
        for source in sources:
            audio = source['audio']
            position_x = source.get('position_x', 0.0)
            reverb = source.get('reverb', 0.2)
            
            # 处理音频位置和混响
            processed = self.place_audio_source(audio, position_x, reverb)
            
            # 添加到场景（可能长度不同，只使用有效部分）
            scene_audio[:len(processed)] += processed
        
        # 防止音频峰值过高
        if np.max(np.abs(scene_audio)) > 0.95:
            scene_audio = scene_audio / np.max(np.abs(scene_audio)) * 0.95
            
        return scene_audio
    
    @staticmethod
    def save_audio(audio: np.ndarray, file_path: str, sample_rate: int = 22050):
        """
        保存音频到文件
        
        Args:
            audio: 音频数据
            file_path: 输出文件路径
            sample_rate: 采样率
        """
        sf.write(file_path, audio, sample_rate)
    
    @staticmethod
    def load_audio(file_path: str, mono: bool = True) -> Tuple[np.ndarray, int]:
        """
        从文件加载音频
        
        Args:
            file_path: 音频文件路径
            mono: 是否转为单声道
            
        Returns:
            Tuple[np.ndarray, int]: (音频数据, 采样率)
        """
        audio, sr = librosa.load(file_path, mono=mono, sr=None)
        return audio, sr 