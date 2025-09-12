"""
AI TTS参数优化器服务
基于大模型智能分析文本内容和角色特征，生成最佳TTS参数配置
优化版：旁白使用默认值，减少token消耗
"""

import json
import logging
import os
import requests
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AITTSOptimizer:
    """AI TTS参数优化器 - 优化版，旁白使用默认值"""
    
    # 旁白默认参数（不走AI分析）
    NARRATOR_DEFAULT_PARAMS = {
        "timeStep": 32,
        "pWeight": 2.0,
        "tWeight": 3.0
    }
    
    # 角色类型默认参数
    CHARACTER_DEFAULT_PARAMS = {
        "timeStep": 30,
        "pWeight": 1.4,
        "tWeight": 3.0
    }
    
    def __init__(self, ollama_detector=None):
        self.ollama_detector = ollama_detector
        self.enable_ai_analysis = True  # 可以通过环境变量控制
    
    def get_smart_tts_params(self, segment: Dict, detected_characters: List[Dict]) -> Dict:
        """🎯 智能TTS参数配置 - 优化版"""
        
        speaker = segment.get('speaker', '旁白')
        text = segment.get('text', '')
        emotion = segment.get('emotion', 'neutral')
        
        # 🔧 优化1：旁白直接使用默认参数，不走AI分析
        if '旁白' in speaker or speaker == 'narrator':
            logger.debug(f"旁白使用默认参数: {self.NARRATOR_DEFAULT_PARAMS}")
            return {
                **self.NARRATOR_DEFAULT_PARAMS,
                "narrator_mode": True,
                "skip_ai_analysis": True
            }
        
        # 🔧 优化2：短文本（<20字符）使用默认参数
        if len(text.strip()) < 20:
            logger.debug(f"短文本使用默认参数: {text[:10]}...")
            return {
                **self.CHARACTER_DEFAULT_PARAMS,
                "short_text_mode": True
            }
        
        # 🔧 优化3：neutral情感的普通对话也可以使用默认参数
        if emotion == 'neutral' and len(text) < 50:
            logger.debug(f"中性短对话使用默认参数: {text[:15]}...")
            return {
                **self.CHARACTER_DEFAULT_PARAMS,
                "neutral_mode": True
            }
        
        # 只对真正需要分析的内容使用AI
        if self.enable_ai_analysis:
            try:
                ai_params = self._ai_analyze_tts_params(segment, detected_characters)
                if ai_params:
                    return ai_params
                else:
                    logger.warning(f"AI TTS参数分析返回空结果")
                    return self.CHARACTER_DEFAULT_PARAMS
            except Exception as e:
                logger.error(f"AI TTS参数分析失败: {str(e)}")
                return self.CHARACTER_DEFAULT_PARAMS
        
        # 快速模式：直接使用默认参数
        return self.CHARACTER_DEFAULT_PARAMS
    
    def _ai_analyze_tts_params(self, segment: Dict, detected_characters: List[Dict]) -> Dict:
        """使用AI智能分析TTS参数 - 简化版提示词"""
        
        speaker = segment.get('speaker', '旁白')
        text = segment.get('text', '')
        emotion = segment.get('emotion', 'neutral')
        
        # 找到角色详细信息
        character_info = None
        for char in detected_characters:
            if char.get('name') == speaker:
                character_info = char
                break
        
        # 🔧 优化：使用简化的提示词
        prompt = self._build_simplified_tts_prompt(segment, character_info)
        
        # 调用Ollama分析
        response = self._call_ollama_for_tts(prompt)
        
        if response:
            return self._parse_tts_analysis_response(response)
        
        return None
    
    def _build_simplified_tts_prompt(self, segment: Dict, character_info: Dict = None) -> str:
        """构建简化的TTS参数分析提示词 - 大幅减少token消耗"""
        
        speaker = segment.get('speaker', '旁白')
        text = segment.get('text', '')
        emotion = segment.get('emotion', 'neutral')
        
        # 角色特征简化描述
        char_traits = "普通角色"
        if character_info:
            gender = character_info.get('gender', 'unknown')
            personality = character_info.get('personality', 'calm')
            char_traits = f"{gender}/{personality}"
        
        # 🔧 大幅简化的提示词
        prompt = f"""分析TTS参数。

角色: {speaker} ({char_traits})
文本: "{text}"
情感: {emotion}

参数范围:
- timeStep: 20-40 (质量vs速度)
- pWeight: 1.0-2.5 (清晰度)  
- tWeight: 2.0-4.0 (表现力)

参考配置:
- 标准对话: timeStep=30, pWeight=1.4, tWeight=3.0
- 激烈情感: timeStep=28, pWeight=1.6, tWeight=3.5
- 温柔角色: timeStep=32, pWeight=1.2, tWeight=2.8

输出JSON:
{{"timeStep": 数值, "pWeight": 数值, "tWeight": 数值, "reason": "简短理由"}}"""
        
        return prompt
    
    def _call_ollama_for_tts(self, prompt: str) -> Optional[str]:
        """调用Ollama进行TTS参数分析 - 优化超时和参数"""
        try:
            # 尝试复用现有的Ollama检测器
            if hasattr(self, 'ollama_detector') and self.ollama_detector:
                response = self.ollama_detector._call_ollama(prompt)
                return response
            else:
                # 直接调用Ollama API
                from app.utils.llm_config_loader import llm_config_loader
                config = llm_config_loader.get_config()
                ollama_url = config["base_url"]
                api_url = f"{ollama_url}/api/generate"
                
                payload = {
                    "model": config["model"],
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # 降低温度，更确定的输出
                        "top_p": 0.9,
                        "max_tokens": 200,   # 🔧 大幅减少max_tokens
                        "num_ctx": 1024      # 🔧 减少上下文长度
                    }
                }
                
                # 🔧 减少超时时间
                response = requests.post(api_url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('response', '')
                
                return None
                
        except Exception as e:
            logger.error(f"Ollama TTS参数分析调用失败: {str(e)}")
            return None
    
    def _parse_tts_analysis_response(self, response: str) -> Dict:
        """解析AI的TTS参数分析结果"""
        try:
            # 提取JSON部分
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                # 验证参数范围
                time_step = int(data.get('timeStep', 30))
                p_w = float(data.get('pWeight', 1.4))
                t_w = float(data.get('tWeight', 3.0))
                
                # 参数范围检查和修正
                time_step = max(20, min(40, time_step))
                p_w = max(1.0, min(2.5, p_w))
                t_w = max(2.0, min(4.0, t_w))
                
                reasoning = data.get('reason', data.get('reasoning', 'AI分析'))
                
                # 🔧 简化日志输出
                logger.info(f"AI TTS: timeStep={time_step}, pWeight={p_w}, tWeight={t_w}")
                logger.debug(f"分析理由: {reasoning}")
                
                return {
                    "timeStep": time_step,
                    "pWeight": round(p_w, 1),
                    "tWeight": round(t_w, 1),
                    "ai_reasoning": reasoning
                }
            
            return None
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"解析AI TTS参数失败: {str(e)}")
            return None
    

    
    def set_enable_ai_analysis(self, enabled: bool):
        """设置是否启用AI分析（可用于性能调优）"""
        self.enable_ai_analysis = enabled
        logger.info(f"AI TTS分析{'启用' if enabled else '禁用'}") 