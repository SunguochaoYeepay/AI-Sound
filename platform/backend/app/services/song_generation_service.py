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
        # 从环境变量获取SongGeneration服务URL，默认使用本地Docker端口
        import os
        self.base_url = os.getenv("SONGGENERATION_URL", "http://localhost:7862")
        # 大幅增加超时时间 - 音乐生成耗时很长，防止超时失败
        self.timeout = 900  # 15分钟超时 (原来5分钟太短)
        # 配置更宽松的httpx客户端
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=30.0,     # 连接超时30秒
                read=900.0,       # 读取超时15分钟
                write=30.0,       # 写入超时30秒
                pool=10.0         # 连接池超时10秒
            ),
            limits=httpx.Limits(
                max_keepalive_connections=1,  # 减少连接数避免资源占用
                max_connections=2,            # 最大连接数限制
                keepalive_expiry=30.0         # 保持连接30秒
            )
        )
        logger.info(f"SongGenerationService初始化，使用服务: {self.base_url}, 超时: {self.timeout}秒")
        
        # 确保音频输出目录存在
        self.output_dir = Path("data/audio/generated_music")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _clean_lyrics_for_songgeneration(self, lyrics: str) -> str:
        """
        🚨 严格清理歌词格式，确保符合SongGeneration引擎要求
        
        关键规则：
        1. 前奏、间奏、尾奏段落不能包含歌词内容
        2. 只有 [verse], [chorus], [bridge] 可以包含歌词
        3. 纯音乐段落：[intro-*], [inst-*], [outro-*], [silence]
        
        Args:
            lyrics: 原始歌词内容
            
        Returns:
            清理后的歌词
        """
        if not lyrics.strip():
            return "[verse]\n暂无歌词内容"
        
        # 需要歌词的标签
        VOCAL_STRUCTS = {'[verse]', '[chorus]', '[bridge]'}
        
        # 纯音乐标签（不能包含歌词）
        INSTRUMENTAL_STRUCTS = {
            '[intro-short]', '[intro-medium]', '[intro-long]',
            '[inst-short]', '[inst-medium]', '[inst-long]', 
            '[outro-short]', '[outro-medium]', '[outro-long]',
            '[silence]'
        }
        
        # 旧标签映射
        LEGACY_MAPPINGS = {
            '[intro]': '[intro-medium]',
            '[outro]': '[outro-medium]',
            '[instrumental]': '[inst-medium]',
            '[inst]': '[inst-medium]'
        }
        
        try:
            # 按双换行分割段落
            paragraphs = [p.strip() for p in lyrics.strip().split('\n\n') if p.strip()]
            cleaned_paragraphs = []
            vocal_found = False
            
            for paragraph in paragraphs:
                lines = paragraph.strip().split('\n')
                if not lines:
                    continue
                
                # 获取标签
                tag_line = lines[0].strip().lower()
                
                # 转换旧标签
                if tag_line in LEGACY_MAPPINGS:
                    tag_line = LEGACY_MAPPINGS[tag_line]
                
                # 检查标签是否有效
                if tag_line not in VOCAL_STRUCTS and tag_line not in INSTRUMENTAL_STRUCTS:
                    # 无效标签，默认为主歌
                    tag_line = '[verse]'
                
                if tag_line in VOCAL_STRUCTS:
                    # 人声段落，保留歌词
                    vocal_found = True
                    if len(lines) > 1:
                        lyrics_content = '\n'.join(lines[1:]).strip()
                        if lyrics_content:
                            cleaned_paragraphs.append(f"{tag_line}\n{lyrics_content}")
                        else:
                            cleaned_paragraphs.append(tag_line)
                    else:
                        cleaned_paragraphs.append(tag_line)
                        
                elif tag_line in INSTRUMENTAL_STRUCTS:
                    # 🚨 纯音乐段落，绝不包含歌词内容
                    cleaned_paragraphs.append(tag_line)
                    logger.info(f"过滤纯音乐段落歌词: {tag_line}")
            
            # 确保至少有一个人声段落
            if not vocal_found:
                cleaned_paragraphs.insert(0, "[verse]\n暂无歌词内容")
            
            result = '\n\n'.join(cleaned_paragraphs)
            logger.info(f"歌词清理完成: {len(paragraphs)} -> {len(cleaned_paragraphs)} 段落")
            return result
            
        except Exception as e:
            logger.error(f"歌词清理失败: {e}")
            # 返回安全的默认格式
            return "[verse]\n暂无歌词内容"
    
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
        分析文本内容的场景和情绪（简化版本，引擎不支持独立分析）
        
        Args:
            content: 文本内容
            
        Returns:
            场景分析结果
        """
        try:
            # 引擎不支持独立场景分析，返回通用分析结果
            logger.info("使用简化场景分析（引擎不支持独立场景分析）")
            return SceneAnalysisResult(
                scene_type="general",
                emotion_tone="neutral",
                intensity=0.5,
                keywords=["background", "music"],
                duration_hint=30,
                style_recommendations=[{"style": "background", "confidence": 0.8}]
            )
            
        except Exception as e:
            logger.error(f"场景分析失败: {str(e)}")
            return None
    
    async def generate_music_async(self, request: MusicGenerationRequest) -> Optional[str]:
        """
        异步生成音乐（适配引擎同步接口）
        
        Args:
            request: 音乐生成请求
            
        Returns:
            任务ID（实际为file_id）
        """
        try:
            # 适配引擎的实际API格式
            engine_request = {
                "lyrics": request.content,  # content -> lyrics
                "genre": getattr(request, 'genre', 'Auto'),
                "descriptions": getattr(request, 'description', '') or request.custom_style or "background music",
                "cfg_coef": getattr(request, 'cfg_coef', 1.5),
                "temperature": getattr(request, 'temperature', 0.9),
                "top_k": getattr(request, 'top_k', 50)
            }
            
            logger.info(f"发送音乐生成请求到引擎: {self.base_url}/generate_async")
            response = await self.session.post(
                f"{self.base_url}/generate_async",
                json=engine_request
            )
            response.raise_for_status()
            
            data = response.json()
            
            # 引擎返回格式: {"success": true, "file_id": "...", "file_path": "..."}
            if data.get("success") and data.get("file_id"):
                file_id = data["file_id"]
                logger.info(f"音乐生成完成，文件ID: {file_id}")
                return file_id
            else:
                logger.error(f"引擎生成失败: {data.get('message', '未知错误')}")
                return None
            
        except Exception as e:
            logger.error(f"音乐生成请求失败: {str(e)}")
            return None
    
    async def get_task_status(self, task_id: str) -> Optional[MusicGenerationResult]:
        """
        获取任务状态（适配引擎同步模式）
        
        Args:
            task_id: 任务ID（实际为file_id）
            
        Returns:
            音乐生成结果
        """
        try:
            # 引擎是同步生成，如果有file_id说明已完成
            # 构造下载URL
            audio_url = f"/download/{task_id}"
            
            return MusicGenerationResult(
                task_id=task_id,
                status="completed",  # 引擎同步完成
                progress=1.0,
                audio_url=audio_url,
                scene_analysis=None,
                music_prompt=None,
                error_message=None,
                generation_time=None
            )
            
        except Exception as e:
            logger.error(f"构造任务状态失败: {str(e)}")
            return None
    
    async def wait_for_completion(self, task_id: str, max_wait_time: int = 900) -> Optional[MusicGenerationResult]:
        """
        等待任务完成（适配引擎同步模式，直接返回结果）
        
        Args:
            task_id: 任务ID
            max_wait_time: 最大等待时间（秒）
            
        Returns:
            音乐生成结果
        """
        # 引擎是同步生成，直接返回完成状态
        logger.info(f"音乐生成任务已同步完成: {task_id}")
        return await self.get_task_status(task_id)
    
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
                filename = f"chapter_{chapter_id}_music_{int(time.time())}.flac"
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
            
            # 🚨 关键修复：清理歌词格式确保引擎兼容性
            cleaned_description = self._clean_lyrics_for_songgeneration(description)
            logger.info(f"歌词清理完成，原始: {len(description)} 字符 -> 清理后: {len(cleaned_description)} 字符")
            
            # 创建生成请求
            request = MusicGenerationRequest(
                content=cleaned_description,
                target_duration=duration,
                custom_style=style,
                volume_level=volume_level
            )
            
            # 生成音乐
            task_id = await self.generate_music_async(request)
            if not task_id:
                raise Exception("音乐生成任务创建失败")
            
            # 等待完成 - 使用更长的超时时间避免生成失败
            result = await self.wait_for_completion(task_id, max_wait_time=900)
            if not result:
                raise Exception("音乐生成超时或失败")
            
            if result.status == "failed":
                raise Exception(f"音乐生成失败: {result.error_message}")
            
            # 下载音乐文件
            if result.audio_url:
                output_filename = f"{name or 'generated_music'}_{int(time.time())}.flac"
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

    # 批量生成音乐方法已移除 - 资源消耗过大，容易导致系统卡死
    # async def batch_generate_music(self, 
    #                              chapters: List[Dict],
    #                              default_duration: int = 30,
    #                              max_concurrent: int = 3) -> Dict[str, Dict]:
    #     """
    #     批量生成音乐 (已禁用)
    #     单个音乐生成就需要很长时间，批量生成会导致系统资源耗尽
    #     """
    #     raise Exception("批量音乐生成功能已禁用，请使用单个生成功能避免系统过载")
    
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
            
            for file_path in list(self.output_dir.glob("*.wav")) + list(self.output_dir.glob("*.flac")):
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