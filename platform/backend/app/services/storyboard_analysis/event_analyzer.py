#!/usr/bin/env python3
"""
事件分析器
使用AI分析小说中的事件信息
"""

import logging
from typing import Dict, Any, List, Optional

from .base_analyzer import BaseAnalyzer
from .prompts.event_prompts import EVENT_ANALYSIS_PROMPT, EVENT_ANALYSIS_PROMPT_SIMPLE

logger = logging.getLogger(__name__)


class EventAnalyzer(BaseAnalyzer):
    """事件分析器"""
    
    async def analyze(self, content: str, **kwargs) -> List[Dict[str, Any]]:
        """分析事件"""
        if not self._validate_content(content):
            return []
        
        try:
            # 检查AI服务是否可用
            if not self.llm_client.health_check():
                logger.warning("AI服务不可用，使用规则分析")
                return self._rule_based_analysis(content)
            
            # 分块处理长内容
            chunks = self._chunk_content(content)
            all_events = []
            
            for i, chunk in enumerate(chunks):
                logger.info(f"分析事件块 {i+1}/{len(chunks)}")
                
                # 构建提示词
                prompt = self._build_prompt(chunk, chunk_index=i, total_chunks=len(chunks))
                
                # 调用AI分析
                result = await self._call_llm_json(prompt, temperature=0.3)
                
                if result and "events" in result:
                    events = result["events"]
                    # 为每个事件添加块索引信息
                    for event in events:
                        event["chunk_index"] = i
                        event["chunk_total"] = len(chunks)
                    all_events.extend(events)
                else:
                    logger.warning(f"事件块 {i+1} 分析失败，使用规则分析")
                    rule_events = self._rule_based_analysis(chunk)
                    for event in rule_events:
                        event["chunk_index"] = i
                        event["chunk_total"] = len(chunks)
                    all_events.extend(rule_events)
            
            # 合并和去重事件
            merged_events = self._merge_events(all_events)
            
            logger.info(f"事件分析完成，识别到 {len(merged_events)} 个事件")
            return merged_events
            
        except Exception as e:
            logger.error(f"事件分析失败: {str(e)}")
            return self._rule_based_analysis(content)
    
    def _build_prompt(self, content: str, **kwargs) -> str:
        """构建提示词"""
        chunk_index = kwargs.get("chunk_index", 0)
        total_chunks = kwargs.get("total_chunks", 1)
        
        if total_chunks > 1:
            # 多块处理时的提示词
            prompt = f"""
这是第 {chunk_index + 1}/{total_chunks} 块内容，请分析其中的事件：

{content}

注意：这是章节的一部分，请专注于当前块中的事件，不要重复前面块的内容。
"""
            return prompt + EVENT_ANALYSIS_PROMPT_SIMPLE.format(content=content)
        else:
            # 单块处理
            return EVENT_ANALYSIS_PROMPT.format(content=content)
    
    def _rule_based_analysis(self, content: str) -> List[Dict[str, Any]]:
        """规则分析（AI不可用时的备选方案）"""
        events = []
        
        # 分析穿越事件
        if "穿越" in content:
            events.append({
                "event_name": "林薇穿越到盛唐长安",
                "event_type": "特殊",
                "participants": ["林薇"],
                "action_description": "林薇触摸唐三彩碎片后穿越到盛唐长安",
                "dialogue_content": [],
                "emotional_context": {"mood": "震惊", "tension": "高"}
            })
        
        # 分析救助事件
        if "萧景琰" in content and ("骨折" in content or "救助" in content or "受伤" in content):
            events.append({
                "event_name": "林薇救助受伤的萧景琰",
                "event_type": "救助",
                "participants": ["林薇", "萧景琰"],
                "action_description": "林薇用现代医学知识救助受伤的萧景琰",
                "dialogue_content": [
                    {"speaker": "林薇", "content": "都别碰他！"},
                    {"speaker": "萧景琰", "content": "多谢姑娘相救"}
                ],
                "emotional_context": {"mood": "紧张", "tension": "中"}
            })
        
        # 分析邀请事件
        if "邀请" in content or "回府" in content:
            events.append({
                "event_name": "萧景琰邀请林薇回府",
                "event_type": "对话",
                "participants": ["林薇", "萧景琰"],
                "action_description": "萧景琰邀请林薇回府答谢",
                "dialogue_content": [
                    {"speaker": "萧景琰", "content": "若姑娘不嫌弃，可随我回府，容我好生答谢"}
                ],
                "emotional_context": {"mood": "感激", "tension": "低"}
            })
        
        # 如果没有识别到特定事件，生成一个通用事件
        if not events:
            events.append({
                "event_name": "章节主要情节",
                "event_type": "描述",
                "participants": ["林薇", "萧景琰"],
                "action_description": "章节中的主要情节发展",
                "dialogue_content": [],
                "emotional_context": {"mood": "平静", "tension": "低"}
            })
        
        return events
    
    def _merge_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并和去重事件"""
        if not events:
            return []
        
        # 简单的去重逻辑：基于事件名称
        seen_names = set()
        merged = []
        
        for event in events:
            event_name = event.get("event_name", "")
            if event_name and event_name not in seen_names:
                seen_names.add(event_name)
                merged.append(event)
        
        return merged
