"""
Ollama AI角色检测器
使用大语言模型进行智能角色识别和分析
"""

import json
import logging
import os
import requests
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class OllamaCharacterDetector:
    """使用Ollama进行角色分析的检测器 - 主力方案"""
    
    def __init__(self, model_name: str = "qwen3:30b", ollama_url: str = None):
        self.model_name = model_name
        # 优先使用环境变量，支持Docker部署
        self.ollama_url = ollama_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.api_url = f"{self.ollama_url}/api/generate"
        
    async def analyze_text(self, text: str, chapter_info: dict) -> dict:
        """使用Ollama分析文本中的角色 - 直接AI分析，简单高效"""
        try:
            from ...utils.websocket_manager import send_analysis_progress
        except ImportError:
            # 如果相对导入失败，尝试绝对导入
            try:
                from app.utils.websocket_manager import send_analysis_progress
            except ImportError:
                # 如果都失败，定义一个mock函数
                async def send_analysis_progress(session_id, progress, message):
                    logger.info(f"[进度 {progress}%] {message}")
                logger.warning("无法导入websocket_manager，使用日志记录进度")
        
        start_time = time.time()
        session_id = chapter_info.get('session_id', chapter_info['chapter_id'])
        
        try:
            # 发送开始分析进度
            await send_analysis_progress(session_id, 10, f"开始分析章节: {chapter_info['chapter_title']}")
            
            # 1. 直接调用Ollama进行全文分析（包括角色识别和文本分段）
            await send_analysis_progress(session_id, 30, "正在调用AI模型进行角色识别...")
            
            prompt = self._build_comprehensive_analysis_prompt(text)
            response = self._call_ollama(prompt)
            
            processing_time = time.time() - start_time
            
            if response:
                await send_analysis_progress(session_id, 80, "正在解析AI分析结果...")
                
                # 解析Ollama返回的完整结果
                result = self._parse_comprehensive_response(response)
                
                await send_analysis_progress(session_id, 100, f"分析完成，识别到{len(result['characters'])}个角色")
                
                # 智能分析阶段：返回所有识别到的角色（不过滤已存在的）
                all_characters = result['characters']
                
                return {
                    "chapter_id": chapter_info['chapter_id'],
                    "chapter_title": chapter_info['chapter_title'],
                    "chapter_number": chapter_info['chapter_number'],
                    "detected_characters": all_characters,  # 返回所有角色
                    "segments": result['segments'],
                    "processing_stats": {
                        "total_segments": len(result['segments']),
                        "dialogue_segments": len([s for s in result['segments'] if s['text_type'] == 'dialogue']),
                        "narration_segments": len([s for s in result['segments'] if s['text_type'] == 'narration']),
                        "characters_found": len(result['characters']),
                        "new_characters_found": len(result['characters']),
                        "analysis_method": "ollama_ai_primary",
                        "processing_time": round(processing_time, 2),
                        "text_length": len(text),
                        "ai_model": self.model_name
                    }
                }
            else:
                # Ollama调用失败，直接抛出错误
                logger.error("❌ Ollama API调用失败，没有返回有效响应")
                await send_analysis_progress(session_id, 0, "AI分析失败")
                raise Exception("Ollama API调用失败，没有返回有效响应")
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Ollama角色分析异常失败: {str(e)}")
            await send_analysis_progress(session_id, 0, f"AI分析失败: {str(e)}")
            raise Exception(f"Ollama角色分析失败: {str(e)}")
    
