"""
音乐场景分析服务 - LLM优化版本
从复杂的SongGeneration服务中分离出的专门模块
负责分析文本内容，推荐适合的音乐风格和参数
"""

import logging
import re
import json
from typing import Dict, List, Optional
from dataclasses import dataclass

from app.services.storyboard_analysis.llm_client import LLMClient
from app.utils.llm_config_loader import llm_config_loader

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
    音乐场景分析器 - LLM优化版本
    基于LLM智能分析的场景理解和音乐推荐
    """
    
    def __init__(self):
        # 初始化LLM客户端
        self.llm_config = llm_config_loader.get_config()
        self.llm = LLMClient(
            model=self.llm_config["model"], 
            base_url=self.llm_config["base_url"]
        )
        self.llm.timeout = self.llm_config["timeout"]
        
        # 保留基础的关键词映射作为后备方案
        self.BASIC_SCENE_KEYWORDS = {
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
        
        # 缓存机制
        self.analysis_cache = {}
        self.cache_max_size = 500
        
        logger.info("音乐场景分析器(LLM优化版)初始化完成")
    
    async def analyze_content(self, content: str) -> MusicSceneAnalysis:
        """
        分析文本内容，返回音乐场景分析结果 - LLM智能分析版本
        
        Args:
            content: 要分析的文本内容
            
        Returns:
            音乐场景分析结果
        """
        try:
            # 检查缓存
            cache_key = f"music_analysis_{hash(content)}"
            if cache_key in self.analysis_cache:
                logger.debug(f"[MUSIC_ANALYSIS] 缓存命中: {cache_key}")
                return self.analysis_cache[cache_key]
            
            # 使用LLM进行智能分析
            llm_result = await self._analyze_with_llm(content)
            
            # 缓存结果
            if len(self.analysis_cache) < self.cache_max_size:
                self.analysis_cache[cache_key] = llm_result
            
            logger.info(f"[MUSIC_ANALYSIS] LLM分析完成: {llm_result.scene_type}({llm_result.style_confidence:.2f}) -> {llm_result.recommended_style}")
            return llm_result
            
        except Exception as e:
            logger.error(f"[MUSIC_ANALYSIS] LLM分析失败: {e}")
            # 降级到基础分析
            return self._analyze_with_basic_rules(content)
    
    async def _analyze_with_llm(self, content: str) -> MusicSceneAnalysis:
        """使用LLM进行智能音乐场景分析"""
        try:
            # 构建LLM提示词
            prompt = f"""你是一个专业的音乐场景分析师。请分析以下文本内容，推荐合适的背景音乐风格和参数。

文本内容：
"{content}"

请从以下维度进行分析：
1. 场景类型识别：战斗、浪漫、神秘、平静、悲伤、冒险、庆祝等
2. 情感基调分析：积极、消极、中性、紧张、舒缓等
3. 强度等级评估：0.0-1.0之间的数值
4. 音乐风格推荐：epic、romantic、dark、ambient、melancholy、adventure、upbeat等
5. 推荐时长：根据内容长度和场景类型推荐合适的音乐时长
6. 置信度评估：对分析结果的信心程度

请返回JSON格式：
{{
    "scene_type": "场景类型",
    "emotion_tone": "情感基调",
    "intensity": 0.5,
    "keywords": ["关键词1", "关键词2"],
    "recommended_style": "推荐音乐风格",
    "recommended_duration": 60,
    "style_confidence": 0.8,
    "reasoning": "分析推理过程"
}}"""

            # 调用LLM
            response = await self.llm.call_json(prompt)
            
            if response and all(key in response for key in ['scene_type', 'emotion_tone', 'intensity', 'recommended_style']):
                # 验证和调整参数
                intensity = max(0.0, min(1.0, float(response.get('intensity', 0.5))))
                duration = max(20, min(120, int(response.get('recommended_duration', 60))))
                confidence = max(0.0, min(1.0, float(response.get('style_confidence', 0.7))))
                
                result = MusicSceneAnalysis(
                    scene_type=response.get('scene_type', 'peaceful'),
                    emotion_tone=response.get('emotion_tone', 'neutral'),
                    intensity=intensity,
                    keywords=response.get('keywords', []),
                    recommended_style=response.get('recommended_style', 'pop'),
                    recommended_duration=duration,
                    style_confidence=confidence
                )
                
                logger.debug(f"[LLM_MUSIC] 分析结果: {response.get('reasoning', '无推理过程')}")
                return result
            else:
                logger.warning(f"[LLM_MUSIC] LLM返回格式错误: {response}")
                return self._analyze_with_basic_rules(content)
                
        except Exception as e:
            logger.error(f"[LLM_MUSIC] LLM分析失败: {str(e)}")
            return self._analyze_with_basic_rules(content)
    
    def _analyze_with_basic_rules(self, content: str) -> MusicSceneAnalysis:
        """使用基础规则进行音乐场景分析（后备方案）"""
        try:
            # 预处理文本
            content_lower = content.lower()
            
            # 统计各场景类型的关键词匹配数
            scene_scores = {}
            matched_keywords = []
            
            for scene_type, scene_info in self.BASIC_SCENE_KEYWORDS.items():
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
                primary_info = self.BASIC_SCENE_KEYWORDS["peaceful"]
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
            
            logger.info(f"[BASIC_MUSIC] 基础分析完成: {primary_scene}({confidence:.2f}) -> {recommended_style}")
            return result
            
        except Exception as e:
            logger.error(f"[BASIC_MUSIC] 基础分析失败: {e}")
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
    
    async def batch_analyze_content(self, content_list: List[str]) -> List[MusicSceneAnalysis]:
        """
        批量分析文本内容，提升性能
        
        Args:
            content_list: 要分析的文本内容列表
            
        Returns:
            音乐场景分析结果列表
        """
        try:
            if not content_list:
                return []
            
            # 构建批量分析提示词
            content_items = "\n".join([f"{i+1}. {content[:100]}..." for i, content in enumerate(content_list)])
            
            prompt = f"""你是一个专业的音乐场景分析师。请批量分析以下文本内容，为每个文本推荐合适的背景音乐风格和参数。

