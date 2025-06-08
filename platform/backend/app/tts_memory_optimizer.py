"""
TTS服务显存优化器
用于解决MegaTTS3的CUDA设备断言错误和显存不足问题
"""

import torch
import gc
import logging
import time
import psutil
from contextlib import contextmanager
from typing import Optional, Dict, Any
import requests
import asyncio

logger = logging.getLogger(__name__)

class TTSMemoryOptimizer:
    """TTS服务显存优化器"""
    
    def __init__(self, tts_service_url: str = "http://localhost:9880"):
        self.tts_service_url = tts_service_url
        self.last_cleanup_time = 0
        self.cleanup_interval = 30  # 30秒清理一次
        self.max_retries = 3
        self.retry_delay = 2  # 重试间隔秒数
    
    def check_cuda_available(self) -> bool:
        """检查CUDA是否可用"""
        return torch.cuda.is_available()
    
    def get_gpu_memory_info(self) -> Dict[str, float]:
        """获取GPU显存信息"""
        if not self.check_cuda_available():
            return {}
        
        try:
            import nvidia_ml_py3 as nvml
            nvml.nvmlInit()
            handle = nvml.nvmlDeviceGetHandleByIndex(0)
            mem_info = nvml.nvmlDeviceGetMemoryInfo(handle)
            
            return {
                'total_gb': mem_info.total / (1024**3),
                'used_gb': mem_info.used / (1024**3),
                'free_gb': mem_info.free / (1024**3),
                'utilization_percent': (mem_info.used / mem_info.total) * 100
            }
        except Exception as e:
            logger.warning(f"无法获取GPU显存信息: {e}")
            return {}
    
    def force_cuda_cleanup(self):
        """强制CUDA显存清理"""
        if not self.check_cuda_available():
            return
        
        try:
            # 基础清理
            gc.collect()
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            
            # 重置统计信息
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.reset_accumulated_memory_stats()
            
            logger.info("执行强制CUDA显存清理")
            
            # 获取清理后的状态
            memory_info = self.get_gpu_memory_info()
            if memory_info:
                logger.info(f"清理后显存使用: {memory_info['used_gb']:.2f}GB / {memory_info['total_gb']:.2f}GB "
                           f"({memory_info['utilization_percent']:.1f}%)")
                           
        except Exception as e:
            logger.error(f"CUDA显存清理失败: {e}")
    
    def restart_tts_service(self) -> bool:
        """重启TTS服务"""
        try:
            # 发送重启请求到TTS服务
            response = requests.post(f"{self.tts_service_url}/restart", timeout=10)
            if response.status_code == 200:
                logger.info("TTS服务重启成功")
                # 等待服务重新启动
                time.sleep(5)
                return True
            else:
                logger.warning(f"TTS服务重启响应异常: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"重启TTS服务失败: {e}")
            return False
    
    def wait_for_service_ready(self, timeout: int = 30) -> bool:
        """等待TTS服务就绪"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.tts_service_url}/health", timeout=5)
                if response.status_code == 200:
                    logger.info("TTS服务已就绪")
                    return True
            except:
                pass
            time.sleep(1)
        
        logger.warning(f"等待{timeout}秒后TTS服务仍未就绪")
        return False
    
    def should_cleanup(self) -> bool:
        """判断是否需要清理"""
        current_time = time.time()
        if current_time - self.last_cleanup_time > self.cleanup_interval:
            return True
        
        # 检查显存使用率
        memory_info = self.get_gpu_memory_info()
        if memory_info and memory_info['utilization_percent'] > 85:
            return True
        
        return False
    
    @contextmanager
    def optimized_synthesis(self, segment_text: str):
        """优化的音频合成上下文管理器"""
        # 预检查
        if self.should_cleanup():
            self.force_cuda_cleanup()
            self.last_cleanup_time = time.time()
        
        memory_before = self.get_gpu_memory_info()
        logger.info(f"开始合成: '{segment_text[:30]}...' "
                   f"显存: {memory_before.get('used_gb', 0):.2f}GB")
        
        try:
            yield self
        finally:
            # 合成后清理
            self.force_cuda_cleanup()
            
            memory_after = self.get_gpu_memory_info()
            logger.info(f"合成完成，显存: {memory_after.get('used_gb', 0):.2f}GB")
    
    async def synthesize_with_retry(self, tts_client, segment_data: Dict) -> Optional[bytes]:
        """带重试机制的音频合成"""
        for attempt in range(self.max_retries):
            try:
                with self.optimized_synthesis(segment_data.get('text_content', '')):
                    # 调用实际的TTS合成
                    audio_data = await self._call_tts_service(tts_client, segment_data)
                    if audio_data:
                        return audio_data
                        
            except Exception as e:
                logger.warning(f"TTS合成尝试 {attempt + 1} 失败: {e}")
                
                if "CUDA" in str(e) or "device-side assert" in str(e):
                    logger.warning("检测到CUDA错误，执行恢复流程")
                    
                    # CUDA错误恢复流程
                    self.force_cuda_cleanup()
                    
                    if attempt == self.max_retries - 1:
                        # 最后一次尝试：重启TTS服务
                        logger.info("最后尝试：重启TTS服务")
                        if self.restart_tts_service():
                            self.wait_for_service_ready()
                        else:
                            logger.error("TTS服务重启失败")
                            break
                    else:
                        # 等待后重试
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    # 非CUDA错误，直接重试
                    await asyncio.sleep(self.retry_delay)
        
        logger.error(f"TTS合成彻底失败，已重试{self.max_retries}次")
        return None
    
    async def _call_tts_service(self, tts_client, segment_data: Dict) -> Optional[bytes]:
        """调用实际的TTS服务"""
        try:
            # 这里需要根据实际的tts_client接口调整
            voice_profile_id = segment_data.get('voice_profile_id')
            text_content = segment_data.get('text_content', '')
            
            if not voice_profile_id or not text_content.strip():
                logger.warning("缺少必要的合成参数")
                return None
            
            # 调用TTS客户端
            response = await tts_client.synthesize(
                voice_profile_id=voice_profile_id,
                text=text_content
            )
            
            if response and response.get('success'):
                return response.get('audio_data')
            else:
                logger.warning(f"TTS服务返回错误: {response}")
                return None
                
        except Exception as e:
            logger.error(f"调用TTS服务异常: {e}")
            raise
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        memory_info = self.get_gpu_memory_info()
        system_memory = psutil.virtual_memory()
        
        return {
            'gpu_memory': memory_info,
            'system_memory': {
                'total_gb': system_memory.total / (1024**3),
                'available_gb': system_memory.available / (1024**3),
                'used_percent': system_memory.percent
            },
            'last_cleanup_time': self.last_cleanup_time,
            'cleanup_interval': self.cleanup_interval,
            'cuda_available': self.check_cuda_available()
        }


# 全局优化器实例
tts_memory_optimizer = TTSMemoryOptimizer()

# 便捷函数
def optimize_tts_memory():
    """优化TTS显存使用的便捷函数"""
    tts_memory_optimizer.force_cuda_cleanup()

def get_tts_memory_stats():
    """获取TTS内存统计的便捷函数"""
    return tts_memory_optimizer.get_optimization_stats()

def synthesis_context(segment_text: str = ""):
    """TTS合成优化上下文的便捷函数"""
    return tts_memory_optimizer.optimized_synthesis(segment_text) 