#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于大语言模型的智能场景分析器
使用Ollama本地服务和千问3模型进行深度场景理解和分析
"""

import os
import json
import logging
import asyncio
import aiohttp
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.sequential_timeline_generator import SceneInfo
from app.services.intelligent_scene_analyzer import SceneAnalysisResult, intelligent_scene_analyzer

logger = logging.getLogger(__name__)

@dataclass
class LLMSceneAnalysisResult:
    """LLM场景分析结果"""
    text_hash: str
    analyzed_scenes: List[SceneInfo]
    narrative_analysis: Dict[str, Any]  # 叙事分析
    emotional_progression: List[Dict[str, Any]]  # 情感变化
    scene_transitions: List[Dict[str, Any]]  # 场景转换
    recommended_soundscape: Dict[str, Any]  # 推荐音景
    processing_time: float
    confidence_score: float
    llm_provider: str
    token_usage: Dict[str, int]

class OllamaLLMSceneAnalyzer:
    """基于Ollama本地服务的智能场景分析器"""
    
    def __init__(self):
        # Ollama配置
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = os.getenv("OLLAMA_MODEL", "qwen3:30b")  # 千问模型 - 修复为实际安装的模型
        
        # 🎯 简化版提示词 - 专注核心环境分析
        self.system_prompt = """你是环境音效分析专家，分析文本中的场景环境。

只返回JSON，不要任何解释。格式：
{
  "scenes": [
    {
      "location": "地点(如forest/indoor/city)",
      "atmosphere": "氛围(如calm/tense/quiet)",
      "weather": "天气(如sunny/rainy/clear)",
      "time_of_day": "时间(如day/night/morning)",
      "keywords": ["环境关键词"],
      "confidence": 0.8
    }
  ],
  "recommended_soundscape": {
    "primary_elements": ["主要环境音"],
    "secondary_elements": ["次要环境音"]
  }
}

要求：双引号包围字符串，数字不用引号。"""

        self.user_prompt_template = """分析以下文本的场景和音景需求：

文本内容：
```
{text}
```

重点分析：
1. 场景的空间特征和环境细节
2. 情感氛围的变化和强度
3. 时间流动和节奏感
4. 适合的环境音效类型和组合
5. 声音设计的创意建议

