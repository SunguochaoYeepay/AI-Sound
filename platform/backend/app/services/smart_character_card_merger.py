#!/usr/bin/env python3
"""
智能角色卡合并器
将对话分析结果智能转换为角色卡，避免重复分析
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class SmartCharacterCardMerger:
    """智能角色卡合并器"""
    
    def merge_dialogue_to_character_card(self, dialogue_result: dict) -> dict:
        """
        将对话分析结果智能合并为角色卡
        
        Args:
            dialogue_result: 对话分析结果，包含segments和detected_characters
            
        Returns:
            dict: 符合5卡分析格式的角色卡
        """
        try:
            segments = dialogue_result.get('segments', [])
            detected_characters = dialogue_result.get('detected_characters', [])
            
            logger.info(f"开始智能合并：{len(detected_characters)}个角色，{len(segments)}个段落")
            
            # 1. 构建角色行为映射
            character_behavior_map = self._build_character_behavior_map(segments)
            
            # 2. 构建角色卡数据
            characters = []
            for char in detected_characters:
                char_name = char.get('name', '')
                behavior_data = character_behavior_map.get(char_name, {})
                
                character_card = {
                    "name": char_name,
                    "role_type": self._determine_role_type(char),
                    "actions": self._extract_actions(behavior_data.get('narration_segments', [])),
                    "dialogue": behavior_data.get('dialogue_segments', []),
                    "emotions": self._extract_emotions(behavior_data.get('dialogue_segments', [])),
                    "description": char.get('personality_description', '')
                }
                characters.append(character_card)
            
            # 3. 构建旁白数据
            narrator_content = self._extract_narrator_content(segments)
            
            result = {
                "characters": characters,
                "narrator": {
                    "type": "旁白/叙述者",
                    "content": narrator_content,
                    "tone": "描述性"
                }
            }
            
            logger.info(f"智能合并完成：{len(characters)}个角色，旁白内容长度{len(narrator_content)}字符")
            return result
            
        except Exception as e:
            logger.error(f"智能合并失败: {str(e)}")
            # 返回空结构作为fallback
            return {
                "characters": [],
                "narrator": {
                    "type": "旁白/叙述者",
                    "content": "",
                    "tone": "描述性"
                }
            }
    
    def _build_character_behavior_map(self, segments: list) -> dict:
        """
        构建角色行为映射表
        
        将segments按角色分组，区分对话和行为描述
        """
        behavior_map = {}
        
        for segment in segments:
            speaker = segment.get('speaker', '')
            text = segment.get('text', '').strip()
            text_type = segment.get('text_type', '')
            
            if not speaker or speaker == '旁白':
                continue
                
            if speaker not in behavior_map:
                behavior_map[speaker] = {
                    'dialogue_segments': [],
                    'narration_segments': [],
                    'inner_monologue_segments': []
                }
            
            if text_type == 'dialogue':
                behavior_map[speaker]['dialogue_segments'].append(text)
            elif text_type == 'narration':
                behavior_map[speaker]['narration_segments'].append(text)
            elif text_type == 'inner_monologue':
                behavior_map[speaker]['inner_monologue_segments'].append(text)
        
        return behavior_map
    
    def _determine_role_type(self, character: dict) -> str:
        """确定角色类型"""
        frequency = character.get('frequency', 1)
        is_main = character.get('is_main_character', False)
        
        if is_main or frequency >= 3:
            return "主角"
        elif frequency >= 2:
            return "配角"
        else:
            return "背景角色"
    
    def _extract_actions(self, narration_segments: list) -> str:
        """提取角色行为描述"""
        if not narration_segments:
            return ""
        
        # 合并所有行为描述，用分号分隔
        actions = []
        for segment in narration_segments:
            # 移除常见的说话动词，保留纯行为描述
            action = segment
            for verb in ['说', '道', '喊', '叫', '问', '答', '轻声道', '喊道', '叫道', '轻声问道']:
                if verb in action:
                    action = action.replace(verb, '').strip()
            if action:
                actions.append(action)
        
        return "；".join(actions)
    
    def _extract_emotions(self, dialogue_segments: list) -> list:
        """从对话中提取情感"""
        emotions = []
        
        # 情感关键词映射
        emotion_keywords = {
            '高兴': ['高兴', '开心', '快乐', '兴奋', '喜悦', '愉快'],
            '愤怒': ['生气', '愤怒', '恼火', '不满', '气愤', '暴怒'],
            '悲伤': ['悲伤', '难过', '痛苦', '伤心', '哀伤', '沮丧'],
            '恐惧': ['害怕', '恐惧', '担心', '紧张', '焦虑', '惊慌'],
            '惊讶': ['惊讶', '吃惊', '震惊', '意外', '诧异', '愕然'],
            '平静': ['平静', '冷静', '淡定', '从容', '镇定', '温和']
        }
        
        for dialogue in dialogue_segments:
            dialogue_lower = dialogue.lower()
            for emotion, keywords in emotion_keywords.items():
                if any(keyword in dialogue_lower for keyword in keywords):
                    if emotion not in emotions:
                        emotions.append(emotion)
        
        return emotions if emotions else ['平静']
    
    def _extract_narrator_content(self, segments: list) -> str:
        """提取旁白内容"""
        narrator_segments = []
        
        for segment in segments:
            speaker = segment.get('speaker', '')
            text = segment.get('text', '').strip()
            text_type = segment.get('text_type', '')
            
            # 收集旁白的叙述内容
            if speaker == '旁白' and text_type in ['narration', 'inner_monologue']:
                narrator_segments.append(text)
        
        return " ".join(narrator_segments)
