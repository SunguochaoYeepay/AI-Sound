"""
顺序时间轴生成器
基于实际音频文件生成精确的环境音时间轴，支持场景切换检测
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import re

from app.utils import get_audio_duration
from app.services.audio_enhancement import AudioEnhancementService

logger = logging.getLogger(__name__)

@dataclass
class DialogueSegment:
    """对话段落信息"""
    index: int
    start_time: float
    end_time: float
    duration: float
    file_path: str
    text_content: str
    speaker: str
    scene_keywords: List[str]

@dataclass
class EnvironmentTrack:
    """环境音轨道信息"""
    start_time: float
    end_time: float
    duration: float
    scene_prompt: str
    tango_prompt: str
    volume_level: float = 0.3
    fade_in: float = 0.5
    fade_out: float = 0.5
    priority: int = 1  # 1=主环境音, 2=音效, 3=氛围

@dataclass
class SceneInfo:
    """场景信息"""
    location: str = "indoor"  # indoor, outdoor, forest, city, etc.
    weather: str = "clear"    # clear, rainy, windy, stormy, etc.
    time_of_day: str = "day"  # day, night, morning, evening
    atmosphere: str = "calm"  # calm, tense, romantic, mysterious
    keywords: List[str] = None
    confidence: float = 0.7

@dataclass
class Timeline:
    """完整时间轴"""
    total_duration: float
    dialogue_segments: List[DialogueSegment]
    environment_tracks: List[EnvironmentTrack]
    scene_changes: List[Dict[str, Any]]


class SequentialTimelineGenerator:
    """顺序时间轴生成器"""
    
    def __init__(self):
        self.audio_enhancement = AudioEnhancementService()
        
        # 场景关键词增强映射
        self.scene_keywords_map = {
            # 地点
            "房间": {"location": "indoor", "keywords": ["room", "indoor"]},
            "室内": {"location": "indoor", "keywords": ["indoor", "room"]},
            "户外": {"location": "outdoor", "keywords": ["outdoor", "nature"]},
            "森林": {"location": "forest", "keywords": ["forest", "trees", "nature"]},
            "城市": {"location": "city", "keywords": ["city", "urban", "traffic"]},
            "海边": {"location": "beach", "keywords": ["ocean", "waves", "beach"]},
            "山": {"location": "mountain", "keywords": ["mountain", "wind", "echo"]},
            "街道": {"location": "street", "keywords": ["street", "traffic", "footsteps"]},
            
            # 天气
            "雨": {"weather": "rainy", "keywords": ["rain", "water", "drops"]},
            "雷": {"weather": "stormy", "keywords": ["thunder", "storm", "lightning"]},
            "风": {"weather": "windy", "keywords": ["wind", "breeze", "air"]},
            "雪": {"weather": "snowy", "keywords": ["snow", "winter", "cold"]},
            
            # 时间
            "夜": {"time_of_day": "night", "keywords": ["night", "crickets", "quiet"]},
            "晚": {"time_of_day": "evening", "keywords": ["evening", "sunset"]},
            "早": {"time_of_day": "morning", "keywords": ["morning", "birds", "dawn"]},
            "午": {"time_of_day": "noon", "keywords": ["noon", "midday"]},
            
            # 氛围
            "紧张": {"atmosphere": "tense", "keywords": ["tense", "suspense", "dramatic"]},
            "恐怖": {"atmosphere": "scary", "keywords": ["scary", "horror", "dark"]},
            "浪漫": {"atmosphere": "romantic", "keywords": ["romantic", "soft", "gentle"]},
            "战斗": {"atmosphere": "action", "keywords": ["action", "battle", "intense"]},
            "安静": {"atmosphere": "calm", "keywords": ["calm", "peaceful", "serene"]},
        }
        
        # TangoFlux提示词模板
        self.tango_templates = {
            "indoor_calm": "soft indoor ambience, gentle air conditioning hum, peaceful room tone",
            "indoor_tense": "tense indoor atmosphere, subtle creaking sounds, dramatic silence",
            "outdoor_day": "outdoor daytime ambience, gentle breeze, distant nature sounds",
            "outdoor_night": "night outdoor ambience, cricket sounds, soft wind through trees",
            "forest": "forest ambience, birds chirping, leaves rustling, natural environment",
            "city": "urban city ambience, distant traffic, urban life sounds",
            "rainy": "heavy rain falling, water drops, storm atmosphere",
            "windy": "strong wind blowing, air movement, atmospheric breeze",
            "action": "intense action atmosphere, dramatic tension, suspenseful ambience",
            "romantic": "romantic soft ambience, gentle warm atmosphere, intimate setting"
        }
    
    def analyze_audio_files(self, audio_files: List[Dict[str, Any]]) -> List[DialogueSegment]:
        """
        分析音频文件，生成对话段落时间轴
        
        Args:
            audio_files: 音频文件信息列表，包含路径和文本内容
            
        Returns:
            对话段落列表
        """
        dialogue_segments = []
        current_time = 0.0
        
        for index, audio_file in enumerate(audio_files):
            file_path = audio_file.get('file_path', '')
            text_content = audio_file.get('text_content', '')
            speaker = audio_file.get('speaker', '旁白')
            
            # 获取实际音频时长
            duration = self._get_audio_duration_safe(file_path)
            if duration is None:
                logger.warning(f"无法获取音频时长: {file_path}")
                duration = self._estimate_duration_from_text(text_content)
            
            # 提取场景关键词
            scene_keywords = self._extract_scene_keywords(text_content)
            
            segment = DialogueSegment(
                index=index,
                start_time=current_time,
                end_time=current_time + duration,
                duration=duration,
                file_path=file_path,
                text_content=text_content,
                speaker=speaker,
                scene_keywords=scene_keywords
            )
            
            dialogue_segments.append(segment)
            current_time += duration
            
            logger.info(f"段落 {index}: {duration:.2f}s, 累计: {current_time:.2f}s")
        
        return dialogue_segments
    
    def detect_scene_changes(self, dialogue_segments: List[DialogueSegment]) -> List[Dict[str, Any]]:
        """
        检测场景切换点
        
        Args:
            dialogue_segments: 对话段落列表
            
        Returns:
            场景切换信息列表
        """
        scene_changes = []
        current_scene = None
        
        for segment in dialogue_segments:
            # 分析当前段落的场景
            scene_info = self._analyze_segment_scene(segment)
            
            # 检测场景是否发生变化
            if self._is_scene_changed(current_scene, scene_info):
                scene_change = {
                    "time": segment.start_time,
                    "segment_index": segment.index,
                    "from_scene": current_scene,
                    "to_scene": scene_info,
                    "confidence": scene_info.confidence
                }
                scene_changes.append(scene_change)
                current_scene = scene_info
                
                logger.info(f"检测到场景切换 @ {segment.start_time:.2f}s: {scene_info.location}/{scene_info.atmosphere}")
        
        return scene_changes
    
    def generate_environment_tracks(self, 
                                  dialogue_segments: List[DialogueSegment],
                                  scene_changes: List[Dict[str, Any]]) -> List[EnvironmentTrack]:
        """
        生成环境音轨道
        
        Args:
            dialogue_segments: 对话段落列表
            scene_changes: 场景切换信息
            
        Returns:
            环境音轨道列表
        """
        environment_tracks = []
        
        if not scene_changes:
            # 如果没有场景切换，生成一个全程的默认环境音
            total_duration = dialogue_segments[-1].end_time if dialogue_segments else 10.0
            default_track = self._create_default_environment_track(total_duration)
            environment_tracks.append(default_track)
            return environment_tracks
        
        # 为每个场景段落生成环境音轨道
        for i, scene_change in enumerate(scene_changes):
            start_time = scene_change["time"]
            
            # 确定结束时间
            if i + 1 < len(scene_changes):
                end_time = scene_changes[i + 1]["time"]
            else:
                end_time = dialogue_segments[-1].end_time if dialogue_segments else start_time + 10.0
            
            # 生成环境音轨道
            scene_info = scene_change["to_scene"]
            track = self._create_environment_track(start_time, end_time, scene_info)
            environment_tracks.append(track)
        
        return environment_tracks
    
    def generate_timeline(self, audio_files: List[Dict[str, Any]]) -> Timeline:
        """
        生成完整的时间轴
        
        Args:
            audio_files: 音频文件信息列表
            
        Returns:
            完整时间轴对象
        """
        logger.info(f"开始生成时间轴，音频文件数: {len(audio_files)}")
        
        # 1. 分析音频文件，生成对话段落时间轴
        dialogue_segments = self.analyze_audio_files(audio_files)
        
        # 2. 检测场景切换
        scene_changes = self.detect_scene_changes(dialogue_segments)
        
        # 3. 生成环境音轨道
        environment_tracks = self.generate_environment_tracks(dialogue_segments, scene_changes)
        
        # 4. 创建完整时间轴
        total_duration = dialogue_segments[-1].end_time if dialogue_segments else 0.0
        
        timeline = Timeline(
            total_duration=total_duration,
            dialogue_segments=dialogue_segments,
            environment_tracks=environment_tracks,
            scene_changes=scene_changes
        )
        
        logger.info(f"时间轴生成完成: 总时长 {total_duration:.2f}s, "
                   f"对话段落 {len(dialogue_segments)}个, "
                   f"环境音轨道 {len(environment_tracks)}个, "
                   f"场景切换 {len(scene_changes)}次")
        
        return timeline
    
    def _get_audio_duration_safe(self, file_path: str) -> Optional[float]:
        """安全获取音频时长"""
        try:
            if not file_path or not os.path.exists(file_path):
                return None
            return get_audio_duration(file_path)
        except Exception as e:
            logger.warning(f"获取音频时长失败 {file_path}: {e}")
            return None
    
    def _estimate_duration_from_text(self, text: str) -> float:
        """根据文本长度估算音频时长"""
        # 简单的估算：中文约4-5字/秒，英文约2-3词/秒
        text_length = len(text.strip())
        estimated_duration = max(1.0, text_length / 4.5)  # 保守估计
        return min(estimated_duration, 30.0)  # 限制最大30秒
    
    def _extract_scene_keywords(self, text: str) -> List[str]:
        """从文本中提取场景关键词"""
        keywords = []
        for keyword, scene_data in self.scene_keywords_map.items():
            if keyword in text:
                keywords.extend(scene_data.get("keywords", []))
        return list(set(keywords))  # 去重
    
    def _analyze_segment_scene(self, segment: DialogueSegment) -> SceneInfo:
        """分析段落场景信息"""
        scene_info = SceneInfo(keywords=segment.scene_keywords)
        
        # 基于关键词分析场景属性
        text = segment.text_content.lower()
        
        for keyword, scene_data in self.scene_keywords_map.items():
            if keyword in segment.text_content:
                if "location" in scene_data:
                    scene_info.location = scene_data["location"]
                if "weather" in scene_data:
                    scene_info.weather = scene_data["weather"]
                if "time_of_day" in scene_data:
                    scene_info.time_of_day = scene_data["time_of_day"]
                if "atmosphere" in scene_data:
                    scene_info.atmosphere = scene_data["atmosphere"]
                
                scene_info.confidence = min(scene_info.confidence + 0.2, 1.0)
        
        return scene_info
    
    def _is_scene_changed(self, current_scene: Optional[SceneInfo], new_scene: SceneInfo) -> bool:
        """判断场景是否发生变化"""
        if current_scene is None:
            return True
        
        # 比较主要属性
        if (current_scene.location != new_scene.location or
            current_scene.weather != new_scene.weather or
            current_scene.atmosphere != new_scene.atmosphere):
            return True
        
        return False
    
    def _create_environment_track(self, start_time: float, end_time: float, scene_info: SceneInfo) -> EnvironmentTrack:
        """创建环境音轨道"""
        duration = end_time - start_time
        
        # 构建TangoFlux提示词
        tango_prompt = self._build_tango_prompt(scene_info)
        
        # 生成场景描述
        scene_prompt = f"{scene_info.location} {scene_info.weather} {scene_info.atmosphere}"
        
        # 根据场景调整音量
        volume_level = self._get_volume_for_scene(scene_info)
        
        return EnvironmentTrack(
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            scene_prompt=scene_prompt,
            tango_prompt=tango_prompt,
            volume_level=volume_level
        )
    
    def _create_default_environment_track(self, total_duration: float) -> EnvironmentTrack:
        """创建默认环境音轨道"""
        default_scene = SceneInfo()
        return self._create_environment_track(0.0, total_duration, default_scene)
    
    def _build_tango_prompt(self, scene_info: SceneInfo) -> str:
        """构建TangoFlux提示词"""
        # 选择合适的模板
        template_key = f"{scene_info.location}_{scene_info.atmosphere}"
        
        if template_key in self.tango_templates:
            base_prompt = self.tango_templates[template_key]
        else:
            # 组合生成
            location_template = self.tango_templates.get(scene_info.location, "ambient background")
            atmosphere_template = self.tango_templates.get(scene_info.atmosphere, "peaceful")
            base_prompt = f"{location_template}, {atmosphere_template}"
        
        # 添加天气效果
        if scene_info.weather != "clear":
            weather_effect = self.tango_templates.get(scene_info.weather, "")
            if weather_effect:
                base_prompt = f"{weather_effect}, {base_prompt}"
        
        # 添加质量描述
        return f"{base_prompt}, cinematic quality, high fidelity audio"
    
    def _get_volume_for_scene(self, scene_info: SceneInfo) -> float:
        """根据场景确定音量级别"""
        base_volume = 0.3
        
        # 根据氛围调整音量
        atmosphere_volume_map = {
            "calm": 0.25,
            "tense": 0.4,
            "action": 0.5,
            "romantic": 0.2,
            "scary": 0.45
        }
        
        return atmosphere_volume_map.get(scene_info.atmosphere, base_volume)
    
    def export_timeline_data(self, timeline: Timeline) -> Dict[str, Any]:
        """导出时间轴数据为字典格式"""
        return {
            "total_duration": timeline.total_duration,
            "dialogue_segments": [
                {
                    "index": seg.index,
                    "start_time": seg.start_time,
                    "end_time": seg.end_time,
                    "duration": seg.duration,
                    "file_path": seg.file_path,
                    "text_content": seg.text_content,
                    "speaker": seg.speaker,
                    "scene_keywords": seg.scene_keywords
                }
                for seg in timeline.dialogue_segments
            ],
            "environment_tracks": [
                {
                    "start_time": track.start_time,
                    "end_time": track.end_time,
                    "duration": track.duration,
                    "scene_prompt": track.scene_prompt,
                    "tango_prompt": track.tango_prompt,
                    "volume_level": track.volume_level,
                    "fade_in": track.fade_in,
                    "fade_out": track.fade_out,
                    "priority": track.priority
                }
                for track in timeline.environment_tracks
            ],
            "scene_changes": timeline.scene_changes
        }


# 全局实例
timeline_generator = SequentialTimelineGenerator()