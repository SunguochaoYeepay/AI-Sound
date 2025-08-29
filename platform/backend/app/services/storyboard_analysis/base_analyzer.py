#!/usr/bin/env python3
"""
基础分析器
提供通用的分析接口
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from .llm_client import LLMClient

logger = logging.getLogger(__name__)


class BaseAnalyzer(ABC):
    """基础分析器"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    @abstractmethod
    async def analyze(self, content: str, **kwargs) -> List[Dict[str, Any]]:
        """分析内容"""
        raise NotImplementedError
    
    async def _call_llm(self, prompt: str, **kwargs) -> Optional[str]:
        """调用LLM"""
        return await self.llm_client.call(prompt, **kwargs)
    
    async def _call_llm_json(self, prompt: str, **kwargs) -> Optional[Dict[str, Any]]:
        """调用LLM并解析JSON"""
        return await self.llm_client.call_json(prompt, **kwargs)
    
    def _validate_content(self, content: str) -> bool:
        """验证内容"""
        if not content or not content.strip():
            logger.warning("内容为空")
            return False
        return True
    
    def _chunk_content(self, content: str, max_length: int = 3000) -> List[str]:
        """分块处理长内容"""
        if len(content) <= max_length:
            return [content]
        
        # 简单的按段落分块
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
