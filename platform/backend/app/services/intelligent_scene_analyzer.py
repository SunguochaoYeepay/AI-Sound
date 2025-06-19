#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能场景分析服务
提供独立的场景分析、缓存匹配和批量生成功能
"""

import os
import hashlib
import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.database import SessionLocal
from app.models.environment_sound import EnvironmentSound, EnvironmentSoundCategory, EnvironmentSoundTag
from app.services.sequential_timeline_generator import SceneInfo

logger = logging.getLogger(__name__)

@dataclass
class SceneAnalysisResult:
    """场景分析结果"""
    text_hash: str
    analyzed_scenes: List[SceneInfo]
    confidence_score: float
    processing_time: float
    total_scenes: int
    unique_locations: List[str]
    unique_atmospheres: List[str]
    recommended_durations: List[float]  # 推荐的环境音时长

@dataclass
class SceneMatchResult:
    """场景匹配结果"""
    environment_sound_id: int
    scene_info: SceneInfo
    match_score: float
    is_exact_match: bool
    recommended_usage: str

@dataclass
class BatchGenerationPlan:
    """批量生成计划"""
    total_scenes: int
    generation_queue: List[Dict[str, Any]]
    estimated_time: float
    estimated_cost: float

class IntelligentSceneAnalyzer:
    """智能场景分析器"""
    
    def __init__(self):
        # 场景关键词增强映射（从timeline_generator继承并扩展）
        self.scene_keywords_map = {
            # 地点类别
            "房间": {"location": "indoor", "keywords": ["room", "indoor", "house"]},
            "室内": {"location": "indoor", "keywords": ["indoor", "room", "building"]},
            "户外": {"location": "outdoor", "keywords": ["outdoor", "nature", "open"]},
            "森林": {"location": "forest", "keywords": ["forest", "trees", "nature", "woods"]},
            "城市": {"location": "city", "keywords": ["city", "urban", "traffic", "street"]},
            "海边": {"location": "beach", "keywords": ["ocean", "waves", "beach", "seaside"]},
            "大海": {"location": "beach", "keywords": ["ocean", "waves", "sea", "water"]},
            "海": {"location": "beach", "keywords": ["ocean", "waves", "sea", "water"]},
            "山": {"location": "mountain", "keywords": ["mountain", "wind", "echo", "highland"]},
            "街道": {"location": "street", "keywords": ["street", "traffic", "footsteps", "road"]},
            "咖啡厅": {"location": "cafe", "keywords": ["cafe", "coffee", "chatter", "urban"]},
            "公园": {"location": "park", "keywords": ["park", "nature", "outdoor", "peaceful"]},
            "学校": {"location": "school", "keywords": ["school", "classroom", "indoor", "learning"]},
            "医院": {"location": "hospital", "keywords": ["hospital", "medical", "indoor", "quiet"]},
            "商场": {"location": "mall", "keywords": ["mall", "shopping", "indoor", "crowd"]},
            "地铁": {"location": "subway", "keywords": ["subway", "train", "underground", "transit"]},
            
            # 天气类别
            "雨": {"weather": "rainy", "keywords": ["rain", "water", "drops", "wet"]},
            "雷": {"weather": "stormy", "keywords": ["thunder", "storm", "lightning", "dramatic"]},
            "风": {"weather": "windy", "keywords": ["wind", "breeze", "air", "movement"]},
            "雪": {"weather": "snowy", "keywords": ["snow", "winter", "cold", "frozen"]},
            "晴": {"weather": "sunny", "keywords": ["sunny", "bright", "clear", "warm"]},
            "阴": {"weather": "cloudy", "keywords": ["cloudy", "overcast", "gray", "muted"]},
            "雾": {"weather": "foggy", "keywords": ["fog", "mist", "mysterious", "unclear"]},
            
            # 时间类别
            "夜": {"time_of_day": "night", "keywords": ["night", "crickets", "quiet", "dark"]},
            "晚": {"time_of_day": "evening", "keywords": ["evening", "sunset", "dusk", "twilight"]},
            "早": {"time_of_day": "morning", "keywords": ["morning", "birds", "dawn", "fresh"]},
            "午": {"time_of_day": "noon", "keywords": ["noon", "midday", "bright", "active"]},
            "深夜": {"time_of_day": "midnight", "keywords": ["midnight", "late", "quiet", "mysterious"]},
            
            # 氛围类别
            "紧张": {"atmosphere": "tense", "keywords": ["tense", "suspense", "dramatic", "intense"]},
            "恐怖": {"atmosphere": "scary", "keywords": ["scary", "horror", "dark", "frightening"]},
            "浪漫": {"atmosphere": "romantic", "keywords": ["romantic", "soft", "gentle", "intimate"]},
            "战斗": {"atmosphere": "action", "keywords": ["action", "battle", "intense", "fighting"]},
            "安静": {"atmosphere": "calm", "keywords": ["calm", "peaceful", "serene", "tranquil"]},
            "悲伤": {"atmosphere": "sad", "keywords": ["sad", "melancholy", "somber", "emotional"]},
            "欢乐": {"atmosphere": "joyful", "keywords": ["joyful", "happy", "cheerful", "celebratory"]},
            "神秘": {"atmosphere": "mysterious", "keywords": ["mysterious", "enigmatic", "unknown", "puzzling"]},
            "轻松": {"atmosphere": "relaxed", "keywords": ["relaxed", "casual", "easy", "comfortable"]},
            "激动": {"atmosphere": "excited", "keywords": ["excited", "energetic", "dynamic", "thrilling"]},
        }
        
        # 常用场景预设
        self.common_scenes = [
            # 室内场景
            {"location": "indoor", "atmosphere": "calm", "weather": "clear", "time_of_day": "day", "duration": 15.0},
            {"location": "indoor", "atmosphere": "tense", "weather": "clear", "time_of_day": "night", "duration": 10.0},
            {"location": "indoor", "atmosphere": "romantic", "weather": "clear", "time_of_day": "evening", "duration": 20.0},
            
            # 户外场景
            {"location": "outdoor", "atmosphere": "calm", "weather": "sunny", "time_of_day": "day", "duration": 15.0},
            {"location": "outdoor", "atmosphere": "tense", "weather": "stormy", "time_of_day": "night", "duration": 12.0},
            
            # 森林场景
            {"location": "forest", "atmosphere": "peaceful", "weather": "clear", "time_of_day": "morning", "duration": 18.0},
            {"location": "forest", "atmosphere": "mysterious", "weather": "foggy", "time_of_day": "night", "duration": 15.0},
            
            # 城市场景
            {"location": "city", "atmosphere": "busy", "weather": "clear", "time_of_day": "day", "duration": 12.0},
            {"location": "city", "atmosphere": "tense", "weather": "rainy", "time_of_day": "night", "duration": 10.0},
            
            # 雨天场景
            {"location": "outdoor", "atmosphere": "calm", "weather": "rainy", "time_of_day": "any", "duration": 20.0},
            {"location": "indoor", "atmosphere": "cozy", "weather": "rainy", "time_of_day": "evening", "duration": 25.0},
        ]
        
        # 场景相似度权重
        self.similarity_weights = {
            "location": 0.4,      # 地点权重40%
            "atmosphere": 0.35,   # 氛围权重35%
            "weather": 0.20,      # 天气权重20%
            "time_of_day": 0.05   # 时间权重5%
        }
        
        # 相似场景映射
        self.similar_locations = {
            "forest": ["outdoor", "nature", "mountain", "park"],
            "indoor": ["room", "house", "building", "cafe", "school"],
            "city": ["urban", "street", "downtown", "mall"],
            "beach": ["ocean", "seaside", "coastal"],
            "mountain": ["highland", "hill", "outdoor", "nature"]
        }
        
        self.similar_atmospheres = {
            "tense": ["scary", "suspense", "dramatic", "intense"],
            "calm": ["peaceful", "relaxing", "serene", "tranquil"],
            "romantic": ["gentle", "soft", "intimate", "loving"],
            "action": ["intense", "dynamic", "energetic", "thrilling"],
            "mysterious": ["enigmatic", "unknown", "puzzling", "dark"]
        }
    
    async def analyze_text_scenes(self, text: str, user_id: Optional[int] = None) -> SceneAnalysisResult:
        """
        分析文本中的场景信息
        
        Args:
            text: 要分析的文本
            user_id: 用户ID（可选，用于个性化分析）
            
        Returns:
            场景分析结果
        """
        start_time = datetime.now()
        
        # 生成文本哈希用于缓存
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        
        # 检查缓存
        cached_result = await self._get_cached_analysis(text_hash)
        if cached_result:
            logger.info(f"使用缓存的场景分析结果: {text_hash}")
            return cached_result
        
        # 分析文本场景
        scenes = []
        sentences = self._split_text_into_sentences(text)
        
        for sentence in sentences:
            scene_info = self._analyze_sentence_scene(sentence)
            if scene_info.confidence >= 0.3:  # 置信度阈值
                scenes.append(scene_info)
        
        # 合并相似场景
        merged_scenes = self._merge_similar_scenes(scenes)
        
        # 生成推荐时长
        recommended_durations = self._suggest_durations(merged_scenes, len(text))
        
        # 计算总体置信度
        confidence_score = sum(s.confidence for s in merged_scenes) / len(merged_scenes) if merged_scenes else 0.0
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        result = SceneAnalysisResult(
            text_hash=text_hash,
            analyzed_scenes=merged_scenes,
            confidence_score=confidence_score,
            processing_time=processing_time,
            total_scenes=len(merged_scenes),
            unique_locations=list(set(s.location for s in merged_scenes)),
            unique_atmospheres=list(set(s.atmosphere for s in merged_scenes)),
            recommended_durations=recommended_durations
        )
        
        # 缓存结果
        await self._cache_analysis_result(result)
        
        logger.info(f"文本场景分析完成: {len(merged_scenes)}个场景, 置信度: {confidence_score:.2f}")
        return result
    
    def find_matching_environment_sounds(self, scene_info: SceneInfo, duration: float = None, 
                                       tolerance: float = 0.2) -> List[SceneMatchResult]:
        """
        为场景信息匹配现有的环境音
        
        Args:
            scene_info: 场景信息
            duration: 目标时长（可选）
            tolerance: 时长容差（20%）
            
        Returns:
            匹配结果列表
        """
        with SessionLocal() as db:
            # 查询所有环境音
            query = db.query(EnvironmentSound).filter(
                EnvironmentSound.generation_status == 'completed'
            )
            
            environment_sounds = query.all()
            matches = []
            
            for sound in environment_sounds:
                # 计算场景匹配度
                match_score = self._calculate_scene_similarity(
                    scene_info, 
                    self._extract_scene_from_sound(sound)
                )
                
                # 检查时长匹配
                duration_match = True
                if duration:
                    duration_diff = abs(sound.duration - duration) / duration
                    duration_match = duration_diff <= tolerance
                
                if match_score > 0.6 and duration_match:  # 匹配阈值
                    match_result = SceneMatchResult(
                        environment_sound_id=sound.id,
                        scene_info=scene_info,
                        match_score=match_score,
                        is_exact_match=match_score > 0.9,
                        recommended_usage=self._get_usage_recommendation(match_score)
                    )
                    matches.append(match_result)
            
            # 按匹配度排序
            matches.sort(key=lambda x: x.match_score, reverse=True)
            
            logger.info(f"为场景 {scene_info.location}/{scene_info.atmosphere} 找到 {len(matches)} 个匹配的环境音")
            return matches[:10]  # 返回前10个最佳匹配
    
    async def generate_batch_plan(self, target_scenes: List[SceneInfo] = None) -> BatchGenerationPlan:
        """
        生成批量生成计划
        
        Args:
            target_scenes: 目标场景列表，为空则使用常用场景
            
        Returns:
            批量生成计划
        """
        if not target_scenes:
            target_scenes = [self._dict_to_scene_info(scene) for scene in self.common_scenes]
        
        generation_queue = []
        total_time = 0.0
        
        with SessionLocal() as db:
            for scene in target_scenes:
                # 检查是否已有相似的环境音
                existing_matches = self.find_matching_environment_sounds(scene)
                
                if not existing_matches or all(m.match_score < 0.8 for m in existing_matches):
                    # 需要生成新的环境音
                    prompt = self._build_generation_prompt(scene)
                    duration = scene.duration if hasattr(scene, 'duration') else 15.0
                    
                    generation_item = {
                        "scene_info": asdict(scene),
                        "prompt": prompt,
                        "duration": duration,
                        "priority": self._get_generation_priority(scene),
                        "estimated_time": duration * 0.5  # 估算生成时间
                    }
                    
                    generation_queue.append(generation_item)
                    total_time += generation_item["estimated_time"]
        
        # 按优先级排序
        generation_queue.sort(key=lambda x: x["priority"], reverse=True)
        
        plan = BatchGenerationPlan(
            total_scenes=len(generation_queue),
            generation_queue=generation_queue,
            estimated_time=total_time,
            estimated_cost=len(generation_queue) * 0.1  # 假设每个场景成本0.1元
        )
        
        logger.info(f"生成批量计划: {len(generation_queue)}个场景, 预计{total_time:.1f}秒")
        return plan
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with SessionLocal() as db:
            # 环境音统计
            total_sounds = db.query(EnvironmentSound).count()
            completed_sounds = db.query(EnvironmentSound).filter(
                EnvironmentSound.generation_status == 'completed'
            ).count()
            
            # 场景标签统计
            scene_tagged_sounds = db.query(EnvironmentSound).filter(
                EnvironmentSound.metadata.isnot(None)
            ).count()
            
            # 使用频率统计
            popular_scenes = db.query(
                EnvironmentSound.metadata,
                func.count(EnvironmentSound.id).label('usage_count')
            ).filter(
                EnvironmentSound.play_count > 0
            ).group_by(EnvironmentSound.metadata).limit(10).all()
            
            return {
                "total_environment_sounds": total_sounds,
                "completed_sounds": completed_sounds,
                "scene_tagged_sounds": scene_tagged_sounds,
                "cache_hit_rate": scene_tagged_sounds / total_sounds if total_sounds > 0 else 0,
                "popular_scenes": [
                    {"scene": scene[0], "usage_count": scene[1]} 
                    for scene in popular_scenes if scene[0]
                ],
                "last_updated": datetime.now().isoformat()
            }
    
    # 私有方法
    def _split_text_into_sentences(self, text: str) -> List[str]:
        """将文本分割为句子"""
        import re
        sentences = re.split(r'[。！？.!?]', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _analyze_sentence_scene(self, sentence: str) -> SceneInfo:
        """分析单句的场景信息"""
        scene_info = SceneInfo()
        confidence = 0.0
        
        # 基于关键词分析
        for keyword, scene_data in self.scene_keywords_map.items():
            if keyword in sentence:
                if "location" in scene_data:
                    scene_info.location = scene_data["location"]
                    confidence += 0.3
                if "weather" in scene_data:
                    scene_info.weather = scene_data["weather"] 
                    confidence += 0.25
                if "time_of_day" in scene_data:
                    scene_info.time_of_day = scene_data["time_of_day"]
                    confidence += 0.15
                if "atmosphere" in scene_data:
                    scene_info.atmosphere = scene_data["atmosphere"]
                    confidence += 0.3
        
        # 更新关键词
        scene_info.keywords = [kw for kw, data in self.scene_keywords_map.items() if kw in sentence]
        scene_info.confidence = min(confidence, 1.0)
        
        return scene_info
    
    def _merge_similar_scenes(self, scenes: List[SceneInfo]) -> List[SceneInfo]:
        """合并相似的场景"""
        if not scenes:
            return []
        
        merged = []
        used_indices = set()
        
        for i, scene1 in enumerate(scenes):
            if i in used_indices:
                continue
                
            # 寻找相似场景进行合并
            similar_scenes = [scene1]
            used_indices.add(i)
            
            for j, scene2 in enumerate(scenes[i+1:], i+1):
                if j in used_indices:
                    continue
                    
                similarity = self._calculate_scene_similarity(scene1, scene2)
                if similarity > 0.8:  # 高相似度场景合并
                    similar_scenes.append(scene2)
                    used_indices.add(j)
            
            # 合并场景属性
            merged_scene = self._merge_scene_attributes(similar_scenes)
            merged.append(merged_scene)
        
        return merged
    
    def _merge_scene_attributes(self, scenes: List[SceneInfo]) -> SceneInfo:
        """合并场景属性"""
        if len(scenes) == 1:
            return scenes[0]
        
        # 取置信度最高的作为基础
        base_scene = max(scenes, key=lambda s: s.confidence)
        
        # 合并关键词
        all_keywords = []
        for scene in scenes:
            if scene.keywords:
                all_keywords.extend(scene.keywords)
        
        base_scene.keywords = list(set(all_keywords))
        base_scene.confidence = sum(s.confidence for s in scenes) / len(scenes)
        
        return base_scene
    
    def _calculate_scene_similarity(self, scene1: SceneInfo, scene2: SceneInfo) -> float:
        """计算两个场景的相似度"""
        similarity = 0.0
        
        # 地点匹配
        if scene1.location == scene2.location:
            similarity += self.similarity_weights["location"]
        elif scene1.location in self.similar_locations.get(scene2.location, []):
            similarity += self.similarity_weights["location"] * 0.5
        
        # 氛围匹配  
        if scene1.atmosphere == scene2.atmosphere:
            similarity += self.similarity_weights["atmosphere"]
        elif scene1.atmosphere in self.similar_atmospheres.get(scene2.atmosphere, []):
            similarity += self.similarity_weights["atmosphere"] * 0.5
        
        # 天气匹配
        if scene1.weather == scene2.weather:
            similarity += self.similarity_weights["weather"]
        
        # 时间匹配
        if scene1.time_of_day == scene2.time_of_day:
            similarity += self.similarity_weights["time_of_day"]
        
        return similarity
    
    def _suggest_durations(self, scenes: List[SceneInfo], text_length: int) -> List[float]:
        """建议环境音时长"""
        base_duration = min(max(text_length / 100, 10.0), 30.0)  # 基础时长10-30秒
        
        durations = []
        for scene in scenes:
            # 根据场景类型调整时长
            if scene.atmosphere == "action":
                duration = base_duration * 0.7  # 动作场景时长短一些
            elif scene.atmosphere in ["calm", "romantic"]:
                duration = base_duration * 1.3  # 平静/浪漫场景时长长一些
            else:
                duration = base_duration
            
            durations.append(round(duration, 1))
        
        return durations
    
    def _extract_scene_from_sound(self, sound: EnvironmentSound) -> SceneInfo:
        """从环境音中提取场景信息"""
        scene_info = SceneInfo()
        
        # 从metadata中提取
        if sound.metadata and isinstance(sound.metadata, dict):
            scene_data = sound.metadata.get('scene_info', {})
            scene_info.location = scene_data.get('location', 'unknown')
            scene_info.atmosphere = scene_data.get('atmosphere', 'neutral')
            scene_info.weather = scene_data.get('weather', 'clear')
            scene_info.time_of_day = scene_data.get('time_of_day', 'day')
            scene_info.confidence = scene_data.get('confidence', 0.5)
        else:
            # 从prompt中推断
            prompt = sound.prompt.lower() if sound.prompt else ""
            scene_info = self._analyze_sentence_scene(prompt)
        
        return scene_info
    
    def _build_generation_prompt(self, scene: SceneInfo) -> str:
        """构建TangoFlux生成提示词"""
        prompt_parts = []
        
        # 基础环境描述
        if scene.location == "forest":
            prompt_parts.append("forest ambience with birds chirping and leaves rustling")
        elif scene.location == "city":
            prompt_parts.append("urban city ambience with distant traffic")
        elif scene.location == "indoor":
            prompt_parts.append("indoor room tone with subtle background noise")
        elif scene.location == "beach":
            prompt_parts.append("ocean waves crashing on shore")
        else:
            prompt_parts.append(f"{scene.location} environmental ambience")
        
        # 天气效果
        if scene.weather == "rainy":
            prompt_parts.append("with gentle rain falling")
        elif scene.weather == "windy":
            prompt_parts.append("with wind blowing")
        elif scene.weather == "stormy":
            prompt_parts.append("with storm and thunder")
        
        # 氛围调节
        if scene.atmosphere == "tense":
            prompt_parts.append("dramatic and suspenseful atmosphere")
        elif scene.atmosphere == "calm":
            prompt_parts.append("peaceful and relaxing mood")
        elif scene.atmosphere == "romantic":
            prompt_parts.append("soft and gentle ambience")
        elif scene.atmosphere == "action":
            prompt_parts.append("intense and energetic atmosphere")
        
        # 时间调节
        if scene.time_of_day == "night":
            prompt_parts.append("nighttime ambience with crickets")
        elif scene.time_of_day == "morning":
            prompt_parts.append("early morning with birds")
        
        return ", ".join(prompt_parts)
    
    def _get_generation_priority(self, scene: SceneInfo) -> int:
        """获取生成优先级"""
        priority = 1
        
        # 常用场景优先级高
        if scene.location in ["indoor", "outdoor", "forest"]:
            priority += 2
        
        if scene.atmosphere in ["calm", "tense"]:
            priority += 2
        
        if scene.weather in ["rainy", "clear"]:
            priority += 1
        
        return priority
    
    def _get_usage_recommendation(self, match_score: float) -> str:
        """获取使用建议"""
        if match_score > 0.95:
            return "perfect_match"
        elif match_score > 0.8:
            return "excellent_match"
        elif match_score > 0.7:
            return "good_match"
        else:
            return "acceptable_match"
    
    def _dict_to_scene_info(self, scene_dict: Dict[str, Any]) -> SceneInfo:
        """字典转场景信息"""
        scene = SceneInfo()
        scene.location = scene_dict.get("location", "indoor")
        scene.atmosphere = scene_dict.get("atmosphere", "calm")
        scene.weather = scene_dict.get("weather", "clear")
        scene.time_of_day = scene_dict.get("time_of_day", "day")
        scene.confidence = scene_dict.get("confidence", 0.8)
        
        # 添加时长属性（扩展SceneInfo）
        if hasattr(scene, 'duration'):
            scene.duration = scene_dict.get("duration", 15.0)
        else:
            # 动态添加属性
            setattr(scene, 'duration', scene_dict.get("duration", 15.0))
        
        return scene
    
    async def _get_cached_analysis(self, text_hash: str) -> Optional[SceneAnalysisResult]:
        """获取缓存的分析结果"""
        # TODO: 实现Redis缓存
        return None
    
    async def _cache_analysis_result(self, result: SceneAnalysisResult):
        """缓存分析结果"""
        # TODO: 实现Redis缓存
        pass


# 全局实例
intelligent_scene_analyzer = IntelligentSceneAnalyzer()