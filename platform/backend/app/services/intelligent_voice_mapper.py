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
        """智能语音匹配 - 不再自动分配，返回空映射"""
        
        logger.info(f"🎭 检测到 {len(detected_characters)} 个角色，但不自动分配voice_id")
        
        # 🔧 不再自动分配任何voice_id，让用户手动分配
        voice_mapping = {}
        
        for character in detected_characters:
            char_name = character['name']
            logger.info(f"⚠️ 角色 '{char_name}' 未分配voice_id，需要用户手动设置")
        
        return voice_mapping
    
    def _find_optimal_voice_for_character(self, character: Dict, available_voices: List[Dict]) -> Optional[int]:
        """为角色找到最佳匹配的语音 - 已禁用自动分配"""
        logger.info(f"❌ 自动分配已禁用，角色 '{character.get('name')}' 需要用户手动分配voice_id")
        return None
    
    def _get_narrator_voice_mapping(self, available_voices: List[Dict]) -> Optional[int]:
        """为旁白角色选择合适的语音 - 已禁用自动分配"""
        logger.info("❌ 旁白自动分配已禁用，需要用户手动设置")
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
        """计算角色与语音的兼容性得分 - 已禁用自动分配"""
        logger.info("❌ 自动兼容性评分已禁用")
        return 0 