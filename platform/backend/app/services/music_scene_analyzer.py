"""
音乐场景分析服务
从复杂的SongGeneration服务中分离出的专门模块
负责分析文本内容，推荐适合的音乐风格和参数
"""

import logging
import re
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MusicSceneAnalysis:
    """音乐场景分析结果"""
    scene_type: str  # 场景类型：战斗、浪漫、神秘、平静、悲伤等
    emotion_tone: str  # 情感基调
    intensity: float  # 强度等级 (0.0-1.0)
    keywords: List[str]  # 关键词
    recommended_style: str  # 推荐音乐风格
    recommended_duration: int  # 推荐时长
    style_confidence: float  # 推荐置信度

class MusicSceneAnalyzer:
    """
    音乐场景分析器
    基于规则和关键词的智能分析
    """
    
    def __init__(self):
        self.scene_keywords = {
            "battle": {
                "keywords": ["战斗", "打斗", "厮杀", "战争", "冲突", "激战", "血战", "决战", "搏斗", "格斗"],
                "style": "epic",
                "intensity": 0.8,
                "duration": 45
            },
            "romance": {
                "keywords": ["爱情", "浪漫", "恋爱", "温柔", "亲吻", "拥抱", "甜蜜", "深情", "柔情", "爱意"],
                "style": "romantic",
                "intensity": 0.3,
                "duration": 60
            },
            "mystery": {
                "keywords": ["神秘", "诡异", "阴森", "恐怖", "诡谲", "奇异", "蹊跷", "古怪", "离奇", "悬疑"],
                "style": "dark",
                "intensity": 0.6,
                "duration": 40
            },
            "peaceful": {
                "keywords": ["平静", "安详", "宁静", "祥和", "静谧", "恬静", "悠闲", "舒缓", "轻松", "温馨"],
                "style": "ambient",
                "intensity": 0.2,
                "duration": 90
            },
            "sad": {
                "keywords": ["悲伤", "哀愁", "忧郁", "凄凉", "哀伤", "痛苦", "伤心", "沉重", "悲哀", "孤独"],
                "style": "melancholy",
                "intensity": 0.4,
                "duration": 70
            },
            "adventure": {
                "keywords": ["冒险", "探索", "旅程", "历险", "奇遇", "征途", "远行", "踏上", "启程", "寻找"],
                "style": "adventure",
                "intensity": 0.5,
                "duration": 50
            },
            "celebration": {
                "keywords": ["庆祝", "欢乐", "喜悦", "狂欢", "盛典", "节日", "欢庆", "喜庆", "快乐", "兴奋"],
                "style": "upbeat",
                "intensity": 0.7,
                "duration": 40
            }
        }
        
        # 风格映射
        self.style_mapping = {
            "epic": "epic",
            "romantic": "pop",
            "dark": "dark",
            "ambient": "ambient",
            "melancholy": "sad",
            "adventure": "cinematic",
            "upbeat": "electronic"
        }
        
        logger.info("音乐场景分析器初始化完成")
    
    def analyze_content(self, content: str) -> MusicSceneAnalysis:
        """
        分析文本内容，返回音乐场景分析结果
        
        Args:
            content: 要分析的文本内容
            
        Returns:
            音乐场景分析结果
        """
        try:
            # 预处理文本
            content_lower = content.lower()
            
            # 统计各场景类型的关键词匹配数
            scene_scores = {}
            matched_keywords = []
            
            for scene_type, scene_info in self.scene_keywords.items():
                score = 0
                scene_keywords = []
                
                for keyword in scene_info["keywords"]:
                    count = content_lower.count(keyword)
                    if count > 0:
                        score += count
                        scene_keywords.extend([keyword] * count)
                
                if score > 0:
                    scene_scores[scene_type] = {
                        "score": score,
                        "keywords": scene_keywords,
                        "info": scene_info
                    }
            
            # 确定主要场景类型
            if not scene_scores:
                # 默认场景：平静
                primary_scene = "peaceful"
                primary_info = self.scene_keywords["peaceful"]
                matched_keywords = []
                confidence = 0.3
            else:
                # 选择得分最高的场景
                primary_scene = max(scene_scores.keys(), key=lambda x: scene_scores[x]["score"])
                primary_info = scene_scores[primary_scene]["info"]
                matched_keywords = scene_scores[primary_scene]["keywords"]
                
                # 计算置信度
                total_words = len(content.split())
                keyword_ratio = len(matched_keywords) / max(total_words, 1)
                confidence = min(keyword_ratio * 5, 1.0)  # 归一化到0-1
            
            # 分析情感基调
            emotion_tone = self._analyze_emotion(content, primary_scene)
            
            # 调整参数
            intensity = primary_info["intensity"]
            if confidence > 0.7:
                intensity = min(intensity + 0.1, 1.0)  # 高置信度增强强度
            elif confidence < 0.3:
                intensity = max(intensity - 0.1, 0.1)  # 低置信度降低强度
            
            # 推荐时长调整
            content_length = len(content)
            base_duration = primary_info["duration"]
            
            if content_length < 100:
                recommended_duration = max(base_duration - 15, 20)
            elif content_length > 500:
                recommended_duration = min(base_duration + 20, 120)
            else:
                recommended_duration = base_duration
            
            # 推荐风格
            recommended_style = self.style_mapping.get(primary_info["style"], "pop")
            
            result = MusicSceneAnalysis(
                scene_type=primary_scene,
                emotion_tone=emotion_tone,
                intensity=intensity,
                keywords=list(set(matched_keywords)),  # 去重
                recommended_style=recommended_style,
                recommended_duration=recommended_duration,
                style_confidence=confidence
            )
            
            logger.info(f"场景分析完成: {primary_scene}({confidence:.2f}) -> {recommended_style}")
            return result
            
        except Exception as e:
            logger.error(f"场景分析失败: {e}")
            # 返回默认分析结果
            return MusicSceneAnalysis(
                scene_type="peaceful",
                emotion_tone="neutral",
                intensity=0.3,
                keywords=[],
                recommended_style="pop",
                recommended_duration=30,
                style_confidence=0.1
            )
    
    def _analyze_emotion(self, content: str, scene_type: str) -> str:
        """分析情感基调"""
        positive_words = ["开心", "高兴", "喜悦", "兴奋", "愉快", "快乐", "幸福", "美好"]
        negative_words = ["悲伤", "痛苦", "难过", "失望", "绝望", "沮丧", "忧愁", "哀伤"]
        intense_words = ["激烈", "强烈", "猛烈", "剧烈", "凶猛", "狂暴", "疯狂", "暴躁"]
        
        content_lower = content.lower()
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        intense_count = sum(1 for word in intense_words if word in content_lower)
        
        if intense_count > 2:
            return "intense"
        elif positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def get_supported_scenes(self) -> List[str]:
        """获取支持的场景类型列表"""
        return list(self.scene_keywords.keys())
    
    def get_style_recommendations(self, scene_type: str) -> List[Dict]:
        """获取指定场景的风格推荐"""
        if scene_type not in self.scene_keywords:
            return []
        
        scene_info = self.scene_keywords[scene_type]
        primary_style = self.style_mapping.get(scene_info["style"], "pop")
        
        return [
            {
                "style": primary_style,
                "confidence": 0.8,
                "description": f"适合{scene_type}场景的主要风格"
            },
            {
                "style": "pop",
                "confidence": 0.5,
                "description": "通用流行风格"
            }
        ]

# 全局分析器实例
_scene_analyzer = None

def get_music_scene_analyzer() -> MusicSceneAnalyzer:
    """获取音乐场景分析器实例（单例模式）"""
    global _scene_analyzer
    if _scene_analyzer is None:
        _scene_analyzer = MusicSceneAnalyzer()
    return _scene_analyzer 