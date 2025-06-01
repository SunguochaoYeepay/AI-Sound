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
from ..adapters.base import SynthesisParams

logger = logging.getLogger(__name__)


class VoiceService:
    """声音服务"""
    
    def __init__(self, db, adapter_factory=None):
        self.db = db
        self.collection = db["voices"]
        # 如果提供了adapter_factory就使用它，否则创建新实例（向后兼容）
        if adapter_factory is not None:
            self.adapter_factory = adapter_factory
        else:
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
                # 正确处理MongoDB文档转换
                if "_id" in doc:
                    del doc["_id"]  # 删除MongoDB的_id字段
                # 确保必要字段存在
                if "id" not in doc:
                    doc["id"] = f"voice_{int(datetime.now().timestamp())}"
                if "created_at" not in doc:
                    doc["created_at"] = datetime.now()
                if "updated_at" not in doc:
                    doc["updated_at"] = datetime.now()
                
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
                # 正确处理MongoDB文档转换
                if "_id" in doc:
                    del doc["_id"]  # 删除MongoDB的_id字段
                # 确保必要字段存在
                if "created_at" not in doc:
                    doc["created_at"] = datetime.now()
                if "updated_at" not in doc:
                    doc["updated_at"] = datetime.now()
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

    async def create_voice_with_file(self, voice_data: VoiceCreate, audio_file, npy_file=None) -> Dict[str, Any]:
        """创建新声音并上传文件"""
        try:
            from fastapi import UploadFile
            import aiofiles
            import json
            
            # 生成声音ID
            voice_id = f"voice_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            
            # 创建声音数据字典
            voice_dict = voice_data.dict()
            
            # 补充必需字段
            voice_dict["id"] = voice_id
            voice_dict["display_name"] = voice_dict.get("display_name") or voice_dict["name"]
            
            # 确保engine_voice_id不为None，避免数据库唯一索引冲突
            if not voice_dict.get("engine_voice_id"):
                voice_dict["engine_voice_id"] = f"{voice_dict['engine_id']}_{voice_id}"
            
            voice_dict["source"] = VoiceSource.UPLOADED.value
            voice_dict["created_at"] = datetime.now()
            voice_dict["updated_at"] = datetime.now()
            
            # 创建声音文件目录
            voice_dir = self.upload_path / voice_id
            voice_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存音频文件
            audio_filename = f"{voice_id}_audio.wav"
            audio_path = voice_dir / audio_filename
            
            async with aiofiles.open(audio_path, 'wb') as f:
                content = await audio_file.read()
                await f.write(content)
            
            # 更新文件路径
            voice_dict["file_path"] = str(audio_path)
            voice_dict["sample_path"] = str(audio_path)  # 使用同一个文件作为样本
            
            # 保存NPY文件（如果提供）
            npy_path = None
            if npy_file:
                npy_filename = f"{voice_id}_features.npy"
                npy_path = voice_dir / npy_filename
                
                async with aiofiles.open(npy_path, 'wb') as f:
                    npy_content = await npy_file.read()
                    await f.write(npy_content)
                
                voice_dict["features_path"] = str(npy_path)
            
            # 创建Voice对象并保存到数据库
            voice = Voice(**voice_dict)
            
            # 检查是否存在相同的engine_id + engine_voice_id组合
            existing_voice = await self.collection.find_one({
                "engine_id": voice.engine_id,
                "engine_voice_id": voice.engine_voice_id
            })
            
            if existing_voice:
                # 如果存在冲突，生成新的engine_voice_id
                voice_dict["engine_voice_id"] = f"{voice.engine_id}_{voice_id}_{uuid.uuid4().hex[:4]}"
                voice = Voice(**voice_dict)
            
            await self.collection.insert_one(voice.dict())
            
            # 返回结果
            result = {
                "voice_id": voice_id,
                "name": voice.name,
                "engine_id": voice.engine_id,
                "audio_file": str(audio_path),
                "features_file": str(npy_path) if npy_path else None,
                "upload_time": datetime.now().isoformat()
            }
            
            # 🎯 新增：同步到对应引擎
            await self._sync_voice_to_engine(voice, audio_path, npy_path)
            
            logger.info(f"声音创建并上传成功: {voice_id}")
            return result
        except Exception as e:
            logger.error(f"创建声音并上传文件失败: {e}")
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
    
    async def preview_voice(self, voice_id: str, text: str = "你好，这是声音预览。") -> Optional[Dict[str, Any]]:
        """声音预览"""
        try:
            # 获取声音信息
            voice = await self.get_voice(voice_id)
            if not voice:
                return None  # 返回None而不是抛出异常
            
            # 获取引擎适配器
            adapter = await self.adapter_factory.get_adapter(voice.engine_id)
            if not adapter:
                logger.warning(f"引擎适配器未找到: {voice.engine_id}")
                return None
            
            # 生成预览音频
            preview_id = f"preview_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            output_filename = f"{preview_id}.wav"
            output_filepath = self.upload_path / "previews" / output_filename
            output_filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # 执行合成
            synthesis_params = SynthesisParams(
                text=text,
                voice_id=voice.engine_voice_id or voice.name,
                speed=1.0,
                pitch=0.0,
                output_path=str(output_filepath)
            )
            
            result = await adapter.synthesize(synthesis_params)
            
            if not result.success:
                logger.error(f"声音合成失败: {result.error_message or '未知错误'}")
                return None
            
            # 构建预览结果 - 使用完整的URL而不是相对路径
            api_host = settings.api.host if settings.api.host != "0.0.0.0" else "127.0.0.1"
            audio_url = f"http://{api_host}:{settings.api.port}/api/voices/preview/{output_filename}"
            
            return {
                "success": True,
                "data": {
                    "voice_id": voice_id,
                    "audio_url": audio_url,
                    "duration": result.duration or 2.5,
                    "text": text
                }
            }
        except Exception as e:
            logger.error(f"声音预览失败: {e}")
            return None
    
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
        """获取指定引擎的声音列表"""
        try:
            return await self.list_voices(engine_id=engine_id, limit=1000)
        except Exception as e:
            logger.error(f"获取引擎声音列表失败: {e}")
            raise

    async def get_language_stats(self) -> Dict[str, Any]:
        """获取语言统计信息"""
        try:
            pipeline = [
                {"$group": {
                    "_id": "$language",
                    "count": {"$sum": 1},
                    "active_count": {"$sum": {"$cond": ["$is_active", 1, 0]}}
                }},
                {"$sort": {"count": -1}}
            ]
            
            cursor = self.collection.aggregate(pipeline)
            language_stats = []
            total_voices = 0
            
            async for doc in cursor:
                language_stats.append({
                    "language": doc["_id"],
                    "total_count": doc["count"],
                    "active_count": doc["active_count"]
                })
                total_voices += doc["count"]
            
            return {
                "total_voices": total_voices,
                "languages": language_stats,
                "language_count": len(language_stats)
            }
        except Exception as e:
            logger.error(f"获取语言统计失败: {e}")
            raise

    async def get_engine_stats(self) -> Dict[str, Any]:
        """获取引擎统计信息"""
        try:
            pipeline = [
                {"$group": {
                    "_id": "$engine_id",
                    "count": {"$sum": 1},
                    "active_count": {"$sum": {"$cond": ["$is_active", 1, 0]}},
                    "avg_usage": {"$avg": "$usage_count"}
                }},
                {"$sort": {"count": -1}}
            ]
            
            cursor = self.collection.aggregate(pipeline)
            engine_stats = []
            total_voices = 0
            
            async for doc in cursor:
                engine_stats.append({
                    "engine_id": doc["_id"],
                    "total_count": doc["count"],
                    "active_count": doc["active_count"],
                    "avg_usage": round(doc.get("avg_usage", 0), 2)
                })
                total_voices += doc["count"]
            
            return {
                "total_voices": total_voices,
                "engines": engine_stats,
                "engine_count": len(engine_stats)
            }
        except Exception as e:
            logger.error(f"获取引擎统计失败: {e}")
            raise

    async def search_similar_voices(
        self, 
        voice_id: Optional[str] = None,
        language: Optional[str] = None,
        gender: Optional[str] = None,
        style: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """搜索相似声音"""
        try:
            query = {"is_active": True}
            
            # 如果提供了参考声音ID，获取其属性
            if voice_id:
                reference_voice = await self.get_voice(voice_id)
                if reference_voice:
                    language = language or reference_voice.language
                    gender = gender or reference_voice.gender.value
                    style = style or reference_voice.style.value
            
            # 构建查询条件
            if language:
                query["language"] = language
            if gender:
                query["gender"] = gender
            if style:
                query["style"] = style
            
            # 排除参考声音本身
            if voice_id:
                query["id"] = {"$ne": voice_id}
            
            cursor = self.collection.find(query).limit(limit)
            similar_voices = []
            
            async for doc in cursor:
                # 正确处理MongoDB文档转换
                if "_id" in doc:
                    del doc["_id"]
                
                similar_voices.append({
                    "id": doc.get("id"),
                    "name": doc.get("name"),
                    "display_name": doc.get("display_name"),
                    "language": doc.get("language"),
                    "gender": doc.get("gender"),
                    "style": doc.get("style"),
                    "engine_id": doc.get("engine_id"),
                    "similarity_score": 0.85  # 模拟相似度分数
                })
            
            return similar_voices
        except Exception as e:
            logger.error(f"搜索相似声音失败: {e}")
            raise

    async def get_voice_sample(self, voice_id: str) -> Optional[str]:
        """获取声音样本文件路径"""
        try:
            voice = await self.get_voice(voice_id)
            if not voice:
                return None
            
            # 检查是否有样本文件
            if voice.sample_path and Path(voice.sample_path).exists():
                return voice.sample_path
            
            # 如果没有样本文件，生成一个
            sample_text = "你好，这是声音样本。"
            sample_filename = f"sample_{voice_id}.wav"
            sample_path = self.upload_path / "samples" / sample_filename
            sample_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 使用引擎生成样本
            adapter = await self.adapter_factory.get_adapter(voice.engine_id)
            if adapter:
                synthesis_params = SynthesisParams(
                    text=sample_text,
                    voice_id=voice.engine_voice_id,
                    output_path=str(sample_path)
                )
                await adapter.synthesize(synthesis_params)
                
                # 更新数据库中的样本路径
                await self.collection.update_one(
                    {"id": voice_id},
                    {"$set": {"sample_path": str(sample_path)}}
                )
                
                return str(sample_path)
            
            return None
        except Exception as e:
            logger.error(f"获取声音样本失败: {e}")
            raise

    async def analyze_voice(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """分析声音特征"""
        try:
            voice = await self.get_voice(voice_id)
            if not voice:
                return None
            
            # 模拟声音分析结果
            analysis_result = {
                "voice_id": voice_id,
                "analysis": {
                    "fundamental_frequency": {
                        "mean": 220.5,
                        "std": 15.2,
                        "min": 180.0,
                        "max": 280.0
                    },
                    "formants": {
                        "f1": 650.0,
                        "f2": 1200.0,
                        "f3": 2500.0
                    },
                    "spectral_features": {
                        "spectral_centroid": 1500.0,
                        "spectral_rolloff": 3000.0,
                        "spectral_bandwidth": 800.0
                    },
                    "voice_quality": {
                        "jitter": 0.02,
                        "shimmer": 0.03,
                        "hnr": 15.5
                    },
                    "emotion_prediction": {
                        "neutral": 0.7,
                        "happy": 0.2,
                        "sad": 0.05,
                        "angry": 0.03,
                        "surprised": 0.02
                    }
                },
                "analyzed_at": datetime.now(),
                "duration": 2.5,
                "sample_rate": 22050
            }
            
            return analysis_result
        except Exception as e:
            logger.error(f"分析声音特征失败: {e}")
            raise

    async def batch_import_voices(self, voices_data: List[VoiceCreate]) -> Dict[str, Any]:
        """批量导入声音"""
        try:
            imported_voices = []
            failed_imports = []
            
            for voice_data in voices_data:
                try:
                    voice = await self.create_voice(voice_data)
                    imported_voices.append({
                        "id": voice.id,
                        "name": voice.name,
                        "status": "success"
                    })
                except Exception as e:
                    failed_imports.append({
                        "name": voice_data.name,
                        "error": str(e),
                        "status": "failed"
                    })
            
            return {
                "success": True,
                "imported_count": len(imported_voices),
                "failed_count": len(failed_imports),
                "imported_voices": imported_voices,
                "failed_imports": failed_imports
            }
        except Exception as e:
            logger.error(f"批量导入声音失败: {e}")
            raise

    async def batch_export_voices(self, voice_ids: List[str]) -> str:
        """批量导出声音"""
        try:
            import zipfile
            import tempfile
            
            # 创建临时zip文件
            temp_dir = Path(tempfile.mkdtemp())
            zip_path = temp_dir / "voices_export.zip"
            
            with zipfile.ZipFile(zip_path, 'w') as zip_file:
                for voice_id in voice_ids:
                    voice = await self.get_voice(voice_id)
                    if voice:
                        # 添加声音信息到zip
                        voice_info = {
                            "id": voice.id,
                            "name": voice.name,
                            "engine_id": voice.engine_id,
                            "language": voice.language,
                            "gender": voice.gender.value if voice.gender else "unknown",
                            "description": voice.description
                        }
                        
                        # 写入声音信息文件
                        info_filename = f"{voice_id}_info.json"
                        zip_file.writestr(info_filename, str(voice_info))
                        
                        # 如果有音频文件，也添加到zip
                        if voice.file_path and Path(voice.file_path).exists():
                            zip_file.write(voice.file_path, f"{voice_id}_audio.wav")
            
            return str(zip_path)
        except Exception as e:
            logger.error(f"批量导出声音失败: {e}")
            raise

    async def clone_voice(self, voice_id: str, new_name: str) -> Optional[Dict[str, Any]]:
        """克隆声音"""
        try:
            original_voice = await self.get_voice(voice_id)
            if not original_voice:
                return None
            
            # 创建克隆的声音数据
            clone_data = VoiceCreate(
                name=new_name,
                display_name=f"{original_voice.display_name} (克隆)",
                engine_id=original_voice.engine_id,
                engine_voice_id=original_voice.engine_voice_id,
                language=original_voice.language,
                gender=original_voice.gender,
                style=original_voice.style,
                source=original_voice.source,
                description=f"克隆自 {original_voice.name}",
                tags=original_voice.tags + ["克隆"]
            )
            
            # 创建克隆声音
            cloned_voice = await self.create_voice(clone_data)
            
            return {
                "success": True,
                "original_voice_id": voice_id,
                "cloned_voice_id": cloned_voice.id,
                "cloned_voice_name": cloned_voice.name
            }
        except Exception as e:
            logger.error(f"克隆声音失败: {e}")
            raise

    async def sync_voices_from_engine(self, engine_id: str) -> Dict[str, Any]:
        """从引擎同步声音"""
        try:
            # 获取引擎适配器
            adapter = await self.adapter_factory.get_adapter(engine_id)
            if not adapter:
                return {
                    "success": False,
                    "error": f"引擎适配器未找到: {engine_id}"
                }
            
            # 从适配器获取声音列表
            engine_voices = await adapter.get_voices()
            
            synced_voices = []
            failed_syncs = []
            
            for engine_voice in engine_voices:
                try:
                    # 检查声音是否已存在
                    existing_voice = await self.collection.find_one({
                        "engine_id": engine_id,
                        "engine_voice_id": engine_voice.get("id")
                    })
                    
                    if not existing_voice:
                        # 创建新声音
                        voice_data = VoiceCreate(
                            name=engine_voice.get("name", "unknown"),
                            display_name=engine_voice.get("display_name", engine_voice.get("name", "unknown")),
                            engine_id=engine_id,
                            engine_voice_id=engine_voice.get("id"),
                            language=engine_voice.get("language", "zh-CN"),
                            gender=VoiceGender(engine_voice.get("gender", "female")),
                            style=VoiceStyle.NEUTRAL,
                            source=VoiceSource.BUILTIN,
                            description=f"从引擎 {engine_id} 同步的声音"
                        )
                        
                        voice = await self.create_voice(voice_data)
                        synced_voices.append({
                            "id": voice.id,
                            "name": voice.name,
                            "status": "created"
                        })
                    else:
                        synced_voices.append({
                            "id": existing_voice["id"],
                            "name": existing_voice["name"],
                            "status": "already_exists"
                        })
                        
                except Exception as e:
                    failed_syncs.append({
                        "engine_voice_id": engine_voice.get("id"),
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "engine_id": engine_id,
                "synced_count": len(synced_voices),
                "failed_count": len(failed_syncs),
                "synced_voices": synced_voices,
                "failed_syncs": failed_syncs
            }
        except Exception as e:
            logger.error(f"从引擎同步声音失败: {e}")
            raise

    async def _sync_voice_to_engine(self, voice: Voice, audio_path: str, npy_path: str):
        """同步声音到对应引擎"""
        try:
            if voice.engine_id == "megatts3":
                # 延迟导入避免循环依赖
                from .engine_service import EngineService
                
                # 创建EngineService实例
                engine_service = EngineService(self.db)
                
                # 上传到MegaTTS3
                result = await engine_service.upload_megatts3_reference(
                    voice.id, 
                    audio_path, 
                    npy_path
                )
                
                if result.get("success"):
                    logger.info(f"声音已同步到MegaTTS3: {voice.id}")
                else:
                    logger.warning(f"声音同步到MegaTTS3失败: {result.get('error', '未知错误')}")
            
            # 未来可以在这里添加其他引擎的同步逻辑
            elif voice.engine_id == "espnet":
                logger.info(f"ESPnet引擎无需额外同步: {voice.id}")
            elif voice.engine_id == "bertvits2":
                logger.info(f"BertVITS2引擎暂不支持声音上传: {voice.id}")
            else:
                logger.info(f"未知引擎类型，跳过同步: {voice.engine_id}")
                
        except Exception as e:
            logger.error(f"同步声音到引擎失败: {e}")
            # 不抛出异常，允许主流程继续