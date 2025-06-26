#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于大语言模型的智能场景分析器
使用Ollama HTTP API进行深度场景理解和分析
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
import re
import time

from app.services.sequential_timeline_generator import SceneInfo
from app.services.intelligent_scene_analyzer import SceneAnalysisResult, intelligent_scene_analyzer

logger = logging.getLogger(__name__)

@dataclass
class SceneAnalysis:
    """单个场景分析结果"""
    location: str
    keywords: List[str]
    confidence: float

@dataclass
class SceneAnalysisResult:
    """场景分析结果"""
    analyzed_scenes: List[SceneAnalysis]
    confidence_score: float
    processing_time: float
    raw_response: str

class OllamaLLMSceneAnalyzer:
    """基于Ollama HTTP API的智能场景分析器"""
    
    def __init__(self):
        # Ollama配置
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = os.getenv("OLLAMA_MODEL", "gemma3:27b")  # 使用可用的gemma3模型
        
        logger.info(f"[LLM_ANALYZER] 初始化完成，模型: {self.model_name}, URL: {self.ollama_base_url}")

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

    async def analyze_text_scenes_with_llm(self, text: str) -> SceneAnalysisResult:
        """使用LLM分析文本中的场景环境"""
        logger.info(f"[LLM_ANALYZER] 开始分析文本，长度: {len(text)}字符")
        
        try:
            # 检测是否为批量分析（包含多个段落的格式）
            is_batch_analysis = self._is_batch_analysis_text(text)
            
            if is_batch_analysis:
                logger.info("[LLM_ANALYZER] 检测到批量分析格式，使用批量提示词")
                prompt = self._create_batch_analysis_prompt(text)
            else:
                logger.info("[LLM_ANALYZER] 使用单段落分析提示词")
                prompt = self._create_single_analysis_prompt(text)
            
            # 直接使用HTTP API调用Ollama
            start_time = time.time()
            
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": 1000 if is_batch_analysis else 500,
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_base_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"[LLM_ANALYZER] Ollama请求失败 {response.status}: {error_text}")
                        return SceneAnalysisResult(
                            analyzed_scenes=[],
                            confidence_score=0.0,
                            processing_time=time.time() - start_time,
                            raw_response=f"HTTP错误: {response.status}"
                        )
                    
                    data = await response.json()
                    analysis_time = time.time() - start_time
                    
                    if not data or 'message' not in data:
                        logger.error("[LLM_ANALYZER] LLM响应格式错误")
                        return SceneAnalysisResult(
                            analyzed_scenes=[],
                            confidence_score=0.0,
                            processing_time=analysis_time,
                            raw_response="响应格式错误"
                        )
                    
                    response_text = data['message']['content'].strip()
                    logger.info(f"[LLM_ANALYZER] LLM分析完成，耗时: {analysis_time:.2f}s")
                    logger.info(f"[LLM_ANALYZER] LLM响应: {response_text[:200]}...")
                    
                    # 解析响应
                    if is_batch_analysis:
                        scenes = self._parse_batch_llm_response(response_text)
                    else:
                        scenes = self._parse_single_llm_response(response_text)
                    
                    # 计算置信度
                    confidence = self._calculate_confidence(scenes, response_text)
                    
                    logger.info(f"[LLM_ANALYZER] 解析完成: {len(scenes)}个场景，置信度: {confidence:.2f}")
                    
                    return SceneAnalysisResult(
                        analyzed_scenes=scenes,
                        confidence_score=confidence,
                        processing_time=analysis_time,
                        raw_response=response_text
                    )
            
        except Exception as e:
            logger.error(f"[LLM_ANALYZER] 分析失败: {str(e)}")
            return SceneAnalysisResult(
                analyzed_scenes=[],
                confidence_score=0.0,
                processing_time=0.0,
                raw_response=f"分析失败: {str(e)}"
            )
    
    def _is_batch_analysis_text(self, text: str) -> bool:
        """检测是否为批量分析文本"""
        # 检查是否包含段落编号和时间范围的格式
        batch_patterns = [
            r'段落\d+\([^)]+\):',  # 段落1(0.0-15.2s):
            r'请分析以下章节',      # 批量分析的开头
            r'\d+\.\d+-\d+\.\d+s', # 时间范围格式
        ]
        
        for pattern in batch_patterns:
            if re.search(pattern, text):
                return True
        
        # 检查是否包含多个段落（简单计数）
        segment_count = len(re.findall(r'段落\d+', text))
        return segment_count > 1

    def _create_batch_analysis_prompt(self, text: str) -> str:
        """创建批量分析的提示词"""
        return f"""请分析以下章节中每个段落的环境声音，提取环境中的声音元素：

{text}

请按段落顺序返回结果，每个段落一行，格式：
段落1: ["关键词1", "关键词2"]
段落2: ["关键词3", "关键词4"]

要求：
- 只提取环境声音：风声、雨声、雷声、虫鸣、鸟叫、水声、脚步声、翻书声等
- 不要提取人物名称或对话内容
- 每个段落最多3个关键词
- 如果段落没有环境声音，返回空数组[]
- 不要解释，直接返回结果"""

    def _create_single_analysis_prompt(self, text: str) -> str:
        """创建单段落分析的提示词"""
        return f"""从以下文本中提取环境声音元素：

{text}

返回格式：["关键词1", "关键词2", "关键词3"]

要求：
- 只提取环境声音：风声、雨声、雷声、虫鸣、鸟叫、水声、脚步声、翻书声等
- 不要提取人物名称或对话内容
- 最多3个关键词
- 如果没有环境声音，返回[]
- 不要解释，直接返回结果"""
    
    def _parse_batch_llm_response(self, response_text: str) -> List[SceneAnalysis]:
        """解析批量分析的LLM响应"""
        scenes = []
        
        # 查找段落格式的响应
        lines = response_text.strip().split('\n')
        segment_pattern = r'段落(\d+):\s*(\[.*?\])'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            match = re.search(segment_pattern, line)
            if match:
                segment_num = int(match.group(1))
                keywords_str = match.group(2)
                
                try:
                    # 解析JSON数组
                    keywords = json.loads(keywords_str)
                    if isinstance(keywords, list) and keywords:
                        # 清理关键词
                        clean_keywords = [kw.strip() for kw in keywords if kw.strip()]
                        if clean_keywords:
                            scenes.append(SceneAnalysis(
                                location="detected_environment",
                                keywords=clean_keywords[:3],  # 最多3个
                                confidence=0.9
                            ))
                            logger.info(f"[BATCH_PARSER] 段落{segment_num}: {clean_keywords}")
                except json.JSONDecodeError:
                    logger.warning(f"[BATCH_PARSER] 段落{segment_num}解析失败: {keywords_str}")
                    continue
        
        # 如果没有找到段落格式，尝试解析为整体结果
        if not scenes:
            logger.info("[BATCH_PARSER] 未找到段落格式，尝试整体解析")
            scenes = self._parse_single_llm_response(response_text)
        
        return scenes
    
    def _parse_single_llm_response(self, response_text: str) -> List[SceneAnalysis]:
        """解析单段落分析的LLM响应"""
        # 尝试提取JSON数组
        json_pattern = r'\[([^\]]*)\]'
        matches = re.findall(json_pattern, response_text)
        
        for match in matches:
            try:
                # 构建完整的JSON字符串
                json_str = f'[{match}]'
                keywords = json.loads(json_str)
                
                if isinstance(keywords, list) and keywords:
                    # 清理关键词
                    clean_keywords = []
                    for kw in keywords:
                        if isinstance(kw, str) and kw.strip():
                            clean_keywords.append(kw.strip())
                    
                    if clean_keywords:
                        return [SceneAnalysis(
                            location="detected_environment",
                            keywords=clean_keywords[:3],  # 最多3个
                            confidence=0.9
                        )]
                        
            except json.JSONDecodeError:
                continue
        
        # 如果JSON解析失败，尝试提取关键词
        logger.info("[SINGLE_PARSER] JSON解析失败，尝试关键词提取")
        keywords = self._extract_keywords_from_text(response_text)
        
        if keywords:
            return [SceneAnalysis(
                location="detected_environment",
                keywords=keywords[:3],
                confidence=0.7  # 关键词提取的置信度较低
            )]
        
        return []
    
    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """从文本中提取可能的关键词"""
        # 常见的声音关键词
        sound_keywords = [
            '风声', '雨声', '雷声', '鸟鸣', '虫鸣', '水声', '海浪', '溪流',
            '脚步声', '敲门声', '汽车声', '飞机声', '音乐声', '说话声',
            '狗叫', '猫叫', '马蹄声', '钟声', '铃声', '哭声', '笑声',
            '火焰', '爆炸', '碰撞', '摩擦', '滴水', '流水', '瀑布'
        ]
        
        found_keywords = []
        text_lower = text.lower()
        
        for keyword in sound_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
                
        return found_keywords[:3]  # 最多返回3个

    def _calculate_confidence(self, scenes: List[SceneAnalysis], response_text: str) -> float:
        """计算整体置信度"""
        if not scenes:
            return 0.0
        
        # 基于场景数量和关键词质量计算置信度
        total_confidence = sum(scene.confidence for scene in scenes)
        avg_confidence = total_confidence / len(scenes)
        
        # 根据响应质量调整
        if "json" in response_text.lower() or "[" in response_text:
            # 如果响应包含JSON格式，提高置信度
            avg_confidence = min(avg_confidence * 1.1, 1.0)
        
        return round(avg_confidence, 2)

# 创建全局分析器实例
llm_scene_analyzer = OllamaLLMSceneAnalyzer()