"""
高级角色检测器
基于多重规则和启发式方法的角色识别
"""

import logging
import re
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class AdvancedCharacterDetector:
    """
    高级角色检测器 - 基于多重规则和启发式方法
    """
    
    def __init__(self):
        # 对话标识符模式
        self.dialogue_patterns = [
            # 直接引语模式
            r'([^，。！？\s]{2,4})[说道讲问答回应喊叫嘟囔嘀咕][:：]?"([^"]+)"',
            r'"([^"]+)"[，。]?([^，。！？\s]{2,4})[说道讲问答]',
            
            # 冒号对话模式
            r'([^，。！？\s]{2,4})[：:]"([^"]+)"',
            r'([^，。！？\s]{2,4})[：:]\s*([^，。！？\n]+)',
            
            # 标记对话模式
            r'【([^】]+)】[：:]?([^，。！？\n]*)',
            r'〖([^〗]+)〗[：:]?([^，。！？\n]*)',
            
            # 动作描述中的角色
            r'([^，。！？\s]{2,4})[走来去到站坐躺跑跳]',
            r'([^，。！？\s]{2,4})[看见听到想起记得]',
            r'([^，。！？\s]{2,4})[笑哭怒喜惊]',
            
            # 称呼模式
            r'([^，。！？\s]{2,4})[师父师傅大人先生小姐]',
            r'[师父师傅大人先生小姐]([^，。！？\s]{2,4})',
        ]
        
        # 排除词汇 - 常见的非角色词汇
        self.excluded_words = {
            '这个', '那个', '什么', '哪里', '为什么', '怎么', '可是', '但是', '所以', '因为',
            '如果', '虽然', '遇到', '慢慢', '而这', '这一', '那一', '当他', '当她', '此时',
            '此后', '然后', '接着', '最后', '从那', '经过', '神奇', '在一', '正发', '无奈',
            '尽管', '自言', '心想', '暗想', '暗道', '心道', '想道', '思考', '突然', '忽然',
            '原来', '果然', '竟然', '居然', '当然', '自然', '显然', '明显', '清楚', '知道',
            '看到', '听到', '感到', '觉得', '认为', '以为', '似乎', '好像', '仿佛', '犹如'
        }
        
        # 角色性格关键词
        self.personality_keywords = {
            'gentle': ['温柔', '轻声', '柔声', '细声', '温和', '和蔼', '慈祥', '温柔地', '轻声道'],
            'fierce': ['凶猛', '暴躁', '粗暴', '凶狠', '狂暴', '霸道', '怒吼', '咆哮', '大喝', '厉声'],
            'calm': ['沉稳', '冷静', '淡定', '从容', '镇定', '平静', '淡淡地', '平静地', '从容说'],
            'lively': ['活泼', '开朗', '爽朗', '欢快', '兴奋', '热情', '兴奋地', '欢快地', '爽朗笑'],
            'wise': ['智慧', '睿智', '聪明', '机智', '深思', '沉思', '思索', '深思熟虑'],
            'brave': ['勇敢', '英勇', '无畏', '果敢', '坚毅', '刚强', '勇气', '胆量']
        }
        
        # 性别推断关键词
        self.gender_keywords = {
            'male': ['师父', '师傅', '大人', '先生', '公子', '少爷', '老爷', '爷爷', '父亲', '爸爸'],
            'female': ['小姐', '姑娘', '夫人', '娘子', '女士', '奶奶', '母亲', '妈妈', '阿姨']
        }
    
    def analyze_text(self, text: str, chapter_info: dict):
        """分析文本中的角色"""
        
        # 1. 分段处理
        segments = self._split_into_segments(text)
        
        # 2. 角色提取
        character_candidates = self._extract_characters(segments)
        
        # 3. 角色验证和过滤
        valid_characters = self._validate_characters(character_candidates, text)
        
        # 4. 角色属性分析
        analyzed_characters = self._analyze_character_attributes(valid_characters, text)
        
        # 5. 构建返回结果
        return {
            "chapter_id": chapter_info['chapter_id'],
            "chapter_title": chapter_info['chapter_title'],
            "chapter_number": chapter_info['chapter_number'],
            "detected_characters": analyzed_characters,
            "segments": [],  # 可以后续添加段落分析
            "processing_stats": {
                "total_segments": len(segments),
                "dialogue_segments": len([s for s in segments if self._is_dialogue(s)]),
                "characters_found": len(analyzed_characters)
            }
        }
    
    def _split_into_segments(self, text: str):
        """将文本分割为段落"""
        # 按句号、感叹号、问号分割，保留标点
        segments = re.split(r'([。！？])', text)
        
        # 重新组合句子
        sentences = []
        for i in range(0, len(segments)-1, 2):
            if i+1 < len(segments):
                sentence = segments[i] + segments[i+1]
                if sentence.strip():
                    sentences.append(sentence.strip())
        
        return sentences
    
    def _extract_characters(self, segments):
        """从段落中提取角色候选"""
        character_mentions = {}
        
        for segment_idx, segment in enumerate(segments):
            for pattern in self.dialogue_patterns:
                matches = re.findall(pattern, segment)
                for match in matches:
                    # 处理不同的匹配组
                    if isinstance(match, tuple):
                        for name in match:
                            if name and len(name) >= 2 and len(name) <= 6:
                                if self._is_valid_character_name(name):
                                    if name not in character_mentions:
                                        character_mentions[name] = {
                                            'frequency': 0,
                                            'segments': [],
                                            'contexts': []
                                        }
                                    character_mentions[name]['frequency'] += 1
                                    character_mentions[name]['segments'].append(segment_idx)
                                    character_mentions[name]['contexts'].append(segment)
                    else:
                        name = match
                        if name and len(name) >= 2 and len(name) <= 6:
                            if self._is_valid_character_name(name):
                                if name not in character_mentions:
                                    character_mentions[name] = {
                                        'frequency': 0,
                                        'segments': [],
                                        'contexts': []
                                    }
                                character_mentions[name]['frequency'] += 1
                                character_mentions[name]['segments'].append(segment_idx)
                                character_mentions[name]['contexts'].append(segment)
        
        return character_mentions
    
    def _is_valid_character_name(self, name: str) -> bool:
        """验证是否为有效的角色名 - 使用AI智能判断"""
        # 基础过滤：明显不合理的情况
        if not name or len(name) < 1:
            return False
        
        # 基础排除：明显的标点符号和特殊字符
        if any(punct in name for punct in ['。', '，', '！', '？', '；', '\n', '\t']):
            return False
        
        # 对于复杂情况，使用AI判断
        try:
            return self._ai_validate_character_name(name)
        except Exception as e:
            logger.warning(f"AI角色名验证失败，使用保守判断: {str(e)}")
            # AI失败时的保守判断
            return len(name) >= 2 and len(name) <= 8 and name not in getattr(self, 'excluded_words', [])
    
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
                "model": "qwen3:30b",  # 使用相同的模型
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
    
    def _validate_characters(self, candidates: dict, full_text: str):
        """验证和过滤角色候选"""
        valid_characters = {}
        
        for name, data in candidates.items():
            # 频率过滤：至少出现2次
            if data['frequency'] >= 2:
                valid_characters[name] = data
            # 或者在全文中有多次提及
            elif full_text.count(name) >= 3:
                data['frequency'] = full_text.count(name)
                valid_characters[name] = data
        
        return valid_characters
    
    def _analyze_character_attributes(self, characters: dict, full_text: str):
        """分析角色属性"""
        analyzed_characters = []
        
        for name, data in characters.items():
            # 分析性格特征
            personality = self._analyze_personality(data['contexts'])
            
            # 推断性别
            gender = self._infer_gender(name, data['contexts'])
            
            # 生成角色配置
            character_config = {
                'name': name,
                'frequency': data['frequency'],
                'character_trait': {
                    'trait': personality['trait'],
                    'confidence': personality['confidence'],
                    'description': personality['description']
                },
                'first_appearance': min(data['segments']) + 1 if data['segments'] else 1,
                'is_main_character': data['frequency'] >= 5,  # 出现5次以上为主要角色
                'recommended_config': {
                    'gender': gender,
                    'personality': personality['trait'],
                    'personality_description': personality['description'],
                    'personality_confidence': personality['confidence'],
                    'description': f'{name}，{gender}角色，{personality["description"]}，在文本中出现{data["frequency"]}次。',
                    'recommended_tts_params': self._get_tts_params(personality['trait']),
                    'voice_type': f'{gender}_{personality["trait"]}',
                    'color': self._get_character_color(personality['trait'])
                }
            }
            
            analyzed_characters.append(character_config)
        
        # 按频率排序
        analyzed_characters.sort(key=lambda x: x['frequency'], reverse=True)
        
        return analyzed_characters
    
    def _analyze_personality(self, contexts: list):
        """分析角色性格"""
        personality_scores = {trait: 0 for trait in self.personality_keywords.keys()}
        
        # 统计性格关键词
        for context in contexts:
            for trait, keywords in self.personality_keywords.items():
                for keyword in keywords:
                    if keyword in context:
                        personality_scores[trait] += 1
        
        # 找出最高分的性格特征
        if max(personality_scores.values()) > 0:
            dominant_trait = max(personality_scores, key=personality_scores.get)
            confidence = min(personality_scores[dominant_trait] / len(contexts), 1.0)
        else:
            dominant_trait = 'calm'  # 默认性格
            confidence = 0.3
        
        trait_descriptions = {
            'gentle': '性格温柔，说话轻声细语',
            'fierce': '性格刚烈，说话直接有力',
            'calm': '性格沉稳，处事冷静',
            'lively': '性格活泼，充满活力',
            'wise': '智慧睿智，深思熟虑',
            'brave': '勇敢果敢，无所畏惧'
        }
        
        return {
            'trait': dominant_trait,
            'confidence': confidence,
            'description': trait_descriptions.get(dominant_trait, '性格温和')
        }
    
    def _infer_gender(self, name: str, contexts: list):
        """推断角色性别"""
        male_score = 0
        female_score = 0
        
        # 基于称呼推断
        for context in contexts:
            for keyword in self.gender_keywords['male']:
                if keyword in context:
                    male_score += 1
            for keyword in self.gender_keywords['female']:
                if keyword in context:
                    female_score += 1
        
        # 基于名字推断（简单规则）
        common_male_chars = ['龙', '虎', '豹', '鹰', '狼', '雄', '强', '刚', '勇', '威']
        common_female_chars = ['凤', '燕', '莺', '花', '月', '雪', '玉', '珠', '美', '丽']
        
        for char in common_male_chars:
            if char in name:
                male_score += 0.5
        
        for char in common_female_chars:
            if char in name:
                female_score += 0.5
        
        return 'male' if male_score > female_score else 'female'
    
    def _get_tts_params(self, personality: str):
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
    
    def _get_character_color(self, personality: str):
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
    
    def _is_dialogue(self, segment: str):
        """判断段落是否包含对话"""
        dialogue_indicators = ['"', '"', '"', '：', ':', '说', '道', '问', '答', '叫', '喊']
        return any(indicator in segment for indicator in dialogue_indicators) 