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
        self.ollama_base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")  # 🔥 改用中文优化模型
        
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
                    "num_predict": 2000 if is_batch_analysis else 500,  # 增加批量分析的token限制
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

    async def validate_and_normalize_keywords(self, paragraph_text: str, candidates: List[str]) -> List[str]:
        """使用LLM对候选关键词进行校验与归一化，输出真实声音词（<=3）。

        - 只保留文本中明确发生的声音
        - 去除动作/视觉/情绪类词
        - 归一化为简洁标准词（如"手机震动打声"→"震动声"）
        - 返回严格JSON数组
        """
        try:
            if not candidates:
                return []

            prompt = (
                "请基于以下段落，仅保留真实发生的声音，并将候选关键词归一化为简洁标准词；"
                "禁止输出动作/视觉/情绪词；最多返回3个；严格以JSON数组返回。\n\n"
                "段落：\n" + paragraph_text.strip() + "\n\n"
                "候选关键词（可能包含错误项）：\n" + json.dumps(candidates, ensure_ascii=False) + "\n\n"
                "要求：\n"
                "- 只保留声音：如 叮声/响/蜂鸣声/脚步声/说话声/马蹄声/空调声/雨声 等\n"
                "- 移除动作/视觉/情绪：如 抓住/瞥见/身影/表情/愤怒 等\n"
                "- 归一化示例：'手机震动打声'→'震动声'，'耳畔响起尖鸣'→'蜂鸣声'，'快步'→'脚步声'\n"
                "- 返回格式：['关键词1','关键词2'] 或 []（严格JSON，无解释）"
            )

            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 300}
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_base_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        return []
                    data = await response.json()
                    content = data.get("message", {}).get("content", "").strip()

            # 解析严格JSON数组
            try:
                # 尝试直接解析整段为JSON数组
                parsed = json.loads(content)
                if isinstance(parsed, list):
                    return [kw.strip() for kw in parsed if isinstance(kw, str) and kw.strip()][:3]
            except Exception:
                pass

            # 回退：提取第一个[]数组
            array_match = re.search(r"\[(.*?)\]", content, re.S)
            if array_match:
                arr_text = "[" + array_match.group(1) + "]"
                try:
                    parsed = json.loads(arr_text)
                    if isinstance(parsed, list):
                        return [kw.strip() for kw in parsed if isinstance(kw, str) and kw.strip()][:3]
                except Exception:
                    return []

            return []
        except Exception:
            return []
    
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
        """创建批量分析的提示词 - 增强时序分析"""
        # 检查是否包含时序分析指导
        if "时序分析要求" in text or "声音事件" in text:
            logger.info("[LLM_ANALYZER] 检测到时序分析提示词，直接使用")
            return text
        else:
            # 使用优化后的提示词
            logger.info("[LLM_ANALYZER] 使用优化后的批量分析提示词")
            return f"""请分析以下文本中的环境音，严格按照以下要求：

🎯 核心要求：
1. 只识别文本中明确提到的声音
2. 关键词要简洁，2-4个字符
3. 不要包含时间、强度等描述性信息
4. 不要包含分析过程或格式标记
5. 不要进行任何联想
6. 瞬间声音用简洁词汇：叮、砰、响、震动等
7. 持续声音用标准词汇：脚步声、说话声、马蹄声等

✅ 正确示例：
- "空调发出轻微嗡鸣" → ["空调声"]
- "手机震动" → ["震动声"]
- "远处传来马蹄声" → ["马蹄声"]
- "叮 ——" → ["叮声"]
- "娇喝声带着怒意" → ["娇喝声"]
- "急促脚步声" → ["脚步声"]
- "耳畔响起尖锐的蜂鸣" → ["蜂鸣声"]
- "前方传来女子的惊呼" → ["惊呼声"]
- "发间珍珠步摇随着挣扎摇晃" → ["步摇声"]

❌ 错误示例：
- 不要联想：看到"御书房"就联想"翻书声"
- 不要描述：不要包含"中强度"、"1.5秒"等描述
- 不要格式：不要包含"**段落**"、"声音事件"等标记
- 不要复杂：不要"手机震动打声"，应该是"震动声"
- 不要重复：不要"耳畔响"，应该是"响"或"蜂鸣声"
- 不要动作：不要"抓住手腕"、"余光瞥见"等动作描述
- 不要视觉：不要"闪过的身影"、"凌乱的发髻"等视觉描述

📚 标准化与归一化（必须遵守）：
- 输出的每个关键词必须是简洁、标准的声音词，优先从下述集合选择或将同义表述归一化：
  - 瞬间类：叮声、响、砰声、啪声、咚声、蜂鸣声、铃声、敲门声、破碎声、爆炸声、惊呼声
  - 持续类：脚步声、说话声、人群声、马蹄声、雨声、风声、雷声、水流声、空调声、音乐声、步摇声
- 归一化示例：
  - "手机震动打声" → "震动声"
  - "耳畔响"/"耳边响起" → "响"（如语义明确为蜂鸣则 → "蜂鸣声"）
  - "快步声"/"发间珍珠步声" → "脚步声"
  - "手机震动"/"震动" → "震动声"
  - 任何包含"步"且指走路产生的声音 → "脚步声"
  - 任何包含"蜂鸣" → "蜂鸣声"
  - 任何包含"马蹄" → "马蹄声"
  - 任何包含"空调"/"嗡鸣"（空调背景） → "空调声"
  - 任何包含"惊呼" → "惊呼声"
  - 任何包含"步摇" → "步摇声"
  - 不要创造新词或复合词（如"手机震动打声"、"耳畔尖鸣响"），必须用标准词表中的一个词

🚫 严格禁止：
- 禁止输出动作描述：如"抓住"、"瞥见"、"闪过"、"凌乱"等
- 禁止输出视觉描述：如"身影"、"发髻"、"表情"等
- 禁止输出情感描述：如"警惕"、"不安"、"愤怒"等
- 只输出声音相关的词汇

{text}

⚠️ 重要：必须为每个段落都返回结果，格式如下：
段落1: ["关键词1", "关键词2"]
段落2: []
段落3: ["关键词1"]
段落4: ["关键词1"]
段落5: []
段落6: ["关键词1"]
段落7: ["关键词1"]
段落8: []
段落9: ["关键词1"]
段落10: []
段落11: []
段落12: []

要求：
- 每个段落最多3个关键词
- 关键词简洁准确
- 无声音的段落必须返回[]
- 不要解释，直接返回结果
- 瞬间声音优先：叮、响、震动等
- 持续声音标准：脚步声、说话声、马蹄声等
- 必须按段落顺序返回，不能跳过任何段落
- 必须分析完所有段落，不能提前结束"""

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
        """解析批量分析的LLM响应 - 增强时序分析"""
        scenes = []
        
        # 首先尝试解析时序分析格式
        if self._is_timeline_analysis_format(response_text):
            logger.info("[BATCH_PARSER] 检测到时序分析格式，使用时序解析")
            scenes = self._parse_timeline_analysis_response(response_text)
        else:
            # 回退到原有的段落格式解析
            logger.info("[BATCH_PARSER] 使用原有段落格式解析")
            scenes = self._parse_legacy_batch_response(response_text)
        
        return scenes
    
    def _is_timeline_analysis_format(self, response_text: str) -> bool:
        """检测是否为时序分析格式"""
        # 检查是否包含时序分析的特征
        timeline_indicators = [
            "声音事件", "无声段", "开始时间", "持续时间", "强度"
        ]
        return any(indicator in response_text for indicator in timeline_indicators)
    
    def _parse_timeline_analysis_response(self, response_text: str) -> List[SceneAnalysis]:
        """解析时序分析响应 - 完全依赖LLM智能分析"""
        scenes = []
        
        logger.info("[TIMELINE_PARSER] 开始解析LLM时序分析响应")
        logger.info(f"[TIMELINE_PARSER] 原始响应: {response_text[:200]}...")
        
        # 预处理：移除Markdown格式
        cleaned_text = response_text.replace('**', '').replace('*', '')
        logger.info(f"[TIMELINE_PARSER] 清理后文本: {cleaned_text[:200]}...")
        
        # 解析声音事件（精确匹配）
        sound_event_pattern = r'-\\s*声音事件\\d+：([^0-9]+)\\s+([0-9.]+)s\\s+([0-9.]+)s\\s+([^0-9]+)\\s+(.+)'
        matches = re.findall(sound_event_pattern, cleaned_text)
        
        # 如果上面的模式没匹配到，尝试更宽松的模式
        if not matches:
            # 尝试匹配LLM实际返回的格式 - 修复正则表达式
            sound_event_pattern = r'声音事件\\d+：([^\\n]+)'
            matches = re.findall(sound_event_pattern, cleaned_text)
            logger.info(f"[TIMELINE_PARSER] 使用宽松模式匹配到 {len(matches)} 个声音事件")
            
            # 如果还是没有匹配到，尝试直接解析LLM输出
            if not matches:
                logger.info("[TIMELINE_PARSER] 尝试直接解析LLM输出(段落块解析)")
                # 逐段落解析：识别“段落X”开头，记录当前段落，提取每段的声音事件
                lines = cleaned_text.split('\n')
                current_segment = None
                segment_to_keywords = {}
                for raw_line in lines:
                    line = raw_line.strip()
                    if not line:
                        continue
                    # 段落标题：段落X： 或 段落X
                    m = re.match(r'^段落(\d+)[:：]?\s*$', line)
                    if m:
                        current_segment = int(m.group(1))
                        segment_to_keywords.setdefault(current_segment, [])
                        continue
                    # 声音事件行：- 声音事件1：空调声 0.0s 2.6s 低强度 描述
                    if '声音事件' in line and '：' in line and current_segment is not None:
                        parts = line.split('：', 1)
                        sound_part = parts[1].strip()
                        # 声音类型为第一个空格前的词
                        sound_type = sound_part.split()[0] if sound_part else ''
                        sound_type = sound_type.strip('，。；、!！?？')
                        if sound_type:
                            segment_to_keywords[current_segment].append(sound_type)
                            logger.info(f"[TIMELINE_PARSER] 段落{current_segment} 声音: {sound_type}")
                    # 无声段行：- 无声段：...
                    elif line.startswith('- 无声段') and current_segment is not None:
                        segment_to_keywords.setdefault(current_segment, [])
                        logger.info(f"[TIMELINE_PARSER] 段落{current_segment} 无声段")
                
                # 将段落关键词转为场景，保证按段落顺序输出
                if segment_to_keywords:
                    for seg_idx in sorted(segment_to_keywords.keys()):
                        kws = [kw.strip() for kw in segment_to_keywords[seg_idx] if kw.strip()]
                        scenes.append(SceneAnalysis(
                            location=f"detected_environment_segment_{seg_idx}",
                            keywords=kws[:3],
                            confidence=0.9 if kws else 0.8
                        ))
                    logger.info(f"[TIMELINE_PARSER] 段落块解析完成: {len(scenes)}个场景")
                else:
                    logger.info("[TIMELINE_PARSER] 段落块解析未提取到任何场景，回退到段落格式解析")
                    return self._parse_legacy_batch_response(response_text)
        
        for match in matches:
            if len(match) == 5:  # 完整格式
                sound_type, start_time, duration, intensity, description = match
            else:  # 简化格式，只提取声音类型
                sound_type = match.strip()
                start_time = "0.0"
                duration = "1.5"
                intensity = "中强度"
                description = sound_type
            sound_type = sound_type.strip()
            
            # 创建场景分析（保留LLM的完整信息）
            scenes.append(SceneAnalysis(
                location=f"{sound_type}_{start_time}s",
                keywords=[sound_type],  # 只保留声音类型，不添加额外信息
                confidence=0.95  # 时序分析更准确
            ))
            logger.info(f"[TIMELINE_PARSER] 声音事件: {sound_type} {start_time}s-{float(start_time)+float(duration):.1f}s {intensity}")
        
        # 如果没有找到声音事件，尝试解析无声段
        silent_pattern = r'-\\s*无声段：([0-9.]+)s\\s+([0-9.]+)s\\s+(.+)'
        silent_matches = re.findall(silent_pattern, cleaned_text)
        
        for match in silent_matches:
            start_time, duration, description = match
            scenes.append(SceneAnalysis(
                location=f"silent_{start_time}s",
                keywords=[],  # 无声段没有关键词
                confidence=0.90
            ))
            logger.info(f"[TIMELINE_PARSER] 无声段: {start_time}s-{float(start_time)+float(duration):.1f}s {description}")
        
        # 如果LLM返回了时序分析格式但没有解析到结果，不要回退到硬编码
        if not scenes:
            logger.warning("[TIMELINE_PARSER] LLM返回时序分析格式但未解析到结果，返回空列表")
            return []
        
        logger.info(f"[TIMELINE_PARSER] 时序解析完成: {len(scenes)}个场景")
        return scenes
    
    def _parse_legacy_batch_response(self, response_text: str) -> List[SceneAnalysis]:
        """解析原有的批量分析响应格式"""
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
                    if isinstance(keywords, list):
                        # 清理关键词
                        clean_keywords = [kw.strip() for kw in keywords if kw.strip()]
                        # 为每个段落都创建场景，即使关键词为空
                        scenes.append(SceneAnalysis(
                            location="detected_environment",
                            keywords=clean_keywords[:3],  # 最多3个
                            confidence=0.9 if clean_keywords else 0.8  # 空关键词的置信度稍低
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

    def _extract_sound_keyword_from_text(self, text: str) -> str:
        """智能提取声音关键词，不依赖硬编码列表"""
        if not text or not isinstance(text, str):
            return ""
        
        # 移除时间信息 (如 "0.0s", "1.5s", "中强度" 等)
        import re
        text = re.sub(r'\d+\.?\d*s', '', text)  # 移除时间
        text = re.sub(r'[高中低]强度', '', text)  # 移除强度描述
        text = re.sub(r'开始时间|持续时间|强度', '', text)  # 移除标签
        
        # 移除常见的描述性词汇
        descriptive_words = ['的', '声', '音', '响', '传来', '发出', '产生', '响起']
        for word in descriptive_words:
            text = text.replace(word, '')
        
        # 清理并提取核心声音词汇
        text = text.strip()
        
        # 如果文本太短或太长，可能不是有效的声音关键词
        if len(text) < 2 or len(text) > 10:
            return ""
        
        # 检查是否包含常见的声音相关字符
        sound_indicators = ['声', '音', '响', '鸣', '叫', '吼', '啸', '嗡', '叮', '咚', '啪', '砰']
        if not any(indicator in text for indicator in sound_indicators):
            # 如果没有声音指示符，检查是否是动作产生的声音
            action_sounds = ['步', '走', '跑', '跳', '敲', '打', '拍', '击', '撞', '摩擦']
            if not any(action in text for action in action_sounds):
                return ""
        
        return text

# 创建全局分析器实例
llm_scene_analyzer = OllamaLLMSceneAnalyzer()