# 回退逻辑已移除 - 大模型失败就是失败！

    def _build_comprehensive_analysis_prompt(self, text: str) -> str:
        """构建综合分析提示词"""
        # 限制文本长度，避免超时
        limited_text = text[:1500] if len(text) > 1500 else text
        
        prompt = f"""你是一个专业的中文小说文本分析专家。请分析以下小说文本，识别角色并正确分段。

文本：
{limited_text}

分析要求：
1. 识别所有说话的角色（包括旁白）
2. 将文本按句子分段，每段标记正确的说话者
3. **核心要求**：正确分离混合对话文本

关键分段规则：
- 混合文本如"项羽冷笑一声："你又是何人？""必须分为两段：
  第一段："项羽冷笑一声：" → 说话者：旁白
  第二段："你又是何人？" → 说话者：项羽
- 所有"某某说："、"某某道："、"某某低声道："等描述性动作文字都是旁白
- 只有引号""内的实际对话内容才是角色发言
- 纯叙述文字（如"只见山势险峻"、"此时天色已晚"）都是旁白

输出格式（严格JSON）：
{{
  "segments": [
    {{"order": 1, "text": "文本内容", "speaker": "说话者", "text_type": "dialogue/narration", "confidence": 0.9}}
  ],
  "characters": [
    {{"name": "角色名", "frequency": 出现次数, "gender": "male/female/neutral", "personality": "calm/brave/gentle", "personality_description": "性格描述", "is_main_character": true/false, "confidence": 0.8}}
  ]
}}

重要提醒：
- 角色名必须完整（如"孙悟空"而不是"悟空"）
- 严格区分叙述（旁白）和对话（角色）
- 必须正确分离动作描述和实际对话
- 只输出JSON，不要任何其他文字"""
        
        return prompt

    def _call_ollama(self, prompt: str) -> Optional[str]:
        """调用Ollama API"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "top_p": 0.8,
                    "max_tokens": 2000,
                    "num_ctx": 4096
                }
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=180
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                logger.error(f"Ollama API调用失败: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Ollama API调用超时")
            return None
        except Exception as e:
            logger.error(f"Ollama API调用异常: {str(e)}")
            return None
    
    def _parse_comprehensive_response(self, response: str) -> Dict:
        """解析Ollama返回的综合分析结果"""
        try:
            # 记录原始响应用于调试
            logger.info(f"Ollama原始响应: {response[:500]}...")
            
            # 提取JSON部分
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                logger.info(f"解析的JSON数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
                
                # 处理segments
                segments = []
                for i, seg_data in enumerate(data.get('segments', [])):
                    segments.append({
                        'order': seg_data.get('order', i + 1),
                        'text': seg_data.get('text', ''),
                        'speaker': seg_data.get('speaker', '旁白'),
                        'confidence': seg_data.get('confidence', 0.8),
                        'detection_rule': 'ollama_ai',
                        'text_type': seg_data.get('text_type', 'narration')
                    })
                
                # 处理characters
                characters = []
                for char_data in data.get('characters', []):
                    if isinstance(char_data, dict) and 'name' in char_data:
                        name = char_data.get('name', '')
                        if name and len(name) >= 2:
                            characters.append({
                                'name': name,
                                'frequency': char_data.get('frequency', 1),
                                'character_trait': {
                                    'trait': char_data.get('personality', 'calm'),
                                    'confidence': char_data.get('confidence', 0.8),
                                    'description': char_data.get('personality_description', '性格特征待分析')
                                },
                                'first_appearance': 1,
                                'is_main_character': char_data.get('is_main_character', False),
                                'recommended_config': {
                                    'gender': self._infer_gender_smart(name, char_data.get('gender', 'unknown')),
                                    'personality': char_data.get('personality', 'calm'),
                                    'personality_description': char_data.get('personality_description', '性格特征待分析'),
                                    'personality_confidence': char_data.get('confidence', 0.8),
                                    'description': f"{name}，{self._infer_gender_smart(name, char_data.get('gender', 'unknown'))}角色，{char_data.get('personality_description', '性格特征待分析')}，在文本中出现{char_data.get('frequency', 1)}次。",
                                    'recommended_tts_params': self._get_tts_params(char_data.get('personality', 'calm')),
                                    'voice_type': f"{self._infer_gender_smart(name, char_data.get('gender', 'unknown'))}_{char_data.get('personality', 'calm')}",
                                    'color': self._get_character_color(char_data.get('personality', 'calm'))
                                }
                            })
                
                return {
                    'segments': segments,
                    'characters': characters
                }
            
            else:
                logger.error("无法从Ollama响应中提取JSON数据")
                return {'segments': [], 'characters': []}
                
        except json.JSONDecodeError as e:
            logger.error(f"解析Ollama JSON响应失败: {str(e)}")
            logger.error(f"原始响应: {response}")
            return {'segments': [], 'characters': []}
        except Exception as e:
            logger.error(f"处理Ollama响应异常: {str(e)}")
            return {'segments': [], 'characters': []}

    def _get_tts_params(self, personality: str) -> Dict:
        """根据性格获取TTS参数"""
        params_map = {
            'gentle': {'time_step': 35, 'p_w': 1.2, 't_w': 2.8},
            'fierce': {'time_step': 28, 'p_w': 1.6, 't_w': 3.2},
            'calm': {'time_step': 32, 'p_w': 1.4, 't_w': 3.0},
            'lively': {'time_step': 30, 'p_w': 1.3, 't_w': 2.9},
            'wise': {'time_step': 34, 'p_w': 1.3, 't_w': 3.1},
            'brave': {'time_step': 29, 'p_w': 1.5, 't_w': 3.1}
        }
        return params_map.get(personality, {'time_step': 32, 'p_w': 1.4, 't_w': 3.0})
    
    def _get_character_color(self, personality: str) -> str:
        """根据性格获取角色颜色"""
        color_map = {
            'gentle': '#FFB6C1',  # 浅粉色
            'fierce': '#FF6347',  # 番茄红
            'calm': '#06b6d4',   # 青色
            'lively': '#32CD32', # 绿色
            'wise': '#9370DB',   # 紫色
            'brave': '#FF8C00'   # 橙色
        }
        return color_map.get(personality, '#06b6d4')
    
    def _infer_gender_smart(self, name: str, ai_gender: str) -> str:
        """智能推断角色性别 - 完全依赖AI判断，移除硬编码"""
        # 如果AI已经正确识别了性别，直接使用
        if ai_gender and ai_gender in ['male', 'female', 'neutral']:
            return ai_gender
        
        # 如果AI没有返回性别信息，调用专门的性别识别AI
        try:
            gender = self._ai_infer_gender(name)
            if gender in ['male', 'female', 'neutral']:
                logger.info(f"AI推断角色 '{name}' 性别: {gender}")
                return gender
        except Exception as e:
            logger.warning(f"AI性别推断失败: {str(e)}")
        
        # 默认返回unknown，让用户手动选择
        logger.warning(f"无法推断角色 '{name}' 的性别")
        return 'unknown'
    
    def _ai_infer_gender(self, character_name: str) -> str:
        """使用AI推断角色性别"""
        try:
            prompt = f"""请判断角色 "{character_name}" 的性别。

判断规则：
1. 基于中文姓名的常见特征
2. 基于文学作品中的角色设定
3. 基于称谓、头衔的语义含义

返回格式（只返回一个词）：
- male（男性）
- female（女性）  
- neutral（中性，如旁白、叙述者）

角色名：{character_name}
性别："""

            response = self._call_ollama(prompt)
            if response:
                # 提取性别判断
                gender = response.strip().lower()
                if 'male' in gender and 'female' not in gender:
                    return 'male'
                elif 'female' in gender:
                    return 'female'
                elif 'neutral' in gender:
                    return 'neutral'
            
            return 'unknown'
            
        except Exception as e:
            logger.error(f"AI性别推断异常: {str(e)}")
            return 'unknown' 