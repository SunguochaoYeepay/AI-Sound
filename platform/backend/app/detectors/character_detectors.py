"""
角色检测器模块
从chapters.py中分离出的角色识别相关类
"""

import json
import logging
import re
import requests
import time
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class ProgrammaticCharacterDetector:
    """
    编程规则角色识别器 - 独立的角色识别引擎
    基于小说角色编程识别规则.md的实现
    
    注意：这是一个独立的分析器，不是AI分析的后备方案！
    用于需要快速、确定性角色识别的场景，如API测试、调试等。
    """
    
    def __init__(self):
        # 对话标识符模式
        self.dialogue_patterns = {
            'direct_quote': [
                r'^([^""''「」『』：:，。！？\s]{2,6})[说道讲叫喊问答回复表示][:：]\s*[""''「」『』]',
                r'^([^""''「」『』：:，。！？\s]{2,6})[说道讲叫喊问答回复表示]，\s*[""''「」『』]',
                r'^([^""''「」『』：:，。！？\s]{2,6})[:：]\s*[""''「」『』]'
            ],
            'colon_marker': [
                r'^([^：:，。！？\s]{2,6})[:：]'
            ],
            'quote_dialogue': [
                r'^([^""''「」『』，。！？\s]{2,6})[^""''「」『』]{0,10}[""''「」『』]',
                r'[""''「」『』][^""''「」『』]+[""''「」『』][^，。！？]*?([^，。！？\s]{2,6})[说道]'
            ],
            'mixed_separation': [
                r'^(.+?)([一-龯]{2,4}[说道讲叫喊问答回复表示自言自语][:：])\s*[""''「」『』](.+?)[""''「」『』](.*)$'
            ]
        }
        
        # 排除词汇
        self.excluded_words = [
            '这个', '那个', '什么', '哪里', '为什么', '怎么',
            '可是', '但是', '所以', '因为', '如果', '虽然',
            '遇到', '慢慢', '而这', '这一', '那一', '当他', '当她',
            '此时', '此后', '然后', '接着', '最后', '从那', '经过',
            '神奇', '在一', '正发', '无奈', '尽管'
        ]
        
        # 叙述词汇
        self.narrative_words = [
            '只见', '忽然', '此时', '这时', '突然', '接着', '然后', 
            '于是', '一天', '师徒', '山势', '峰岩', '话说', '却说'
        ]
    
    def segment_text_with_speakers(self, text: str) -> List[Dict]:
        """将文本分段并识别说话者"""
        segments = []
        
        # 按句号分割文本
        sentences = [s.strip() for s in text.split('。') if s.strip()]
        
        for i, sentence in enumerate(sentences):
            segment_info = self.identify_speaker(sentence)
            segments.append({
                'order': i + 1,
                'text': sentence + '。',
                'speaker': segment_info['speaker'],
                'confidence': segment_info['confidence'],
                'detection_rule': segment_info['rule'],
                'text_type': segment_info['text_type']
            })
        
        return segments
    
    def identify_speaker(self, text: str) -> Dict:
        """识别单个句子的说话者"""
        
        # 规则1: 混合文本分离模式
        mixed_result = self.detect_mixed_text(text)
        if mixed_result:
            return mixed_result
        
        # 规则2: 直接引语模式 - 增强版
        direct_patterns = [
            # 标准格式: 角色名+说话动词+冒号+引号
            r'^([一-龯]{2,6})[说道讲叫喊问答回复表示][:：]\s*[""''「」『』]',
            # 带逗号格式: 角色名+说话动词+逗号+引号  
            r'^([一-龯]{2,6})[说道讲叫喊问答回复表示]，\s*[""''「」『』]',
            # 简化格式: 角色名+冒号+引号
            r'^([一-龯]{2,6})[:：]\s*[""''「」『』]',
            # 后置格式: 引号+内容+引号+角色名+说话动词
            r'[""''「」『』][^""''「」『』]+[""''「」『』][^，。！？]*?([一-龯]{2,6})[说道讲叫喊问答回复表示]'
        ]
        
        for pattern in direct_patterns:
            match = re.search(pattern, text)
            if match:
                potential_speaker = match.group(1)
                # 从潜在说话者中提取角色名
                speaker = self._extract_character_name_from_action(potential_speaker)
                if not speaker:
                    speaker = potential_speaker  # 如果提取失败，使用原始匹配
                
                if self.is_valid_character_name(speaker):
                    return {
                        'speaker': speaker,
                        'confidence': 0.95,
                        'rule': 'direct_quote',
                        'text_type': 'dialogue'
                    }
        
        # 规则3: 对话标记模式
        for pattern in self.dialogue_patterns['colon_marker']:
            match = re.search(pattern, text)
            if match:
                speaker = match.group(1)
                if self.is_valid_character_name(speaker):
                    return {
                        'speaker': speaker,
                        'confidence': 0.9,
                        'rule': 'colon_marker',
                        'text_type': 'dialogue'
                    }
        
        # 规则4: 引号对话模式
        if any(quote in text for quote in ['"', '"', '"', '「', '」', '『', '』', "'", "'"]):
            for pattern in self.dialogue_patterns['quote_dialogue']:
                match = re.search(pattern, text)
                if match:
                    speaker = match.group(1)
                    if self.is_valid_character_name(speaker):
                        return {
                            'speaker': speaker,
                            'confidence': 0.85,
                            'rule': 'quote_dialogue',
                            'text_type': 'dialogue'
                        }
        
        # 规则5: 旁白识别模式
        return self.detect_narration(text)
    
    def detect_mixed_text(self, text: str) -> Optional[Dict]:
        """检测混合文本（叙述+对话）"""
        # 先尝试提取说话动作部分 - 更精确的模式
        action_patterns = [
            # 模式1: 角色名+修饰词+说话动词+冒号+引号
            r'([一-龯]{2,6})[^，。！？]*?[说道讲叫喊问答回复表示][:：]\s*[""''「」『』]',
            # 模式2: 角色名+自言自语+冒号+引号 (特殊处理)
            r'([一-龯]{2,6})[^，。！？]*?自言自语道[:：]\s*[""''「」『』]'
        ]
        
        for pattern in action_patterns:
            match = re.search(pattern, text)
            if match:
                potential_speaker = match.group(1)
                
                # 从潜在说话者中提取真正的角色名
                speaker_name = self._extract_character_name_from_action(potential_speaker)
                
                if speaker_name and self.is_valid_character_name(speaker_name):
                    return {
                        'speaker': speaker_name,
                        'confidence': 0.95,
                        'rule': 'mixed_separation',
                        'text_type': 'dialogue'
                    }
        return None
    
    def _extract_character_name_from_action(self, action_text: str) -> Optional[str]:
        """从说话动作文本中提取角色名"""
        # 常见的角色名模式
        character_patterns = [
            # 直接匹配常见角色名
            r'(孙悟空|唐僧|猪八戒|沙僧|白骨精|观音|如来|玉帝)',
            # 匹配以特定字开头的角色名
            r'(白[一-龯]{1,2})',  # 白骨精、白娘子等
            r'(孙[一-龯]{1,2})',  # 孙悟空等
            r'(唐[一-龯]{0,2})',  # 唐僧等
            # 通用模式：去掉修饰词后的2-4字角色名
            r'(?:不胜|十分|非常|很是|颇为|甚是|极其)?([一-龯]{2,4})(?:不胜|十分|非常|很是|颇为|甚是|极其|欢喜|愤怒|高兴|悲伤|惊讶|害怕|着急|焦急)?'
        ]
        
        for pattern in character_patterns:
            match = re.search(pattern, action_text)
            if match:
                candidate = match.group(1)
                # 验证候选角色名
                if self.is_valid_character_name(candidate):
                    return candidate
        
        return None
    
    def detect_narration(self, text: str) -> Dict:
        """检测旁白/叙述文本"""
        # 1. 不包含任何对话标记的文本
        has_dialogue_markers = bool(re.search(r'[""''「」『』：:][说道讲叫喊问答回复表示]', text))
        
        # 2. 不以角色名开头的描述性文本  
        starts_with_character = bool(re.search(r'^[一-龯]{2,4}[说道讲叫喊问答回复表示]', text))
        
        # 3. 包含描述性词汇的文本
        has_narrative_words = any(word in text for word in self.narrative_words)
        
        if not has_dialogue_markers and not starts_with_character and (has_narrative_words or len(text) > 50):
            return {
                'speaker': '旁白',
                'confidence': 0.9,
                'rule': 'narration',
                'text_type': 'narration'
            }
        
        # 默认归类为旁白
        return {
            'speaker': '旁白',
            'confidence': 0.7,
            'rule': 'default_narration',
            'text_type': 'narration'
        }
    
    def is_valid_character_name(self, name: str) -> bool:
        """验证角色名是否有效 - 结合AI智能判断与基础规则"""
        # 基础过滤：明显不合理的情况
        if not name or len(name) < 1:
            return False
        
        # 基础排除：明显的标点符号
        if any(punct in name for punct in ['。', '，', '！', '？', '；', '\n', '\t']):
            return False
        
        # 对于复杂情况，使用AI判断
        try:
            return self._ai_validate_character_name(name)
        except Exception as e:
            logger.warning(f"AI角色名验证失败，使用保守判断: {str(e)}")
            # AI失败时的保守判断
            return len(name) >= 2 and len(name) <= 8 and not name in self.excluded_words
    
    def _ai_validate_character_name(self, name: str) -> bool:
        """使用AI验证角色名是否合理"""
        try:
            prompt = f"""判断 "{name}" 是否是一个合理的小说角色名。

判断标准：
1. 是否可能是人名、神话角色名、动物名等
2. 是否不是动词、形容词、副词等语法词汇
3. 是否不是"什么"、"哪里"等疑问词
4. 是否不是"但是"、"所以"等连接词
5. 是否能作为小说中的说话角色

特别注意：
- "旁白"、"叙述者"、"作者"等是有效的特殊角色
- 神话小说中的角色名可能较长或包含特殊字符
- 现代小说可能有外国人名的音译

请返回：
- valid（有效的角色名）
- invalid（无效的名称）

名称：{name}
判断："""

            response = self._call_ollama_simple(prompt)
            if response:
                # 提取判断结果
                result = response.strip().lower()
                if 'valid' in result and 'invalid' not in result:
                    return True
                elif 'invalid' in result:
                    return False
            
            # AI无法判断时，使用保守规则
            return len(name) >= 2 and len(name) <= 8
            
        except Exception as e:
            logger.error(f"AI角色名验证异常: {str(e)}")
            return len(name) >= 2 and len(name) <= 8
    
    def _call_ollama_simple(self, prompt: str) -> Optional[str]:
        """简化的Ollama调用，用于快速判断"""
        try:
            payload = {
                "model": "qwen2.5:14b",  # 🔥 使用中文优化模型
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # 低温度确保稳定判断
                    "max_tokens": 50,   # 只需要很短的回答
                }
            }
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=30  # 短超时
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            
            return None
            
        except Exception as e:
            logger.warning(f"简化Ollama调用失败: {str(e)}")
            return None
    
    def extract_dialogue_characters(self, segments: List[Dict]) -> Dict[str, int]:
        """提取有对话的角色及其频次"""
        dialogue_characters = {}
        
        for segment in segments:
            if segment['text_type'] == 'dialogue' and segment['speaker'] != '旁白':
                speaker = segment['speaker']
                dialogue_characters[speaker] = dialogue_characters.get(speaker, 0) + 1
        
        return dialogue_characters
    
    def analyze_text_segments(self, text: str) -> Dict:
        """分析文本并返回完整的分段和角色信息"""
        segments = self.segment_text_with_speakers(text)
        dialogue_characters = self.extract_dialogue_characters(segments)
        
        # 统计旁白段落
        narrator_segments = [s for s in segments if s['speaker'] == '旁白']
        
        # 构建角色列表（只包含有对话的角色 + 旁白）
        characters = []
        
        # 添加对话角色
        for char_name, frequency in dialogue_characters.items():
            characters.append({
                'name': char_name,
                'frequency': frequency,
                'character_trait': {
                    'trait': 'calm',  # 默认性格
                    'confidence': 0.8,
                    'description': f'{char_name}角色，需要进一步分析性格特征'
                },
                'first_appearance': 1,
                'is_main_character': frequency >= 3,
                'recommended_config': {
                    'gender': 'unknown',
                    'personality': 'calm',
                    'personality_description': '性格特征待分析',
                    'personality_confidence': 0.8,
                    'description': f'{char_name}角色，在文本中有{frequency}次对话。',
                    'recommended_tts_params': {'time_step': 32, 'p_w': 1.4, 't_w': 3.0},
                    'voice_type': 'unknown',
                    'color': '#007bff'
                }
            })
        
        # 添加旁白角色（如果有旁白内容）
        if narrator_segments:
            characters.append({
                'name': '旁白',
                'frequency': len(narrator_segments),
                'character_trait': {
                    'trait': 'calm',
                    'confidence': 1.0,
                    'description': '小说叙述者，负责描述场景和情节发展'
                },
                'first_appearance': 1,
                'is_main_character': True,
                'recommended_config': {
                    'gender': 'neutral',
                    'personality': 'calm',
                    'personality_description': '专业旁白，声音清晰稳定，适合叙述',
                    'personality_confidence': 1.0,
                    'description': '旁白角色，负责小说的叙述部分，需要专业、清晰的声音。',
                    'recommended_tts_params': {'time_step': 32, 'p_w': 1.4, 't_w': 3.0},
                    'voice_type': 'narrator',
                    'color': '#6c757d'
                }
            })
        
        return {
            'segments': segments,
            'detected_characters': characters,
            'processing_stats': {
                'total_segments': len(segments),
                'dialogue_segments': len([s for s in segments if s['text_type'] == 'dialogue']),
                'narration_segments': len(narrator_segments),
                'characters_found': len(characters),
                'analysis_method': 'programming_rules'
            }
        } 