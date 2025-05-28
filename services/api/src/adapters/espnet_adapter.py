"""
ESPnet引擎适配器实现
"""

import asyncio
import httpx
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

from .base import BaseTTSAdapter, SynthesisParams, SynthesisResult, EngineStatus, ParameterMapper

logger = logging.getLogger(__name__)


class ESPnetAdapter(BaseTTSAdapter):
    """ESPnet TTS引擎适配器"""
    
    def __init__(self, engine_id: str, config: Dict[str, Any]):
        super().__init__(engine_id, config)
        
        # ESPnet配置
        self.model_path = config.get("model_path", "")
        self.device = config.get("device", "cpu")
        self.endpoint = config.get("endpoint", "http://localhost:8080")
        self.timeout = config.get("timeout", 30)
        
        # HTTP客户端
        self._client: Optional[httpx.AsyncClient] = None
        
        # 声音映射
        self._voice_mapping = {}
    
    async def initialize(self) -> None:
        """初始化ESPnet适配器"""
        try:
            self.status = EngineStatus.INITIALIZING
            
            # 创建HTTP客户端
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
            
            # 检查模型文件
            if self.model_path and not os.path.exists(self.model_path):
                raise FileNotFoundError(f"模型文件不存在: {self.model_path}")
            
            # 测试连接
            await self._test_connection()
            
            # 加载声音列表
            await self._load_voices()
            
            self.status = EngineStatus.READY
            logger.info(f"ESPnet适配器初始化成功: {self.engine_id}")
            
        except Exception as e:
            self.status = EngineStatus.ERROR
            logger.error(f"ESPnet适配器初始化失败: {self.engine_id} - {e}")
            raise
    
    async def synthesize(self, params: SynthesisParams) -> SynthesisResult:
        """执行语音合成"""
        try:
            if not self._client:
                raise RuntimeError("适配器未初始化")
            
            # 映射参数
            espnet_params = self._map_synthesis_params(params)
            
            # 调用ESPnet API
            response = await self._client.post(
                f"{self.endpoint}/synthesize",
                json=espnet_params
            )
            response.raise_for_status()
            
            # 处理响应
            if params.output_path:
                # 保存音频文件
                audio_data = response.content
                output_path = Path(params.output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, "wb") as f:
                    f.write(audio_data)
                
                # 计算时长（估算）
                duration = len(params.text) * 0.1  # 粗略估算
                
                return SynthesisResult(
                    success=True,
                    output_path=str(output_path),
                    duration=duration,
                    sample_rate=params.sample_rate
                )
            else:
                return SynthesisResult(
                    success=True,
                    duration=len(params.text) * 0.1,
                    sample_rate=params.sample_rate
                )
                
        except Exception as e:
            logger.error(f"ESPnet合成失败: {e}")
            return SynthesisResult(
                success=False,
                error_message=str(e)
            )
    
    async def get_voices(self) -> List[Dict[str, Any]]:
        """获取可用声音列表"""
        try:
            if not self._client:
                await self.initialize()
            
            response = await self._client.get(f"{self.endpoint}/voices")
            response.raise_for_status()
            
            voices_data = response.json()
            return voices_data.get("voices", [])
            
        except Exception as e:
            logger.error(f"获取ESPnet声音列表失败: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if not self._client:
                return {
                    "status": "error",
                    "message": "客户端未初始化"
                }
            
            start_time = asyncio.get_event_loop().time()
            
            # 检查API可用性
            response = await self._client.get(f"{self.endpoint}/health")
            response.raise_for_status()
            
            end_time = asyncio.get_event_loop().time()
            response_time = (end_time - start_time) * 1000
            
            health_data = response.json()
            
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "engine_status": health_data.get("status", "unknown"),
                "model_loaded": health_data.get("model_loaded", False),
                "available_voices": len(self._voice_mapping)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def cleanup(self) -> None:
        """清理资源"""
        try:
            if self._client:
                await self._client.aclose()
                self._client = None
            
            self.status = EngineStatus.OFFLINE
            logger.info(f"ESPnet适配器已清理: {self.engine_id}")
            
        except Exception as e:
            logger.error(f"ESPnet适配器清理失败: {e}")
    
    async def _test_connection(self) -> None:
        """测试连接"""
        try:
            response = await self._client.get(f"{self.endpoint}/health")
            response.raise_for_status()
        except Exception as e:
            raise ConnectionError(f"无法连接到ESPnet服务: {e}")
    
    async def _load_voices(self) -> None:
        """加载声音映射"""
        try:
            voices = await self.get_voices()
            self._voice_mapping = {
                voice.get("id", voice.get("name", str(i))): voice
                for i, voice in enumerate(voices)
            }
            logger.info(f"已加载 {len(self._voice_mapping)} 个声音")
        except Exception as e:
            logger.warning(f"加载声音映射失败: {e}")
            self._voice_mapping = {}
    
    def _map_synthesis_params(self, params: SynthesisParams) -> Dict[str, Any]:
        """映射合成参数到ESPnet格式"""
        # 映射声音ID
        voice_id = params.voice_id
        if voice_id in self._voice_mapping:
            voice_info = self._voice_mapping[voice_id]
            espnet_voice_id = voice_info.get("espnet_id", voice_id)
        else:
            espnet_voice_id = voice_id
        
        # 映射语速（ESPnet使用速率，范围通常0.5-2.0）
        speaking_rate = ParameterMapper.linear_map(
            params.speed, (0.1, 3.0), (0.5, 2.0)
        )
        
        # 映射音调（ESPnet使用音高比例）
        pitch_scale = ParameterMapper.linear_map(
            params.pitch, (-12.0, 12.0), (0.5, 2.0)
        )
        
        # 构建ESPnet参数
        espnet_params = {
            "text": params.text,
            "speaker": espnet_voice_id,
            "speed": speaking_rate,
            "pitch": pitch_scale,
            "volume": params.volume,
            "sample_rate": params.sample_rate,
            "format": "wav"
        }
        
        # 添加自定义参数
        espnet_params.update(params.extra_params)
        
        return espnet_params
    
    def _estimate_duration(self, text: str, speed: float) -> float:
        """估算音频时长"""
        # 简单估算：每个字符约0.1秒，根据语速调整
        base_duration = len(text) * 0.1
        return base_duration / speed
    
    async def get_voice_info(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """获取声音详细信息"""
        return self._voice_mapping.get(voice_id)
    
    async def set_model(self, model_path: str) -> bool:
        """设置模型"""
        try:
            response = await self._client.post(
                f"{self.endpoint}/model",
                json={"model_path": model_path}
            )
            response.raise_for_status()
            
            self.model_path = model_path
            await self._load_voices()  # 重新加载声音
            
            return True
        except Exception as e:
            logger.error(f"设置ESPnet模型失败: {e}")
            return False