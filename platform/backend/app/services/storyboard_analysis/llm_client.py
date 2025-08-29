#!/usr/bin/env python3
"""
AI客户端封装
支持Ollama、OpenAI等LLM调用
"""

import asyncio
import json
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class LLMClient:
    """AI客户端封装"""
    
    def __init__(self, model: str = "qwen2.5:7b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.timeout = 30
    
    async def call(self, prompt: str, **kwargs) -> Optional[str]:
        """调用LLM"""
        try:
            # 构建请求参数
            request_data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "top_p": kwargs.get("top_p", 0.9),
                    "max_tokens": kwargs.get("max_tokens", 4000)
                }
            }
            
            # 发送请求
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=request_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.error(f"LLM调用失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"LLM调用异常: {str(e)}")
            return None
    
    async def call_json(self, prompt: str, **kwargs) -> Optional[Dict[str, Any]]:
        """调用LLM并解析JSON响应"""
        try:
            response = await self.call(prompt, **kwargs)
            if response:
                # 清理响应中的markdown标记
                cleaned_response = response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()
                
                # 尝试解析JSON
                return json.loads(cleaned_response)
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}")
            logger.error(f"原始响应: {response}")
            return None
        except Exception as e:
            logger.error(f"JSON调用异常: {str(e)}")
            return None
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return False
