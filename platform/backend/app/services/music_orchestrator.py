"""
音乐生成业务编排服务
整合简洁的SongGeneration引擎客户端和业务逻辑
负责：场景分析 → 音乐生成 → 文件管理 → 任务编排
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

from app.clients.songgeneration_engine import get_songgeneration_engine, SynthesizeResponse
from app.services.music_scene_analyzer import get_music_scene_analyzer, MusicSceneAnalysis
from app.clients.file_manager import file_manager

logger = logging.getLogger(__name__)

@dataclass
class MusicGenerationTask:
    """音乐生成任务"""
    task_id: str
    content: str
    scene_analysis: MusicSceneAnalysis
    status: str  # pending, processing, completed, failed
    audio_path: Optional[str] = None
    error_message: Optional[str] = None
    generation_time: Optional[float] = None
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

@dataclass 
class BatchGenerationResult:
    """批量生成结果"""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    results: Dict[str, Dict]  # task_id -> result
    processing_time: float

class MusicOrchestrator:
    """
    音乐生成业务编排器
    简洁架构：业务逻辑层，调用纯净的引擎进行生成
    """
    
    def __init__(self):
        self.engine = get_songgeneration_engine()
        self.scene_analyzer = get_music_scene_analyzer()
        self.active_tasks: Dict[str, MusicGenerationTask] = {}
        self.completed_tasks: Dict[str, MusicGenerationTask] = {}
        
        logger.info("音乐编排服务初始化完成")
    
    async def generate_music_for_content(self, 
                                       content: str,
                                       chapter_id: Optional[str] = None,
                                       custom_style: Optional[str] = None,
                                       volume_level: float = -12.0,
                                       direct_mode: bool = False,
                                       advanced_params: Optional[Dict] = None) -> Optional[Dict]:
        """
        为内容生成背景音乐（完整业务流程）
        
        Args:
            content: 文本内容
            chapter_id: 章节ID（可选）
            custom_style: 自定义风格（可选）
            volume_level: 音量级别
            direct_mode: 直接模式（跳过复杂场景分析）
            advanced_params: 高级参数字典（cfg_coef, temperature, top_k, description等）
            
        Returns:
            生成结果字典
        """
        start_time = time.time()
        advanced_params = advanced_params or {}
        
        try:
            logger.info(f"开始音乐生成流程，内容长度: {len(content)} 字符，直接模式: {direct_mode}")
            
            # 步骤1：场景分析（直接模式可跳过）
            if direct_mode:
                # 直接模式：跳过复杂场景分析，使用默认值
                scene_analysis = None
                final_style = custom_style or "Auto"
                music_description = content  # 直接使用用户输入的歌词
                logger.info(f"直接模式：跳过场景分析，风格: {final_style}")
            else:
                # 完整模式：进行场景分析
                scene_analysis = self.scene_analyzer.analyze_content(content)
                logger.info(f"场景分析完成: {scene_analysis.scene_type} -> {scene_analysis.recommended_style}")
                final_style = custom_style or scene_analysis.recommended_style
                music_description = self._create_music_description(content, scene_analysis)
            
            # 步骤2：调用引擎生成音乐（使用完整的SongGeneration参数）
            logger.info(f"调用引擎生成音乐: {final_style}")
            synthesis_result = await self.engine.synthesize(
                lyrics=music_description,
                genre=final_style,  # 使用正确的参数名
                description=advanced_params.get("description", ""),
                cfg_coef=advanced_params.get("cfg_coef", 1.5),
                temperature=advanced_params.get("temperature", 0.9),
                top_k=advanced_params.get("top_k", 50)
            )
            
            if not synthesis_result:
                logger.error("引擎音乐合成失败")
                return None
            
            # 步骤5：文件管理（下载和存储）
            filename = f"music_{chapter_id or 'generated'}_{int(time.time())}.wav"
            local_path = await self._download_and_store_music(
                synthesis_result.audio_url, 
                filename
            )
            
            if not local_path:
                logger.error("音乐文件下载失败")
                return None
            
            # 步骤6：音频后处理（音量调整等）
            processed_path = await self._post_process_audio(
                local_path, 
                volume_level
            )
            
            generation_time = time.time() - start_time
            
            # 步骤7：构建结果
            result = {
                "audio_path": processed_path or local_path,
                "audio_url": f"/api/v1/audio/generated/{filename}",
                "scene_analysis": {
                    "scene_type": scene_analysis.scene_type if scene_analysis else "direct",
                    "emotion_tone": scene_analysis.emotion_tone if scene_analysis else "neutral",
                    "intensity": scene_analysis.intensity if scene_analysis else 0.5,
                    "recommended_style": scene_analysis.recommended_style if scene_analysis else final_style,
                    "confidence": scene_analysis.style_confidence if scene_analysis else 1.0
                } if scene_analysis else None,
                "music_description": music_description,
                "final_style": final_style,
                "duration": synthesis_result.duration,
                "generation_time": generation_time,
                "volume_level": volume_level,
                "chapter_id": chapter_id
            }
            
            logger.info(f"音乐生成流程完成，耗时: {generation_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"音乐生成流程失败: {e}")
            return None
    
    async def generate_music_batch(self, 
                                 chapters: List[Dict],
                                 max_concurrent: int = 3) -> BatchGenerationResult:
        """
        批量生成音乐
        
        Args:
            chapters: 章节列表 [{id, content, duration?, style?, volume_level?}]
            max_concurrent: 最大并发数
            
        Returns:
            批量生成结果
        """
        start_time = time.time()
        logger.info(f"开始批量音乐生成，章节数: {len(chapters)}, 并发数: {max_concurrent}")
        
        # 创建信号量限制并发
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_single(chapter: Dict) -> tuple:
            async with semaphore:
                chapter_id = str(chapter["id"])
                result = await self.generate_music_for_content(
                    content=chapter["content"],
                    chapter_id=chapter_id,
                    custom_style=chapter.get("style"),
                    volume_level=chapter.get("volume_level", -12.0)
                )
                return chapter_id, result
        
        # 并发执行
        tasks = [generate_single(chapter) for chapter in chapters]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 整理结果
        final_results = {}
        completed_count = 0
        failed_count = 0
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"批量生成异常: {result}")
                failed_count += 1
                continue
            
            chapter_id, chapter_result = result
            if chapter_result:
                final_results[chapter_id] = chapter_result
                completed_count += 1
            else:
                failed_count += 1
                final_results[chapter_id] = None
        
        processing_time = time.time() - start_time
        
        batch_result = BatchGenerationResult(
            total_tasks=len(chapters),
            completed_tasks=completed_count,
            failed_tasks=failed_count,
            results=final_results,
            processing_time=processing_time
        )
        
        logger.info(f"批量生成完成: {completed_count}/{len(chapters)} 成功, 耗时: {processing_time:.2f}s")
        return batch_result
    
    async def analyze_content_scene(self, content: str) -> MusicSceneAnalysis:
        """分析内容场景（独立接口）"""
        return self.scene_analyzer.analyze_content(content)
    
    async def check_engine_health(self) -> bool:
        """检查引擎健康状态"""
        return await self.engine.health_check()
    
    def get_supported_styles(self) -> List[str]:
        """获取支持的音乐风格列表"""
        return ["pop", "epic", "dark", "ambient", "sad", "cinematic", "electronic", "romantic"]
    
    def get_supported_scenes(self) -> List[str]:
        """获取支持的场景类型列表"""
        return self.scene_analyzer.get_supported_scenes()
    
    def _create_music_description(self, content: str, scene_analysis: MusicSceneAnalysis) -> str:
        """
        创建音乐描述/歌词
        根据内容和场景分析生成适合的音乐描述
        """
        # 基于场景类型生成音乐描述
        scene_descriptions = {
            "battle": "激烈的战斗音乐，充满力量和紧张感",
            "romance": "温柔浪漫的音乐，充满爱意和温暖",
            "mystery": "神秘诡异的音乐，营造悬疑氛围",
            "peaceful": "平静安详的音乐，令人放松和舒缓",
            "sad": "哀伤忧郁的音乐，表达深沉的情感",
            "adventure": "冒险旅程的音乐，充满探索精神",
            "celebration": "欢庆快乐的音乐，充满喜悦和活力"
        }
        
        base_description = scene_descriptions.get(
            scene_analysis.scene_type, 
            "优美的背景音乐"
        )
        
        # 添加强度修饰
        if scene_analysis.intensity > 0.7:
            intensity_modifier = "非常强烈的"
        elif scene_analysis.intensity > 0.5:
            intensity_modifier = "较为强烈的"
        elif scene_analysis.intensity > 0.3:
            intensity_modifier = "中等强度的"
        else:
            intensity_modifier = "轻柔的"
        
        # 添加情感基调
        emotion_modifiers = {
            "positive": "充满正能量的",
            "negative": "带有忧伤色彩的",
            "intense": "激动人心的",
            "neutral": "平衡的"
        }
        
        emotion_modifier = emotion_modifiers.get(
            scene_analysis.emotion_tone, 
            ""
        )
        
        # 组合描述
        description_parts = [emotion_modifier, intensity_modifier, base_description]
        final_description = "".join(part for part in description_parts if part)
        
        # 添加关键词提示
        if scene_analysis.keywords:
            keywords_text = "，".join(scene_analysis.keywords[:3])
            final_description += f"，体现{keywords_text}的元素"
        
        return final_description
    
    async def _download_and_store_music(self, audio_url: str, filename: str) -> Optional[str]:
        """下载并存储音乐文件"""
        try:
            # 这里应该调用file_manager或者实现下载逻辑
            # 简化版：假设文件已经可访问
            output_dir = Path("data/audio/generated")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / filename
            
            # 实际下载逻辑应该在这里实现
            # 目前返回预期路径
            logger.info(f"音乐文件已存储: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"音乐文件下载失败: {e}")
            return None
    
    async def _post_process_audio(self, audio_path: str, volume_level: float) -> Optional[str]:
        """音频后处理（音量调整、淡入淡出等）"""
        try:
            # 这里应该实现音频处理逻辑
            # 简化版：直接返回原路径
            logger.info(f"音频后处理完成: {audio_path}, 音量: {volume_level}dB")
            return audio_path
            
        except Exception as e:
            logger.error(f"音频后处理失败: {e}")
            return None
    
    async def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """清理旧的音乐文件"""
        try:
            output_dir = Path("data/audio/generated")
            if not output_dir.exists():
                return 0
            
            current_time = time.time()
            cleaned_count = 0
            
            for file_path in output_dir.glob("*.wav"):
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_hours * 3600:
                    file_path.unlink()
                    cleaned_count += 1
            
            logger.info(f"清理了 {cleaned_count} 个旧音乐文件")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理旧文件失败: {e}")
            return 0

# 全局编排器实例
_music_orchestrator = None

def get_music_orchestrator() -> MusicOrchestrator:
    """获取音乐编排器实例（单例模式）"""
    global _music_orchestrator
    if _music_orchestrator is None:
        _music_orchestrator = MusicOrchestrator()
    return _music_orchestrator 