"""
角色服务
提供角色管理和声音映射的核心业务逻辑
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from ..models.character import (
    Character, CharacterCreate, CharacterUpdate, VoiceMapping, VoiceMappingCreate,
    CharacterVoiceTest, CharacterVoiceTestResult, CharacterStats,
    CharacterType, CharacterGender
)
from ..models.voice import Voice
from ..adapters.factory import AdapterFactory
from ..core.config import settings

logger = logging.getLogger(__name__)


class CharacterService:
    """角色服务"""
    
    def __init__(self, db):
        self.db = db
        self.collection = db["characters"]
        self.voice_collection = db["voices"]
        self.adapter_factory = AdapterFactory()
    
    async def list_characters(
        self,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        character_type: Optional[CharacterType] = None,
        gender: Optional[CharacterGender] = None,
        category: Optional[str] = None,
        active_only: bool = False,
        with_voices_only: bool = False
    ) -> List[Character]:
        """获取角色列表"""
        try:
            # 构建查询条件
            query = {}
            
            if search:
                query["$or"] = [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"display_name": {"$regex": search, "$options": "i"}},
                    {"description": {"$regex": search, "$options": "i"}},
                    {"tags": {"$regex": search, "$options": "i"}}
                ]
            
            if character_type:
                query["type"] = character_type.value
            if gender:
                query["gender"] = gender.value
            if category:
                query["category"] = category
            if active_only:
                query["is_active"] = True
            if with_voices_only:
                query["voice_mappings.0"] = {"$exists": True}
            
            cursor = self.collection.find(query).skip(skip).limit(limit)
            characters = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                characters.append(Character(**doc))
            
            return characters
        except Exception as e:
            logger.error(f"获取角色列表失败: {e}")
            raise
    
    async def get_character(self, character_id: str) -> Optional[Character]:
        """获取指定角色"""
        try:
            doc = await self.collection.find_one({"id": character_id})
            if doc:
                doc["_id"] = str(doc["_id"])
                return Character(**doc)
            return None
        except Exception as e:
            logger.error(f"获取角色失败: {e}")
            raise
    
    async def create_character(self, character_data: CharacterCreate) -> Character:
        """创建新角色"""
        try:
            # 生成角色ID
            character_id = f"char_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            
            # 创建角色对象
            character = Character(
                id=character_id,
                **character_data.dict()
            )
            
            # 保存到数据库
            await self.collection.insert_one(character.dict())
            
            logger.info(f"角色已创建: {character_id}")
            return character
        except Exception as e:
            logger.error(f"创建角色失败: {e}")
            raise
    
    async def update_character(self, character_id: str, character_data: CharacterUpdate) -> Optional[Character]:
        """更新角色"""
        try:
            # 检查角色是否存在
            existing = await self.get_character(character_id)
            if not existing:
                return None
            
            # 准备更新数据
            update_data = {k: v for k, v in character_data.dict().items() if v is not None}
            update_data["updated_at"] = datetime.now()
            
            # 更新数据库
            result = await self.collection.update_one(
                {"id": character_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"角色已更新: {character_id}")
                return await self.get_character(character_id)
            
            return existing
        except Exception as e:
            logger.error(f"更新角色失败: {e}")
            raise
    
    async def delete_character(self, character_id: str) -> bool:
        """删除角色"""
        try:
            result = await self.collection.delete_one({"id": character_id})
            
            if result.deleted_count > 0:
                logger.info(f"角色已删除: {character_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除角色失败: {e}")
            raise
    
    async def add_voice_mapping(
        self, 
        character_id: str, 
        mapping_data: VoiceMappingCreate
    ) -> Optional[Character]:
        """为角色添加声音映射"""
        try:
            # 检查角色是否存在
            character = await self.get_character(character_id)
            if not character:
                return None
            
            # 检查声音是否存在
            voice_doc = await self.voice_collection.find_one({"id": mapping_data.voice_id})
            if not voice_doc:
                raise ValueError("声音不存在")
            
            # 创建声音映射
            voice_mapping = VoiceMapping(
                voice_name=voice_doc.get("display_name", voice_doc.get("name")),
                **mapping_data.dict()
            )
            
            # 如果设置为默认声音，先清除其他默认设置
            if mapping_data.is_default:
                await self.collection.update_one(
                    {"id": character_id},
                    {"$set": {"voice_mappings.$[].is_default": False}}
                )
            
            # 添加新映射
            result = await self.collection.update_one(
                {"id": character_id},
                {
                    "$push": {"voice_mappings": voice_mapping.dict()},
                    "$set": {
                        "updated_at": datetime.now(),
                        **({"default_voice_id": mapping_data.voice_id} if mapping_data.is_default else {})
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"声音映射已添加: {character_id} -> {mapping_data.voice_id}")
                return await self.get_character(character_id)
            
            return character
        except Exception as e:
            logger.error(f"添加声音映射失败: {e}")
            raise
    
    async def remove_voice_mapping(self, character_id: str, voice_id: str) -> Optional[Character]:
        """删除角色的声音映射"""
        try:
            # 检查角色是否存在
            character = await self.get_character(character_id)
            if not character:
                return None
            
            # 删除映射
            result = await self.collection.update_one(
                {"id": character_id},
                {
                    "$pull": {"voice_mappings": {"voice_id": voice_id}},
                    "$set": {"updated_at": datetime.now()}
                }
            )
            
            # 如果删除的是默认声音，清除默认设置
            if character.default_voice_id == voice_id:
                await self.collection.update_one(
                    {"id": character_id},
                    {"$unset": {"default_voice_id": ""}}
                )
            
            if result.modified_count > 0:
                logger.info(f"声音映射已删除: {character_id} -> {voice_id}")
                return await self.get_character(character_id)
            
            return character
        except Exception as e:
            logger.error(f"删除声音映射失败: {e}")
            raise
    
    async def set_default_voice(self, character_id: str, voice_id: str) -> Optional[Character]:
        """设置角色的默认声音"""
        try:
            # 检查角色是否存在
            character = await self.get_character(character_id)
            if not character:
                return None
            
            # 检查声音映射是否存在
            voice_mapping_exists = any(
                mapping.voice_id == voice_id for mapping in character.voice_mappings
            )
            if not voice_mapping_exists:
                raise ValueError("声音映射不存在")
            
            # 清除所有默认设置
            await self.collection.update_one(
                {"id": character_id},
                {"$set": {"voice_mappings.$[].is_default": False}}
            )
            
            # 设置新的默认声音
            result = await self.collection.update_one(
                {"id": character_id, "voice_mappings.voice_id": voice_id},
                {
                    "$set": {
                        "voice_mappings.$.is_default": True,
                        "default_voice_id": voice_id,
                        "updated_at": datetime.now()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"默认声音已设置: {character_id} -> {voice_id}")
                return await self.get_character(character_id)
            
            return character
        except Exception as e:
            logger.error(f"设置默认声音失败: {e}")
            raise
    
    async def test_character_voice(
        self, 
        character_id: str, 
        test_data: CharacterVoiceTest
    ) -> CharacterVoiceTestResult:
        """测试角色声音"""
        try:
            # 获取角色信息
            character = await self.get_character(character_id)
            if not character:
                raise ValueError("角色不存在")
            
            # 确定使用的声音
            voice_id = test_data.voice_id or character.default_voice_id
            if not voice_id:
                if character.voice_mappings:
                    # 使用优先级最高的声音
                    voice_mapping = max(character.voice_mappings, key=lambda x: x.priority)
                    voice_id = voice_mapping.voice_id
                else:
                    raise ValueError("角色没有配置声音")
            
            # 获取声音信息
            voice_doc = await self.voice_collection.find_one({"id": voice_id})
            if not voice_doc:
                raise ValueError("声音不存在")
            
            # 获取引擎适配器
            adapter = await self.adapter_factory.get_adapter(voice_doc["engine_id"])
            if not adapter:
                raise ValueError(f"引擎适配器未找到: {voice_doc['engine_id']}")
            
            # 确定参数
            speed = test_data.speed if test_data.speed is not None else character.default_speed
            pitch = test_data.pitch if test_data.pitch is not None else character.default_pitch
            volume = test_data.volume if test_data.volume is not None else character.default_volume
            
            # 生成测试音频
            test_id = f"test_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            output_filename = f"{test_id}.wav"
            output_filepath = settings.tts.output_path / "tests" / output_filename
            output_filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # 执行合成
            synthesis_params = {
                "text": test_data.text,
                "voice_id": voice_doc["engine_voice_id"],
                "speed": speed,
                "pitch": pitch,
                "volume": volume,
                "output_path": str(output_filepath)
            }
            
            result = await adapter.synthesize(**synthesis_params)
            
            # 更新使用次数
            await self.collection.update_one(
                {"id": character_id},
                {
                    "$inc": {"usage_count": 1},
                    "$set": {"last_used_at": datetime.now()}
                }
            )
            
            # 构建测试结果
            audio_url = f"/api/characters/test/{output_filename}"
            
            return CharacterVoiceTestResult(
                character_id=character_id,
                voice_id=voice_id,
                voice_name=voice_doc.get("display_name", voice_doc.get("name")),
                engine_id=voice_doc["engine_id"],
                audio_url=audio_url,
                duration=result.get("duration"),
                parameters_used={
                    "speed": speed,
                    "pitch": pitch,
                    "volume": volume
                }
            )
        except Exception as e:
            logger.error(f"测试角色声音失败: {e}")
            raise
    
    async def get_character_stats(self) -> CharacterStats:
        """获取角色统计信息"""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": 1},
                        "active": {"$sum": {"$cond": ["$is_active", 1, 0]}},
                        "by_type": {
                            "$push": {
                                "type": "$type",
                                "count": 1
                            }
                        },
                        "by_gender": {
                            "$push": {
                                "gender": "$gender",
                                "count": 1
                            }
                        },
                        "by_category": {
                            "$push": {
                                "category": "$category",
                                "count": 1
                            }
                        },
                        "with_voices": {
                            "$sum": {
                                "$cond": [
                                    {"$gt": [{"$size": "$voice_mappings"}, 0]},
                                    1,
                                    0
                                ]
                            }
                        },
                        "total_mappings": {"$sum": {"$size": "$voice_mappings"}},
                        "total_usage": {"$sum": "$usage_count"}
                    }
                }
            ]
            
            cursor = self.collection.aggregate(pipeline)
            result = await cursor.to_list(length=1)
            
            if result:
                stats = result[0]
                
                # 统计类型分布
                type_counts = {}
                for item in stats["by_type"]:
                    char_type = item["type"]
                    type_counts[char_type] = type_counts.get(char_type, 0) + 1
                
                # 统计性别分布
                gender_counts = {}
                for item in stats["by_gender"]:
                    gender = item["gender"]
                    gender_counts[gender] = gender_counts.get(gender, 0) + 1
                
                # 统计分类分布
                category_counts = {}
                for item in stats["by_category"]:
                    category = item["category"]
                    category_counts[category] = category_counts.get(category, 0) + 1
                
                return CharacterStats(
                    total_characters=stats["total"],
                    active_characters=stats["active"],
                    by_type=type_counts,
                    by_gender=gender_counts,
                    by_category=category_counts,
                    with_voices=stats["with_voices"],
                    total_voice_mappings=stats["total_mappings"],
                    total_usage=stats["total_usage"]
                )
            
            return CharacterStats(
                total_characters=0,
                active_characters=0,
                by_type={},
                by_gender={},
                by_category={},
                with_voices=0,
                total_voice_mappings=0,
                total_usage=0
            )
        except Exception as e:
            logger.error(f"获取角色统计失败: {e}")
            raise
    
    async def get_character_by_name(self, name: str) -> Optional[Character]:
        """根据名称获取角色"""
        try:
            doc = await self.collection.find_one({
                "$or": [
                    {"name": name},
                    {"display_name": name}
                ]
            })
            if doc:
                doc["_id"] = str(doc["_id"])
                return Character(**doc)
            return None
        except Exception as e:
            logger.error(f"根据名称获取角色失败: {e}")
            raise
    
    async def update_usage_count(self, character_id: str):
        """更新角色使用次数"""
        try:
            await self.collection.update_one(
                {"id": character_id},
                {
                    "$inc": {"usage_count": 1},
                    "$set": {"last_used_at": datetime.now()}
                }
            )
        except Exception as e:
            logger.error(f"更新角色使用次数失败: {e}")