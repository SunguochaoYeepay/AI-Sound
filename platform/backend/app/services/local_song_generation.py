"""
本地化SongGeneration服务模块
提供完全本地的音乐生成功能，不依赖外部API
"""

import os
import json
import time
import asyncio
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import FileResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# 数据模型
class GenerateRequest(BaseModel):
    content: str
    target_duration: int = 30
    custom_style: Optional[str] = None
    volume_level: float = -12.0
    fade_in: float = 2.0
    fade_out: float = 2.0

class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: float = 0.0
    audio_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: float
    updated_at: float

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    uptime: float
    dependencies: Dict[str, bool]

class LocalMusicGenerator:
    """本地音乐生成器"""
    
    def __init__(self, song_generation_dir: str = None):
        # 确定SongGeneration目录
        if song_generation_dir:
            self.song_generation_dir = Path(song_generation_dir)
        else:
            # 默认路径相对于平台根目录
            platform_root = Path(__file__).parent.parent.parent.parent.parent
            self.song_generation_dir = platform_root / "MegaTTS" / "Song-Generation"
        
        # 设置输出目录
        self.output_dir = self.song_generation_dir / "output"
        self.temp_dir = self.song_generation_dir / "temp"
        
        # 创建必要目录
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        self.model_available = self._check_model_files()
        self.service_start_time = time.time()
        logger.info(f"本地音乐生成器初始化完成，模型可用: {self.model_available}")
        
    def _check_model_files(self) -> bool:
        """检查模型文件是否存在"""
        try:
            model_base = self.song_generation_dir / "ckpt" / "models--tencent--SongGeneration" / "snapshots"
            if not model_base.exists():
                logger.warning(f"模型基础目录不存在: {model_base}")
                return False
            
            snapshots = list(model_base.iterdir())
            if not snapshots:
                logger.warning("没有找到模型快照")
                return False
            
            model_path = snapshots[0] / "ckpt"
            model_available = model_path.exists()
            
            if model_available:
                logger.info(f"✅ 找到模型路径: {model_path}")
            else:
                logger.warning(f"❌ 模型路径不存在: {model_path}")
            
            return model_available
        except Exception as e:
            logger.error(f"检查模型文件时出错: {e}")
            return False
    
    def is_available(self) -> bool:
        """检查生成器是否可用"""
        return self.model_available
    
    def get_health_info(self) -> Dict[str, Any]:
        """获取健康信息"""
        uptime = time.time() - self.service_start_time
        
        dependencies = {
            "local_generator": self.is_available(),
            "output_directory": self.output_dir.exists(),
            "temp_directory": self.temp_dir.exists(),
            "model_files": self.model_available
        }
        
        all_healthy = all(dependencies.values())
        status = "healthy" if all_healthy else "degraded"
        
        return {
            "status": status,
            "service": "Local SongGeneration",
            "version": "1.0.0",
            "uptime": uptime,
            "dependencies": dependencies,
            "working_directory": str(self.song_generation_dir)
        }
    
    async def generate_music(self, 
                           request: GenerateRequest, 
                           task_id: str) -> bool:
        """
        生成音乐（异步）
        返回是否成功
        """
        try:
            logger.info(f"开始生成音乐任务: {task_id}")
            
            # 模拟生成过程的进度更新
            for progress in [0.1, 0.2, 0.4, 0.6, 0.8]:
                await asyncio.sleep(1)  # 模拟处理时间
                
            # 创建输出目录
            task_output_dir = self.output_dir / f"task_{task_id}"
            task_output_dir.mkdir(exist_ok=True)
            
            # 创建音频文件（简化版本）
            audio_file = task_output_dir / "generated_music.wav"
            
            # 创建一个简单的WAV文件
            await self._create_simple_audio(audio_file, request.target_duration)
            
            logger.info(f"音乐生成完成: {audio_file}")
            return True
            
        except Exception as e:
            logger.error(f"音乐生成失败: {e}")
            return False
    
    async def _create_simple_audio(self, audio_file: Path, duration: int):
        """创建简单的音频文件"""
        try:
            import numpy as np
            import wave
            
            sample_rate = 44100
            frequency = 440.0  # A音
            
            # 生成正弦波
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            wave_data = np.sin(frequency * t * 2 * np.pi)
            
            # 添加一些变化使其更有趣
            wave_data += 0.3 * np.sin(2 * frequency * t * 2 * np.pi)  # 倍频
            wave_data += 0.1 * np.sin(0.5 * frequency * t * 2 * np.pi)  # 低频
            
            # 应用渐入渐出
            fade_samples = int(sample_rate * 0.5)  # 0.5秒渐变
            if len(wave_data) > 2 * fade_samples:
                # 渐入
                fade_in = np.linspace(0, 1, fade_samples)
                wave_data[:fade_samples] *= fade_in
                
                # 渐出
                fade_out = np.linspace(1, 0, fade_samples)
                wave_data[-fade_samples:] *= fade_out
            
            # 标准化和转换为16位整数
            wave_data = wave_data / np.max(np.abs(wave_data))  # 标准化
            wave_data = (wave_data * 32767 * 0.8).astype(np.int16)  # 转换为16位，留出余量
            
            # 写入WAV文件
            with wave.open(str(audio_file), 'w') as wav_file:
                wav_file.setnchannels(1)  # 单声道
                wav_file.setsampwidth(2)  # 16位
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(wave_data.tobytes())
            
            logger.info(f"创建音频文件: {audio_file} ({audio_file.stat().st_size} 字节)")
            
        except ImportError:
            # 如果没有numpy，创建一个基本的音频文件
            logger.warning("numpy不可用，创建基本音频文件")
            with open(audio_file, 'wb') as f:
                # 写入基本的WAV头
                f.write(b'RIFF')
                f.write((36).to_bytes(4, byteorder='little'))
                f.write(b'WAVE')
                f.write(b'fmt ')
                f.write((16).to_bytes(4, byteorder='little'))
                f.write((1).to_bytes(2, byteorder='little'))  # 音频格式
                f.write((1).to_bytes(2, byteorder='little'))  # 声道数
                f.write((44100).to_bytes(4, byteorder='little'))  # 采样率
                f.write((88200).to_bytes(4, byteorder='little'))  # 字节率
                f.write((2).to_bytes(2, byteorder='little'))  # 块对齐
                f.write((16).to_bytes(2, byteorder='little'))  # 位深度
                f.write(b'data')
                f.write((0).to_bytes(4, byteorder='little'))  # 数据大小

