#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能关键词转换服务
使用大语言模型将中文环境音关键词转换为高质量的英文TangoFlux提示词
"""

import os
import json
import logging
import asyncio
import aiohttp
from typing import List, Dict, Optional
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)

@dataclass
class KeywordConversionResult:
    """关键词转换结果"""
    original_keywords: List[str]
    english_prompt: str
    enhanced_prompt: str
    confidence_score: float
    processing_time: float

class IntelligentKeywordConverter:
    """智能关键词转换器"""
    
    def __init__(self):
        # Ollama配置
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
        
        # 关键词缓存，提高效率
        self._conversion_cache = {}
        
        logger.info(f"[KEYWORD_CONVERTER] 初始化完成，模型: {self.model_name}")

    async def convert_keywords_to_prompt(
        self, 
        keywords: List[str], 
        duration: float,
        context: str = "environment_mixing"
    ) -> KeywordConversionResult:
        """
        智能转换中文关键词为TangoFlux英文提示词
        
        Args:
            keywords: 中文关键词列表
            duration: 音频时长
            context: 使用场景上下文
            
        Returns:
            KeywordConversionResult: 转换结果
        """
        start_time = time.time()
        
        try:
            # 检查缓存
            cache_key = f"{','.join(keywords)}_{duration}_{context}"
            if cache_key in self._conversion_cache:
                cached_result = self._conversion_cache[cache_key]
                logger.info(f"[KEYWORD_CONVERTER] 使用缓存结果: {keywords}")
                return KeywordConversionResult(
                    original_keywords=keywords,
                    english_prompt=cached_result['english_prompt'],
                    enhanced_prompt=cached_result['enhanced_prompt'],
                    confidence_score=cached_result['confidence_score'],
                    processing_time=time.time() - start_time
                )
            
            # 构建智能提示词
            prompt = self._create_conversion_prompt(keywords, duration, context)
            
            # 调用LLM
            llm_response = await self._call_ollama(prompt)
            
            if not llm_response:
                # LLM失败时的降级方案
                logger.warning("[KEYWORD_CONVERTER] LLM调用失败，使用降级方案")
                return self._fallback_conversion(keywords, duration)
            
            # 解析LLM响应
            result = self._parse_llm_response(llm_response, keywords, duration)
            
            # 缓存结果
            self._conversion_cache[cache_key] = {
                'english_prompt': result.english_prompt,
                'enhanced_prompt': result.enhanced_prompt,
                'confidence_score': result.confidence_score
            }
            
            # 限制缓存大小
            if len(self._conversion_cache) > 100:
                # 删除最老的缓存项
                oldest_key = next(iter(self._conversion_cache))
                del self._conversion_cache[oldest_key]
            
            result.processing_time = time.time() - start_time
            logger.info(f"[KEYWORD_CONVERTER] 转换完成: {keywords} -> {result.english_prompt}")
            
            return result
            
        except Exception as e:
            logger.error(f"[KEYWORD_CONVERTER] 转换失败: {str(e)}")
            return self._fallback_conversion(keywords, duration)

    def _create_conversion_prompt(self, keywords: List[str], duration: float, context: str) -> str:
        """创建转换提示词"""
        keywords_text = "、".join(keywords)
        
        duration_desc = "short" if duration < 5 else "medium" if duration < 15 else "long"
        
        prompt = f"""你是一个专业的音效提示词专家。请将以下中文环境音关键词转换为高质量的英文TangoFlux音效生成提示词。

输入关键词: {keywords_text}
音频时长: {duration}秒 ({duration_desc} duration)
使用场景: {context}

要求：
1. 将中文关键词准确转换为对应的英文音效描述
2. 提供详细、具体的音效特征描述
3. 考虑音效的质量、清晰度和自然度
4. 根据时长调整描述的复杂度

请按以下JSON格式返回：
{{
    "basic_english": "基础英文转换",
    "enhanced_prompt": "增强的详细提示词（适合TangoFlux生成）",
    "confidence": 0.95
}}

例子：
输入: ["脚步声", "木地板"]
输出: {{
    "basic_english": "footsteps on wooden floor",
    "enhanced_prompt": "clear footsteps walking on creaky wooden floor, natural rhythm, indoor ambience, high quality audio",
    "confidence": 0.92
}}

