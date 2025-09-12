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
        
        # 🔥 改进分段逻辑：优先按对话边界分割，然后按句号分割
        # 1. 首先尝试按对话边界分割（角色名+说话动词+冒号）
        dialogue_split_pattern = r'([一-龯]{2,6}[^，。！？]*?[说道讲叫喊问答回复表示][:：])'
        
        # 检查是否包含对话模式
        if re.search(dialogue_split_pattern, text):
            # 🔥 使用更精确的方法：先找到所有对话位置，然后手动分割
            dialogue_matches = list(re.finditer(dialogue_split_pattern, text))
            
            refined_sentences = []
            last_end = 0
            
            for match in dialogue_matches:
                 # 🔥 关键修复：精确定位对话动作的开始位置
                 dialogue_action = match.group(1)  # 说话动作部分
                 
                 # 🔥 关键修复：在匹配的文本中找到真正的对话动作开始位置
                 # 排除前面可能的旁白内容，精确匹配角色名+说话动作
                 match_text = text[match.start():match.end()]
                 
                 # 🔥 修复：分行处理，避免跨行匹配导致的错误识别
                 action_match = None
                 character_name = None
                 action_start_in_match = 0
                 
                 # 按行分析，寻找真正的角色名+说话动作
                 lines = match_text.split('\n')
                 for line_idx, line in enumerate(lines):
                     # 🔥 修复：使用更精确的模式，只提取纯粹的角色名
                     line_pattern = r'([一-龯]{2,6})[^，。！？]*?[说道讲叫喊问答回复表示][:：]'
                     line_match = re.search(line_pattern, line)
                     if line_match:
                         # 🔥 关键：只提取角色名部分，去掉修饰词
                         raw_character = line_match.group(1)
                         # 进一步精确提取：如果角色名超过4个字符，可能包含修饰词
                         if len(raw_character) > 4:
                             # 尝试提取前2-3个字符作为角色名
                             for length in [2, 3, 4]:
                                 potential_name = raw_character[:length]
                                 # 检查是否是常见角色名模式
                                 if potential_name in ['太监', '皇帝', '大臣', '将军', '侍卫', '宫女', '刘邦', '项羽', '林渊']:
                                     character_name = potential_name
                                     break
                             else:
                                 # 如果没有匹配到常见角色名，使用前2个字符
                                 character_name = raw_character[:2]
                         else:
                             character_name = raw_character
                         
                         # 计算在整个match_text中的位置
                         line_start = sum(len(lines[i]) + 1 for i in range(line_idx))  # +1 for \n
                         action_start_in_match = line_start + line_match.start()
                         action_match = line_match
                         break
                 
                 if action_match and character_name:
                     # 🔥 关键修复：计算真正的对话开始位置
                     true_dialogue_start = match.start() + action_start_in_match
                     
                     logger.debug(f"[角色分段] 提取的角色名: '{character_name}'")
                     logger.debug(f"[角色分段] 真正对话开始位置: {true_dialogue_start}")
                     logger.debug(f"[角色分段] 匹配文本: '{match_text[:100]}{'...' if len(match_text) > 100 else ''}'")
                     logger.debug(f"[角色分段] 动作匹配: '{action_match.group()}'")
                     
                     # 添加对话前的所有内容（包括匹配中的前缀部分）
                     before_dialogue = text[last_end:true_dialogue_start].strip()
                     if before_dialogue:
                         # 按句号分割前面的内容
                         before_parts = [s.strip() for s in before_dialogue.split('。') if s.strip()]
                         refined_sentences.extend(before_parts)
                     
                     # 🔥 关键修复：寻找完整对话内容的结束位置
                     # 从对话动作结束位置开始寻找对话内容
                     dialogue_content_start = match.end()
                     remaining_text = text[dialogue_content_start:]
                     
                     # 🔥 修复：寻找对话的真正结束位置，需要考虑连续的对话内容
                     dialogue_end_pos = dialogue_content_start
                     
                     # 按句子分割剩余文本，寻找对话的结束
                     sentences_in_remaining = re.split(r'([！!？?。])', remaining_text)
                     
                     for i in range(0, len(sentences_in_remaining), 2):  # 每两个元素为一组（内容+标点）
                         if i < len(sentences_in_remaining):
                             sentence_content = sentences_in_remaining[i]
                             punctuation = sentences_in_remaining[i+1] if i+1 < len(sentences_in_remaining) else ''
                             
                             # 检查这个句子是否是旁白的开始
                             narration_start_patterns = [
                                 r'^\s*[^一-龯]*?(?:只见|此时|这时|忽然|突然|只听|只闻|林渊|刘邦|项羽|历史上)',
                                 r'^\s*[一-龯]{2,}[^说道讲叫喊问答回复表示]*?[心头|内心|想到|感到|看到|听到]',
                             ]
                             
                             is_narration_start = any(re.match(pattern, sentence_content) for pattern in narration_start_patterns)
                             
                             if is_narration_start:
                                 # 遇到旁白，对话结束
                                 break
                             else:
                                 # 继续是对话内容，更新结束位置
                                 dialogue_end_pos += len(sentence_content) + len(punctuation)
                     
                     # 🔥 关键：从真正的对话开始位置到对话内容结束位置提取完整对话
                     pure_dialogue = text[true_dialogue_start:dialogue_end_pos].strip()
                     dialogue_end = dialogue_end_pos
                     
                     refined_sentences.append(pure_dialogue)
                     last_end = dialogue_end
                 else:
                     # 如果无法精确定位，使用原始逻辑
                     before_dialogue = text[last_end:match.start()].strip()
                     if before_dialogue:
                         before_parts = [s.strip() for s in before_dialogue.split('。') if s.strip()]
                         refined_sentences.extend(before_parts)
                     
                     remaining_text = text[match.end():]
                     dialogue_end_match = re.search(r'[！!？?。]', remaining_text)
                     
                     if dialogue_end_match:
                         dialogue_end = match.end() + dialogue_end_match.end()
                         full_dialogue = text[match.start():dialogue_end].strip()
                         refined_sentences.append(full_dialogue)
                         last_end = dialogue_end
                     else:
                         refined_sentences.append(text[match.start():].strip())
                         last_end = len(text)
            
            # 添加最后剩余的内容
            remaining = text[last_end:].strip()
            if remaining:
                remaining_parts = [s.strip() for s in remaining.split('。') if s.strip()]
                refined_sentences.extend(remaining_parts)
            
            sentences = refined_sentences
        else:
            # 如果没有对话模式，直接按句号分割
            sentences = [s.strip() for s in text.split('。') if s.strip()]
        
        # 🔧 修复：过滤无效的标点符号片段
        valid_sentences = []
        for sentence in sentences:
            # 过滤只包含标点符号或过短的片段
            if self._is_valid_text_segment(sentence):
                valid_sentences.append(sentence)
            else:
                logger.debug(f"过滤无效文本片段: '{sentence}'")
        
        for i, sentence in enumerate(valid_sentences):
            segment_info = self.identify_speaker(sentence)
            
            # 🔥 新增：处理混合文本的拆分
            if segment_info.get('text_type') == 'mixed' and 'action_part' in segment_info:
                # 拆分为两个段落：旁白部分 + 对话部分
                action_part = segment_info['action_part']
                dialogue_part = segment_info['dialogue_part']
                speaker_name = segment_info['speaker']
                
                # 添加旁白段落（动作描述）
                segments.append({
                    'order': len(segments) + 1,
                    'text': action_part,
                    'speaker': '旁白',
                    'voice_name': '旁白',  # 🔥 修复：确保voice_name与speaker一致
                    'confidence': 0.95,
                    'detection_rule': 'mixed_split_action',
                    'text_type': 'narration'
                })
                
                # 添加对话段落
                segments.append({
                    'order': len(segments) + 1,
                    'text': dialogue_part,
                    'speaker': speaker_name,
                    'voice_name': speaker_name,  # 🔥 修复：确保voice_name与speaker一致
                    'confidence': 0.95,
                    'detection_rule': 'mixed_split_dialogue',
                    'text_type': 'dialogue'
                })
                
                logger.info(f"[混合文本拆分] '{sentence}' -> 旁白: '{action_part}' + {speaker_name}对话: '{dialogue_part}'")
            
            # 原有的正常处理逻辑
            elif segment_info['confidence'] >= 0.5:  # 只保留置信度>=0.5的段落
                segments.append({
                    'order': len(segments) + 1,  # 重新编号，确保连续性
                    'text': sentence + '。',
                    'speaker': segment_info['speaker'],
                    'voice_name': segment_info['speaker'],  # 🔥 修复：确保voice_name与speaker一致
                    'confidence': segment_info['confidence'],
                    'detection_rule': segment_info['rule'],
                    'text_type': segment_info['text_type']
                })
            else:
                logger.debug(f"过滤低置信度段落 (confidence={segment_info['confidence']}): '{sentence}'")
        
        return segments

    def _is_valid_text_segment(self, text: str) -> bool:
        """检查文本片段是否有效，过滤纯标点符号"""
        if not text or len(text.strip()) == 0:
            return False
        
        # 过滤只包含标点符号的片段
        punct_only_patterns = [
            r'^[：:，,。.！!？?；;""''「」『』\s]*$',  # 只有标点符号和空格
            r'^[：:]+$',  # 只有冒号
            r'^[，,]+$',  # 只有逗号
            r'^[""''「」『』\s]*$',  # 只有引号和空格
        ]
        
        for pattern in punct_only_patterns:
            if re.match(pattern, text.strip()):
                return False
        
        # 过滤过短的非中文片段
        if len(text.strip()) < 2:
            return False
            
        return True
    
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
            # 🔥 新增：角色名+修饰词+说话动词+冒号（无引号）- 处理"太监假尖着嗓子喊道："这类格式
            r'^([一-龯]{2,6})[^，。！？]*?[说道讲叫喊问答回复表示][:：]',
            # 简化格式: 角色名+冒号+引号
            r'^([一-龯]{2,6})[:：]\s*[""''「」『』]',
            # 后置格式: 引号+内容+引号+角色名+说话动词
            r'[""''「」『』][^""''「」『』]+[""''「」『』][^，。！？]*?([一-龯]{2,6})[说道讲叫喊问答回复表示]'
        ]
        
        for i, pattern in enumerate(direct_patterns):
            match = re.search(pattern, text)
            if match:
                potential_speaker = match.group(1)
                
                # 🔥 特殊处理：对于第3个模式（无引号的冒号对话），需要提取角色名
                if i == 2:  # 第3个模式：角色名+修饰词+说话动词+冒号
                    speaker = self._extract_character_name_from_action(potential_speaker)
                    if not speaker:
                        speaker = potential_speaker  # 如果提取失败，使用原始匹配
                else:
                    # 其他模式直接使用匹配结果
                    speaker = potential_speaker
                
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
        
        # 🔥 新增规则5: 对话特征识别模式 - 减少误判
        dialogue_feature_result = self.detect_dialogue_features(text)
        if dialogue_feature_result:
            return dialogue_feature_result
        
        # 🔥 移除兜底机制：让上层智能检测服务决定如何处理无法识别的情况
        # 只有明确识别出旁白特征时才返回旁白，否则返回"无法识别"
        narration_result = self.detect_narration(text)
        if narration_result['confidence'] >= 0.8:  # 只有高置信度的旁白判断才返回
            return narration_result
        
        # 无法识别，返回"无法识别"状态，让上层处理
        return {
            'speaker': None,
            'confidence': 0.0,
            'rule': 'cannot_identify',
            'text_type': 'unknown'
        }
    
    def detect_mixed_text(self, text: str) -> Optional[Dict]:
        """检测混合文本（叙述+对话）- 专门处理需要拆分的情况"""
        
        # 🔥 修复：专门检测"角色名+动作+说话动词+冒号+对话内容"格式
        # 匹配模式：角色名 + 可能的修饰词 + 说话动词 + 冒号 + 对话内容
        split_pattern = r'^([一-龯]{2,6}[^，。！？]*?[说道讲叫喊问答回复表示][:：])(.+)$'
        match = re.search(split_pattern, text.strip())
        
        if match:
            action_part = match.group(1).strip()  # "苏婉咬着牙说道："
            dialogue_part = match.group(2).strip()  # "当时我一看就急了..."
            
            # 提取角色名
            speaker_match = re.search(r'^([一-龯]{2,6})', action_part)
            if speaker_match:
                speaker_name = speaker_match.group(1)
                
                # 🔥 重要：如果对话部分长度足够，且不是纯粹的旁白，则认为是混合文本
                if len(dialogue_part) > 5 and not self._is_pure_narration(dialogue_part):
                    logger.debug(f"[混合文本检测] 识别混合文本: '{action_part}' + '{dialogue_part[:30]}...'")
                    
                    return {
                        'speaker': speaker_name,
                        'confidence': 0.9,
                        'rule': 'mixed_text',
                        'text_type': 'mixed',
                        'action_part': action_part,
                        'dialogue_part': dialogue_part
                    }
        
        return None
    
    def detect_dialogue_features(self, text: str) -> Optional[Dict]:
        """🔥 新增：检测对话特征，减少误判旁白"""
        
        # 对话特征指标
        dialogue_score = 0
        max_score = 10
        
        # 1. 称谓词检测（+3分）
        honorifics = ['陛下', '皇上', '父皇', '母后', '王爷', '公主', '大人', '将军', '师父', '师傅', 
                     '老爷', '夫人', '小姐', '先生', '老师', '医生', '警官', '法官']
        pronouns = ['你', '我', '他', '她', '您', '咱', '咱们', '我们', '你们', '他们', '她们']
        
        has_honorifics = any(word in text for word in honorifics)
        has_pronouns = any(text.count(word) >= 1 for word in pronouns)
        
        if has_honorifics:
            dialogue_score += 3
        if has_pronouns:
            dialogue_score += 2
            
        # 2. 疑问句和感叹句（+2分）  
        if text.endswith('？') or text.endswith('?'):
            dialogue_score += 2
        if text.endswith('！') or text.endswith('!'):
            dialogue_score += 2
            
        # 3. 对话语气词（+1分）
        dialogue_particles = ['呢', '吧', '啊', '呀', '嘛', '哦', '哟', '喂', '嗯', '嘿', '哎', '唉']
        has_particles = any(word in text for word in dialogue_particles)
        if has_particles:
            dialogue_score += 1
            
        # 4. 命令/请求语气（+1分）
        command_patterns = [r'请.*', r'.*吧[！!。]?$', r'^快.*', r'^去.*', r'^来.*', r'^别.*', r'^不要.*']
        has_command = any(re.search(pattern, text) for pattern in command_patterns)
        if has_command:
            dialogue_score += 1
            
        # 5. 对话连接词（+1分）
        dialogue_connectors = ['可是', '但是', '不过', '然而', '那么', '所以', '因此', '既然', '如果', '要是']
        has_connectors = any(word in text for word in dialogue_connectors)
        if has_connectors:
            dialogue_score += 1
            
        # 6. 减分项：明显的叙述标志（大幅加强）
        narrative_markers = [
            # 时间地点标志
            '只见', '只听', '只觉', '忽然', '突然', '此时', '这时', '接着', '然后', '于是',
            # 场景描述标志  
            '御书房', '房内', '室内', '门外', '窗外', '院子', '大殿', '宫殿',
            # 动作描述标志
            '把玩着', '握紧拳头', '咽了咽', '转头看', '上前', '走来', '走去',
            '目光', '眼神', '神情', '表情', '脸色', '神色',
            # 身体动作
            '裙摆', '衣袖', '长发', '双手', '拳头', '手指',
            # 心理描述  
            '心中', '内心', '暗想', '暗自', '心里', '想到', '感到', '觉得'
        ]
        
        narrative_score = 0
        for marker in narrative_markers:
            if marker in text:
                narrative_score += 1
                
        # 强力减分：每个叙述标志-2分
        dialogue_score -= narrative_score * 2
        
        # 7. 额外减分：纯描述性句子特征
        # 如果文本包含大量描述性词汇且没有引号，很可能是旁白
        descriptive_patterns = [
            r'.*[一-龯]+着.*',  # "把玩着"、"咽了咽"等
            r'.*目光.*',       # "目光锐利"等
            r'.*神情.*',       # "神情凝重"等  
            r'.*突然.*',       # "突然上前"等
        ]
        
        descriptive_count = sum(1 for pattern in descriptive_patterns if re.search(pattern, text))
        if descriptive_count >= 2 and '"' not in text and '"' not in text:
            dialogue_score -= 3  # 重度减分
            
        # 判断是否为对话（提高阈值）
        dialogue_threshold = 4  # 提高阈值：至少4分才认为是对话
        
        if dialogue_score >= dialogue_threshold:
            # 推测说话者（基于称谓和上下文）
            speaker = self._infer_speaker_from_context(text)
            
            # 🔥 修复：如果无法确定说话者，不返回对话结果
            if speaker is None:
                return None
                
            confidence = min(0.85, 0.6 + (dialogue_score / max_score) * 0.25)  # 0.6-0.85区间
            
            return {
                'speaker': speaker,
                'confidence': confidence,
                'rule': 'dialogue_features',
                'text_type': 'dialogue',
                'dialogue_score': dialogue_score
            }
            
        return None
    
    def _infer_speaker_from_context(self, text: str) -> str:
        """从对话内容推测说话者 - 保守推测，避免虚构角色"""
        
        # 🔥 修复：不再推测具体的角色名，只返回通用标识
        # 原因：推测出的"大臣"、"公主"等角色名可能不存在于实际文本中
        
        # 检查是否真的包含对话内容
        has_quotes = '"' in text or '"' in text or '"' in text or "'" in text or "'" in text
        has_dialogue_words = any(word in text for word in ['说', '道', '问', '答', '叫', '喊'])
        
        if has_quotes or has_dialogue_words:
            # 只有真正包含对话特征时才返回"角色"
            return '角色'  # 通用标识，不推测具体身份
        else:
            # 没有明确对话特征，可能是误判
            return None  # 返回None表示不确定是对话
    
    def _is_pure_narration(self, text: str) -> bool:
        """判断文本是否是纯粹的旁白描述"""
        
        # 旁白特征词汇
        narration_indicators = [
            '只见', '此时', '这时', '忽然', '突然', '只听', '只闻', 
            '他们', '小华', '抬起', '看着', '意识到', '一起', '向', '扑'
        ]
        
        # 如果包含明显的旁白特征词汇，认为是旁白
        narration_count = sum(1 for word in narration_indicators if word in text)
        
        # 对话特征词汇（第一人称表述）
        dialogue_indicators = ['我', '你', '他', '她', '当时我', '我一看', '我刚']
        dialogue_count = sum(1 for word in dialogue_indicators if word in text)
        
        # 如果旁白特征明显多于对话特征，认为是纯旁白
        return narration_count > dialogue_count and narration_count >= 2
    
    def _extract_character_name_from_action(self, raw_text: str) -> Optional[str]:
        """从说话动作文本中提取角色名"""
        # 常见的角色名模式
        character_patterns = [
            # 直接匹配常见角色名
            r'(孙悟空|唐僧|猪八戒|沙僧|白骨精|观音|如来|玉帝|太监|皇帝|陛下|大臣|将军)',
            # 匹配以特定字开头的角色名
            r'(白[一-龯]{1,2})',  # 白骨精、白娘子等
            r'(孙[一-龯]{1,2})',  # 孙悟空等
            r'(唐[一-龯]{0,2})',  # 唐僧等
            r'(太[一-龯]{0,2})',  # 太监、太子等
            # 🔥 新增：匹配开头的角色名（处理"太监假尖着嗓子"这类情况）
            r'^([一-龯]{2,4})(?=假|真|正|忽然|突然|慢慢|快速|轻声|大声|小声|尖着|粗着)',
            # 通用模式：去掉修饰词后的2-4字角色名
            r'(?:不胜|十分|非常|很是|颇为|甚是|极其|假|真|正)?([一-龯]{2,4})(?:不胜|十分|非常|很是|颇为|甚是|极其|欢喜|愤怒|高兴|悲伤|惊讶|害怕|着急|焦急|假|真|正)?'
        ]
        
        for pattern in character_patterns:
            match = re.search(pattern, raw_text)
            if match:
                candidate = match.group(1)
                # 验证候选角色名
                if self.is_valid_character_name(candidate):
                    return candidate
        
        return None
    
    def detect_narration(self, text: str) -> Dict:
        """检测旁白/叙述文本"""
        # 🔧 修复：检查是否为有效的文本片段
        if not self._is_valid_text_segment(text):
            # 对于无效片段，返回极低置信度，避免被处理
            return {
                'speaker': '旁白',
                'confidence': 0.1,
                'rule': 'invalid_segment',
                'text_type': 'narration'
            }
        
        # 1. 不包含任何对话标记的文本
        has_dialogue_markers = bool(re.search(r'[""''「」『』：:][说道讲叫喊问答回复表示]', text))
        
        # 2. 不以角色名开头的描述性文本  
        starts_with_character = bool(re.search(r'^[一-龯]{2,4}[说道讲叫喊问答回复表示]', text))
        
        # 3. 包含描述性词汇的文本
        has_narrative_words = any(word in text for word in self.narrative_words)
        
        # 4. 检查是否包含实际内容（不只是标点符号）
        has_meaningful_content = bool(re.search(r'[一-龯a-zA-Z0-9]', text))
        
        if not has_dialogue_markers and not starts_with_character and has_meaningful_content and (has_narrative_words or len(text) > 50):
            return {
                'speaker': '旁白',
                'confidence': 0.9,
                'rule': 'narration',
                'text_type': 'narration'
            }
        
        # 对于较短但有内容的文本，低置信度归类为旁白
        if has_meaningful_content and len(text.strip()) >= 5:
            return {
                'speaker': '旁白',
                'confidence': 0.7,
                'rule': 'default_narration',
                'text_type': 'narration'
            }
        
        # 对于明显无效的文本，返回极低置信度
        return {
            'speaker': '旁白',
            'confidence': 0.1,
            'rule': 'low_confidence_fallback',
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
            from app.utils.llm_config_loader import llm_config_loader
            config = llm_config_loader.get_config()
            payload = {
                "model": config["model"],  # 使用统一配置的模型
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # 低温度确保稳定判断
                    "max_tokens": 50,   # 只需要很短的回答
                }
            }
            
            from app.utils.llm_config_loader import llm_config_loader
            config = llm_config_loader.get_config()
            response = requests.post(
                f"{config['base_url']}/api/generate",
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