文本内容列表：
{content_items}

请为每个文本从以下维度进行分析：
1. 场景类型识别：战斗、浪漫、神秘、平静、悲伤、冒险、庆祝等
2. 情感基调分析：积极、消极、中性、紧张、舒缓等
3. 强度等级评估：0.0-1.0之间的数值
4. 音乐风格推荐：epic、romantic、dark、ambient、melancholy、adventure、upbeat等
5. 推荐时长：根据内容长度和场景类型推荐合适的音乐时长
6. 置信度评估：对分析结果的信心程度

请返回JSON格式：
{{
  "results": [
    {{
      "index": 1,
      "scene_type": "场景类型",
      "emotion_tone": "情感基调",
      "intensity": 0.5,
      "keywords": ["关键词1", "关键词2"],
      "recommended_style": "推荐音乐风格",
      "recommended_duration": 60,
      "style_confidence": 0.8,
      "reasoning": "分析推理过程"
    }},
    ...
  ]
}}"""

            # 调用LLM
            response = await self.llm.call_json(prompt)
            
            if response and 'results' in response:
                results = []
                for item in response['results']:
                    index = item.get('index', 0) - 1  # 转换为0基索引
                    if 0 <= index < len(content_list):
                        # 验证和调整参数
                        intensity = max(0.0, min(1.0, float(item.get('intensity', 0.5))))
                        duration = max(20, min(120, int(item.get('recommended_duration', 60))))
                        confidence = max(0.0, min(1.0, float(item.get('style_confidence', 0.7))))
                        
                        result = MusicSceneAnalysis(
                            scene_type=item.get('scene_type', 'peaceful'),
                            emotion_tone=item.get('emotion_tone', 'neutral'),
                            intensity=intensity,
                            keywords=item.get('keywords', []),
                            recommended_style=item.get('recommended_style', 'pop'),
                            recommended_duration=duration,
                            style_confidence=confidence
                        )
                        
                        results.append(result)
                        
                        # 缓存结果
                        cache_key = f"music_analysis_{hash(content_list[index])}"
                        if len(self.analysis_cache) < self.cache_max_size:
                            self.analysis_cache[cache_key] = result
                
                logger.info(f"[BATCH_MUSIC] 批量分析了{len(results)}个文本")
                return results
            else:
                logger.warning(f"[BATCH_MUSIC] LLM返回格式错误: {response}")
                # 降级到逐个分析
                return [await self.analyze_content(content) for content in content_list]
                
        except Exception as e:
            logger.error(f"[BATCH_MUSIC] 批量分析失败: {str(e)}")
            # 降级到逐个分析
            return [await self.analyze_content(content) for content in content_list]
    
    def clear_cache(self):
        """清空缓存"""
        self.analysis_cache.clear()
        logger.info("[MUSIC_ANALYSIS] 缓存已清空")
    
    def get_cache_stats(self) -> Dict[str, any]:
        """获取缓存统计信息"""
        return {
            "cache_size": len(self.analysis_cache),
            "cache_max_size": self.cache_max_size,
            "cache_usage": len(self.analysis_cache) / self.cache_max_size
        }
    
    def get_supported_scenes(self) -> List[str]:
        """获取支持的场景类型列表"""
        return list(self.BASIC_SCENE_KEYWORDS.keys())
    
    def get_style_recommendations(self, scene_type: str) -> List[Dict]:
        """获取指定场景的风格推荐"""
        if scene_type not in self.BASIC_SCENE_KEYWORDS:
            return []
        
        scene_info = self.BASIC_SCENE_KEYWORDS[scene_type]
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