"""
MegaTTS3引擎适配器实现
"""

import asyncio
import httpx
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

from .base import BaseTTSAdapter, SynthesisParams, SynthesisResult, EngineStatus, ParameterMapper

logger = logging.getLogger(__name__)


class MegaTTS3Adapter(BaseTTSAdapter):
    """MegaTTS3引擎适配器"""
    
    def __init__(self, engine_id: str, config: Dict[str, Any]):
        super().__init__(engine_id, config)
        
        # MegaTTS3配置
        self.model_path = config.get("model_path", "")
        self.config_path = config.get("config_path", "")
        self.device = config.get("device", "cpu")
        self.device_id = config.get("device_id", 0)
        self.endpoint = config.get("endpoint", "")
        self.use_api = bool(self.endpoint)
        self.timeout = config.get("timeout", 60)
        
        # HTTP客户端（API模式）
        self._client: Optional[httpx.AsyncClient] = None
        
        # 本地模型（本地模式）
        self._model = None
        self._loaded_model_path = None
        
        # 声音映射
        self._voice_mapping = {}
    
    async def initialize(self) -> None:
        """初始化MegaTTS3适配器"""
        try:
            self.status = EngineStatus.INITIALIZING
            
            if self.use_api:
                await self._initialize_api_mode()
            else:
                await self._initialize_local_mode()
            
            # 加载声音列表
            await self._load_voices()
            
            self.status = EngineStatus.READY
            logger.info(f"MegaTTS3适配器初始化成功: {self.engine_id}")
            
        except Exception as e:
            self.status = EngineStatus.ERROR
            logger.error(f"MegaTTS3适配器初始化失败: {self.engine_id} - {e}")
            raise
    
    async def _initialize_api_mode(self) -> None:
        """初始化API模式"""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
        
        # 测试API连接
        try:
            response = await self._client.get(f"{self.endpoint}/health")
            response.raise_for_status()
        except Exception as e:
            raise ConnectionError(f"无法连接到MegaTTS3 API: {e}")
    
    async def _initialize_local_mode(self) -> None:
        """初始化本地模式"""
        if not self.model_path or not os.path.exists(self.model_path):
            raise FileNotFoundError(f"模型文件不存在: {self.model_path}")
        
        # 在后台线程中加载模型
        await asyncio.get_event_loop().run_in_executor(
            None, self._load_local_model
        )
    
    def _load_local_model(self) -> None:
        """加载本地模型（在线程中执行）"""
        try:
            # 这里应该是实际的MegaTTS3模型加载代码
            # 由于没有实际的MegaTTS3库，这里仅作示例
            
            # 示例代码（实际实现需要替换）
            # import megatts3
            # self._model = megatts3.TTS(
            #     model_path=self.model_path,
            #     config_path=self.config_path,
            #     device=self.device,
            #     device_id=self.device_id
            # )
            
            # 临时实现：仅记录模型路径
            self._loaded_model_path = self.model_path
            logger.info(f"本地模型已加载: {self.model_path}")
            
        except Exception as e:
            logger.error(f"加载本地模型失败: {e}")
            raise
    
    async def synthesize(self, params: SynthesisParams) -> SynthesisResult:
        """执行语音合成"""
        try:
            if self.use_api:
                return await self._synthesize_via_api(params)
            else:
                return await self._synthesize_local(params)
                
        except Exception as e:
            logger.error(f"MegaTTS3合成失败: {e}")
            return SynthesisResult(
                success=False,
                error_message=str(e)
            )
    
    async def _synthesize_via_api(self, params: SynthesisParams) -> SynthesisResult:
        """通过API进行合成"""
        if not self._client:
            raise RuntimeError("API客户端未初始化")
        
        # 映射参数
        api_params = self._map_synthesis_params(params)
        
        # 调用API
        response = await self._client.post(
            f"{self.endpoint}/synthesize",
            json=api_params
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
            
            # 获取响应头中的元数据
            headers = response.headers
            duration = float(headers.get("X-Audio-Duration", "0"))
            sample_rate = int(headers.get("X-Audio-Sample-Rate", str(params.sample_rate)))
            
            return SynthesisResult(
                success=True,
                output_path=str(output_path),
                duration=duration,
                sample_rate=sample_rate
            )
        else:
            return SynthesisResult(
                success=True,
                sample_rate=params.sample_rate
            )
    
    async def _synthesize_local(self, params: SynthesisParams) -> SynthesisResult:
        """本地合成"""
        if not self._loaded_model_path:
            raise RuntimeError("本地模型未加载")
        
        # 在线程池中执行合成
        result = await asyncio.get_event_loop().run_in_executor(
            None, self._synthesize_local_sync, params
        )
        
        return result
    
    def _synthesize_local_sync(self, params: SynthesisParams) -> SynthesisResult:
        """同步本地合成（在线程中执行）"""
        try:
            # 这里应该是实际的MegaTTS3合成代码
            # 由于没有实际的库，使用命令行工具或示例实现
            
            output_path = Path(params.output_path) if params.output_path else None
            
            # 示例：使用命令行工具（需要根据实际MegaTTS3接口调整）
            if output_path:
                # 构建命令行参数
                cmd = [
                    "python", "-m", "megatts3.synthesize",
                    "--text", params.text,
                    "--voice", params.voice_id,
                    "--speed", str(params.speed),
                    "--pitch", str(params.pitch),
                    "--output", str(output_path),
                    "--model", self._loaded_model_path,
                    "--device", self.device
                ]
                
                # 执行命令
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                
                if result.returncode != 0:
                    raise RuntimeError(f"合成失败: {result.stderr}")
                
                # 估算时长
                duration = self._estimate_duration(params.text, params.speed)
                
                return SynthesisResult(
                    success=True,
                    output_path=str(output_path),
                    duration=duration,
                    sample_rate=params.sample_rate
                )
            else:
                # 仅返回成功状态
                return SynthesisResult(
                    success=True,
                    duration=self._estimate_duration(params.text, params.speed),
                    sample_rate=params.sample_rate
                )
                
        except Exception as e:
            return SynthesisResult(
                success=False,
                error_message=str(e)
            )
    
    async def get_voices(self) -> List[Dict[str, Any]]:
        """获取可用声音列表"""
        try:
            if self.use_api:
                if not self._client:
                    await self.initialize()
                
                response = await self._client.get(f"{self.endpoint}/voices")
                response.raise_for_status()
                
                voices_data = response.json()
                return voices_data.get("voices", [])
            else:
                # 本地模式：返回预定义的声音列表
                return self._get_builtin_voices()
                
        except Exception as e:
            logger.error(f"获取MegaTTS3声音列表失败: {e}")
            return []
    
    def _get_builtin_voices(self) -> List[Dict[str, Any]]:
        """获取内置声音列表"""
        # 返回预定义的中文声音
        return [
            {
                "id": "zh_female_001",
                "name": "中文女声1",
                "language": "zh-CN",
                "gender": "female",
                "description": "温柔的中文女声"
            },
            {
                "id": "zh_male_001", 
                "name": "中文男声1",
                "language": "zh-CN",
                "gender": "male",
                "description": "稳重的中文男声"
            },
            {
                "id": "zh_female_002",
                "name": "中文女声2",
                "language": "zh-CN", 
                "gender": "female",
                "description": "活泼的中文女声"
            }
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            start_time = asyncio.get_event_loop().time()
            
            if self.use_api:
                if not self._client:
                    return {
                        "status": "error",
                        "message": "API客户端未初始化"
                    }
                
                response = await self._client.get(f"{self.endpoint}/health")
                response.raise_for_status()
                
                end_time = asyncio.get_event_loop().time()
                response_time = (end_time - start_time) * 1000
                
                health_data = response.json()
                
                return {
                    "status": "healthy",
                    "mode": "api",
                    "response_time_ms": response_time,
                    "engine_status": health_data.get("status", "unknown"),
                    "model_loaded": health_data.get("model_loaded", False),
                    "available_voices": len(self._voice_mapping)
                }
            else:
                # 本地模式健康检查
                model_loaded = self._loaded_model_path is not None
                
                return {
                    "status": "healthy" if model_loaded else "error",
                    "mode": "local",
                    "model_loaded": model_loaded,
                    "model_path": self._loaded_model_path,
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
            
            if self._model:
                # 清理本地模型
                del self._model
                self._model = None
            
            self._loaded_model_path = None
            self.status = EngineStatus.OFFLINE
            logger.info(f"MegaTTS3适配器已清理: {self.engine_id}")
            
        except Exception as e:
            logger.error(f"MegaTTS3适配器清理失败: {e}")
    
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
        """映射合成参数到MegaTTS3格式"""
        # 映射声音ID
        voice_id = params.voice_id
        if voice_id in self._voice_mapping:
            voice_info = self._voice_mapping[voice_id]
            mega_voice_id = voice_info.get("mega_id", voice_id)
        else:
            mega_voice_id = voice_id
        
        # MegaTTS3参数映射
        mega_params = {
            "text": params.text,
            "speaker": mega_voice_id,
            "speed": params.speed,
            "pitch": params.pitch,
            "volume": params.volume,
            "sample_rate": params.sample_rate,
            "format": "wav"
        }
        
        # 添加自定义参数
        mega_params.update(params.extra_params)
        
        return mega_params
    
    def _estimate_duration(self, text: str, speed: float) -> float:
        """估算音频时长"""
        # 中文文本时长估算：每个字符约0.15秒
        base_duration = len(text) * 0.15
        return base_duration / speed
    
    async def get_voice_info(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """获取声音详细信息"""
        return self._voice_mapping.get(voice_id)
    
    async def set_model(self, model_path: str, config_path: str = "") -> bool:
        """设置模型"""
        try:
            if self.use_api:
                response = await self._client.post(
                    f"{self.endpoint}/model",
                    json={
                        "model_path": model_path,
                        "config_path": config_path
                    }
                )
                response.raise_for_status()
            else:
                self.model_path = model_path
                self.config_path = config_path
                await asyncio.get_event_loop().run_in_executor(
                    None, self._load_local_model
                )
            
            await self._load_voices()  # 重新加载声音
            return True
            
        except Exception as e:
            logger.error(f"设置MegaTTS3模型失败: {e}")
            return False