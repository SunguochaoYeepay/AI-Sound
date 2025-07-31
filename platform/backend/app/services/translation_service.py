"""翻译服务
负责中文到英文的自动翻译功能
"""

import logging
import aiohttp
import json
import re
import os
from typing import Dict

logger = logging.getLogger(__name__)

class TranslationService:
    """翻译服务 - 使用Ollama进行中文到英文的翻译"""
    
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
        self.model = "qwen2.5:14b"  # 使用中文友好的模型
    
    async def translate_chinese_to_english(self, chinese_text: str) -> str:
        """将中文文本翻译为英文
        
        Args:
            chinese_text: 中文文本
            
        Returns:
            翻译后的英文文本
        """
        if not chinese_text or not chinese_text.strip():
            return ""
        
        # 检查是否已经是英文（简单判断）
        if self._is_likely_english(chinese_text):
            return chinese_text
        
        try:
            prompt = f"""请将以下中文文本翻译为英文，保持原意和语境。如果是图片生成提示词，请翻译为适合AI图片生成的英文提示词格式。

中文文本：{chinese_text}

英文翻译："""
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # 较低温度确保翻译准确性
                        "max_tokens": 1000,
                        "top_p": 0.9
                    }
                }
                
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        translated_text = result.get('response', '').strip()
                        
                        # 清理翻译结果
                        translated_text = self._clean_translation_result(translated_text)
                        
                        logger.info(f"翻译成功: {chinese_text[:50]}... -> {translated_text[:50]}...")
                        return translated_text
                    else:
                        logger.error(f"Ollama API调用失败: {response.status}")
                        return chinese_text  # 翻译失败时返回原文
                        
        except Exception as e:
            logger.error(f"翻译失败: {str(e)}")
            return chinese_text  # 翻译失败时返回原文
    
    def _is_likely_english(self, text: str) -> bool:
        """简单判断文本是否可能是英文"""
        if not text:
            return True
        
        # 计算ASCII字符比例
        ascii_chars = sum(1 for char in text if ord(char) < 128)
        total_chars = len(text)
        ascii_ratio = ascii_chars / total_chars if total_chars > 0 else 0
        
        # 如果ASCII字符比例超过80%，认为是英文
        return ascii_ratio > 0.8
    
    def _clean_translation_result(self, text: str) -> str:
        """清理翻译结果，移除不必要的前缀和后缀"""
        if not text:
            return ""
        
        # 按行分割，只取第一行作为翻译结果
        lines = text.strip().split('\n')
        cleaned_text = lines[0].strip()
        
        # 移除常见的翻译前缀
        prefixes_to_remove = [
            "英文翻译：",
            "English translation:",
            "English Translation:",
            "Translation:",
            "翻译：",
            "英文：",
            "English:",
            "英文提示词格式：",
            "如果需要用于AI图像生成的提示词，则可以这样写："
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned_text.startswith(prefix):
                cleaned_text = cleaned_text[len(prefix):].strip()
        
        # 移除引号
        if cleaned_text.startswith('"') and cleaned_text.endswith('"'):
            cleaned_text = cleaned_text[1:-1]
        
        # 如果清理后的文本为空或包含中文说明，尝试从其他行找翻译结果
        if not cleaned_text or any(char in cleaned_text for char in '如果需要用于则可以这样写'):
            for line in lines[1:]:
                line = line.strip()
                if line and not any(char in line for char in '如果需要用于则可以这样写：'):
                    # 移除可能的前缀
                    for prefix in prefixes_to_remove:
                        if line.startswith(prefix):
                            line = line[len(prefix):].strip()
                    if line:
                        cleaned_text = line
                        break
        
        return cleaned_text.strip()
    
    async def translate_prompt_pair(self, chinese_prompt: str, chinese_negative: str = "") -> Dict[str, str]:
        """翻译提示词对（正面和负面提示词）
        
        Args:
            chinese_prompt: 中文正面提示词
            chinese_negative: 中文负面提示词
            
        Returns:
            包含英文翻译的字典
        """
        result = {
            "english_prompt": "",
            "english_negative": ""
        }
        
        # 翻译正面提示词
        if chinese_prompt:
            result["english_prompt"] = await self.translate_chinese_to_english(chinese_prompt)
        
        # 翻译负面提示词
        if chinese_negative:
            result["english_negative"] = await self.translate_chinese_to_english(chinese_negative)
        
        return result