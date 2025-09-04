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
import re

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
                # 清理响应中的markdown标记和思考过程
                cleaned_response = self._clean_llm_response(response)
                
                # 尝试解析JSON
                try:
                    return json.loads(cleaned_response)
                except json.JSONDecodeError as e:
                    logger.warning(f"直接JSON解析失败，尝试提取JSON: {str(e)}")
                    # 尝试从响应中提取JSON部分
                    extracted_json = self._extract_json_from_response(cleaned_response)
                    if extracted_json:
                        return json.loads(extracted_json)
                    else:
                        logger.error(f"无法提取有效JSON，原始响应: {response[:200]}...")
                        return None
            return None
            
        except Exception as e:
            logger.error(f"JSON调用异常: {str(e)}")
            return None
    
    def _clean_llm_response(self, response: str) -> str:
        """清理LLM响应，移除markdown标记和思考过程"""
        try:
            # 移除思考过程标签
            response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
            
            # 移除markdown代码块标记
            response = re.sub(r'```json\s*', '', response)
            response = re.sub(r'```\s*$', '', response)
            
            # 移除多余的空白字符
            response = response.strip()
            
            # 如果响应以{开头，尝试找到匹配的}结尾
            if response.startswith('{'):
                # 找到最后一个完整的JSON对象
                brace_count = 0
                end_pos = -1
                for i, char in enumerate(response):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_pos = i
                            break
                
                if end_pos > 0:
                    response = response[:end_pos + 1]
            
            return response
            
        except Exception as e:
            logger.error(f"清理响应失败: {str(e)}")
            return response
    
    def _extract_json_from_response(self, response: str) -> Optional[str]:
        """从响应中提取JSON部分"""
        try:
            # 查找JSON对象的开始和结束
            start_pos = response.find('{')
            if start_pos == -1:
                return None
            
            # 计算括号匹配
            brace_count = 0
            end_pos = -1
            
            for i in range(start_pos, len(response)):
                char = response[i]
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i
                        break
            
            if end_pos > start_pos:
                json_str = response[start_pos:end_pos + 1]
                # 验证JSON有效性
                try:
                    json.loads(json_str)
                    return json_str
                except json.JSONDecodeError:
                    pass
            
            return None
            
        except Exception as e:
            logger.error(f"提取JSON失败: {str(e)}")
            return None
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return False
