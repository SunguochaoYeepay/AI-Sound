"""
角色声音映射模块

提供角色和声音的映射功能，用于小说多角色语音合成。
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from .voice_feature import VoiceFeatureExtractor

logger = logging.getLogger("tts.character_voice")

class CharacterVoiceMapper:
    """
    角色声音映射器
    
    管理小说角色和声音之间的映射关系，支持自动推荐音色。
    """
    
    def __init__(
        self,
        voice_extractor: VoiceFeatureExtractor = None,
        mapping_path: str = "./data/character_mapping.json"
    ):
        """
        初始化角色声音映射器
        
        Args:
            voice_extractor: 声纹特征提取器实例
            mapping_path: 角色映射文件路径
        """
        self.mapping_path = mapping_path
        self.voice_extractor = voice_extractor or VoiceFeatureExtractor()
        self.mapping = self._load_mapping()
        
        # 确保存储目录存在
        os.makedirs(os.path.dirname(mapping_path), exist_ok=True)
        
    def _load_mapping(self) -> Dict:
        """加载角色映射"""
        if os.path.exists(self.mapping_path):
            try:
                with open(self.mapping_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载角色映射失败: {e}")
                return {"characters": {}, "last_updated": datetime.now().isoformat()}
        return {"characters": {}, "last_updated": datetime.now().isoformat()}
    
    def _save_mapping(self):
        """保存角色映射"""
        try:
            self.mapping["last_updated"] = datetime.now().isoformat()
            with open(self.mapping_path, 'w', encoding='utf-8') as f:
                json.dump(self.mapping, f, ensure_ascii=False, indent=2)
            logger.info(f"角色映射已保存到 {self.mapping_path}")
        except Exception as e:
            logger.error(f"保存角色映射失败: {e}")
    
    def map_character(self, character_name: str, voice_id: str, attributes: Dict = None) -> Dict:
        """
        映射角色到声音
        
        Args:
            character_name: 角色名称
            voice_id: 声音ID
            attributes: 角色属性
            
        Returns:
            Dict: 角色信息
        """
        # 检查声音是否存在
        voice_info = self.voice_extractor.get_voice(voice_id)
        if not voice_info:
            raise ValueError(f"声音ID {voice_id} 不存在")
        
        # 准备角色属性
        if attributes is None:
            attributes = {}
        
        # 创建/更新角色映射
        character_info = {
            "name": character_name,
            "voice_id": voice_id,
            "voice_name": voice_info["name"],
            "attributes": attributes,
            "mapped_at": datetime.now().isoformat()
        }
        
        self.mapping["characters"][character_name] = character_info
        self._save_mapping()
        
        return character_info
    
    def get_character_voice(self, character_name: str) -> Optional[Dict]:
        """获取角色对应的声音信息"""
        character_info = self.mapping["characters"].get(character_name)
        if not character_info:
            return None
            
        voice_id = character_info["voice_id"]
        voice_info = self.voice_extractor.get_voice(voice_id)
        
        if not voice_info:
            # 如果声音不存在，清理此映射
            del self.mapping["characters"][character_name]
            self._save_mapping()
            return None
            
        return {
            "character": character_info,
            "voice": voice_info
        }
    
    def get_all_characters(self) -> List[Dict]:
        """获取所有角色列表"""
        return list(self.mapping["characters"].values())
    
    def delete_character(self, character_name: str) -> bool:
        """删除角色映射"""
        if character_name in self.mapping["characters"]:
            del self.mapping["characters"][character_name]
            self._save_mapping()
            return True
        return False
    
    def analyze_novel_characters(self, novel_text: str) -> Dict[str, int]:
        """
        分析小说中的角色
        
        Args:
            novel_text: 小说文本
            
        Returns:
            Dict[str, int]: 角色出现频率统计
        """
        import re
        
        # 角色识别规则
        patterns = [
            r'"([^"]+)"\s*[，,。.！!？?]?\s*([^，,。.！!？?"\n]{1,10})说道?',  # "对话"某人说
            r'([^，,。.！!？?"\n]{1,10})说道?[：:][""]([^""]+)[""]'  # 某人说："对话"
        ]
        
        # 找出所有对话与说话者
        characters = {}
        
        for pattern in patterns:
            regex = re.compile(pattern)
            for match in regex.finditer(novel_text):
                if pattern.startswith('"'):
                    speaker = match.group(2).strip()
                else:
                    speaker = match.group(1).strip()
                    
                if len(speaker) <= 10 and len(speaker) >= 1:  # 避免误匹配过长内容
                    characters[speaker] = characters.get(speaker, 0) + 1
                
        return characters
    
    def suggest_character_mapping(self, novel_text: str) -> Dict[str, List[str]]:
        """
        建议小说角色声音映射
        
        Args:
            novel_text: 小说文本
            
        Returns:
            Dict[str, List[str]]: 建议的角色-声音映射
        """
        # 分析小说角色
        characters = self.analyze_novel_characters(novel_text)
        
        # 获取可用声音
        voices = self.voice_extractor.get_all_voices()
        
        # 简单启发式匹配规则
        suggestions = {}
        
        male_voices = [v for v in voices if v.get("attributes", {}).get("gender") == "male"]
        female_voices = [v for v in voices if v.get("attributes", {}).get("gender") == "female"]
        
        for character, count in sorted(characters.items(), key=lambda x: x[1], reverse=True):
            # 简单的性别推断
            if any(keyword in character for keyword in ["先生", "男", "爸", "哥", "弟", "叔", "爷", "王", "李", "张"]):
                suggestions[character] = [v["id"] for v in male_voices[:3]]
            elif any(keyword in character for keyword in ["女士", "女", "妈", "姐", "妹", "婶", "奶", "萍", "芳", "英"]):
                suggestions[character] = [v["id"] for v in female_voices[:3]]
            else:
                # 混合推荐
                mixed = []
                if male_voices:
                    mixed.append(male_voices[0]["id"])
                if female_voices:
                    mixed.append(female_voices[0]["id"])
                suggestions[character] = mixed
                
        return suggestions 