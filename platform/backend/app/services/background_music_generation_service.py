"""
背景音乐生成服务
整合SongGeneration和MusicSceneAnalyzer，为小说章节生成智能背景音乐
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Union
from datetime import datetime
from pathlib import Path

from .song_generation_service import get_song_generation_service, MusicGenerationRequest
from .music_scene_analyzer import get_music_scene_analyzer, MusicSceneAnalysis

logger = logging.getLogger(__name__)

class BackgroundMusicGenerationService:
    """背景音乐生成服务"""
    
    def __init__(self):
        self.song_service = get_song_generation_service()
        self.scene_analyzer = get_music_scene_analyzer()
        
        # 音乐生成配置
        self.default_config = {
            "volume_levels": {
                "battle": -9.0,
                "romance": -15.0,
                "mystery": -12.0,
                "peaceful": -18.0,
                "sad": -14.0
            },
            "duration_adjustments": {
                "battle": 1.2,
                "romance": 0.9,
                "mystery": 1.1,
                "peaceful": 0.8,
                "sad": 1.0
            },
            "fade_settings": {
                "standard": {"fade_in": 2.0, "fade_out": 2.0},
                "smooth": {"fade_in": 3.0, "fade_out": 3.0},
                "quick": {"fade_in": 1.0, "fade_out": 1.0}
            }
        }
        
        logger.info("BackgroundMusicGenerationService 初始化完成")
    
    async def check_service_health(self) -> Dict:
        """检查服务健康状态"""
        try:
            # 检查SongGeneration服务
            song_service_ok = await self.song_service.health_check()
            
            # 检查场景分析器
            analyzer_ok = self.scene_analyzer is not None
            
            return {
                "status": "healthy" if (song_service_ok and analyzer_ok) else "degraded",
                "services": {
                    "song_generation": "healthy" if song_service_ok else "unhealthy",
                    "scene_analyzer": "healthy" if analyzer_ok else "unhealthy"
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def generate_chapter_background_music(self, 
                                              chapter_id: Union[str, int],
                                              chapter_content: str,
                                              user_preferences: Dict = None) -> Dict:
        """
        为章节生成背景音乐
        
        Args:
            chapter_id: 章节ID
            chapter_content: 章节内容
            user_preferences: 用户偏好设置
            
        Returns:
            音乐生成结果
        """
        logger.info(f"开始为章节 {chapter_id} 生成背景音乐")
        
        try:
            # 1. 场景分析
            scene_analysis = await self.scene_analyzer.analyze_chapter_music_scene(
                chapter_content, 
                {"chapter_id": chapter_id}
            )
            
            logger.info(f"章节 {chapter_id} 场景分析完成: {scene_analysis.primary_scene.scene_type}")
            
            # 2. 根据用户偏好调整配置
            music_config = self._build_music_config(scene_analysis, user_preferences)
            
            # 3. 创建音乐生成请求
            generation_request = MusicGenerationRequest(
                content=self._prepare_content_for_generation(chapter_content, scene_analysis),
                target_duration=music_config["duration"],
                custom_style=music_config["style"],
                volume_level=music_config["volume_level"],
                fade_in=music_config["fade_in"],
                fade_out=music_config["fade_out"]
            )
            
            # 4. 生成背景音乐
            music_result = await self.song_service.generate_music_for_chapter(
                chapter_content=generation_request.content,
                chapter_id=chapter_id,
                duration=generation_request.target_duration,
                style=generation_request.custom_style,
                volume_level=generation_request.volume_level
            )
            
            if not music_result:
                raise Exception("音乐生成失败")
            
            # 5. 整理返回结果
            result = {
                "chapter_id": chapter_id,
                "generation_status": "completed",
                "music_info": {
                    "audio_path": music_result["audio_path"],
                    "audio_url": music_result.get("audio_url"),
                    "duration": music_result.get("duration", generation_request.target_duration),
                    "volume_level": music_result.get("volume_level", generation_request.volume_level),
                    "generation_time": music_result.get("generation_time")
                },
                "scene_analysis": {
                    "primary_scene": {
                        "type": scene_analysis.primary_scene.scene_type,
                        "emotion": scene_analysis.primary_scene.emotion_tone,
                        "intensity": scene_analysis.primary_scene.intensity,
                        "keywords": scene_analysis.primary_scene.keywords,
                        "confidence": scene_analysis.primary_scene.confidence
                    },
                    "overall_mood": scene_analysis.overall_mood,
                    "tempo_preference": scene_analysis.tempo_preference,
                    "volume_suggestion": scene_analysis.volume_suggestion,
                    "transition_points": scene_analysis.transition_points
                },
                "music_config": music_config,
                "style_recommendations": scene_analysis.style_recommendations,
                "created_at": datetime.now().isoformat()
            }
            
            logger.info(f"章节 {chapter_id} 背景音乐生成完成")
            return result
            
        except Exception as e:
            logger.error(f"章节 {chapter_id} 背景音乐生成失败: {str(e)}")
            return {
                "chapter_id": chapter_id,
                "generation_status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def generate_direct_music(self, 
                                   description: str,
                                   style: str = "peaceful",
                                   target_duration: int = 120,
                                   volume_level: float = -12.0,
                                   name: str = "") -> Dict:
        """
        直接基于描述生成音乐（跳过场景分析）
        
        Args:
            description: 音乐描述
            style: 音乐风格
            target_duration: 目标时长
            volume_level: 音量等级
            name: 音乐名称
            
        Returns:
            音乐生成结果
        """
        logger.info(f"开始直接生成音乐，风格: {style}, 时长: {target_duration}秒")
        
        try:
            # 直接创建音乐生成配置，跳过场景分析
            music_config = {
                "style": style,
                "duration": target_duration,
                "volume_level": volume_level,
                "fade_in": 2.0,
                "fade_out": 2.0,
                "intensity": 0.7,  # 默认强度
                "tempo_preference": 120  # 修复：使用整数BPM值而不是字符串
            }
            
            # 直接调用音乐生成服务
            music_result = await self.song_service.generate_music_direct(
                description=description,
                style=style,
                duration=target_duration,
                volume_level=volume_level,
                name=name
            )
            
            if not music_result:
                raise Exception("音乐生成失败")
            
            # 组织返回结果
            result = {
                "chapter_id": f"direct_{int(datetime.now().timestamp())}",
                "generation_status": "completed",
                "music_info": {
                    "audio_path": music_result["audio_path"],
                    "audio_url": music_result.get("audio_url"),
                    "duration": music_result.get("duration", target_duration),
                    "volume_level": music_result.get("volume_level", volume_level),
                    "generation_time": music_result.get("generation_time")
                },
                "scene_analysis": {
                    "primary_scene": {
                        "type": style,
                        "emotion": "custom",
                        "intensity": 0.7,
                        "keywords": [description[:50] + "..." if len(description) > 50 else description],
                        "confidence": 1.0
                    },
                    "overall_mood": style,
                    "tempo_preference": 120,  # 修复：使用整数BPM值
                    "volume_suggestion": volume_level,
                    "transition_points": []
                },
                "music_config": music_config,
                "style_recommendations": [  # 修复：使用正确的StyleRecommendation格式
                    {
                        "style": style,
                        "priority": 1,
                        "confidence": 1.0,
                        "description": f"直接生成的{style}风格音乐",
                        "keywords": [description[:30] + "..." if len(description) > 30 else description],
                        "duration": target_duration
                    }
                ],
                "created_at": datetime.now().isoformat()
            }
            
            logger.info(f"直接音乐生成完成")
            return result
            
        except Exception as e:
            logger.error(f"直接音乐生成失败: {str(e)}")
            return {
                "chapter_id": f"direct_{int(datetime.now().timestamp())}",
                "generation_status": "failed",
                "error": str(e),
                "created_at": datetime.now().isoformat()
            }
    
    async def batch_generate_background_music(self, 
                                            chapters: List[Dict],
                                            user_preferences: Dict = None,
                                            max_concurrent: int = 2) -> Dict:
        """
        批量生成背景音乐
        
        Args:
            chapters: 章节列表 [{id, content, title?}]
            user_preferences: 用户偏好
            max_concurrent: 最大并发数
            
        Returns:
            批量生成结果
        """
        logger.info(f"开始批量生成背景音乐，章节数量: {len(chapters)}")
        
        # 创建信号量限制并发
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_single_chapter(chapter: Dict) -> tuple:
            async with semaphore:
                chapter_id = chapter["id"]
                result = await self.generate_chapter_background_music(
                    chapter_id=chapter_id,
                    chapter_content=chapter["content"],
                    user_preferences=user_preferences
                )
                return chapter_id, result
        
        # 并发执行
        tasks = [generate_single_chapter(chapter) for chapter in chapters]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 整理结果
        final_results = {}
        success_count = 0
        failed_count = 0
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"批量生成中出现异常: {str(result)}")
                failed_count += 1
                continue
            
            chapter_id, chapter_result = result
            final_results[str(chapter_id)] = chapter_result
            
            if chapter_result.get("generation_status") == "completed":
                success_count += 1
            else:
                failed_count += 1
        
        logger.info(f"批量背景音乐生成完成，成功: {success_count}, 失败: {failed_count}")
        
        return {
            "batch_status": "completed",
            "total_chapters": len(chapters),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": final_results,
            "completed_at": datetime.now().isoformat()
        }
    
    async def get_music_style_preview(self, content_sample: str) -> Dict:
        """
        获取音乐风格预览
        
        Args:
            content_sample: 内容样本
            
        Returns:
            风格预览信息
        """
        try:
            scene_analysis = await self.scene_analyzer.analyze_chapter_music_scene(content_sample)
            
            return {
                "primary_style": scene_analysis.primary_scene.scene_type,
                "confidence": scene_analysis.primary_scene.confidence,
                "intensity": scene_analysis.primary_scene.intensity,
                "mood": scene_analysis.overall_mood,
                "tempo_range": scene_analysis.tempo_preference,
                "volume_suggestion": scene_analysis.volume_suggestion,
                "keywords": scene_analysis.primary_scene.keywords,
                "style_recommendations": scene_analysis.style_recommendations,
                "available_styles": self.scene_analyzer.get_supported_scene_types()
            }
            
        except Exception as e:
            logger.error(f"获取音乐风格预览失败: {str(e)}")
            return {
                "primary_style": "peaceful",
                "confidence": 0.5,
                "error": str(e)
            }
    
    def _build_music_config(self, scene_analysis: MusicSceneAnalysis, user_preferences: Dict = None) -> Dict:
        """构建音乐生成配置"""
        
        # 基础配置
        scene_type = scene_analysis.primary_scene.scene_type
        base_duration = scene_analysis.primary_scene.duration_hint
        
        # 音量配置
        volume_level = self.default_config["volume_levels"].get(scene_type, -15.0)
        # 根据强度调整音量
        intensity_adjustment = (scene_analysis.primary_scene.intensity - 0.5) * 3.0
        volume_level = max(-20.0, min(-6.0, volume_level + intensity_adjustment))
        
        # 时长配置
        duration_factor = self.default_config["duration_adjustments"].get(scene_type, 1.0)
        target_duration = int(base_duration * duration_factor)
        
        # 淡入淡出配置
        fade_mode = "standard"
        if user_preferences:
            fade_mode = user_preferences.get("fade_mode", "standard")
        
        fade_settings = self.default_config["fade_settings"].get(fade_mode, 
                                                               self.default_config["fade_settings"]["standard"])
        
        # 用户偏好覆盖
        if user_preferences:
            if "music_volume" in user_preferences:
                volume_level = user_preferences["music_volume"]
            if "music_duration" in user_preferences:
                target_duration = user_preferences["music_duration"]
            if "custom_style" in user_preferences:
                scene_type = user_preferences["custom_style"]
        
        return {
            "style": scene_type,
            "duration": target_duration,
            "volume_level": volume_level,
            "fade_in": fade_settings["fade_in"],
            "fade_out": fade_settings["fade_out"],
            "intensity": scene_analysis.primary_scene.intensity,
            "tempo_preference": scene_analysis.tempo_preference
        }
    
    def _prepare_content_for_generation(self, content: str, scene_analysis: MusicSceneAnalysis) -> str:
        """为音乐生成准备内容描述"""
        
        # 提取关键信息
        keywords = scene_analysis.primary_scene.keywords
        mood = scene_analysis.overall_mood
        scene_type = scene_analysis.primary_scene.scene_type
        
        # 构建音乐提示词
        prompt_parts = [
            f"场景类型: {scene_type}",
            f"整体氛围: {mood}",
            f"关键元素: {', '.join(keywords[:5])}"
        ]
        
        # 如果有次要场景，添加变化提示
        if scene_analysis.secondary_scenes:
            secondary_styles = [s.scene_type for s in scene_analysis.secondary_scenes[:2]]
            prompt_parts.append(f"次要元素: {', '.join(secondary_styles)}")
        
        # 如果有转换点，添加动态提示
        if scene_analysis.transition_points:
            prompt_parts.append("包含场景转换")
        
        # 组合提示词
        music_prompt = " | ".join(prompt_parts)
        
        logger.debug(f"音乐生成提示词: {music_prompt}")
        return music_prompt
    
    async def get_music_generation_status(self, task_id: str) -> Optional[Dict]:
        """
        获取音乐生成任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        try:
            result = await self.song_service.get_task_status(task_id)
            
            if result:
                return {
                    "task_id": result.task_id,
                    "status": result.status,
                    "progress": result.progress,
                    "audio_url": result.audio_url,
                    "error_message": result.error_message,
                    "generation_time": result.generation_time
                }
            return None
            
        except Exception as e:
            logger.error(f"获取音乐生成状态失败: {str(e)}")
            return None
    
    async def cancel_music_generation(self, task_id: str) -> bool:
        """
        取消音乐生成任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        try:
            # 这里可以添加取消逻辑，目前先返回True
            logger.info(f"尝试取消音乐生成任务: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"取消音乐生成任务失败: {str(e)}")
            return False
    
    def get_supported_styles(self) -> List[Dict]:
        """获取支持的音乐风格"""
        styles = []
        
        for style_name in self.scene_analyzer.get_supported_scene_types():
            style_info = self.scene_analyzer.get_scene_type_info(style_name)
            if style_info:
                styles.append({
                    "name": style_name,
                    "display_name": self._get_style_display_name(style_name),
                    "description": self._get_style_description(style_name),
                    "keywords": style_info["keywords"][:5],
                    "intensity_range": style_info["intensity_range"],
                    "bpm_range": style_info["bpm_range"],
                    "volume_range": style_info["volume_range"]
                })
        
        return styles
    
    def _get_style_display_name(self, style_name: str) -> str:
        """获取风格显示名称"""
        display_names = {
            "battle": "战斗",
            "romance": "浪漫",
            "mystery": "悬疑",
            "peaceful": "平静",
            "sad": "悲伤"
        }
        return display_names.get(style_name, style_name)
    
    def _get_style_description(self, style_name: str) -> str:
        """获取风格描述"""
        descriptions = {
            "battle": "激烈的战斗场面，节奏强劲，充满力量",
            "romance": "温馨浪漫的情感场景，旋律优美，情绪温和",
            "mystery": "神秘悬疑的氛围，节奏适中，营造紧张感",
            "peaceful": "平静安详的环境，节奏缓慢，令人放松",
            "sad": "悲伤忧郁的情绪，旋律深沉，触动心弦"
        }
        return descriptions.get(style_name, "未知风格")
    
    async def cleanup_old_music_files(self, max_age_hours: int = 24) -> int:
        """清理旧的音乐文件"""
        try:
            return await self.song_service.cleanup_old_files(max_age_hours)
        except Exception as e:
            logger.error(f"清理音乐文件失败: {str(e)}")
            return 0
    
    def get_service_info(self) -> Dict:
        """获取服务信息"""
        return {
            "service_name": "BackgroundMusicGenerationService",
            "version": "1.0.0",
            "supported_styles": len(self.scene_analyzer.get_supported_scene_types()),
            "default_config": self.default_config,
            "description": "为小说章节生成智能背景音乐的综合服务"
        }

# 全局服务实例
_background_music_service = None

def get_background_music_generation_service() -> BackgroundMusicGenerationService:
    """获取BackgroundMusicGenerationService实例（单例模式）"""
    global _background_music_service
    if _background_music_service is None:
        _background_music_service = BackgroundMusicGenerationService()
    return _background_music_service 