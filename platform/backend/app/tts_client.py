"""
MegaTTS3 客户端适配器
与 localhost:7929 的 MegaTTS3 引擎通信
简化版本 - 只做语音合成，不做虚假的声音克隆
"""

import aiohttp
import logging
import os
import time
import re
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
    time_step: int = 32
    p_weight: float = 1.4
    t_weight: float = 3.0
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
    MegaTTS3 HTTP 客户端 - 简化版
    """
    
    def __init__(self, base_url: str = "http://localhost:7929"):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=300)
        
    def _sanitize_text(self, text: str) -> str:
        """清理文本，移除可能导致Header问题的字符"""
        if not text:
            return ""
        
        # 简单清理，避免复杂的正则表达式
        text = text.strip()
        # 只移除明显的控制字符
        text = text.replace('\r', '').replace('\n', ' ')
        
        return text
        
    async def health_check(self) -> Dict[str, Any]:
        """检查MegaTTS3服务健康状态"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"status": "healthy", "data": data}
                    else:
                        return {"status": "unhealthy", "error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def synthesize_speech(self, request: TTSRequest) -> TTSResponse:
        """语音合成 - 唯一的核心功能"""
        start_time = time.time()
        
        try:
            # 验证文件
            if not os.path.exists(request.reference_audio_path):
                return TTSResponse(
                    success=False,
                    message=f"参考音频不存在: {request.reference_audio_path}",
                    error_code="FILE_NOT_FOUND"
                )
            
            # 清理文本
            clean_text = self._sanitize_text(request.text)
            if not clean_text:
                return TTSResponse(
                    success=False,
                    message="文本为空或无效",
                    error_code="INVALID_TEXT"
                )
            
            # 🚨 修复：先读取所有文件内容，避免嵌套with问题
            audio_content = None
            latent_content = None
            audio_filename = os.path.basename(request.reference_audio_path)
            latent_filename = None
            
            # 读取音频文件
            with open(request.reference_audio_path, 'rb') as f:
                audio_content = f.read()
            
            # 读取latent文件（如果有）
            if request.latent_file_path and os.path.exists(request.latent_file_path):
                with open(request.latent_file_path, 'rb') as f:
                    latent_content = f.read()
                    latent_filename = os.path.basename(request.latent_file_path)
            
            # 构建表单数据 - 使用已读取的内容
            form_data = aiohttp.FormData()
            form_data.add_field('text', clean_text)
            form_data.add_field('time_step', str(request.time_step))
            form_data.add_field('p_w', str(request.p_weight))
            form_data.add_field('t_w', str(request.t_weight))
            
            # 🚨 详细请求参数日志
            logger.info(f"=== TTS请求参数详情 ===")
            logger.info(f"目标URL: {self.base_url}/api/v1/tts/synthesize_file")
            logger.info(f"文本内容: '{clean_text}' (长度: {len(clean_text)})")
            logger.info(f"time_step: {request.time_step} (类型: {type(request.time_step)})")
            logger.info(f"p_w: {request.p_weight} (类型: {type(request.p_weight)})")
            logger.info(f"t_w: {request.t_weight} (类型: {type(request.t_weight)})")
            logger.info(f"参考音频: {audio_filename} (大小: {len(audio_content)} bytes)")
            if latent_content:
                logger.info(f"Latent文件: {latent_filename} (大小: {len(latent_content)} bytes)")
            else:
                logger.info(f"Latent文件: 无")
            logger.info(f"输出路径: {request.output_audio_path}")
            logger.info(f"=== 请求参数结束 ===")
            
            # 添加音频文件内容
            form_data.add_field(
                'audio_file',
                audio_content,
                filename=audio_filename,
                content_type='audio/wav'
            )
            
            # 添加latent文件内容（如果有）
            if latent_content and latent_filename:
                form_data.add_field(
                    'latent_file',
                    latent_content,
                    filename=latent_filename,
                    content_type='application/octet-stream'
                )
            
            # 发送请求
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/v1/tts/synthesize_file",
                    data=form_data
                ) as response:
                    
                    processing_time = time.time() - start_time
                    
                    # 🚨 详细响应日志
                    logger.info(f"=== TTS响应详情 ===")
                    logger.info(f"HTTP状态码: {response.status}")
                    logger.info(f"响应头: {dict(response.headers)}")
                    logger.info(f"处理时间: {processing_time:.2f}秒")
                    
                    if response.status == 200:
                        # 成功 - 保存音频
                        audio_content = await response.read()
                        
                        # 🚨 详细音频调试信息
                        logger.info(f"=== 音频文件调试 ===")
                        logger.info(f"音频内容大小: {len(audio_content)} bytes")
                        logger.info(f"音频内容前16字节: {audio_content[:16] if len(audio_content) >= 16 else audio_content}")
                        logger.info(f"是否以RIFF开头: {audio_content.startswith(b'RIFF')}")
                        logger.info(f"输出路径: {request.output_audio_path}")
                        
                        os.makedirs(os.path.dirname(request.output_audio_path), exist_ok=True)
                        
                        with open(request.output_audio_path, 'wb') as output_f:
                            output_f.write(audio_content)
                        
                        # 验证保存后的文件
                        if os.path.exists(request.output_audio_path):
                            saved_size = os.path.getsize(request.output_audio_path)
                            logger.info(f"保存后文件大小: {saved_size} bytes")
                            logger.info(f"文件保存成功: {saved_size == len(audio_content)}")
                        else:
                            logger.error(f"文件保存失败: {request.output_audio_path}")
                        
                        logger.info(f"=== 音频调试结束 ===")
                        
                        logger.info(f"TTS合成成功: {request.output_audio_path} (耗时: {processing_time:.2f}s)")
                        
                        return TTSResponse(
                            success=True,
                            message="合成完成",
                            audio_path=request.output_audio_path,
                            processing_time=processing_time
                        )
                    else:
                        # 失败
                        error_text = await response.text()
                        logger.error(f"=== TTS合成失败详情 ===")
                        logger.error(f"HTTP状态码: {response.status}")
                        logger.error(f"错误响应: {error_text}")
                        logger.error(f"请求URL: {self.base_url}/api/v1/tts/synthesize_file")
                        logger.error(f"发送的参数:")
                        logger.error(f"  - text: '{clean_text[:50]}...' (长度: {len(clean_text)})")
                        logger.error(f"  - time_step: {request.time_step}")
                        logger.error(f"  - p_w: {request.p_weight}")
                        logger.error(f"  - t_w: {request.t_weight}")
                        logger.error(f"  - audio_file: {audio_filename}")
                        logger.error(f"=== 失败详情结束 ===")
                        
                        return TTSResponse(
                            success=False,
                            message=f"合成失败: {error_text}",
                            processing_time=processing_time,
                            error_code=f"HTTP_{response.status}"
                        )
        
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"TTS合成异常: {str(e)}")
            return TTSResponse(
                success=False,
                message=f"合成异常: {str(e)}",
                processing_time=processing_time,
                error_code="EXCEPTION"
            )
    
    async def validate_reference_audio(self, audio_path: str, voice_name: str) -> Dict[str, Any]:
        """
        验证参考音频文件
        这就是所谓的"声音克隆" - 实际上只是验证文件能用
        """
        try:
            if not os.path.exists(audio_path):
                return {
                    "success": False,
                    "message": f"音频文件不存在: {audio_path}",
                    "error_code": "FILE_NOT_FOUND"
                }
            
            # 检查文件大小
            file_size = os.path.getsize(audio_path)
            if file_size == 0:
                return {
                    "success": False,
                    "message": "音频文件为空",
                    "error_code": "EMPTY_FILE"
                }
            
            if file_size > 50 * 1024 * 1024:  # 50MB限制
                return {
                    "success": False,
                    "message": "音频文件过大",
                    "error_code": "FILE_TOO_LARGE"
                }
            
            logger.info(f"参考音频验证成功: {voice_name}")
            
            return {
                "success": True,
                "message": "参考音频验证完成",
                "reference_audio_path": audio_path,
                "voice_name": voice_name,
                "file_size": file_size
            }
            
        except Exception as e:
            logger.error(f"音频验证异常: {str(e)}")
            return {
                "success": False,
                "message": f"验证异常: {str(e)}",
                "error_code": "VALIDATION_ERROR"
            }

# 全局客户端实例
_tts_client = None

def get_tts_client() -> MegaTTS3Client:
    """获取TTS客户端单例"""
    global _tts_client
    if _tts_client is None:
        _tts_client = MegaTTS3Client()
    return _tts_client 