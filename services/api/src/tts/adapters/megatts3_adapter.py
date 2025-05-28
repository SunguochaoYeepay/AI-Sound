"""
MegaTTS3 服务适配器
"""

import logging
import httpx
from typing import Dict, Any, Optional, List

from ..engine import TTSEngine

logger = logging.getLogger(__name__)

class MegaTTS3Adapter(TTSEngine):
    """MegaTTS3 服务适配器"""
    
    def __init__(self, service_url: str):
        """
        初始化 MegaTTS3 适配器
        
        Args:
            service_url: MegaTTS3 服务的 URL
        """
        self.service_url = service_url
        self.client = httpx.AsyncClient(base_url=service_url, timeout=60.0)
        logger.info(f"初始化 MegaTTS3 适配器，服务URL: {service_url}")
        
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        emotion_type: Optional[str] = None,
        emotion_intensity: float = 0.5,
        speed_scale: float = 1.0,
        pitch_scale: float = 1.0,
        energy_scale: float = 1.0,
        **kwargs: Dict[str, Any]
    ) -> bytes:
        """
        文本转语音合成
        
        Args:
            text: 要合成的文本
            voice_id: 音色ID
            emotion_type: 情感类型
            emotion_intensity: 情感强度
            speed_scale: 语速缩放
            pitch_scale: 音高缩放
            energy_scale: 音量缩放
            **kwargs: 其他参数
            
        Returns:
            WAV 格式的音频数据
        """
        try:
            # 构建请求参数
            params = {
                "text": text,
                "voice_id": voice_id,
                "emotion_type": emotion_type,
                "emotion_intensity": emotion_intensity,
                "speed_scale": speed_scale,
                "pitch_scale": pitch_scale,
                "energy_scale": energy_scale,
            }
            
            # 添加其他参数
            for key, value in kwargs.items():
                if value is not None:
                    params[key] = value
            
            logger.debug(f"MegaTTS3 合成请求: {params}")
            
            # 发送请求
            response = await self.client.post("/api/tts", json=params)
            
            # 检查响应状态
            if response.status_code != 200:
                error_msg = f"MegaTTS3 合成失败，状态码: {response.status_code}, 响应: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            # 返回音频数据
            return response.content
            
        except Exception as e:
            logger.error(f"MegaTTS3 合成异常: {str(e)}")
            raise
    
    async def get_available_voices(self) -> Dict[str, Dict[str, Any]]:
        """
        获取可用音色列表
        
        Returns:
            音色ID到音色信息的映射
        """
        try:
            # 发送请求
            response = await self.client.get("/api/voices")
            
            # 检查响应状态
            if response.status_code != 200:
                error_msg = f"获取MegaTTS3音色列表失败，状态码: {response.status_code}, 响应: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            # 解析响应
            result = response.json()
            voices = result.get("voices", {})
            
            # 返回音色列表
            return voices
            
        except Exception as e:
            logger.error(f"获取MegaTTS3音色列表异常: {str(e)}")
            # 返回空列表，避免因为获取音色失败导致整个服务不可用
            return {}
            
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            服务是否健康
        """
        try:
            # 发送请求
            response = await self.client.get("/health")
            
            # 检查响应状态
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"MegaTTS3健康检查异常: {str(e)}")
            return False