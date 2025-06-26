"""
SongGeneration核心服务
负责调用音乐生成模块，为章节内容生成匹配的背景音乐
"""

import asyncio
import logging
import httpx
import requests
import time
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

from ..config import settings

logger = logging.getLogger(__name__)

@dataclass
class MusicGenerationRequest:
    """音乐生成请求"""
    content: str
    target_duration: int = 30
    custom_style: Optional[str] = None
    volume_level: float = -12.0
    fade_in: float = 2.0
    fade_out: float = 2.0

@dataclass
class MusicGenerationResult:
    """音乐生成结果"""
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: float = 0.0
    audio_url: Optional[str] = None
    audio_path: Optional[str] = None
    scene_analysis: Optional[Dict] = None
    music_prompt: Optional[Dict] = None
    error_message: Optional[str] = None
    generation_time: Optional[float] = None

@dataclass
class SceneAnalysisResult:
    """场景分析结果"""
    scene_type: str
    emotion_tone: str
    intensity: float
    keywords: List[str]
    duration_hint: int
    style_recommendations: List[Dict]

class SongGenerationService:
    """SongGeneration核心服务"""
    
    def __init__(self):
        # 从环境变量获取SongGeneration服务URL，默认使用Docker服务名
        import os
        self.base_url = os.getenv("SONGGENERATION_URL", "http://songgeneration:8081")
        self.timeout = 300  # 5分钟超时
        self.session = httpx.AsyncClient(timeout=self.timeout)
        logger.info(f"SongGenerationService初始化，使用服务: {self.base_url}")
        
        # 确保音频输出目录存在
        self.output_dir = Path("data/audio/generated_music")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()
    
    async def check_service_health(self) -> bool:
        """检查SongGeneration服务健康状态"""
        try:
            response = await self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"SongGeneration服务健康检查通过: {health_data.get('status')}")
                return health_data.get("status") == "healthy"
            else:
                logger.warning(f"SongGeneration健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"SongGeneration健康检查异常: {e}")
            return False
    
    async def health_check(self) -> bool:
        """健康检查方法别名，与check_service_health等价"""
        return await self.check_service_health()
    
    async def analyze_scene(self, content: str) -> Optional[SceneAnalysisResult]:
        """
        分析文本内容的场景和情绪
        
        Args:
            content: 文本内容
            
        Returns:
            场景分析结果
        """
        try:
            response = await self.session.post(
                f"{self.base_url}/analyze-scene",
                json=content
            )
            response.raise_for_status()
            
            data = response.json()
            return SceneAnalysisResult(
                scene_type=data["scene_type"],
                emotion_tone=data["emotion_tone"],
                intensity=data["intensity"],
                keywords=data["keywords"],
                duration_hint=data["duration_hint"],
                style_recommendations=data["style_recommendations"]
            )
            
        except Exception as e:
            logger.error(f"场景分析失败: {str(e)}")
            return None
    
    async def generate_music_async(self, request: MusicGenerationRequest) -> Optional[str]:
        """
        异步生成音乐
        
        Args:
            request: 音乐生成请求
            
        Returns:
            任务ID
        """
        try:
            response = await self.session.post(
                f"{self.base_url}/generate",
                json={
                    "content": request.content,
                    "target_duration": request.target_duration,
                    "custom_style": request.custom_style,
                    "volume_level": request.volume_level,
                    "fade_in": request.fade_in,
                    "fade_out": request.fade_out
                }
            )
            response.raise_for_status()
            
            data = response.json()
            task_id = data["task_id"]
            
            logger.info(f"音乐生成任务已提交: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"提交音乐生成任务失败: {str(e)}")
            return None
    
    async def get_task_status(self, task_id: str) -> Optional[MusicGenerationResult]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            音乐生成结果
        """
        try:
            response = await self.session.get(f"{self.base_url}/tasks/{task_id}")
            response.raise_for_status()
            
            data = response.json()
            return MusicGenerationResult(
                task_id=data["task_id"],
                status=data["status"],
                progress=data.get("progress", 0.0),
                audio_url=data.get("audio_url"),
                scene_analysis=data.get("scene_analysis"),
                music_prompt=data.get("music_prompt"),
                error_message=data.get("error_message"),
                generation_time=data.get("generation_time")
            )
            
        except Exception as e:
            logger.error(f"获取任务状态失败: {str(e)}")
            return None
    
    async def wait_for_completion(self, task_id: str, max_wait_time: int = 300) -> Optional[MusicGenerationResult]:
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            max_wait_time: 最大等待时间（秒）
            
        Returns:
            音乐生成结果
        """
        start_time = time.time()
        poll_interval = 5  # 5秒轮询一次
        
        logger.info(f"开始等待音乐生成任务完成: {task_id}")
        
        while time.time() - start_time < max_wait_time:
            result = await self.get_task_status(task_id)
            
            if not result:
                logger.error(f"无法获取任务状态: {task_id}")
                return None
            
            logger.info(f"任务 {task_id} 状态: {result.status}, 进度: {result.progress:.2f}")
            
            if result.status == "completed":
                logger.info(f"音乐生成完成: {task_id}")
                return result
            elif result.status == "failed":
                logger.error(f"音乐生成失败: {task_id}, 错误: {result.error_message}")
                return result
            
            await asyncio.sleep(poll_interval)
        
        logger.warning(f"音乐生成任务超时: {task_id}")
        return None
    
    async def download_generated_music(self, audio_url: str, output_filename: str) -> Optional[str]:
        """
        下载生成的音乐文件
        
        Args:
            audio_url: 音频URL
            output_filename: 输出文件名
            
        Returns:
            本地文件路径
        """
        try:
            # 构建完整URL
            if audio_url.startswith("/"):
                full_url = f"{self.base_url}{audio_url}"
            else:
                full_url = audio_url
            
            # 确定输出路径
            output_path = self.output_dir / output_filename
            
            async with httpx.AsyncClient(timeout=60) as client:
                async with client.stream("GET", full_url) as response:
                    response.raise_for_status()
                    
                    with open(output_path, 'wb') as f:
                        async for chunk in response.aiter_bytes():
                            f.write(chunk)
            
            logger.info(f"音乐文件下载完成: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"下载音乐文件失败: {str(e)}")
            return None
    
    async def generate_music_for_chapter(self,
                                       chapter_content: str,
                                       chapter_id: Union[str, int],
                                       duration: int = 30,
                                       style: Optional[str] = None,
                                       volume_level: float = -12.0) -> Optional[Dict]:
        """
        为章节生成背景音乐
        
        Args:
            chapter_content: 章节内容
            chapter_id: 章节ID
            duration: 音乐时长（秒）
            style: 音乐风格（可选）
            volume_level: 音量等级
            
        Returns:
            生成结果字典
        """
        logger.info(f"开始为章节 {chapter_id} 生成背景音乐")
        
        try:
            # 1. 场景分析
            scene_analysis = await self.analyze_scene(chapter_content)
            if not scene_analysis:
                logger.error(f"章节 {chapter_id} 场景分析失败")
                return None
            
            logger.info(f"章节 {chapter_id} 场景分析完成: {scene_analysis.scene_type}")
            
            # 2. 创建生成请求
            request = MusicGenerationRequest(
                content=chapter_content,
                target_duration=duration,
                custom_style=style or scene_analysis.scene_type,
                volume_level=volume_level,
                fade_in=2.0,
                fade_out=2.0
            )
            
            # 3. 提交生成任务
            task_id = await self.generate_music_async(request)
            if not task_id:
                logger.error(f"章节 {chapter_id} 音乐生成任务提交失败")
                return None
            
            # 4. 等待任务完成
            result = await self.wait_for_completion(task_id)
            if not result or result.status != "completed":
                logger.error(f"章节 {chapter_id} 音乐生成失败")
                return None
            
            # 5. 下载音乐文件
            if result.audio_url:
                filename = f"chapter_{chapter_id}_music_{int(time.time())}.wav"
                local_path = await self.download_generated_music(result.audio_url, filename)
                
                if local_path:
                    result.audio_path = local_path
                    
                    return {
                        "task_id": result.task_id,
                        "audio_path": result.audio_path,
                        "audio_url": result.audio_url,
                        "scene_analysis": result.scene_analysis,
                        "music_prompt": result.music_prompt,
                        "generation_time": result.generation_time,
                        "volume_level": volume_level,
                        "duration": duration
                    }
            
            logger.error(f"章节 {chapter_id} 音乐文件下载失败")
            return None
            
        except Exception as e:
            logger.error(f"章节 {chapter_id} 音乐生成过程失败: {str(e)}")
            return None
    
    async def generate_music_direct(self,
                                   description: str,
                                   style: str = "peaceful",
                                   duration: int = 120,
                                   volume_level: float = -12.0,
                                   name: str = "") -> Optional[Dict]:
        """
        直接生成音乐（非章节模式）
        
        Args:
            description: 音乐描述
            style: 音乐风格
            duration: 时长（秒）
            volume_level: 音量等级
            name: 音乐名称
            
        Returns:
            音乐生成结果
        """
        logger.info(f"开始直接音乐生成: {style} - {description[:50]}...")
        
        try:
            # 检查服务健康状态
            if not await self.check_service_health():
                raise Exception("SongGeneration服务不可用")
            
            # 创建生成请求
            request = MusicGenerationRequest(
                content=description,
                target_duration=duration,
                custom_style=style,
                volume_level=volume_level
            )
            
            # 生成音乐
            task_id = await self.generate_music_async(request)
            if not task_id:
                raise Exception("音乐生成任务创建失败")
            
            # 等待完成
            result = await self.wait_for_completion(task_id, max_wait_time=300)
            if not result:
                raise Exception("音乐生成超时或失败")
            
            if result.status == "failed":
                raise Exception(f"音乐生成失败: {result.error_message}")
            
            # 下载音乐文件
            if result.audio_url:
                output_filename = f"{name or 'generated_music'}_{int(time.time())}.wav"
                downloaded_path = await self.download_generated_music(
                    result.audio_url, 
                    output_filename
                )
                
                if downloaded_path:
                    return {
                        "audio_path": downloaded_path,
                        "audio_url": f"/api/v1/audio/generated/{output_filename}",
                        "duration": duration,
                        "volume_level": volume_level,
                        "generation_time": result.generation_time,
                        "title": name or "生成的音乐",
                        "task_id": task_id
                    }
            
            raise Exception("音乐文件下载失败")
            
        except Exception as e:
            logger.error(f"直接音乐生成失败: {str(e)}")
            raise Exception(f"音乐生成失败: {str(e)}")

    async def batch_generate_music(self, 
                                 chapters: List[Dict],
                                 default_duration: int = 30,
                                 max_concurrent: int = 3) -> Dict[str, Dict]:
        """
        批量生成音乐
        
        Args:
            chapters: 章节列表，每个元素包含 {id, content, duration?, style?, volume_level?}
            default_duration: 默认时长
            max_concurrent: 最大并发数
            
        Returns:
            生成结果字典 {chapter_id: result}
        """
        logger.info(f"开始批量生成音乐，章节数量: {len(chapters)}")
        
        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_single_chapter(chapter: Dict) -> tuple:
            async with semaphore:
                chapter_id = chapter["id"]
                result = await self.generate_music_for_chapter(
                    chapter_content=chapter["content"],
                    chapter_id=chapter_id,
                    duration=chapter.get("duration", default_duration),
                    style=chapter.get("style"),
                    volume_level=chapter.get("volume_level", -12.0)
                )
                return chapter_id, result
        
        # 并发执行
        tasks = [generate_single_chapter(chapter) for chapter in chapters]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 整理结果
        final_results = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"批量生成中出现异常: {str(result)}")
                continue
            
            chapter_id, chapter_result = result
            final_results[str(chapter_id)] = chapter_result
        
        success_count = sum(1 for r in final_results.values() if r is not None)
        logger.info(f"批量音乐生成完成，成功: {success_count}/{len(chapters)}")
        
        return final_results
    
    async def get_style_recommendations(self, content: str) -> List[Dict]:
        """
        获取音乐风格推荐
        
        Args:
            content: 文本内容
            
        Returns:
            风格推荐列表
        """
        scene_analysis = await self.analyze_scene(content)
        if scene_analysis:
            return scene_analysis.style_recommendations
        return []
    
    def get_supported_styles(self) -> List[str]:
        """获取支持的音乐风格列表"""
        return ["battle", "romance", "mystery", "peaceful", "sad"]
    
    async def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """
        清理旧的音乐文件
        
        Args:
            max_age_hours: 文件最大保留时间（小时）
            
        Returns:
            清理的文件数量
        """
        try:
            import time
            current_time = time.time()
            deleted_count = 0
            
            for file_path in self.output_dir.glob("*.wav"):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_hours * 3600:
                        file_path.unlink()
                        deleted_count += 1
                        logger.debug(f"清理旧音乐文件: {file_path}")
            
            logger.info(f"清理完成，删除了 {deleted_count} 个旧音乐文件")
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理旧文件失败: {str(e)}")
            return 0

# 全局服务实例
_song_generation_service = None

def get_song_generation_service() -> SongGenerationService:
    """获取SongGenerationService实例（单例模式）"""
    global _song_generation_service
    if _song_generation_service is None:
        _song_generation_service = SongGenerationService()
    return _song_generation_service 