现在请转换上述关键词："""

        return prompt

    async def _call_ollama(self, prompt: str) -> Optional[str]:
        """调用Ollama LLM"""
        try:
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {
                    "temperature": 0.3,  # 较低的温度保证稳定性
                    "top_p": 0.9,
                    "num_predict": 300,
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_base_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status != 200:
                        logger.error(f"[KEYWORD_CONVERTER] Ollama请求失败: {response.status}")
                        return None
                    
                    data = await response.json()
                    
                    if not data or 'message' not in data:
                        logger.error("[KEYWORD_CONVERTER] LLM响应格式错误")
                        return None
                    
                    return data['message']['content'].strip()
                    
        except Exception as e:
            logger.error(f"[KEYWORD_CONVERTER] LLM调用异常: {str(e)}")
            return None

    def _parse_llm_response(self, response: str, keywords: List[str], duration: float) -> KeywordConversionResult:
        """解析LLM响应"""
        try:
            # 尝试解析JSON
            response_clean = response.strip()
            
            # 提取JSON部分
            json_start = response_clean.find('{')
            json_end = response_clean.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response_clean[json_start:json_end]
                data = json.loads(json_str)
                
                basic_english = data.get('basic_english', '')
                enhanced_prompt = data.get('enhanced_prompt', '')
                confidence = float(data.get('confidence', 0.8))
                
                # 确保有内容
                if not basic_english or not enhanced_prompt:
                    raise ValueError("解析结果为空")
                
                return KeywordConversionResult(
                    original_keywords=keywords,
                    english_prompt=basic_english,
                    enhanced_prompt=enhanced_prompt,
                    confidence_score=confidence,
                    processing_time=0.0
                )
            else:
                raise ValueError("未找到JSON格式")
                
        except Exception as e:
            logger.warning(f"[KEYWORD_CONVERTER] JSON解析失败，尝试文本解析: {str(e)}")
            
            # 文本解析降级方案
            lines = response.strip().split('\n')
            basic_english = ""
            enhanced_prompt = ""
            
            for line in lines:
                line = line.strip()
                if '英文' in line or 'english' in line.lower():
                    basic_english = line.split(':')[-1].strip(' "')
                elif '增强' in line or 'enhanced' in line.lower():
                    enhanced_prompt = line.split(':')[-1].strip(' "')
            
            if not basic_english:
                basic_english = f"ambient sound of {', '.join(keywords)}"
            if not enhanced_prompt:
                enhanced_prompt = f"{basic_english}, high quality environmental audio"
            
            return KeywordConversionResult(
                original_keywords=keywords,
                english_prompt=basic_english,
                enhanced_prompt=enhanced_prompt,
                confidence_score=0.6,  # 较低置信度
                processing_time=0.0
            )

    def _fallback_conversion(self, keywords: List[str], duration: float) -> KeywordConversionResult:
        """降级转换方案（LLM不可用时）"""
        
        # 简单的关键词映射（作为最后的降级方案）
        basic_mapping = {
            '脚步': 'footsteps',
            '蜂鸣': 'electronic beep',
            '马蹄': 'horse hooves',
            '雨': 'rain',
            '风': 'wind',
            '鸟': 'birds',
            '水': 'water',
            '火': 'fire',
            '雷': 'thunder',
            '门': 'door',
            '车': 'car engine',
            '人': 'people talking'
        }
        
        # 转换关键词
        english_parts = []
        for keyword in keywords:
            found = False
            for key, value in basic_mapping.items():
                if key in keyword:
                    english_parts.append(value)
                    found = True
                    break
            if not found:
                english_parts.append(f"ambient {keyword} sound")
        
        basic_english = ", ".join(english_parts)
        
        # 根据时长生成增强提示词
        duration_desc = "short duration" if duration < 5 else "medium duration" if duration < 15 else "long duration"
        quality_desc = "high quality, clear, natural environmental sound"
        
        enhanced_prompt = f"{basic_english}, {duration_desc}, {quality_desc}"
        
        return KeywordConversionResult(
            original_keywords=keywords,
            english_prompt=basic_english,
            enhanced_prompt=enhanced_prompt,
            confidence_score=0.4,  # 低置信度，表示使用了降级方案
            processing_time=0.0
        )

# 全局实例
intelligent_keyword_converter = IntelligentKeywordConverter() 