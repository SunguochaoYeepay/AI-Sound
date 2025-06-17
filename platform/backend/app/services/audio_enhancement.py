"""
音频增强服务 - 集成 TangoFlux 音效生成
"""
import requests
import base64
import logging
import asyncio
from typing import Optional, Dict, Any
import numpy as np
from pydub import AudioSegment
import io

logger = logging.getLogger(__name__)

class AudioEnhancementService:
    """音频增强服务 - 结合语音合成和音效生成"""
    
    def __init__(self):
        self.tangoflux_api_url = "https://api-inference.huggingface.co/models/declare-lab/TangoFlux"
        self.huggingface_token = None  # 需要配置 HF token
        
    def set_huggingface_token(self, token: str):
        """设置 Hugging Face API token"""
        self.huggingface_token = token
    
    async def generate_scene_audio(self, prompt: str, duration: int = 10) -> Optional[bytes]:
        """
        使用 TangoFlux 生成场景音效
        
        Args:
            prompt: 音效描述文本，如 "Thunder and lightning storm"
            duration: 音频时长（秒）
            
        Returns:
            音频数据（bytes）
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.huggingface_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "duration": duration,
                    "steps": 50,  # 使用50步获得更好质量
                }
            }
            
            response = requests.post(
                self.tangoflux_api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"TangoFlux API 错误: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"生成场景音效失败: {e}")
            return None
    
    def extract_scene_description(self, text: str) -> str:
        """
        从文本中提取场景描述，生成音效提示词
        
        Args:
            text: 小说文本
            
        Returns:
            音效生成提示词
        """
        # 简单的关键词映射 - 实际可以用更智能的NLP模型
        scene_keywords = {
            "雷声": "thunder and lightning storm",
            "雨": "heavy rain falling",
            "风": "strong wind blowing",
            "海浪": "ocean waves crashing",
            "鸟叫": "birds chirping in forest",
            "火": "crackling fire",
            "脚步声": "footsteps on wooden floor",
            "敲门": "knocking on door",
            "汽车": "car engine starting",
            "人群": "crowd cheering and applauding",
            "战斗": "sword clashing metal sounds",
            "森林": "peaceful forest ambience",
            "城市": "busy urban street sounds",
            "夜晚": "quiet night ambience with crickets"
        }
        
        # 检测文本中的场景关键词
        detected_scenes = []
        for keyword, prompt in scene_keywords.items():
            if keyword in text:
                detected_scenes.append(prompt)
        
        if detected_scenes:
            return detected_scenes[0]  # 返回第一个匹配的场景
        else:
            return "ambient background music"  # 默认背景音
    
    def mix_audio(self, voice_audio: bytes, background_audio: bytes, 
                  voice_volume: float = 1.0, background_volume: float = 0.3) -> bytes:
        """
        混合语音和背景音效
        
        Args:
            voice_audio: 语音音频数据
            background_audio: 背景音效数据
            voice_volume: 语音音量（0.0-1.0）
            background_volume: 背景音音量（0.0-1.0）
            
        Returns:
            混合后的音频数据
        """
        try:
            # 加载音频
            voice = AudioSegment.from_wav(io.BytesIO(voice_audio))
            background = AudioSegment.from_wav(io.BytesIO(background_audio))
            
            # 调整音量
            voice = voice + (20 * np.log10(voice_volume))
            background = background + (20 * np.log10(background_volume))
            
            # 调整背景音长度匹配语音
            if len(background) < len(voice):
                # 循环播放背景音
                loops = int(len(voice) / len(background)) + 1
                background = background * loops
            
            background = background[:len(voice)]
            
            # 混合音频
            mixed = voice.overlay(background)
            
            # 导出为bytes
            output = io.BytesIO()
            mixed.export(output, format="wav")
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"音频混合失败: {e}")
            return voice_audio  # 返回原始语音
    
    async def enhance_novel_audio(self, text: str, voice_audio: bytes) -> bytes:
        """
        增强小说音频 - 添加场景音效
        
        Args:
            text: 原始文本
            voice_audio: 语音音频
            
        Returns:
            增强后的音频
        """
        try:
            # 提取场景描述
            scene_prompt = self.extract_scene_description(text)
            logger.info(f"检测到场景: {scene_prompt}")
            
            # 生成背景音效
            background_audio = await self.generate_scene_audio(scene_prompt)
            
            if background_audio:
                # 混合音频
                enhanced_audio = self.mix_audio(voice_audio, background_audio)
                logger.info("音频增强成功")
                return enhanced_audio
            else:
                logger.warning("背景音效生成失败，返回原始语音")
                return voice_audio
                
        except Exception as e:
            logger.error(f"音频增强失败: {e}")
            return voice_audio

# 全局实例
audio_enhancement_service = AudioEnhancementService() 