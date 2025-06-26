"""
SongGeneration引擎客户端
类似MegaTTS3的简洁设计：纯粹的音乐生成引擎
输入：歌词文本 → 输出：音频文件
"""

import httpx
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SynthesizeRequest:
    """音乐合成请求"""
    lyrics: str
    style: str = "pop"
    duration: int = 30

@dataclass
class SynthesizeResponse:
    """音乐合成响应"""
    audio_url: str
    duration: float
    generation_time: float

class SongGenerationEngineClient:
    """
    SongGeneration引擎客户端
    简洁设计：只负责与引擎通信，不包含业务逻辑
    """
    
    def __init__(self, base_url: str = "http://localhost:8081", timeout: int = 300):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        logger.info(f"SongGeneration引擎客户端初始化: {self.base_url}")
    
    async def health_check(self) -> bool:
        """检查引擎健康状态"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("status") == "healthy"
                return False
        except Exception as e:
            logger.warning(f"SongGeneration引擎健康检查失败: {e}")
            return False
    
    async def synthesize(self, lyrics: str, style: str = "pop", duration: int = 30) -> Optional[SynthesizeResponse]:
        """
        合成音乐
        纯粹的生成功能：歌词输入 → 音频输出
        
        Args:
            lyrics: 歌词内容
            style: 音乐风格
            duration: 目标时长
            
        Returns:
            合成响应或None（如果失败）
        """
        try:
            logger.info(f"开始音乐合成: {lyrics[:50]}... (风格: {style}, 时长: {duration}s)")
            
            request_data = {
                "lyrics": lyrics,
                "style": style,
                "duration": duration
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/synthesize",
                    json=request_data
                )
                response.raise_for_status()
                
                data = response.json()
                return SynthesizeResponse(
                    audio_url=data["audio_url"],
                    duration=data["duration"],
                    generation_time=data["generation_time"]
                )
                
        except Exception as e:
            logger.error(f"音乐合成失败: {e}")
            return None
    
    async def get_engine_info(self) -> Optional[Dict[str, Any]]:
        """获取引擎信息"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/")
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            logger.warning(f"获取引擎信息失败: {e}")
            return None

# 全局客户端实例
_engine_client = None

def get_songgeneration_engine() -> SongGenerationEngineClient:
    """获取SongGeneration引擎客户端实例（单例模式）"""
    global _engine_client
    if _engine_client is None:
        # 从环境变量或配置获取引擎URL
        import os
        engine_url = os.getenv("SONGGENERATION_URL", "http://localhost:8081")
        _engine_client = SongGenerationEngineClient(engine_url)
    return _engine_client 