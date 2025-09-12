"""
TangoFlux核心生成器
只负责调用TangoFlux API生成音频，不涉及数据库操作
"""

import logging
import asyncio
import aiohttp
import time
import base64
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class TangoFluxCoreGenerator:
    """TangoFlux核心生成器 - 只负责音频生成"""
    
    def __init__(self, tangoflux_url: str = 'http://localhost:7930', output_dir: str = 'data/environment_sounds'):
        self.tangoflux_url = tangoflux_url
        self.tangoflux_timeout = 300  # 5分钟超时
        
        # 输出目录
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 移除硬编码的强度配置，直接使用书籍分析结果中的参数
        
        logger.info(f"[TANGOFLUX_CORE] 核心生成器初始化完成: {self.tangoflux_url}")
    
    async def check_service_health(self) -> bool:
        """检查TangoFlux服务健康状态"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.tangoflux_url}/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("[TANGOFLUX_CORE] 服务健康检查通过")
                        return True
                    else:
                        logger.warning(f"[TANGOFLUX_CORE] 服务状态异常: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"[TANGOFLUX_CORE] 服务健康检查失败: {str(e)}")
            return False
    
    def build_prompt(self, english_prompt: str) -> str:
        """构建生成提示词 - 直接使用持久化的英文提示词，不添加硬编码后缀"""
        if not english_prompt or not english_prompt.strip():
            logger.warning(f"[TANGOFLUX_CORE] 英文提示词为空，这不应该发生在新的同步流程中")
            return "Natural ambient sound, environmental audio, realistic and clear"
        
        prompt = english_prompt.strip()
        logger.info(f"[TANGOFLUX_CORE] 使用持久化提示词: {prompt}")
        return prompt
    
    async def generate_audio(self, track_data: Dict[str, Any]) -> Optional[str]:
        """
        生成单个音频文件 - 使用轨道数据中的所有参数
        
        Args:
            track_data: 包含所有生成参数的轨道数据
            
        Returns:
            生成的音频文件路径，失败返回None
        """
        try:
            # 从轨道数据中提取参数
            english_prompt = track_data.get('english_prompt', '')
            duration = float(track_data.get('duration', 30.0))
            keyword = track_data.get('keyword', '环境音')
            
            # 构建提示词 - 直接使用书籍分析结果中的英文提示词
            prompt = self.build_prompt(english_prompt)
            
            # 生成任务ID
            task_id = f"audio_{int(time.time() * 1000)}"
            
            logger.info(f"[TANGOFLUX_CORE] 开始生成音频: {keyword} (任务ID: {task_id})")
            
            # 调用TangoFlux API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.tangoflux_url}/api/v1/generate_base64",
                    json={
                        'text': prompt,
                        'steps': int(track_data.get('steps', 150)),  # 优先使用轨道数据中的推理步数
                        'duration': int(duration),  # 使用轨道数据中的时长
                        'sample_rate': int(track_data.get('sample_rate', 44100))  # 优先使用轨道数据中的采样率
                    },
                    timeout=aiohttp.ClientTimeout(total=self.tangoflux_timeout)
                ) as response:
                    
                    if response.status == 200:
                        response_data = await response.json()
                        
                        # 检查响应格式
                        if response_data.get('success') and 'audio_base64' in response_data:
                            # 解码base64音频数据
                            audio_data = base64.b64decode(response_data['audio_base64'])
                            
                            if not audio_data or len(audio_data) == 0:
                                logger.error(f"[TANGOFLUX_CORE] 音频数据为空: {task_id}")
                                return None
                            
                            # 保存文件
                            safe_keyword = "".join(c for c in keyword if c.isalnum() or c in (' ', '-', '_')).strip()
                            if not safe_keyword:
                                safe_keyword = "environment_sound"
                            
                            filename = f"{safe_keyword}_{int(time.time())}.wav"
                            output_path = self.output_dir / filename
                            
                            with open(output_path, 'wb') as f:
                                f.write(audio_data)
                            
                            # 验证文件
                            if not output_path.exists():
                                logger.error(f"[TANGOFLUX_CORE] 文件保存失败: {output_path}")
                                return None
                            
                            logger.info(f"[TANGOFLUX_CORE] 音频生成成功: {output_path} ({len(audio_data)} 字节)")
                            return str(output_path)
                        else:
                            logger.error(f"[TANGOFLUX_CORE] 响应格式错误: {response_data}")
                            return None
                    else:
                        error_text = await response.text()
                        logger.error(f"[TANGOFLUX_CORE] API错误: {response.status} - {error_text}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error(f"[TANGOFLUX_CORE] 生成超时: {keyword}")
            return None
        except Exception as e:
            logger.error(f"[TANGOFLUX_CORE] 生成失败: {keyword} - {str(e)}")
            return None
    
    async def batch_generate_audio(self, track_data_list: list, max_concurrent: int = 3) -> list:
        """
        批量生成音频 - 使用轨道数据
        
        Args:
            track_data_list: 轨道数据列表，每个包含完整的生成参数
            max_concurrent: 最大并发数
            
        Returns:
            生成结果列表，每个元素为 {'success': bool, 'file_path': str, 'error': str}
        """
        logger.info(f"[TANGOFLUX_CORE] 开始批量生成 {len(track_data_list)} 个音频")
        
        # 检查服务健康状态
        if not await self.check_service_health():
            logger.error("[TANGOFLUX_CORE] 服务不可用，批量生成取消")
            return [{'success': False, 'error': '服务不可用'} for _ in track_data_list]
        
        # 创建任务队列
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_with_semaphore(track_data):
            async with semaphore:
                file_path = await self.generate_audio(track_data)
                
                if file_path:
                    return {'success': True, 'file_path': file_path, 'error': None}
                else:
                    return {'success': False, 'file_path': None, 'error': '生成失败'}
        
        # 并发执行生成任务
        generation_tasks = [generate_with_semaphore(track_data) for track_data in track_data_list]
        results = await asyncio.gather(*generation_tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({'success': False, 'file_path': None, 'error': str(result)})
            else:
                processed_results.append(result)
        
        # 统计结果
        successful = len([r for r in processed_results if r['success']])
        failed = len([r for r in processed_results if not r['success']])
        
        logger.info(f"[TANGOFLUX_CORE] 批量生成完成: {successful}个成功, {failed}个失败")
        
        return processed_results
