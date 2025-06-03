"""
TTS合成服务
提供文本转语音的核心业务逻辑
"""

import uuid
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging

from ..models.tts import (
    SynthesisRequest, BatchSynthesisRequest, 
    SynthesisResult, BatchSynthesisResult,
    TTSTask, TTSEngine, AudioFormat
)
from ..adapters.factory import AdapterFactory
from ..core.config import settings
from ..core.queue import task_queue, TaskPriority
from ..core.websocket import websocket_manager

logger = logging.getLogger(__name__)


class TTSService:
    """TTS合成服务"""
    
    def __init__(self, adapter_factory: AdapterFactory = None):
        self.adapter_factory = adapter_factory or AdapterFactory()
        self.output_path = Path(settings.tts.output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        self._tasks: Dict[str, TTSTask] = {}
    
    async def synthesize_text(self, request: SynthesisRequest) -> SynthesisResult:
        """同步文本合成"""
        try:
            # 选择引擎
            engine_name = request.engine.value if request.engine else settings.tts.default_engine
            adapter = await self.adapter_factory.get_adapter(engine_name)
            
            if not adapter:
                raise ValueError(f"不支持的TTS引擎: {engine_name}")
            
            # 生成输出文件名
            task_id = str(uuid.uuid4())
            output_filename = f"output_{task_id}.{request.format.value}"
            output_filepath = self.output_path / output_filename
            
            # 准备合成参数
            synthesis_params = {
                "text": request.text,
                "voice_id": request.voice_id,
                "speed": request.speed,
                "pitch": request.pitch,
                "volume": request.volume,
                "sample_rate": request.sample_rate,
                "output_path": str(output_filepath)
            }
            
            # 执行合成
            result = await adapter.synthesize_safe(**synthesis_params)
            
            # 检查合成是否成功
            if not result.success:
                raise ValueError(result.error_message or "合成失败")
            
            # 构建结果 - 使用完整的URL而不是相对路径
            api_host = settings.api.host if settings.api.host != "0.0.0.0" else "127.0.0.1"
            audio_url = f"http://{api_host}:{settings.api.port}/api/audio/{output_filename}"
            file_size = output_filepath.stat().st_size if output_filepath.exists() else 0
            
            return SynthesisResult(
                task_id=task_id,
                audio_url=audio_url,
                duration=result.duration,
                file_size=file_size,
                sample_rate=result.sample_rate or request.sample_rate,
                format=request.format
            )
            
        except Exception as e:
            logger.error(f"文本合成失败: {e}")
            raise
    
    async def synthesize_text_async(self, request: SynthesisRequest) -> str:
        """异步文本合成"""
        task_id = str(uuid.uuid4())
        
        # 创建任务记录
        task = TTSTask(
            id=task_id,
            type="synthesis",
            status="pending",
            request_data=request.dict(),
            created_at=datetime.now()
        )
        self._tasks[task_id] = task
        
        # 添加到任务队列
        await task_queue.add_task(
            self._execute_synthesis_task,
            task_id,
            request,
            name=f"synthesis_{task_id}",
            priority=TaskPriority.NORMAL
        )
        
        return task_id
    
    async def batch_synthesize_async(self, request: BatchSynthesisRequest) -> str:
        """异步批量文本合成"""
        task_id = str(uuid.uuid4())
        
        # 创建任务记录
        task = TTSTask(
            id=task_id,
            type="batch_synthesis",
            status="pending",
            request_data=request.dict(),
            created_at=datetime.now()
        )
        self._tasks[task_id] = task
        
        # 添加到任务队列
        await task_queue.add_task(
            self._execute_batch_synthesis_task,
            task_id,
            request,
            name=f"batch_synthesis_{task_id}",
            priority=TaskPriority.NORMAL
        )
        
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[TTSTask]:
        """获取任务状态"""
        return self._tasks.get(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self._tasks.get(task_id)
        if not task:
            return False
        
        if task.status in ["pending", "running"]:
            # 尝试从队列中取消
            await task_queue.cancel_task(task_id)
            task.status = "cancelled"
            return True
        
        return False
    
    async def get_available_engines(self) -> List[str]:
        """获取可用的TTS引擎列表"""
        return await self.adapter_factory.get_available_engines()
    
    async def _execute_synthesis_task(self, task_id: str, request: SynthesisRequest) -> None:
        """执行合成任务"""
        task = self._tasks.get(task_id)
        if not task:
            return
        
        try:
            task.status = "running"
            task.started_at = datetime.now()
            
            # 发送进度通知
            await websocket_manager.send_task_progress(task_id, 10.0, "开始合成...")
            
            # 执行合成
            result = await self.synthesize_text(request)
            
            # 更新任务状态
            task.status = "completed"
            task.completed_at = datetime.now()
            task.progress = 100.0
            task.result_data = result.dict()
            
            # 发送完成通知
            await websocket_manager.send_task_completed(task_id, result.dict())
            
        except Exception as e:
            task.status = "failed"
            task.completed_at = datetime.now()
            task.error_message = str(e)
            
            # 发送失败通知
            await websocket_manager.send_task_failed(task_id, str(e))
            
            logger.error(f"合成任务失败 {task_id}: {e}")
    
    async def _execute_batch_synthesis_task(self, task_id: str, request: BatchSynthesisRequest) -> None:
        """执行批量合成任务"""
        task = self._tasks.get(task_id)
        if not task:
            return
        
        try:
            task.status = "running"
            task.started_at = datetime.now()
            
            results = []
            total_texts = len(request.texts)
            
            for i, text in enumerate(request.texts):
                # 发送进度通知
                progress = (i / total_texts) * 90.0  # 90%用于合成，10%用于后处理
                await websocket_manager.send_task_progress(
                    task_id, progress, f"正在合成第{i+1}/{total_texts}段文本..."
                )
                
                # 创建单个合成请求
                single_request = SynthesisRequest(
                    text=text,
                    voice_id=request.voice_id,
                    engine=request.engine,
                    speed=request.speed,
                    pitch=request.pitch,
                    volume=request.volume,
                    format=request.format,
                    sample_rate=request.sample_rate
                )
                
                # 执行合成
                result = await self.synthesize_text(single_request)
                results.append(result)
            
            # 处理合并请求
            concat_result = None
            if request.concat_output and results:
                await websocket_manager.send_task_progress(task_id, 95.0, "正在合并音频文件...")
                concat_result = await self._concat_audio_files(results, task_id, request.format)
            
            # 计算总时长
            total_duration = sum(r.duration for r in results if r.duration)
            
            # 构建批量结果
            batch_result = BatchSynthesisResult(
                task_id=task_id,
                results=results,
                concat_result=concat_result,
                total_duration=total_duration
            )
            
            # 更新任务状态
            task.status = "completed"
            task.completed_at = datetime.now()
            task.progress = 100.0
            task.result_data = batch_result.dict()
            
            # 发送完成通知
            await websocket_manager.send_task_completed(task_id, batch_result.dict())
            
        except Exception as e:
            task.status = "failed"
            task.completed_at = datetime.now()
            task.error_message = str(e)
            
            # 发送失败通知
            await websocket_manager.send_task_failed(task_id, str(e))
            
            logger.error(f"批量合成任务失败 {task_id}: {e}")
    
    async def _concat_audio_files(self, results: List[SynthesisResult], task_id: str, format: AudioFormat) -> SynthesisResult:
        """合并音频文件"""
        try:
            # 这里应该实现音频文件合并逻辑
            # 暂时返回第一个文件作为示例
            if not results:
                raise ValueError("没有可合并的音频文件")
            
            concat_filename = f"concat_{task_id}.{format.value}"
            concat_filepath = self.output_path / concat_filename
            
            # TODO: 实现实际的音频合并逻辑
            # 可以使用ffmpeg、pydub等工具
            
            total_duration = sum(r.duration for r in results if r.duration)
            file_size = sum(r.file_size for r in results if r.file_size)
            
            # 构建完整的音频URL
            api_host = settings.api.host if settings.api.host != "0.0.0.0" else "127.0.0.1"
            audio_url = f"http://{api_host}:{settings.api.port}/api/audio/{concat_filename}"
            
            return SynthesisResult(
                task_id=f"concat_{task_id}",
                audio_url=audio_url,
                duration=total_duration,
                file_size=file_size,
                sample_rate=results[0].sample_rate,
                format=format
            )
            
        except Exception as e:
            logger.error(f"音频文件合并失败: {e}")
            raise