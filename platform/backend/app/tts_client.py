"""
MegaTTS3 客户端适配器
与 localhost:7929 的 MegaTTS3 引擎通信
"""

import aiohttp
import logging
import os
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import asyncio
import json

logger = logging.getLogger(__name__)

@dataclass
class TTSRequest:
    """TTS合成请求数据"""
    text: str
    reference_audio_path: str
    output_audio_path: str
    time_step: int = 20
    p_weight: float = 1.0
    t_weight: float = 1.0
    latent_file_path: Optional[str] = None

@dataclass
class TTSResponse:
    """TTS合成响应数据"""
    success: bool
    message: str
    audio_path: Optional[str] = None
    processing_time: Optional[float] = None
    error_code: Optional[str] = None

class MegaTTS3Client:
    """
    MegaTTS3 HTTP 客户端
    """
    
    def __init__(self, base_url: str = "http://localhost:7929"):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=300)  # 5分钟超时
        self.max_retries = 3
        
    async def health_check(self) -> Dict[str, Any]:
        """
        检查MegaTTS3服务健康状态
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "healthy",
                            "response_time": data.get("response_time", "unknown"),
                            "version": data.get("version", "unknown"),
                            "timestamp": data.get("timestamp", "unknown")
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "error": f"HTTP {response.status}",
                            "message": await response.text()
                        }
        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "error": "连接超时",
                "message": "MegaTTS3服务连接超时"
            }
        except aiohttp.ClientError as e:
            return {
                "status": "error",
                "error": "连接失败",
                "message": f"无法连接到MegaTTS3服务: {str(e)}"
            }
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return {
                "status": "error",
                "error": "未知错误",
                "message": str(e)
            }
    
    async def synthesize_speech(self, request: TTSRequest) -> TTSResponse:
        """
        文本转语音合成
        """
        start_time = time.time()
        
        try:
            # 验证参考音频文件
            if not os.path.exists(request.reference_audio_path):
                return TTSResponse(
                    success=False,
                    message=f"参考音频文件不存在: {request.reference_audio_path}",
                    error_code="REFERENCE_AUDIO_NOT_FOUND"
                )
            
            # 验证潜向量文件（如果提供）
            if request.latent_file_path and not os.path.exists(request.latent_file_path):
                logger.warning(f"潜向量文件不存在，将跳过: {request.latent_file_path}")
                request.latent_file_path = None
            
            # 构建请求数据
            form_data = aiohttp.FormData()
            form_data.add_field('text', request.text)
            form_data.add_field('time_step', str(request.time_step))
            form_data.add_field('p_weight', str(request.p_weight))
            form_data.add_field('t_weight', str(request.t_weight))
            
            # 添加参考音频文件
            with open(request.reference_audio_path, 'rb') as f:
                form_data.add_field(
                    'reference_audio',
                    f,
                    filename=os.path.basename(request.reference_audio_path),
                    content_type='audio/*'
                )
            
            # 添加潜向量文件（如果有）
            if request.latent_file_path:
                with open(request.latent_file_path, 'rb') as f:
                    form_data.add_field(
                        'latent_file',
                        f,
                        filename=os.path.basename(request.latent_file_path),
                        content_type='application/octet-stream'
                    )
            
            # 发送请求
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/tts/synthesize",
                    data=form_data
                ) as response:
                    
                    processing_time = time.time() - start_time
                    
                    if response.status == 200:
                        # 成功响应，保存音频文件
                        audio_content = await response.read()
                        
                        # 确保输出目录存在
                        os.makedirs(os.path.dirname(request.output_audio_path), exist_ok=True)
                        
                        # 保存音频文件
                        with open(request.output_audio_path, 'wb') as f:
                            f.write(audio_content)
                        
                        logger.info(f"TTS合成成功: {request.output_audio_path} (耗时: {processing_time:.2f}s)")
                        
                        return TTSResponse(
                            success=True,
                            message="合成完成",
                            audio_path=request.output_audio_path,
                            processing_time=processing_time
                        )
                    
                    else:
                        # 错误响应
                        error_text = await response.text()
                        try:
                            error_data = json.loads(error_text)
                            error_message = error_data.get('detail', error_text)
                            error_code = error_data.get('error_code', 'TTS_ERROR')
                        except json.JSONDecodeError:
                            error_message = error_text
                            error_code = f"HTTP_{response.status}"
                        
                        logger.error(f"TTS合成失败: HTTP {response.status} - {error_message}")
                        
                        return TTSResponse(
                            success=False,
                            message=error_message,
                            processing_time=processing_time,
                            error_code=error_code
                        )
        
        except asyncio.TimeoutError:
            processing_time = time.time() - start_time
            logger.error(f"TTS合成超时: {processing_time:.2f}s")
            return TTSResponse(
                success=False,
                message="合成超时",
                processing_time=processing_time,
                error_code="TIMEOUT"
            )
        
        except aiohttp.ClientError as e:
            processing_time = time.time() - start_time
            logger.error(f"TTS合成网络错误: {str(e)}")
            return TTSResponse(
                success=False,
                message=f"网络错误: {str(e)}",
                processing_time=processing_time,
                error_code="NETWORK_ERROR"
            )
        
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"TTS合成未知错误: {str(e)}")
            return TTSResponse(
                success=False,
                message=f"未知错误: {str(e)}",
                processing_time=processing_time,
                error_code="UNKNOWN_ERROR"
            )
    
    async def clone_voice(self, reference_audio_path: str, voice_name: str) -> Dict[str, Any]:
        """
        声音克隆 - 生成潜向量文件
        """
        start_time = time.time()
        
        try:
            if not os.path.exists(reference_audio_path):
                return {
                    "success": False,
                    "message": f"参考音频文件不存在: {reference_audio_path}",
                    "error_code": "REFERENCE_AUDIO_NOT_FOUND"
                }
            
            # 构建表单数据
            form_data = aiohttp.FormData()
            form_data.add_field('voice_name', voice_name)
            
            with open(reference_audio_path, 'rb') as f:
                form_data.add_field(
                    'reference_audio',
                    f,
                    filename=os.path.basename(reference_audio_path),
                    content_type='audio/*'
                )
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/voice/clone",
                    data=form_data
                ) as response:
                    
                    processing_time = time.time() - start_time
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"声音克隆成功: {voice_name} (耗时: {processing_time:.2f}s)")
                        
                        return {
                            "success": True,
                            "message": "声音克隆完成",
                            "latent_file_path": result.get("latent_file_path"),
                            "voice_id": result.get("voice_id"),
                            "processing_time": processing_time
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"声音克隆失败: HTTP {response.status} - {error_text}")
                        
                        return {
                            "success": False,
                            "message": f"克隆失败: {error_text}",
                            "processing_time": processing_time,
                            "error_code": f"HTTP_{response.status}"
                        }
        
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"声音克隆错误: {str(e)}")
            return {
                "success": False,
                "message": f"克隆错误: {str(e)}",
                "processing_time": processing_time,
                "error_code": "CLONE_ERROR"
            }
    
    async def get_voice_quality_score(self, audio_path: str) -> Dict[str, Any]:
        """
        音质评估
        """
        try:
            if not os.path.exists(audio_path):
                return {
                    "success": False,
                    "message": f"音频文件不存在: {audio_path}",
                    "error_code": "AUDIO_NOT_FOUND"
                }
            
            form_data = aiohttp.FormData()
            with open(audio_path, 'rb') as f:
                form_data.add_field(
                    'audio_file',
                    f,
                    filename=os.path.basename(audio_path),
                    content_type='audio/*'
                )
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/voice/quality",
                    data=form_data
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "quality_score": result.get("quality_score", 3.0),
                            "metrics": result.get("metrics", {}),
                            "message": "音质评估完成"
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "message": f"音质评估失败: {error_text}",
                            "error_code": f"HTTP_{response.status}"
                        }
        
        except Exception as e:
            logger.error(f"音质评估错误: {str(e)}")
            return {
                "success": False,
                "message": f"评估错误: {str(e)}",
                "error_code": "QUALITY_ERROR"
            }
    
    async def get_system_info(self) -> Dict[str, Any]:
        """
        获取MegaTTS3系统信息
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/system/info") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {
                            "error": f"HTTP {response.status}",
                            "message": await response.text()
                        }
        except Exception as e:
            logger.error(f"获取系统信息失败: {str(e)}")
            return {
                "error": "connection_failed",
                "message": str(e)
            }

# 全局客户端实例
_tts_client = None

def get_tts_client() -> MegaTTS3Client:
    """
    获取TTS客户端单例
    """
    global _tts_client
    if _tts_client is None:
        _tts_client = MegaTTS3Client()
    return _tts_client 