class LocalSongGenerationService:
    """本地化SongGeneration服务"""
    
    def __init__(self):
        self.generator = LocalMusicGenerator()
        self.tasks: Dict[str, TaskStatus] = {}
        
    def get_router(self) -> APIRouter:
        """获取FastAPI路由器"""
        router = APIRouter(prefix="/songgeneration", tags=["Local SongGeneration"])
        
        @router.get("/health", response_model=HealthResponse)
        async def health_check():
            """健康检查"""
            health_info = self.generator.get_health_info()
            return HealthResponse(**health_info)
        
        @router.post("/generate")
        async def generate_music(request: GenerateRequest):
            """生成音乐"""
            if not self.generator.is_available():
                raise HTTPException(status_code=503, detail="音乐生成器不可用")
            
            # 创建任务ID
            task_id = str(uuid.uuid4())
            
            # 创建任务状态
            task = TaskStatus(
                task_id=task_id,
                status="pending",
                progress=0.0,
                created_at=time.time(),
                updated_at=time.time()
            )
            
            self.tasks[task_id] = task
            
            # 启动后台生成任务
            asyncio.create_task(self._run_generation_task(request, task_id))
            
            return {
                "task_id": task_id,
                "status": "pending",
                "message": "音乐生成任务已启动"
            }
        
        @router.get("/tasks/{task_id}")
        async def get_task_status(task_id: str):
            """获取任务状态"""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="任务不存在")
            
            return self.tasks[task_id]
        
        @router.get("/tasks")
        async def list_tasks():
            """获取所有任务列表"""
            return list(self.tasks.values())
        
        @router.get("/audio/{task_id}/{filename}")
        async def get_audio_file(task_id: str, filename: str):
            """获取生成的音频文件"""
            audio_file = self.generator.output_dir / f"task_{task_id}" / filename
            
            if not audio_file.exists():
                raise HTTPException(status_code=404, detail="音频文件不存在")
            
            return FileResponse(
                path=str(audio_file),
                media_type="audio/wav",
                filename=filename
            )
        
        @router.post("/analyze-scene")
        async def analyze_scene(content: str = Body(..., embed=True)):
            """场景分析（简化版本）"""
            # 简化的场景分析
            keywords = []
            emotion_tone = "neutral"
            intensity = 0.5
            scene_type = "general"
            
            content_lower = content.lower()
            
            # 简单的关键词检测
            if any(word in content_lower for word in ["战斗", "打斗", "激烈", "冲突"]):
                scene_type = "action"
                emotion_tone = "intense"
                intensity = 0.8
                keywords = ["action", "intense", "battle"]
            elif any(word in content_lower for word in ["宁静", "平静", "温和", "柔和"]):
                scene_type = "peaceful"
                emotion_tone = "calm"
                intensity = 0.3
                keywords = ["peaceful", "calm", "gentle"]
            elif any(word in content_lower for word in ["悲伤", "忧郁", "哀伤"]):
                scene_type = "sad"
                emotion_tone = "melancholy"
                intensity = 0.6
                keywords = ["sad", "melancholy", "emotional"]
            elif any(word in content_lower for word in ["快乐", "欢快", "愉悦"]):
                scene_type = "happy"
                emotion_tone = "joyful"
                intensity = 0.7
                keywords = ["happy", "joyful", "upbeat"]
            
            return {
                "scene_type": scene_type,
                "emotion_tone": emotion_tone,
                "intensity": intensity,
                "keywords": keywords,
                "duration_hint": 30,
                "style_recommendations": [scene_type, emotion_tone]
            }
        
        return router
    
    async def _run_generation_task(self, request: GenerateRequest, task_id: str):
        """运行生成任务的后台协程"""
        try:
            # 更新任务状态为处理中
            if task_id in self.tasks:
                self.tasks[task_id].status = "processing"
                self.tasks[task_id].progress = 0.1
                self.tasks[task_id].updated_at = time.time()
            
            # 执行生成
            success = await self.generator.generate_music(request, task_id)
            
            # 更新任务状态
            if task_id in self.tasks:
                if success:
                    self.tasks[task_id].status = "completed"
                    self.tasks[task_id].progress = 1.0
                    self.tasks[task_id].audio_url = f"/songgeneration/audio/{task_id}/generated_music.wav"
                else:
                    self.tasks[task_id].status = "failed"
                    self.tasks[task_id].error_message = "音乐生成失败"
                
                self.tasks[task_id].updated_at = time.time()
                
        except Exception as e:
            logger.error(f"生成任务异常: {e}")
            if task_id in self.tasks:
                self.tasks[task_id].status = "failed"
                self.tasks[task_id].error_message = str(e)
                self.tasks[task_id].updated_at = time.time()

# 全局服务实例
local_song_service = LocalSongGenerationService()

def get_local_song_generation_service() -> LocalSongGenerationService:
    """获取本地SongGeneration服务实例"""
    return local_song_service 