"""角色管理核心服务"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, or_, and_
from fastapi import HTTPException, UploadFile
import logging
import os
import json
import shutil
from datetime import datetime

from app.models.character import Character
from app.models import VoiceProfile, SystemLog, UsageStats
from app.schemas.character import CharacterCreate, CharacterUpdate, CharacterResponse
from app.utils import log_system_event, get_audio_duration, update_usage_stats
from app.utils.character_utils import validate_audio_file, validate_image_file
from app.core.config import settings

logger = logging.getLogger(__name__)

class CharacterManagementService:
    """角色管理核心服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_characters_with_filters(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str = "",
        voice_type: str = "",
        quality_min: float = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        tags: str = "",
        status: str = "",
        book_id: Optional[int] = None,
        chapter_id: Optional[int] = None,
        avatar_filter: str = "",
        audio_filter: str = ""
    ) -> Dict[str, Any]:
        """获取带过滤条件的角色列表"""
        try:
            # 构建基础查询
            query = self.db.query(Character)
            
            # 应用过滤条件
            query = self._apply_filters(
                query, search, voice_type, quality_min, status, 
                book_id, chapter_id, tags, avatar_filter, audio_filter
            )
            
            # 在应用排序前计算统计信息（避免ORDER BY与聚合函数冲突）
            stats = self._calculate_stats(query)
            
            # 获取总数
            total = query.count()
            
            # 应用排序
            query = self._apply_sorting(query, sort_by, sort_order)
            
            # 应用分页
            offset = (page - 1) * page_size
            characters = query.offset(offset).limit(page_size).all()
            
            # 转换为字典格式
            character_list = [character.to_dict() for character in characters]
            
            return {
                "success": True,
                "data": character_list,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "pages": (total + page_size - 1) // page_size
                },
                "stats": stats,
                "filters": {
                    "search": search,
                    "voice_type": voice_type,
                    "quality_min": quality_min,
                    "status": status,
                    "book_id": book_id,
                    "chapter_id": chapter_id,
                    "tags": tags
                }
            }
            
        except Exception as e:
            logger.error(f"获取角色列表失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取角色列表失败: {str(e)}")
    
    def _apply_filters(
        self, 
        query, 
        search: str, 
        voice_type: str, 
        quality_min: float, 
        status: str,
        book_id: Optional[int], 
        chapter_id: Optional[int], 
        tags: str, 
        avatar_filter: str, 
        audio_filter: str
    ):
        """应用查询过滤条件"""
        # 搜索过滤
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Character.name.like(search_pattern),
                    Character.description.like(search_pattern)
                )
            )
        
        # 声音类型过滤
        if voice_type and voice_type in ['male', 'female', 'child', 'elder', 'custom']:
            query = query.filter(Character.voice_type == voice_type)
        
        # 质量分过滤
        if quality_min > 0:
            query = query.filter(Character.quality_score >= quality_min)
        
        # 状态过滤
        if status:
            query = query.filter(Character.status == status)
        
        # 书籍过滤
        if book_id:
            query = query.filter(Character.book_id == book_id)
        
        # 章节过滤
        if chapter_id:
            query = query.filter(Character.chapter_id == chapter_id)
        
        # 标签过滤
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            for tag in tag_list:
                query = query.filter(Character.tags.like(f'%"{tag}"%'))
        
        # 头像设置过滤
        if avatar_filter == "has_avatar":
            query = query.filter(Character.avatar_path.isnot(None))
            query = query.filter(Character.avatar_path != "")
        elif avatar_filter == "no_avatar":
            query = query.filter(or_(Character.avatar_path.is_(None), Character.avatar_path == ""))
        
        # 音频文件过滤
        if audio_filter == "has_audio":
            query = query.filter(and_(
                Character.reference_audio_path.isnot(None),
                Character.reference_audio_path != "",
                Character.latent_file_path.isnot(None),
                Character.latent_file_path != ""
            ))
        elif audio_filter == "no_audio":
            query = query.filter(or_(
                Character.reference_audio_path.is_(None),
                Character.reference_audio_path == "",
                Character.latent_file_path.is_(None),
                Character.latent_file_path == ""
            ))
        
        return query
    
    def _apply_sorting(self, query, sort_by: str, sort_order: str):
        """应用排序"""
        sort_field = getattr(Character, sort_by, Character.created_at)
        if sort_order == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))
        return query
    
    def _calculate_stats(self, base_query) -> Dict[str, Any]:
        """计算统计信息"""
        return {
            'total_count': base_query.count(),
            'configured_count': base_query.filter(Character.status == 'configured').count(),
            'unconfigured_count': base_query.filter(Character.status == 'unconfigured').count(),
            'average_quality': base_query.with_entities(func.avg(Character.quality_score)).scalar() or 0
        }
    
    def get_character_by_id(self, character_id: int) -> Optional[Character]:
        """根据ID获取角色"""
        return self.db.query(Character).filter(Character.id == character_id).first()
    
    def check_character_exists(self, name: str) -> Dict[str, Any]:
        """检查角色是否存在"""
        try:
            # 查找同名角色
            existing_characters = self.db.query(Character).filter(
                Character.name.ilike(f"%{name}%")
            ).all()
            
            if existing_characters:
                character_list = []
                for char in existing_characters:
                    character_data = char.to_dict()
                    character_list.append(character_data)
                
                return {
                    "success": True,
                    "exists": True,
                    "data": {
                        "characters": character_list,
                        "count": len(character_list),
                        "message": f"找到 {len(character_list)} 个相似角色"
                    }
                }
            else:
                return {
                    "success": True,
                    "exists": False,
                    "data": {
                        "characters": [],
                        "count": 0,
                        "message": "未找到相似角色"
                    }
                }
                
        except Exception as e:
            logger.error(f"检查角色存在性失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"检查角色存在性失败: {str(e)}")
    
    def get_voice_statistics(self) -> Dict[str, Any]:
        """获取声音统计信息"""
        try:
            total_characters = self.db.query(Character).count()
            configured_characters = self.db.query(Character).filter(
                Character.status == 'configured'
            ).count()
            
            # 获取今日使用统计
            today = datetime.now().date()
            today_usage = self.db.query(func.sum(UsageStats.usage_count)).filter(
                func.date(UsageStats.date) == today
            ).scalar() or 0
            
            return {
                "success": True,
                "data": {
                    "total_characters": total_characters,
                    "configured_characters": configured_characters,
                    "today_usage": today_usage
                }
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")
    
    def delete_character(self, character_id: int, force: bool = False) -> Dict[str, Any]:
        """删除角色"""
        try:
            character = self.get_character_by_id(character_id)
            if not character:
                raise HTTPException(status_code=404, detail="角色不存在")
            
            # 检查是否有关联的音频文件
            if not force and (character.reference_audio_path or character.latent_file_path):
                return {
                    "success": False,
                    "message": "角色有关联的音频文件，请使用强制删除或先清理文件",
                    "requires_force": True
                }
            
            # 删除关联文件
            if character.reference_audio_path and os.path.exists(character.reference_audio_path):
                os.remove(character.reference_audio_path)
            
            if character.latent_file_path and os.path.exists(character.latent_file_path):
                os.remove(character.latent_file_path)
            
            if character.avatar_path and os.path.exists(character.avatar_path):
                os.remove(character.avatar_path)
            
            # 删除数据库记录
            self.db.delete(character)
            self.db.commit()
            
            return {
                "success": True,
                "message": f"角色 '{character.name}' 删除成功"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除角色失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"删除角色失败: {str(e)}")

    def create_character(self, character_data: CharacterCreate) -> Dict[str, Any]:
        """创建新角色"""
        try:
            # 🔧 修复：基于书籍ID和角色名称检查冲突
            existing_query = self.db.query(Character).filter(
                Character.name == character_data.name
            )
            
            # 如果指定了书籍ID，则检查同一书籍内的名称冲突
            if character_data.book_id:
                existing_query = existing_query.filter(Character.book_id == character_data.book_id)
            
            existing = existing_query.first()
            
            if existing:
                raise HTTPException(
                    status_code=400, 
                    detail=f"在书籍ID {character_data.book_id} 中角色名称 '{character_data.name}' 已存在"
                )
            
            # 创建角色对象
            character = Character(
                name=character_data.name,
                description=character_data.description or "",
                voice_type=getattr(character_data, 'voice_type', None) or "custom",
                quality_score=getattr(character_data, 'quality_score', None) or 0.0,
                status="unconfigured",
                tags=json.dumps(getattr(character_data, 'tags', None) or []),
                book_id=character_data.book_id,
                chapter_id=character_data.chapter_id,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 保存到数据库
            self.db.add(character)
            self.db.commit()
            self.db.refresh(character)
            
            # 记录系统日志
            logger.info(f"创建角色: {character.name} (ID: {character.id})")
            
            return {
                "success": True,
                "data": character.to_dict(),
                "message": f"角色 '{character.name}' 创建成功"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建角色失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"创建角色失败: {str(e)}")

    def update_character(self, character_id: int, character_data: CharacterUpdate) -> Dict[str, Any]:
        """更新角色信息"""
        try:
            character = self.get_character_by_id(character_id)
            if not character:
                raise HTTPException(status_code=404, detail="角色不存在")
            
            # 🔧 修复：基于书籍ID检查名称冲突（如果更改了名称）
            if character_data.name and character_data.name != character.name:
                existing_query = self.db.query(Character).filter(
                    Character.name == character_data.name,
                    Character.id != character_id
                )
                
                # 如果当前角色有书籍ID，则检查同一书籍内的名称冲突
                if character.book_id:
                    existing_query = existing_query.filter(Character.book_id == character.book_id)
                
                existing = existing_query.first()
                
                if existing:
                    raise HTTPException(
                        status_code=400,
                        detail=f"在书籍ID {character.book_id} 中角色名称 '{character_data.name}' 已存在"
                    )
            
            # 更新字段
            update_data = character_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if field == "tags" and value is not None:
                    setattr(character, field, json.dumps(value))
                elif value is not None:
                    setattr(character, field, value)
            
            character.updated_at = datetime.now()
            
            # 保存更改
            self.db.commit()
            self.db.refresh(character)
            
            # 记录系统日志
            logger.info(f"更新角色: {character.name} (ID: {character_id}, 更新字段: {list(update_data.keys())})")
            
            return {
                "success": True,
                "data": character.to_dict(),
                "message": f"角色 '{character.name}' 更新成功"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新角色失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"更新角色失败: {str(e)}")

    def upload_character_audio(
        self, 
        character_id: int, 
        audio_file: UploadFile,
        audio_type: str = "reference"
    ) -> Dict[str, Any]:
        """上传角色音频文件"""
        try:
            character = self.get_character_by_id(character_id)
            if not character:
                raise HTTPException(status_code=404, detail="角色不存在")
            
            # 根据文件类型进行验证
            if audio_type == "latent":
                # NPY文件验证
                if not audio_file.filename.lower().endswith('.npy'):
                    raise HTTPException(status_code=400, detail="Latent文件必须是.npy格式")
            else:
                # 音频文件验证
                is_valid, error_msg = validate_audio_file(audio_file)
                if not is_valid:
                    raise HTTPException(status_code=400, detail=error_msg)
            
            # 创建保存目录
            audio_dir = os.path.join(settings.UPLOAD_DIR, "characters", str(character_id), "audio")
            os.makedirs(audio_dir, exist_ok=True)
            
            # 生成文件名
            file_extension = os.path.splitext(audio_file.filename)[1]
            if audio_type == "reference":
                filename = f"reference{file_extension}"
            else:
                filename = f"latent{file_extension}"
            
            file_path = os.path.join(audio_dir, filename)
            
            # 保存文件
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(audio_file.file, buffer)
            
            # 更新数据库
            if audio_type == "reference":
                # 获取音频时长
                duration = get_audio_duration(file_path)
                character.reference_audio_path = file_path
                character.reference_audio_duration = duration
            else:
                # NPY文件不需要时长
                character.latent_file_path = file_path
                duration = None
            
            character.updated_at = datetime.now()
            self.db.commit()
            
            # 记录系统日志
            if audio_type == "reference":
                logger.info(f"上传角色音频: {character.name} - {audio_type} (ID: {character_id}, 文件: {file_path}, 时长: {duration}s)")
            else:
                logger.info(f"上传角色NPY文件: {character.name} - {audio_type} (ID: {character_id}, 文件: {file_path})")
            
            return {
                "success": True,
                "data": {
                    "file_path": file_path,
                    "duration": duration if audio_type == "reference" else None,
                    "audio_type": audio_type
                },
                "message": f"{'音频文件' if audio_type == 'reference' else 'NPY文件'}上传成功"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"上传音频文件失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"上传音频文件失败: {str(e)}")

    def upload_character_avatar(
        self, 
        character_id: int, 
        avatar_file: UploadFile
    ) -> Dict[str, Any]:
        """上传角色头像"""
        try:
            character = self.get_character_by_id(character_id)
            if not character:
                raise HTTPException(status_code=404, detail="角色不存在")
            
            # 验证图片文件
            allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
            file_extension = os.path.splitext(avatar_file.filename)[1].lower()
            
            if file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail="不支持的图片格式，请使用 JPG、PNG、GIF 或 WebP 格式"
                )
            
            # 创建保存目录
            avatar_dir = os.path.join(settings.UPLOAD_DIR, "characters", str(character_id), "avatar")
            os.makedirs(avatar_dir, exist_ok=True)
            
            # 生成文件名
            filename = f"avatar{file_extension}"
            file_path = os.path.join(avatar_dir, filename)
            
            # 删除旧头像
            if character.avatar_path and os.path.exists(character.avatar_path):
                os.remove(character.avatar_path)
            
            # 保存新头像
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(avatar_file.file, buffer)
            
            # 更新数据库
            character.avatar_path = file_path
            character.updated_at = datetime.now()
            self.db.commit()
            
            # 记录系统日志
            logger.info(f"上传角色头像: {character.name} (ID: {character_id}, 文件: {file_path})")
            
            return {
                "success": True,
                "data": {
                    "avatar_path": file_path
                },
                "message": "头像上传成功"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"上传头像失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"上传头像失败: {str(e)}")

    def remove_character_avatar(self, character_id: int) -> Dict[str, Any]:
        """移除角色头像"""
        try:
            character = self.get_character_by_id(character_id)
            if not character:
                raise HTTPException(status_code=404, detail="角色不存在")
            
            # 删除头像文件
            if character.avatar_path and os.path.exists(character.avatar_path):
                try:
                    os.remove(character.avatar_path)
                    logger.info(f"删除头像文件: {character.avatar_path}")
                except Exception as e:
                    logger.warning(f"删除头像文件失败: {str(e)}")
            
            # 清除数据库中的头像路径
            character.avatar_path = None
            character.updated_at = datetime.now()
            self.db.commit()
            
            # 记录系统日志
            log_system_event(
                self.db,
                "character_avatar_removed",
                f"移除角色头像: {character.name}",
                {"character_id": character_id}
            )
            
            return {
                "success": True,
                "data": {
                    "avatar_path": None
                },
                "message": "头像移除成功"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"移除头像失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"移除头像失败: {str(e)}")

    def batch_create_characters(self, characters_data: List[CharacterCreate]) -> Dict[str, Any]:
        """批量创建角色"""
        try:
            created_characters = []
            failed_characters = []
            
            for char_data in characters_data:
                try:
                    # 🔧 调试：输出角色创建信息
                    logger.info(f"尝试创建角色: {char_data.name}, book_id: {char_data.book_id}, chapter_id: {char_data.chapter_id}")
                    
                    # 🔧 修复：更合理的名称冲突检查逻辑
                    existing_query = self.db.query(Character).filter(
                        Character.name == char_data.name
                    )
                    
                    # 检查冲突的逻辑：
                    # 1. 首先检查全局角色库（book_id为None）是否有同名角色
                    # 2. 如果有全局同名角色，则不允许创建（全局角色具有最高优先级）
                    # 3. 如果没有全局同名角色，再检查指定书籍内是否有同名角色
                    
                    # 先检查全局角色库
                    global_existing = existing_query.filter(Character.book_id.is_(None)).first()
                    if global_existing:
                        logger.warning(f"全局角色已存在: {char_data.name}, ID: {global_existing.id}")
                        failed_characters.append({
                            "name": char_data.name,
                            "reason": "角色名称已存在于全局角色库中"
                        })
                        continue
                    
                    # 如果没有全局同名角色，检查指定书籍内的冲突
                    if char_data.book_id:
                        book_existing = existing_query.filter(Character.book_id == char_data.book_id).first()
                        if book_existing:
                            logger.warning(f"书籍内角色已存在: {char_data.name}, ID: {book_existing.id}, 书籍ID: {char_data.book_id}")
                            failed_characters.append({
                                "name": char_data.name,
                                "reason": f"角色名称已存在于书籍ID {char_data.book_id} 中"
                            })
                            continue
                    
                    # 创建角色
                    character = Character(
                        name=char_data.name,
                        description=char_data.description or "",
                        voice_type="custom",  # 默认值
                        quality_score=0.0,  # 默认值
                        status="unconfigured",
                        tags=json.dumps([]),  # 默认空数组
                        book_id=char_data.book_id,
                        chapter_id=char_data.chapter_id,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    
                    self.db.add(character)
                    self.db.flush()  # 获取ID但不提交
                    
                    created_characters.append(character.to_dict())
                    
                except Exception as e:
                    failed_characters.append({
                        "name": char_data.name,
                        "reason": str(e)
                    })
            
            # 提交所有成功的创建
            self.db.commit()
            
            # 记录系统日志
            logger.info(f"批量创建角色: 成功 {len(created_characters)} 个，失败 {len(failed_characters)} 个")
            
            return {
                "success": True,
                "data": {
                    "created_characters": created_characters,
                    "failed_characters": failed_characters,
                    "summary": {
                        "total": len(characters_data),
                        "created": len(created_characters),
                        "failed": len(failed_characters)
                    }
                },
                "message": f"批量创建完成: 成功 {len(created_characters)} 个，失败 {len(failed_characters)} 个"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"批量创建角色失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"批量创建角色失败: {str(e)}")
    
    def batch_create_characters(self, characters_data: List[CharacterCreate]) -> Dict[str, Any]:
        """批量创建角色（简化版：只创建角色信息，不处理文件）"""
        created_characters = []
        failed_characters = []
        
        try:
            for i, char_data in enumerate(characters_data):
                try:
                    # 检查角色是否已存在
                    existing_query = self.db.query(Character).filter(Character.name == char_data.name)
                    
                    if char_data.book_id:
                        # 检查书籍内角色冲突
                        existing = existing_query.filter(Character.book_id == char_data.book_id).first()
                        if existing:
                            logger.warning(f"角色已存在于书籍中: {char_data.name}, ID: {existing.id}")
                            failed_characters.append({
                                "name": char_data.name,
                                "reason": f"角色名称已存在于书籍ID {char_data.book_id} 中"
                            })
                            continue
                    else:
                        # 检查全局角色库的冲突
                        global_existing = existing_query.filter(Character.book_id.is_(None)).first()
                        if global_existing:
                            logger.warning(f"全局角色已存在: {char_data.name}, ID: {global_existing.id}")
                            failed_characters.append({
                                "name": char_data.name,
                                "reason": "角色名称已存在于全局角色库中"
                            })
                            continue
                    
                    # 创建角色（只包含基本信息）
                    character = Character(
                        name=char_data.name,
                        description=char_data.description or "",
                        voice_type="custom",  # 默认值
                        quality_score=0.0,  # 默认值
                        status="unconfigured",  # 默认未配置状态
                        tags=json.dumps([]),  # 默认空数组
                        book_id=char_data.book_id,
                        chapter_id=char_data.chapter_id,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    
                    self.db.add(character)
                    self.db.flush()  # 获取ID但不提交
                    
                    logger.info(f"✅ 创建角色: {char_data.name} (ID: {character.id})")
                    created_characters.append(character.to_dict())
                    
                except Exception as e:
                    logger.error(f"创建角色 {char_data.name} 失败: {str(e)}")
                    failed_characters.append({
                        "name": char_data.name,
                        "reason": str(e)
                    })
            
            # 提交所有成功的创建
            self.db.commit()
            
            # 记录系统日志
            logger.info(f"批量创建角色: 成功 {len(created_characters)} 个，失败 {len(failed_characters)} 个")
            
            return {
                "success": True,
                "data": {
                    "created_characters": created_characters,
                    "failed_characters": failed_characters,
                    "summary": {
                        "total": len(characters_data),
                        "created": len(created_characters),
                        "failed": len(failed_characters)
                    }
                },
                "message": f"批量创建完成: 成功 {len(created_characters)} 个，失败 {len(failed_characters)} 个"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"批量创建角色失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"批量创建角色失败: {str(e)}")