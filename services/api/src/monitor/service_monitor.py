"""
服务监控模块
"""

import time
import asyncio
import logging
from typing import Dict, Any, Optional

from ..tts.engine import TTSEngineRouter

logger = logging.getLogger(__name__)

class ServiceMonitor:
    """服务监控器"""
    
    def __init__(self, engine_router: TTSEngineRouter, check_interval: int = 30):
        """
        初始化服务监控器
        
        Args:
            engine_router: TTS引擎路由器
            check_interval: 健康检查间隔（秒）
        """
        self.engine_router = engine_router
        self.check_interval = check_interval
        self._running = False
        self._task = None
        
    async def start_monitoring(self):
        """启动服务监控"""
        if self._running:
            logger.warning("服务监控已经在运行")
            return
            
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info(f"服务监控已启动，检查间隔: {self.check_interval}秒")
        
    async def stop_monitoring(self):
        """停止服务监控"""
        if not self._running:
            return
            
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("服务监控已停止")
        
    async def _monitor_loop(self):
        """监控循环"""
        try:
            while self._running:
                await self._check_services()
                await asyncio.sleep(self.check_interval)
        except asyncio.CancelledError:
            logger.info("服务监控循环已取消")
            raise
        except Exception as e:
            logger.error(f"服务监控循环异常: {str(e)}")
            self._running = False
            
    async def _check_services(self):
        """检查所有服务"""
        try:
            logger.debug("执行服务健康检查")
            results = await self.engine_router.check_all_engines_health()
            
            # 记录健康状态
            for engine_type, is_healthy in results.items():
                status = "健康" if is_healthy else "不健康"
                logger.info(f"引擎 {engine_type} 健康状态: {status}")
                
            return results
        except Exception as e:
            logger.error(f"服务健康检查异常: {str(e)}")
            return {}
            
    def get_health_status(self) -> Dict[str, Dict[str, Any]]:
        """获取缓存的健康状态"""
        return self.engine_router.get_health_status()