"""
AI TTS参数优化器服务
基于大模型智能分析文本内容和角色特征，生成最佳TTS参数配置
"""

import json
import logging
import os
import requests
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AITTSOptimizer:
    """AI TTS参数优化器 - 基于大模型智能分析"""
    
    def __init__(self, ollama_detector=None):
        self.ollama_detector = ollama_detector
    
    def get_smart_tts_params(self, segment: Dict, detected_characters: List[Dict]) -> Dict:
        """🎯 AI智能TTS参数配置 - 基于大模型分析，而非硬编码规则"""
        
        speaker = segment.get('speaker', '旁白')
        text = segment.get('text', '')
        emotion = segment.get('emotion', 'neutral')
        
        try:
            # 尝试调用AI智能分析TTS参数
            ai_params = self._ai_analyze_tts_params(segment, detected_characters)
            if ai_params:
                return ai_params
        except Exception as e:
            logger.warning(f"AI TTS参数分析失败，降级到规则模式: {str(e)}")
        
        # 降级方案：使用简化规则（不再有复杂硬编码）
        return self._fallback_tts_params(speaker, text, emotion)
    
    def _ai_analyze_tts_params(self, segment: Dict, detected_characters: List[Dict]) -> Dict:
        """使用AI智能分析TTS参数"""
        
        # 获取角色信息
        speaker = segment.get('speaker', '旁白')
        text = segment.get('text', '')
        emotion = segment.get('emotion', 'neutral')
        
        # 找到角色详细信息
        character_info = None
        for char in detected_characters:
            if char.get('name') == speaker:
                character_info = char
                break
        
        # 构建AI分析提示词
        prompt = self._build_tts_analysis_prompt(segment, character_info)
        
        # 调用Ollama分析
        response = self._call_ollama_for_tts(prompt)
        
        if response:
            return self._parse_tts_analysis_response(response)
        
        return None
    
    def _build_tts_analysis_prompt(self, segment: Dict, character_info: Dict = None) -> str:
        """构建TTS参数分析提示词"""
        
        speaker = segment.get('speaker', '旁白')
        text = segment.get('text', '')
        emotion = segment.get('emotion', 'neutral')
        
        character_desc = "未知角色"
        if character_info:
            personality = character_info.get('personality', 'calm')
            gender = character_info.get('gender', 'unknown')
            desc = character_info.get('personality_description', '')
            character_desc = f"{gender}角色，性格{personality}，{desc}"
        
        prompt = f"""你是专业的语音合成参数调优专家。请根据以下信息分析并生成最佳的TTS参数配置。

当前段落信息：
- 说话者：{speaker}
- 文本内容："{text}"
- 检测情感：{emotion}
- 角色特征：{character_desc}

TTS参数说明：
- timeStep (10-40)：推理步数，影响生成质量和速度
  * 20-25：快速生成，适合短句
  * 30-35：标准质量，适合一般对话
  * 35-40：高质量，适合重要台词
  
- pWeight (1.0-2.5)：发音强度权重，控制清晰度
  * 1.0-1.5：保持自然口音，适合温柔角色
  * 1.5-2.0：标准清晰度，适合一般对话
  * 2.0-2.5：高清晰度，适合旁白或激烈情感
  
- tWeight (2.0-5.0)：音色相似度权重，控制表现力
  * 2.0-3.0：基础相似度，保持稳定
  * 3.0-4.0：增强表现力，适合情感对话
  * 4.0-5.0：强烈表现力，适合剧烈情感

应用场景参考：
- 标准语音合成：pWeight=2.0, tWeight=3.0
- 方言/口音保留：pWeight=1.0-1.5, tWeight=3.0-5.0  
- 情感语音（惊喜/悲伤）：pWeight=1.5-2.5, tWeight≥3.0
- 含噪声参考音频：pWeight≥3.0, tWeight≥3.0
- 旁白叙述：pWeight=2.0, tWeight=3.0
- 温柔角色：pWeight=1.2, tWeight=2.8
- 激烈角色：pWeight=1.6, tWeight=3.2

请基于文本内容、角色特征、情感状态进行智能分析，输出最适合的参数。

输出格式（仅输出JSON）：
{{
    "timeStep": 数值,
    "pWeight": 数值,
    "tWeight": 数值,
    "reasoning": "参数选择的分析依据"
}}"""
        
        return prompt
    
    def _call_ollama_for_tts(self, prompt: str) -> Optional[str]:
        """调用Ollama进行TTS参数分析"""
        try:
            # 尝试复用现有的Ollama检测器
            if hasattr(self, 'ollama_detector') and self.ollama_detector:
                # 使用简化的调用方式
                response = self.ollama_detector._call_ollama(prompt)
                return response
            else:
                # 直接调用Ollama API
                ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
                api_url = f"{ollama_url}/api/generate"
                
                payload = {
                    "model": "qwen3:30b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.8,
                        "max_tokens": 500,
                        "num_ctx": 2048
                    }
                }
                
                response = requests.post(api_url, json=payload, timeout=60)
                
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
                time_step = int(data.get('timeStep', 32))
                p_w = float(data.get('pWeight', 1.4))
                t_w = float(data.get('tWeight', 3.0))
                
                # 参数范围检查和修正
                time_step = max(10, min(40, time_step))
                p_w = max(1.0, min(2.5, p_w))
                t_w = max(2.0, min(5.0, t_w))
                
                reasoning = data.get('reasoning', 'AI智能分析')
                
                logger.info(f"AI TTS参数分析: timeStep={time_step}, pWeight={p_w}, tWeight={t_w}, 原因: {reasoning}")
                
                return {
                    "timeStep": time_step,
                    "pWeight": round(p_w, 2),
                    "tWeight": round(t_w, 2),
                    "ai_reasoning": reasoning
                }
            
            return None
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"解析AI TTS参数失败: {str(e)}, 响应: {response[:200]}")
            return None
    
    def _fallback_tts_params(self, speaker: str, text: str, emotion: str) -> Dict:
        """降级方案：简化的规则配置（最小化硬编码）"""
        
        # 基础参数
        time_step = 32
        p_w = 1.4
        t_w = 3.0
        
        # 只保留最核心的区分规则
        if '旁白' in speaker:
            # 旁白：标准清晰
            p_w = 2.0
            t_w = 3.0
        elif emotion in ['angry', 'excited']:
            # 激烈情感：增强表现力
            p_w = 1.6
            t_w = 3.5
        elif emotion in ['sad', 'gentle']:
            # 温柔情感：柔和自然
            p_w = 1.2
            t_w = 2.8
        
        # 基于文本长度的简单调整
        if len(text) > 50:
            time_step = 35  # 长文本提高质量
        elif len(text) < 20:
            time_step = 28  # 短文本快速生成
            
        return {
            "timeStep": time_step,
            "pWeight": p_w,
            "tWeight": t_w,
            "fallback_mode": True
        } 