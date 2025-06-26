"""
智能语音映射器服务
专门处理角色与语音配置文件的智能匹配
"""

import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class IntelligentVoiceMapper:
    """智能语音映射器 - 角色与语音的智能匹配"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def intelligent_voice_mapping(
        self, 
        detected_characters: List[Dict], 
        user_preferences: Dict = None
    ) -> Dict[str, int]:
        """智能语音匹配"""
        
        # 获取可用语音
        available_voices = await self._get_available_voices()
        voice_mapping = {}
        
        # 简单的匹配逻辑（可以后续优化）
        for i, character in enumerate(detected_characters):
            char_name = character['name']
            
            # 为旁白角色特殊处理
            if char_name == '旁白':
                narrator_voice = self._get_narrator_voice_mapping(available_voices)
                if narrator_voice:
                    voice_mapping[char_name] = narrator_voice
                continue
            
            # 其他角色智能分配
            optimal_voice = self._find_optimal_voice_for_character(character, available_voices)
            if optimal_voice:
                voice_mapping[char_name] = optimal_voice
            elif i < len(available_voices):
                # 回退方案：简单分配
                voice_mapping[char_name] = available_voices[i]['id']
        
        return voice_mapping
    
    def _find_optimal_voice_for_character(self, character: Dict, available_voices: List[Dict]) -> Optional[int]:
        """为角色找到最佳匹配的语音"""
        
        char_gender = character.get('gender', 'unknown')
        char_personality = character.get('personality', 'calm')
        char_age = character.get('age_range', 'adult')
        
        # 按匹配度排序可用语音
        voice_scores = []
        
        for voice in available_voices:
            score = 0
            voice_type = voice.get('voice_type', '').lower()
            voice_name = voice.get('name', '').lower()
            voice_desc = voice.get('description', '').lower()
            
            # 性别匹配 (高权重)
            if char_gender == 'male' and ('male' in voice_type or '男' in voice_name):
                score += 50
            elif char_gender == 'female' and ('female' in voice_type or '女' in voice_name):
                score += 50
            elif char_gender == 'neutral' and ('neutral' in voice_type or '中性' in voice_name):
                score += 50
            
            # 性格匹配 (中权重)
            personality_keywords = {
                'gentle': ['温柔', '柔和', 'gentle', 'soft'],
                'fierce': ['激烈', '强势', 'fierce', 'strong'],
                'calm': ['平静', '稳重', 'calm', 'steady'],
                'lively': ['活泼', '开朗', 'lively', 'cheerful'],
                'wise': ['智慧', '睿智', 'wise', 'intelligent'],
                'brave': ['勇敢', '坚定', 'brave', 'firm']
            }
            
            if char_personality in personality_keywords:
                keywords = personality_keywords[char_personality]
                for keyword in keywords:
                    if keyword in voice_name or keyword in voice_desc:
                        score += 30
                        break
            
            # 年龄匹配 (低权重)
            age_keywords = {
                'young': ['年轻', '青春', 'young', 'youth'],
                'adult': ['成人', '成熟', 'adult', 'mature'],
                'elder': ['年长', '老练', 'elder', 'experienced']
            }
            
            if char_age in age_keywords:
                keywords = age_keywords[char_age]
                for keyword in keywords:
                    if keyword in voice_name or keyword in voice_desc:
                        score += 20
                        break
            
            voice_scores.append((voice['id'], score))
        
        # 按得分排序，返回最高分的语音
        voice_scores.sort(key=lambda x: x[1], reverse=True)
        
        if voice_scores and voice_scores[0][1] > 0:
            logger.info(f"角色 {character['name']} 匹配到语音 {voice_scores[0][0]}，得分: {voice_scores[0][1]}")
            return voice_scores[0][0]
        
        return None
    
    def _get_narrator_voice_mapping(self, available_voices: List[Dict]) -> Optional[int]:
        """为旁白角色选择合适的语音"""
        
        # 优先选择标记为"旁白"或"中性"的语音
        for voice in available_voices:
            voice_type = voice.get('voice_type', '').lower()
            voice_name = voice.get('name', '').lower()
            
            if voice_type == 'neutral' or '旁白' in voice_name or 'narrator' in voice_name:
                return voice.get('id')
        
        # 其次选择女性温和声音
        for voice in available_voices:
            voice_type = voice.get('voice_type', '').lower()
            voice_name = voice.get('name', '').lower()
            
            if voice_type == 'female' and ('温柔' in voice_name or '柔和' in voice_name):
                return voice.get('id')
        
        # 最后选择第一个可用声音
        if available_voices:
            return available_voices[0].get('id')
        
        return None
    
    async def _get_available_voices(self) -> List[Dict]:
        """获取可用语音列表"""
        try:
            from ..models import VoiceProfile
            voices = self.db.query(VoiceProfile).filter(VoiceProfile.status == 'active').all()
            return [
                {
                    'id': voice.id,
                    'name': voice.name,
                    'voice_type': voice.type,
                    'description': voice.description or ""
                }
                for voice in voices
            ]
        except Exception as e:
            logger.error(f"获取可用语音失败: {str(e)}")
            return []
    
    def get_voice_compatibility_score(self, character: Dict, voice: Dict) -> int:
        """计算角色与语音的兼容性得分"""
        
        score = 0
        char_gender = character.get('gender', 'unknown')
        char_personality = character.get('personality', 'calm')
        
        voice_type = voice.get('voice_type', '').lower()
        voice_name = voice.get('name', '').lower()
        voice_desc = voice.get('description', '').lower()
        
        # 性别匹配评分
        if char_gender == 'male' and ('male' in voice_type or '男' in voice_name):
            score += 100
        elif char_gender == 'female' and ('female' in voice_type or '女' in voice_name):
            score += 100
        elif char_gender == 'neutral' and ('neutral' in voice_type or '中性' in voice_name):
            score += 100
        elif char_gender == 'unknown':
            score += 50  # 未知性别给中等分
        
        # 性格匹配评分
        personality_boost = {
            'gentle': ['温柔', '柔和', 'gentle', 'soft'],
            'fierce': ['激烈', '强势', 'fierce', 'strong'],
            'calm': ['平静', '稳重', 'calm', 'steady'],
            'lively': ['活泼', '开朗', 'lively', 'cheerful'],
            'wise': ['智慧', '睿智', 'wise', 'intelligent'],
            'brave': ['勇敢', '坚定', 'brave', 'firm']
        }.get(char_personality, [])
        
        for keyword in personality_boost:
            if keyword in voice_name or keyword in voice_desc:
                score += 50
                break
        
        return score 