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
            logger.info("开始事件分析...")
            
            # 强制使用AI分析，不进行健康检查
            chunks = self._chunk_content(content)
            logger.info(f"内容分块数量: {len(chunks)}")
            all_events = []
            
            for i, chunk in enumerate(chunks):
                logger.info(f"分析事件块 {i+1}/{len(chunks)}")
                logger.info(f"块内容长度: {len(chunk)}")
                
                # 构建提示词
                prompt = self._build_prompt(chunk, chunk_index=i, total_chunks=len(chunks))
                
                # 强制调用AI分析
                logger.info("调用AI分析...")
                result = await self._call_llm_json(prompt, temperature=0.3)
                
                if result and "events" in result:
                    events = result["events"]
                    logger.info(f"AI识别到 {len(events)} 个事件")
                    # 为每个事件添加块索引信息
                    for event in events:
                        event["chunk_index"] = i
                        event["chunk_total"] = len(chunks)
                    all_events.extend(events)
                else:
                    logger.error(f"AI分析失败，返回结果: {result}")
                    raise Exception(f"AI分析失败，无法获取事件数据")
            
            # 合并和去重事件
            merged_events = self._merge_events(all_events)
            
            logger.info(f"事件分析完成，识别到 {len(merged_events)} 个事件")
            for i, event in enumerate(merged_events):
                logger.info(f"事件 {i+1}: {event.get('event_name', 'Unknown')}")
            
            return merged_events
            
        except Exception as e:
            logger.error(f"事件分析失败: {str(e)}")
            raise Exception(f"事件分析失败: {str(e)}")
    
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

重要：请仔细识别并提取所有对话内容，包括引号内的对话和说话者。
"""
            return prompt + EVENT_ANALYSIS_PROMPT_SIMPLE.format(content=content)
        else:
            # 单块处理
            enhanced_prompt = """
你是一个专业的文学分析专家，专门分析小说中的事件信息。

请分析以下小说章节中的关键事件：

原文内容：
{content}

请识别并分析所有重要事件，每个事件包含以下信息：

1. **事件名称**：简洁描述事件的核心内容
2. **事件类型**：对话/动作/描述/特殊/转折等
3. **参与者**：参与事件的所有角色
4. **动作描述**：详细的动作和情节描述
5. **对话内容**：如果有对话，必须提取完整的对话内容和说话者
6. **情感上下文**：事件发生时的情感氛围和紧张度

分析要求：
- 识别推动情节发展的关键事件
- **必须准确提取所有对话内容和说话者**
- 注意事件的因果关系
- 分析事件对角色发展的影响

特别注意：
- 仔细查找引号内的对话内容
- 根据上下文推断说话者身份
- 确保每个对话都有明确的说话者

请以JSON格式返回分析结果：

{{
  "events": [
    {{
      "event_name": "事件名称",
      "event_type": "事件类型",
      "participants": ["角色1", "角色2"],
      "action_description": "详细的动作描述",
      "dialogue_content": [
        {{
          "speaker": "说话者",
          "content": "对话内容"
        }}
      ],
      "emotional_context": {{
        "mood": "情绪氛围",
        "tension": "紧张度",
        "importance": "重要性"
      }}
    }}
  ]
}}

请确保返回的是有效的JSON格式，不要包含其他文字说明。
"""
            return enhanced_prompt.format(content=content)
    
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
