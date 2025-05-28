"""
声音服务
提供声音管理的核心业务逻辑
"""

import os
import uuid
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging

from ..models.voice import (
    Voice, VoiceCreate, VoiceUpdate, VoicePreview, VoicePreviewResult,
    VoiceUpload, VoiceStats, VoiceGender, VoiceStyle, VoiceSource
)
from ..adapters.factory import AdapterFactory
from ..core.config import settings

logger = logging.getLogger(__name__)


class VoiceService:
    """声音服务"""
    
    def __init__(self, db):
        self.db = db
        self.collection = db["voices"]
        self.adapter_factory = AdapterFactory()
        self.upload_path = Path(settings.tts.output_path) / "voices"
        self.upload_path.mkdir(parents=True, exist_ok=True)
    
    async def list_voices(
        self,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        engine_id: Optional[str] = None,
        gender: Optional[VoiceGender] = None,
        language: Optional[str] = None,
        style: Optional[VoiceStyle] = None,
        source: Optional[VoiceSource] = None,
        active_only: bool = False
    ) -> List[Voice]:
        """获取声音列表"""
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
            
            if engine_id:
                query["engine_id"] = engine_id
            if gender:
                query["gender"] = gender.value
            if language:
                query["language"] = language
            if style:
                query["style"] = style.value
            if source:
                query["source"] = source.value
            if active_only:
                query["is_active"] = True
            
            cursor = self.collection.find(query).skip(skip).limit(limit)
            voices = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                voices.append(Voice(**doc))
            
            return voices
        except Exception as e:
            logger.error(f"获取声音列表失败: {e}")
            raise
    
    async def get_voice(self, voice_id: str) -> Optional[Voice]:
        """获取指定声音"""
        try:
            doc = await self.collection.find_one({"id": voice_id})
            if doc:
                doc["_id"] = str(doc["_id"])
                return Voice(**doc)
            return None
        except Exception as e:
            logger.error(f"获取声音失败: {e}")
            raise
    
    async def create_voice(self, voice_data: VoiceCreate) -> Voice:
        """创建新声音"""
        try:
            # 生成声音ID
            voice_id = f"voice_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            
            # 创建声音对象
            voice = Voice(
                id=voice_id,
                **voice_data.dict()
            )
            
            # 保存到数据库
            await self.collection.insert_one(voice.dict())
            
            logger.info(f"声音已创建: {voice_id}")
            return voice
        except Exception as e:
            logger.error(f"创建声音失败: {e}")
            raise
    
    async def update_voice(self, voice_id: str, voice_data: VoiceUpdate) -> Optional[Voice]:
        """更新声音"""
        try:
            # 检查声音是否存在
            existing = await self.get_voice(voice_id)
            if not existing:
                return None
            
            # 准备更新数据
            update_data = {k: v for k, v in voice_data.dict().items() if v is not None}
            update_data["updated_at"] = datetime.now()
            
            # 更新数据库
            result = await self.collection.update_one(
                {"id": voice_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"声音已更新: {voice_id}")
                return await self.get_voice(voice_id)
            
            return existing
        except Exception as e:
            logger.error(f"更新声音失败: {e}")
            raise
    
    async def delete_voice(self, voice_id: str) -> bool:
        """删除声音"""
        try:
            # 获取声音信息
            voice = await self.get_voice(voice_id)
            if not voice:
                return False
            
            # 删除相关文件
            if voice.file_path:
                try:
                    file_path = Path(voice.file_path)
                    if file_path.exists():
                        file_path.unlink()
                        logger.info(f"声音文件已删除: {voice.file_path}")
                except Exception as e:
                    logger.warning(f"删除声音文件失败: {e}")
            
            # 从数据库删除
            result = await self.collection.delete_one({"id": voice_id})
            
            if result.deleted_count > 0:
                logger.info(f"声音已删除: {voice_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除声音失败: {e}")
            raise
    
    async def preview_voice(self, voice_id: str, preview_data: VoicePreview) -> VoicePreviewResult:
        """声音预览"""
        try:
            # 获取声音信息
            voice = await self.get_voice(voice_id)
            if not voice:
                raise ValueError("声音未找到")
            
            # 获取引擎适配器
            adapter = await self.adapter_factory.get_adapter(voice.engine_id)
            if not adapter:
                raise ValueError(f"引擎适配器未找到: {voice.engine_id}")
            
            # 生成预览音频
            preview_id = f"preview_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            output_filename = f"{preview_id}.wav"
            output_filepath = self.upload_path / "previews" / output_filename
            output_filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # 执行合成
            synthesis_params = {
                "text": preview_data.text,
                "voice_id": voice.engine_voice_id,
                "speed": preview_data.speed,
                "pitch": preview_data.pitch,
                "output_path": str(output_filepath)
            }
            
            result = await adapter.synthesize(**synthesis_params)
            
            # 构建预览结果
            audio_url = f"/api/voices/preview/{output_filename}"
            
            return VoicePreviewResult(
                voice_id=voice_id,
                audio_url=audio_url,
                duration=result.get("duration")
            )
        except Exception as e:
            logger.error(f"声音预览失败: {e}")
            raise
    
    async def upload_voice_file(self, voice_id: str, file_data: bytes, upload_info: VoiceUpload) -> bool:
        """上传声音文件"""
        try:
            # 获取声音信息
            voice = await self.get_voice(voice_id)
            if not voice:
                return False
            
            # 验证文件校验和
            file_hash = hashlib.md5(file_data).hexdigest()
            if file_hash != upload_info.checksum:
                raise ValueError("文件校验和不匹配")
            
            # 保存文件
            file_path = self.upload_path / voice_id / upload_info.filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, "wb") as f:
                f.write(file_data)
            
            # 更新声音信息
            await self.collection.update_one(
                {"id": voice_id},
                {"$set": {
                    "file_path": str(file_path),
                    "metadata.file_size": upload_info.file_size,
                    "source": VoiceSource.UPLOADED.value,
                    "updated_at": datetime.now()
                }}
            )
            
            logger.info(f"声音文件已上传: {voice_id} -> {file_path}")
            return True
        except Exception as e:
            logger.error(f"上传声音文件失败: {e}")
            raise
    
    async def analyze_voice_features(self, voice_id: str) -> Dict[str, Any]:
        """分析声音特征"""
        try:
            # 获取声音信息
            voice = await self.get_voice(voice_id)
            if not voice or not voice.file_path:
                raise ValueError("声音文件未找到")
            
            # TODO: 实现声音特征分析
            # 这里可以使用librosa、praat-parselmouth等库进行音频特征提取
            
            # 示例特征数据
            features = {
                "pitch_mean": 220.0,
                "pitch_range": 50.0,
                "speaking_rate": 5.0,
                "energy_level": 0.8,
                "formant_frequencies": [800, 1200, 2400],
                "spectral_features": {
                    "spectral_centroid": 2000.0,
                    "spectral_bandwidth": 1500.0,
                    "zero_crossing_rate": 0.1
                }
            }
            
            # 更新声音特征
            await self.collection.update_one(
                {"id": voice_id},
                {"$set": {
                    "features": features,
                    "updated_at": datetime.now()
                }}
            )
            
            return features
        except Exception as e:
            logger.error(f"分析声音特征失败: {e}")
            raise
    
    async def get_voice_stats(self) -> VoiceStats:
        """获取声音统计信息"""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": 1},
                        "active": {"$sum": {"$cond": ["$is_active", 1, 0]}},
                        "by_gender": {
                            "$push": {
                                "gender": "$gender",
                                "count": 1
                            }
                        },
                        "by_language": {
                            "$push": {
                                "language": "$language",
                                "count": 1
                            }
                        },
                        "by_engine": {
                            "$push": {
                                "engine": "$engine_id",
                                "count": 1
                            }
                        },
                        "by_source": {
                            "$push": {
                                "source": "$source",
                                "count": 1
                            }
                        },
                        "total_usage": {"$sum": "$usage_count"}
                    }
                }
            ]
            
            cursor = self.collection.aggregate(pipeline)
            result = await cursor.to_list(length=1)
            
            if result:
                stats = result[0]
                
                # 统计性别分布
                gender_counts = {}
                for item in stats["by_gender"]:
                    gender = item["gender"]
                    gender_counts[gender] = gender_counts.get(gender, 0) + 1
                
                # 统计语言分布
                language_counts = {}
                for item in stats["by_language"]:
                    language = item["language"]
                    language_counts[language] = language_counts.get(language, 0) + 1
                
                # 统计引擎分布
                engine_counts = {}
                for item in stats["by_engine"]:
                    engine = item["engine"]
                    engine_counts[engine] = engine_counts.get(engine, 0) + 1
                
                # 统计来源分布
                source_counts = {}
                for item in stats["by_source"]:
                    source = item["source"]
                    source_counts[source] = source_counts.get(source, 0) + 1
                
                return VoiceStats(
                    total_voices=stats["total"],
                    active_voices=stats["active"],
                    by_gender=gender_counts,
                    by_language=language_counts,
                    by_engine=engine_counts,
                    by_source=source_counts,
                    total_usage=stats["total_usage"]
                )
            
            return VoiceStats(
                total_voices=0,
                active_voices=0,
                by_gender={},
                by_language={},
                by_engine={},
                by_source={},
                total_usage=0
            )
        except Exception as e:
            logger.error(f"获取声音统计失败: {e}")
            raise
    
    async def update_usage_count(self, voice_id: str):
        """更新声音使用次数"""
        try:
            await self.collection.update_one(
                {"id": voice_id},
                {
                    "$inc": {"usage_count": 1},
                    "$set": {"last_used_at": datetime.now()}
                }
            )
        except Exception as e:
            logger.error(f"更新声音使用次数失败: {e}")
    
    async def get_voices_by_engine(self, engine_id: str) -> List[Voice]:
        """根据引擎获取声音列表"""
        try:
            return await self.list_voices(engine_id=engine_id, active_only=True)
        except Exception as e:
            logger.error(f"根据引擎获取声音失败: {e}")
            raise