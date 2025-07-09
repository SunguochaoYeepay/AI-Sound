from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.character import Character
from app.schemas.character import CharacterCreate, CharacterUpdate, CharacterMatchResult
import logging

logger = logging.getLogger(__name__)

class CharacterService:
    def __init__(self, db: Session):
        self.db = db

    def create_characters_from_analysis(self, book_id: int, chapter_id: int, detected_characters: List[Dict]) -> List[Character]:
        """
        从分析结果创建角色记录
        """
        try:
            created_characters = []
            
            for char_data in detected_characters:
                character_name = char_data.get('name', '').strip()
                if not character_name:
                    continue
                
                # 检查是否已存在同名角色
                existing_character = self.db.query(Character).filter(
                    Character.name == character_name,
                    Character.book_id == book_id,
                    Character.chapter_id == chapter_id
                ).first()
                
                if existing_character:
                    # 更新现有角色信息
                    existing_character.description = char_data.get('description', existing_character.description)
                    created_characters.append(existing_character)
                else:
                    # 创建新角色记录
                    new_character = Character(
                        name=character_name,
                        description=char_data.get('description', ''),
                        book_id=book_id,
                        chapter_id=chapter_id,
                        voice_profile=char_data.get('voice_profile'),
                        voice_config=char_data.get('voice_config')
                    )
                    self.db.add(new_character)
                    created_characters.append(new_character)
            
            self.db.commit()
            logger.info(f"为章节 {chapter_id} 创建了 {len(created_characters)} 个角色记录")
            return created_characters
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建角色记录失败: {str(e)}")
            raise e

    def sync_characters_with_analysis(self, book_id: int, chapter_id: int) -> Dict[str, Any]:
        """
        同步角色记录与分析结果
        """
        try:
            # 这里需要从分析结果中获取角色信息
            # 由于目前分析结果存储在AnalysisResult表中，我们需要获取最新的分析结果
            from app.models.analysis_result import AnalysisResult
            
            analysis_result = self.db.query(AnalysisResult).filter(
                AnalysisResult.chapter_id == chapter_id,
                AnalysisResult.status == 'completed'
            ).order_by(AnalysisResult.created_at.desc()).first()
            
            if not analysis_result:
                return {
                    'success': False,
                    'message': '未找到章节分析结果'
                }
            
            # 获取检测到的角色
            detected_characters = analysis_result.detected_characters or []
            if isinstance(detected_characters, str):
                import json
                detected_characters = json.loads(detected_characters)
            
            # 创建或更新角色记录
            characters = self.create_characters_from_analysis(book_id, chapter_id, detected_characters)
            
            return {
                'success': True,
                'message': f'成功同步 {len(characters)} 个角色',
                'characters': characters
            }
            
        except Exception as e:
            logger.error(f"同步角色记录失败: {str(e)}")
            return {
                'success': False,
                'message': f'同步失败: {str(e)}'
            }

    def match_characters_by_chapter(self, book_id: int, chapter_id: int) -> Dict[str, Any]:
        """
        根据书籍和章节匹配角色配置
        """
        try:
            # 获取当前章节的所有角色（待匹配的角色）
            current_characters = self.db.query(Character).filter(
                Character.chapter_id == chapter_id
            ).all()
            
            # 获取同一本书下其他章节的已配置角色
            configured_characters = self.db.query(Character).filter(
                Character.book_id == book_id,
                Character.chapter_id != chapter_id,
                Character.voice_config.isnot(None)
            ).all()
            
            matched = []
            unmatched = []
            
            for current_char in current_characters:
                match_found = False
                
                # 查找同名角色
                for configured_char in configured_characters:
                    if current_char.name == configured_char.name:
                        matched.append(CharacterMatchResult(
                            matched=True,
                            character=configured_char,
                            current_config=current_char.voice_config,
                            matched_config=configured_char.voice_config
                        ))
                        match_found = True
                        break
                
                if not match_found:
                    unmatched.append({
                        'name': current_char.name,
                        'id': current_char.id
                    })
            
            return {
                'matched': matched,
                'unmatched': unmatched,
                'total_count': len(current_characters),
                'matched_count': len(matched)
            }
            
        except Exception as e:
            logger.error(f"匹配角色失败: {str(e)}")
            raise e

    def apply_character_matches(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        应用匹配结果
        """
        try:
            applied_count = 0
            
            for match in matches:
                # 获取目标角色
                target_character = self.db.query(Character).filter(
                    Character.id == match['target_id']
                ).first()
                
                if target_character:
                    # 应用匹配的配置
                    target_character.voice_config = match['matched_config']
                    target_character.voice_profile = match.get('voice_profile')
                    applied_count += 1
            
            self.db.commit()
            
            return {
                'applied_count': applied_count
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"应用匹配失败: {str(e)}")
            raise e

    # ... existing methods ... 