现在请返回符合格式要求的JSON分析结果："""

    async def check_ollama_status(self) -> bool:
        """检查Ollama服务状态"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_base_url}/api/tags", timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        # 检查是否有可用的模型
                        models = [model.get("name", "") for model in data.get("models", [])]
                        logger.info(f"Ollama可用模型: {models}")
                        return len(models) > 0
                    return False
        except Exception as e:
            logger.error(f"检查Ollama状态失败: {e}")
            return False

    async def check_model_available(self, model_name: str) -> bool:
        """检查指定模型是否可用"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_base_url}/api/tags", timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model.get("name", "") for model in data.get("models", [])]
                        # 检查模型名称匹配（支持部分匹配）
                        for model in models:
                            if model_name.split(":")[0] in model:
                                logger.info(f"找到匹配模型: {model}")
                                return True
                        logger.warning(f"未找到模型 {model_name}，可用模型: {models}")
                        return False
                    return False
        except Exception as e:
            logger.error(f"检查模型可用性失败: {e}")
            return False

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def analyze_with_ollama(self, text: str) -> tuple[Dict[str, Any], Dict[str, int], str]:
        """使用Ollama和千问3分析场景"""
        
        # 构建完整的提示词
        full_prompt = f"{self.system_prompt}\n\n{self.user_prompt_template.format(text=text)}"
        
        try:
            payload = {
                "model": self.model_name,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_k": 40,
                    "top_p": 0.9,
                    "num_predict": 4000
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=90)  # 优化超时设置
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama请求失败 {response.status}: {error_text}")
                    
                    data = await response.json()
                    content = data.get("response", "")
                    
                    if not content.strip():
                        raise Exception("Ollama返回空响应")
                    
                    # 尝试提取JSON内容
                    import re
                    
                    # 记录原始响应用于调试
                    logger.info(f"Ollama原始响应: {content[:1000]}...")
                    
                    # 首先尝试直接解析整个内容
                    try:
                        result = json.loads(content)
                        logger.info("成功直接解析整个响应为JSON")
                    except json.JSONDecodeError:
                        # 如果直接解析失败，尝试提取第一个完整的JSON对象
                        logger.warning("直接解析失败，尝试提取JSON对象")
                        
                        # 寻找第一个完整的JSON对象（处理可能的多个JSON对象问题）
                        json_pattern = r'\{(?:[^{}]|{(?:[^{}]|{[^{}]*})*})*\}'
                        json_matches = re.findall(json_pattern, content, re.DOTALL)
                        
                        if json_matches:
                            # 使用第一个匹配的JSON对象
                            json_str = json_matches[0]
                            logger.info(f"找到JSON对象: {json_str[:500]}...")
                            
                            try:
                                result = json.loads(json_str)
                                logger.info("成功解析提取的JSON对象")
                            except json.JSONDecodeError as e:
                                logger.error(f"提取的JSON对象解析失败: {e}")
                                logger.error(f"JSON内容: {json_str[:500]}...")
                                
                                # 尝试清理JSON内容
                                cleaned_json = self._clean_json_content(json_str)
                                if cleaned_json:
                                    try:
                                        result = json.loads(cleaned_json)
                                        logger.info("成功解析清理后的JSON")
                                    except json.JSONDecodeError as e2:
                                        logger.error(f"清理后的JSON仍然解析失败: {e2}")
                                        raise Exception(f"无法解析LLM返回的JSON: {e}")
                                else:
                                    raise Exception(f"无法解析LLM返回的JSON: {e}")
                        else:
                            logger.error(f"未找到有效的JSON对象，原始内容: {content[:500]}...")
                            raise Exception("LLM返回的内容中未找到有效的JSON对象")
                    
                    # 估算token使用量（中文按字符数估算）
                    prompt_chars = len(full_prompt)
                    response_chars = len(content)
                    token_usage = {
                        "prompt_tokens": prompt_chars // 2,  # 中文大约2字符=1token
                        "completion_tokens": response_chars // 2,
                        "total_tokens": (prompt_chars + response_chars) // 2
                    }
                    
                    logger.info(f"Ollama分析完成，使用模型: {self.model_name}")
                    return result, token_usage, "ollama"
            
        except Exception as e:
            logger.error(f"Ollama分析失败: {e}")
            raise

    def _clean_json_content(self, json_str: str) -> str:
        """清理JSON内容，处理常见的格式问题"""
        try:
            import re
            
            # 移除前后空白字符和多余的标记
            cleaned = json_str.strip()
            
            # 移除可能的markdown标记或其他前缀
            if '```' in cleaned:
                cleaned = re.sub(r'```[a-zA-Z]*\n?', '', cleaned)
                cleaned = re.sub(r'```', '', cleaned)
            
            # 💡 最简单有效的方法：直接替换所有不带引号的键名
            # 匹配独立的单词后跟冒号的模式（确保不在字符串内）
            # 使用负前瞻确保不匹配已经在引号内的内容
            
            # 步骤1: 修复属性名缺少引号的问题
            # 匹配这种模式: 空白 + 单词 + 空白 + 冒号
            unquoted_key_pattern = r'(\s+)([a-zA-Z_][a-zA-Z0-9_]*)\s*:'
            
            def quote_key_replacement(match):
                indent = match.group(1)
                key = match.group(2)
                return f'{indent}"{key}":'
            
            cleaned = re.sub(unquoted_key_pattern, quote_key_replacement, cleaned)
            
            # 步骤2: 修复缺少逗号的问题
            # 在换行符前添加逗号，如果行尾不是 { [ , } ]
            lines = cleaned.split('\n')
            for i in range(len(lines) - 1):
                current_line = lines[i].strip()
                next_line = lines[i + 1].strip()
                
                # 如果当前行不为空，不以逗号、大括号、方括号结尾
                # 且下一行不以大括号、方括号开头，则添加逗号
                if (current_line and 
                    not current_line.endswith((',', '{', '}', '[', ']')) and
                    next_line and
                    not next_line.startswith(('}', ']'))):
                    lines[i] = lines[i].rstrip() + ','
            
            cleaned = '\n'.join(lines)
            
            # 步骤3: 清理多余的逗号
            # 移除 } 和 ] 前面的逗号
            cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)
            
            # 移除重复的逗号
            cleaned = re.sub(r',\s*,', ',', cleaned)
            
            # 步骤4: 确保括号匹配
            open_braces = cleaned.count('{')
            close_braces = cleaned.count('}')
            if open_braces > close_braces:
                cleaned += '}' * (open_braces - close_braces)
            
            open_brackets = cleaned.count('[')
            close_brackets = cleaned.count(']')
            if open_brackets > close_brackets:
                cleaned += ']' * (open_brackets - close_brackets)
            
            return cleaned
            
        except Exception as e:
            logger.error(f"清理JSON内容失败: {e}")
            return None

    async def analyze_text_scenes_with_llm(self, text: str, user_id: Optional[int] = None, 
                                         preferred_provider: str = "ollama") -> LLMSceneAnalysisResult:
        """使用LLM分析文本场景"""
        start_time = datetime.now()
        
        # 生成文本哈希
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        try:
            # 检查Ollama服务状态
            if not await self.check_ollama_status():
                logger.warning("Ollama服务不可用，回退到基础分析器")
                return await self._fallback_to_basic_analyzer(text, user_id)
            
            # 检查模型是否可用
            if not await self.check_model_available(self.model_name):
                logger.warning(f"模型 {self.model_name} 不可用，回退到基础分析器")
                return await self._fallback_to_basic_analyzer(text, user_id)
            
            # 使用Ollama分析
            logger.info(f"开始使用Ollama分析文本，模型: {self.model_name}")
            
            llm_result, token_usage, provider = await self.analyze_with_ollama(text)
            
            # 调试：记录LLM返回的原始结果
            logger.info(f"LLM返回的原始结果: {json.dumps(llm_result, ensure_ascii=False, indent=2)}")
            
            # 解析LLM结果并转换为标准格式
            analyzed_scenes = []
            scenes_data = llm_result.get("scenes", [])
            
            # 如果没有scenes键，检查是否有其他可能的场景数据
            if not scenes_data and "scene" in llm_result:
                # 处理单个场景的情况
                scenes_data = [llm_result["scene"]]
            
            for i, scene_data in enumerate(scenes_data):
                scene = SceneInfo(
                    location=scene_data.get("location", scene_data.get("type", "unknown")),
                    weather=scene_data.get("weather", "clear"),
                    time_of_day=scene_data.get("time_of_day", "day"),
                    atmosphere=scene_data.get("atmosphere", "neutral"),
                    keywords=scene_data.get("keywords", []),
                    confidence=scene_data.get("confidence", 0.8)
                )
                analyzed_scenes.append(scene)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 计算整体置信度
            confidences = [scene.confidence for scene in analyzed_scenes]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.8
            
            result = LLMSceneAnalysisResult(
                text_hash=text_hash,
                analyzed_scenes=analyzed_scenes,
                narrative_analysis=llm_result.get("narrative_analysis", {}),
                emotional_progression=llm_result.get("emotional_progression", []),
                scene_transitions=llm_result.get("scene_transitions", []),
                recommended_soundscape=llm_result.get("recommended_soundscape", {}),
                processing_time=processing_time,
                confidence_score=avg_confidence,
                llm_provider=provider,
                token_usage=token_usage
            )
            
            logger.info(f"LLM分析完成，识别了 {len(analyzed_scenes)} 个场景，处理时间: {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"LLM分析失败，回退到基础分析器: {e}")
            return await self._fallback_to_basic_analyzer(text, user_id)

    async def _fallback_to_basic_analyzer(self, text: str, user_id: Optional[int] = None) -> LLMSceneAnalysisResult:
        """回退到基础分析器"""
        start_time = datetime.now()
        
        logger.info("使用基础分析器进行场景分析")
        basic_result = await intelligent_scene_analyzer.analyze_text_scenes(text, user_id)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 转换为LLM结果格式
        result = LLMSceneAnalysisResult(
            text_hash=basic_result.text_hash,
            analyzed_scenes=basic_result.analyzed_scenes,
            narrative_analysis={},  # 基础分析器不提供这些高级分析，使用空字典
            emotional_progression=[],
            scene_transitions=[],
            recommended_soundscape={},
            processing_time=processing_time,
            confidence_score=basic_result.confidence_score,
            llm_provider="basic_analyzer",  # 标识为基础分析器
            token_usage={}
        )
        
        return result

    def generate_enhanced_prompts(self, llm_result: LLMSceneAnalysisResult) -> List[Dict[str, Any]]:
        """基于LLM分析结果生成增强的提示词"""
        enhanced_prompts = []
        
        for i, scene in enumerate(llm_result.analyzed_scenes):
            # 基础环境描述
            base_prompt = self._build_base_environment_prompt(scene)
            
            # 如果有LLM的额外信息，添加更详细的描述
            enhanced_prompt = base_prompt
            
            if llm_result.recommended_soundscape:
                soundscape = llm_result.recommended_soundscape
                
                # 添加主要音效元素
                if soundscape.get("primary_elements"):
                    primary_elements = ", ".join(soundscape["primary_elements"])
                    enhanced_prompt += f", featuring {primary_elements}"
                
                # 添加次要音效元素
                if soundscape.get("secondary_elements"):
                    secondary_elements = ", ".join(soundscape["secondary_elements"])
                    enhanced_prompt += f", with subtle {secondary_elements}"
                
                # 添加环境层次
                if soundscape.get("ambient_layers"):
                    layers = ", ".join(soundscape["ambient_layers"])
                    enhanced_prompt += f", layered with {layers}"
            
            # 计算场景时长
            duration = self._calculate_scene_duration(scene, llm_result)
            
            # 计算生成优先级
            priority = self._calculate_generation_priority(scene, llm_result)
            
            # 动态元素
            dynamic_elements = self._extract_dynamic_elements(scene, llm_result.recommended_soundscape or {})
            
            prompt_data = {
                "scene_index": i,
                "title": f"场景{i+1}: {scene.location} - {scene.atmosphere}",
                "prompt": enhanced_prompt,
                "duration": duration,
                "priority": priority,
                "scene_details": {
                    "location": scene.location,
                    "weather": scene.weather,
                    "time_of_day": scene.time_of_day,
                    "atmosphere": scene.atmosphere,
                    "keywords": scene.keywords
                },
                "fade_settings": {
                    "fade_in": self._get_fade_duration(i, llm_result, "in"),
                    "fade_out": self._get_fade_duration(i, llm_result, "out")
                },
                "dynamic_elements": dynamic_elements,
                "generation_tips": {
                    "complexity": "high" if scene.confidence > 0.8 else "medium",
                    "recommended_model": "TangoFlux",
                    "style_hints": f"{scene.atmosphere} {scene.weather} {scene.time_of_day}"
                }
            }
            
            enhanced_prompts.append(prompt_data)
        
        return enhanced_prompts

    def _build_base_environment_prompt(self, scene: SceneInfo) -> str:
        """构建基础环境提示词"""
        location_map = {
            "forest": "dense forest ambience with rustling leaves and distant wildlife",
            "city": "urban environment with distant traffic and city sounds",
            "indoor": "quiet indoor atmosphere with subtle room tone",
            "ocean": "oceanic soundscape with waves and seabird calls",
            "mountain": "mountain atmosphere with wind and distant echoes",
            "desert": "arid desert ambience with subtle wind and sparse sounds",
            "village": "peaceful village sounds with gentle activity",
            "castle": "medieval castle atmosphere with stone echoes"
        }
        
        weather_map = {
            "rainy": "with gentle rain falling",
            "stormy": "with dramatic storm sounds and thunder",
            "windy": "with strong wind gusts",
            "sunny": "with bright, clear atmosphere",
            "foggy": "with mysterious, muffled ambience",
            "snowy": "with soft snow falling and muffled sounds"
        }
        
        time_map = {
            "morning": "early morning with bird songs",
            "day": "during daytime with full activity",
            "evening": "evening time with settling sounds",
            "night": "nighttime with nocturnal sounds",
            "dawn": "at dawn with awakening nature",
            "dusk": "at dusk with calming atmosphere"
        }
        
        atmosphere_map = {
            "calm": "peaceful and serene mood",
            "tense": "suspenseful and dramatic atmosphere", 
            "romantic": "intimate and warm feeling",
            "mysterious": "enigmatic and intriguing mood",
            "scary": "dark and ominous atmosphere",
            "joyful": "cheerful and uplifting mood",
            "sad": "melancholic and somber tone"
        }
        
        # 构建基础描述
        base = location_map.get(scene.location, f"{scene.location} environment")
        
        # 添加天气
        if scene.weather != "clear":
            weather_desc = weather_map.get(scene.weather, f"with {scene.weather} weather")
            base += f", {weather_desc}"
        
        # 添加时间
        if scene.time_of_day != "day":
            time_desc = time_map.get(scene.time_of_day, f"{scene.time_of_day} time")
            base += f", {time_desc}"
        
        # 添加氛围
        if scene.atmosphere != "neutral":
            atmosphere_desc = atmosphere_map.get(scene.atmosphere, f"{scene.atmosphere} mood")
            base += f", {atmosphere_desc}"
        
        return base

    def _calculate_scene_duration(self, scene: SceneInfo, llm_result: LLMSceneAnalysisResult) -> float:
        """计算场景建议时长"""
        base_duration = 15.0  # 基础时长15秒
        
        # 根据氛围调整时长
        atmosphere_multipliers = {
            "calm": 1.2,
            "tense": 0.8,
            "romantic": 1.5,
            "mysterious": 1.3,
            "scary": 0.9,
            "joyful": 1.0,
            "sad": 1.4
        }
        
        multiplier = atmosphere_multipliers.get(scene.atmosphere, 1.0)
        duration = base_duration * multiplier
        
        # 根据置信度微调
        confidence_factor = 0.8 + (scene.confidence * 0.4)  # 0.8-1.2范围
        duration *= confidence_factor
        
        # 如果有LLM推荐的时长，参考它
        if (llm_result.recommended_soundscape and 
            llm_result.recommended_soundscape.get("overall_duration")):
            try:
                recommended = float(llm_result.recommended_soundscape["overall_duration"])
                # 取推荐时长和计算时长的平均值
                duration = (duration + recommended) / 2
            except (ValueError, TypeError):
                pass
        
        return round(duration, 1)

    def _calculate_generation_priority(self, scene: SceneInfo, llm_result: LLMSceneAnalysisResult) -> int:
        """计算生成优先级 (1-5, 5最高)"""
        priority = 3  # 默认优先级
        
        # 根据置信度调整
        if scene.confidence > 0.9:
            priority += 1
        elif scene.confidence < 0.6:
            priority -= 1
        
        # 根据氛围重要性调整
        important_atmospheres = {"tense", "scary", "romantic", "mysterious"}
        if scene.atmosphere in important_atmospheres:
            priority += 1
        
        # 根据关键词数量调整
        if len(scene.keywords) > 5:
            priority += 1
        elif len(scene.keywords) < 2:
            priority -= 1
        
        return max(1, min(5, priority))

    def _get_fade_duration(self, scene_index: int, llm_result: LLMSceneAnalysisResult, 
                          fade_type: str) -> float:
        """获取淡入淡出时长"""
        base_fade = 2.0
        
        # 检查是否有场景转换信息
        if llm_result.scene_transitions:
            for transition in llm_result.scene_transitions:
                if fade_type == "in" and transition.get("to_scene_index") == scene_index:
                    return float(transition.get("transition_duration", base_fade))
                elif fade_type == "out" and transition.get("from_scene_index") == scene_index:
                    return float(transition.get("transition_duration", base_fade))
        
        # 根据场景特点调整
        scene = llm_result.analyzed_scenes[scene_index]
        if scene.atmosphere in {"calm", "romantic", "sad"}:
            return base_fade * 1.5  # 慢淡入淡出
        elif scene.atmosphere in {"tense", "scary"}:
            return base_fade * 0.5  # 快淡入淡出
        
        return base_fade

    def _extract_dynamic_elements(self, scene: SceneInfo, soundscape: Dict[str, Any]) -> List[str]:
        """提取动态元素"""
        dynamic_elements = []
        
        # 从音景推荐中提取
        if soundscape.get("dynamic_changes"):
            dynamic_elements.extend(soundscape["dynamic_changes"])
        
        # 根据场景特征添加默认动态元素
        if scene.weather == "rainy":
            dynamic_elements.extend(["rain_intensity_changes", "water_droplets"])
        
        if scene.weather == "stormy":
            dynamic_elements.extend(["thunder_rolls", "wind_gusts"])
        
        if scene.location == "forest":
            dynamic_elements.extend(["bird_calls", "rustling_leaves"])
        
        if scene.atmosphere == "tense":
            dynamic_elements.extend(["tension_builds", "dramatic_pauses"])
        
        return list(set(dynamic_elements))  # 去重

# 创建全局实例
llm_scene_analyzer = OllamaLLMSceneAnalyzer()