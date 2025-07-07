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
    
    def __init__(self, base_url: str = None):
        # MegaTTS3 运行在7929端口
        if base_url is None:
            base_url = os.getenv("MEGATTS3_URL", "http://localhost:7929")
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(
            total=300,    # 总超时5分钟
            connect=30,   # 连接超时30秒
            sock_read=180 # 读取超时3分钟
        )
        
    def _sanitize_text(self, text: str) -> str:
        """清理文本，处理特殊字符和TTS不兼容的内容"""
        if not text:
            return ""
        
        # 基础清理
        text = text.strip()
        text = text.replace('\r', '').replace('\n', ' ')
        
        # 🔥 统一字符替换规则表
        text = self._apply_character_replacement_rules(text)
        
        # 🔥 检测并记录未知不兼容字符
        text = self._detect_and_clean_incompatible_chars(text)
        
        # 🔥 新增：处理象声词和特殊效果文本
        clean_text = text.strip()
        
        # 🎯 优先处理象声词 - 无论文本长度
        sound_effects = ['叮', '咚', '嘭', '砰', '啪', '咔', '嘎', '咯', '滴答', '嗒嗒', '呼呼', '哗啦']
        for sound in sound_effects:
            if sound in clean_text:
                # 为象声词添加语境
                if '叮' in clean_text:
                    clean_text = clean_text.replace('叮', '手机提示音响起')
                elif any(s in clean_text for s in ['咚', '嘭', '砰', '啪']):
                    for s in ['咚', '嘭', '砰', '啪']:
                        clean_text = clean_text.replace(s, '发出声响')
                elif any(s in clean_text for s in ['咔', '嘎', '咯']):
                    for s in ['咔', '嘎', '咯']:
                        clean_text = clean_text.replace(s, '机械声音')
                elif any(s in clean_text for s in ['滴答', '嗒嗒']):
                    for s in ['滴答', '嗒嗒']:
                        clean_text = clean_text.replace(s, '时钟滴答声')
                elif any(s in clean_text for s in ['呼呼', '哗啦']):
                    for s in ['呼呼', '哗啦']:
                        clean_text = clean_text.replace(s, '风声水声')
                break
        
        # 清理多余空格和标点
        clean_text = ' '.join(clean_text.split())
        
        # 🎯 如果替换后只剩下象声词描述+无意义符号，清理符号
        if any(desc in clean_text for desc in ['手机提示音响起', '发出声响', '机械声音', '时钟滴答声', '风声水声']):
            # 移除末尾的无意义标点
            clean_text = clean_text.rstrip('- .,;!?')
        
        # 最终检查：如果文本仍然过短或为空，返回默认文本
        if len(clean_text.strip()) < 2:
            clean_text = "停顿"
        
        return clean_text
    
    def _apply_character_replacement_rules(self, text: str) -> str:
        """应用统一的字符替换规则"""
        # 🎯 统一字符替换规则表 - 易于维护和扩展
        replacement_rules = {
            # 破折号标准化 (Unicode范围: 8208-8213)
            '——': '-',    # 双破折号
            '—': '-',     # em dash (U+2014)
            '–': '-',     # en dash (U+2013)
            '−': '-',     # minus sign (U+2212)
            '‒': '-',     # figure dash (U+2012)
            
            # 引号标准化
            '"': '"',     # 中文左引号 (U+201C)
            '"': '"',     # 中文右引号 (U+201D)
            ''': "'",     # 中文左单引号 (U+2018)
            ''': "'",     # 中文右单引号 (U+2019)
            '‹': '"',     # 左尖括号引号 (U+2039)
            '›': '"',     # 右尖括号引号 (U+203A)
            '«': '"',     # 左双尖括号 (U+00AB)
            '»': '"',     # 右双尖括号 (U+00BB)
            
            # 省略号标准化
            '…': '...',   # horizontal ellipsis (U+2026)
            '⋯': '...',   # midline horizontal ellipsis (U+22EF)
            
            # 特殊空格标准化
            '\u00A0': ' ', # 不间断空格 (U+00A0)
            '\u2003': ' ', # em space (U+2003)
            '\u2002': ' ', # en space (U+2002)
            '\u2009': ' ', # thin space (U+2009)
            '\u200B': '',  # 零宽空格 (U+200B)
            '\u200C': '',  # 零宽非连字符 (U+200C)
            '\u200D': '',  # 零宽连字符 (U+200D)
            
            # 其他特殊标点
            '•': '*',     # bullet (U+2022)
            '◦': '*',     # white bullet (U+25E6)
            '‡': '*',     # double dagger (U+2021)
            '†': '*',     # dagger (U+2020)
            '§': '',      # section sign (U+00A7)
            '¶': '',      # pilcrow sign (U+00B6)
            
            # 数学符号简化
            '×': 'x',     # multiplication sign (U+00D7)
            '÷': '/',     # division sign (U+00F7)
            '±': '+/-',   # plus-minus sign (U+00B1)
            '≈': '约',    # almost equal to (U+2248)
            '≠': '不等于', # not equal to (U+2260)
            
            # 货币符号标准化
            '£': '元',    # pound sign (U+00A3)
            '€': '元',    # euro sign (U+20AC)
            '$': '元',    # dollar sign (U+0024)
            '¥': '元',    # yen sign (U+00A5)
            '₹': '元',    # indian rupee sign (U+20B9)
        }
        
        # 应用所有替换规则
        for old_char, new_char in replacement_rules.items():
            text = text.replace(old_char, new_char)
        
        return text
    
    def _detect_and_clean_incompatible_chars(self, text: str) -> str:
        """检测并清理未知的不兼容字符"""
        import re
        
        # 🔍 定义TTS兼容的字符范围
        # 基本ASCII + 中日韩统一汉字 + 常用标点
        compatible_ranges = [
            (0x0020, 0x007E),     # 基本ASCII可见字符
            (0x4E00, 0x9FFF),     # 中日韩统一汉字
            (0x3400, 0x4DBF),     # 中日韩统一汉字扩展A
            (0x20000, 0x2A6DF),   # 中日韩统一汉字扩展B
            (0x3000, 0x303F),     # 中日韩符号和标点
            (0xFF00, 0xFFEF),     # 全角ASCII、全角标点
        ]
        
        def is_compatible_char(char):
            """检查字符是否在兼容范围内"""
            code = ord(char)
            return any(start <= code <= end for start, end in compatible_ranges)
        
        # 检测不兼容字符
        incompatible_chars = []
        cleaned_text = ""
        
        for char in text:
            if is_compatible_char(char):
                cleaned_text += char
            else:
                # 发现不兼容字符
                unicode_code = ord(char)
                char_name = f"U+{unicode_code:04X}"
                
                if (char, unicode_code) not in incompatible_chars:
                    incompatible_chars.append((char, unicode_code))
                    # 记录到日志，用于后续扩展规则
                    logger.warning(f"⚠️ TTS不兼容字符: '{char}' ({char_name}) - 建议添加到替换规则")
                
                # 尝试智能替换或移除
                replacement = self._get_fallback_replacement(char, unicode_code)
                cleaned_text += replacement
        
        # 如果发现新的不兼容字符，记录统计信息
        if incompatible_chars:
            logger.info(f"📊 本次发现 {len(incompatible_chars)} 种不兼容字符")
            for char, code in incompatible_chars[:5]:  # 只显示前5个
                logger.info(f"  - '{char}' (U+{code:04X})")
            if len(incompatible_chars) > 5:
                logger.info(f"  - ... 还有 {len(incompatible_chars) - 5} 个")
        
        return cleaned_text
    
    def _get_fallback_replacement(self, char: str, unicode_code: int) -> str:
        """为未知字符提供回退替换"""
        # 根据Unicode范围进行智能替换
        if 0x2000 <= unicode_code <= 0x206F:  # 常规标点
            return ' '
        elif 0x2070 <= unicode_code <= 0x209F:  # 上标和下标
            return ''
        elif 0x20A0 <= unicode_code <= 0x20CF:  # 货币符号
            return '元'
        elif 0x2100 <= unicode_code <= 0x214F:  # 字母式符号
            return ''
        elif 0x2190 <= unicode_code <= 0x21FF:  # 箭头
            return '→'
        elif 0x2200 <= unicode_code <= 0x22FF:  # 数学运算符
            return ''
        elif 0x2300 <= unicode_code <= 0x23FF:  # 杂项技术符号
            return ''
        elif 0x2500 <= unicode_code <= 0x257F:  # 制表符
            return '|'
        elif 0x25A0 <= unicode_code <= 0x25FF:  # 几何形状
            return '□'
        else:
            # 默认移除未知字符
            return ''
        
    async def health_check(self) -> Dict[str, Any]:
        """检查MegaTTS3服务健康状态"""
        try:
            # 检查7929端口的健康状态
            health_url = self.base_url
            # 强制禁用SSL，避免端口变化
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(
                timeout=self.timeout,
                connector=connector,
                connector_owner=True
            ) as session:
                async with session.get(f"{health_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"status": "healthy", "data": data}
                    else:
                        return {"status": "unhealthy", "error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def synthesize_speech(self, request: TTSRequest) -> TTSResponse:
        """语音合成 - 唯一的核心功能，带重试机制"""
        max_retries = 2  # 最多重试2次
        
        for attempt in range(max_retries + 1):
            start_time = time.time()
            
            try:
                if attempt > 0:
                    logger.info(f"[RETRY] TTS合成重试第 {attempt} 次: {request.text[:30]}...")
                    # 重试前等待一下
                    await asyncio.sleep(2 * attempt)
                
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
                
                # 构建REST API表单数据
                form_data = aiohttp.FormData()
                form_data.add_field('text', clean_text)
                form_data.add_field('time_step', str(request.time_step))
                form_data.add_field('p_w', str(request.p_weight))
                form_data.add_field('t_w', str(request.t_weight))
                form_data.add_field('audio_file', audio_content, filename=audio_filename, content_type='audio/wav')
                if latent_content:
                    form_data.add_field('latent_file', latent_content, filename=latent_filename, content_type='application/octet-stream')
                
                # 发送请求到REST API
                # 强制禁用SSL和自动重定向，避免7929->7930的端口变化
                connector = aiohttp.TCPConnector(ssl=False)
                async with aiohttp.ClientSession(
                    timeout=self.timeout,
                    connector=connector,
                    connector_owner=True
                ) as session:
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
            
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                processing_time = time.time() - start_time
                logger.warning(f"[RETRY] TTS合成网络错误 (尝试 {attempt + 1}/{max_retries + 1}): {str(e)}")
                
                # 如果还有重试机会，继续重试
                if attempt < max_retries:
                    continue
                    
                # 最后一次重试也失败了
                logger.error(f"TTS合成网络错误，重试 {max_retries} 次后仍失败: {str(e)}")
                return TTSResponse(
                    success=False,
                    message=f"网络错误，重试 {max_retries} 次后仍失败: {str(e)}",
                    processing_time=processing_time,
                    error_code="NETWORK_ERROR"
                )
                
            except Exception as e:
                processing_time = time.time() - start_time
                logger.warning(f"[RETRY] TTS合成异常 (尝试 {attempt + 1}/{max_retries + 1}): {str(e)}")
                
                # 如果还有重试机会，继续重试
                if attempt < max_retries:
                    continue
                    
                # 最后一次重试也失败了
                logger.error(f"TTS合成异常，重试 {max_retries} 次后仍失败: {str(e)}")
                return TTSResponse(
                    success=False,
                    message=f"合成异常，重试 {max_retries} 次后仍失败: {str(e)}",
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
        import os
        megatts3_url = os.getenv("MEGATTS3_URL", "http://localhost:7929")
        logger.info(f"创建TTS客户端，URL: {megatts3_url}，当前实例ID: {id(_tts_client)}")
        _tts_client = MegaTTS3Client(base_url=megatts3_url)
    else:
        logger.debug(f"复用TTS客户端，实例ID: {id(_tts_client)}")
    return _tts_client 

def reset_tts_client():
    """重置TTS客户端单例"""
    global _tts_client
    _tts_client = None 