"""角色CRUD操作服务"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
import logging
import os
import json
import shutil
from datetime import datetime

from app.models.character import Character
from app.schemas.character import CharacterCreate, CharacterUpdate, CharacterResponse
from app.utils import log_system_event, get_audio_duration
from app.utils.character_utils import validate_audio_file
from app.core.config import settings

logger = logging.getLogger(__name__)

class CharacterCRUDService:
    """角色CRUD操作服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_character(self, character_data: CharacterCreate) -> Dict[str, Any]:
        """创建新角色"""
        try:
            # 检查角色名称是否已存在
            existing = self.db.query(Character).filter(
                Character.name == character_data.name
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=400, 
                    detail=f"角色名称 '{character_data.name}' 已存在"
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
            log_system_event(
                self.db,
                "character_created",
                f"创建角色: {character.name}",
                {"character_id": character.id}
            )
            
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
            character = self.db.query(Character).filter(
                Character.id == character_id
            ).first()
            
            if not character:
                raise HTTPException(status_code=404, detail="角色不存在")
            
            # 检查名称冲突（如果更改了名称）
            if character_data.name and character_data.name != character.name:
                existing = self.db.query(Character).filter(
                    Character.name == character_data.name,
                    Character.id != character_id
                ).first()
                
                if existing:
                    raise HTTPException(
                        status_code=400,
                        detail=f"角色名称 '{character_data.name}' 已存在"
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
            log_system_event(
                self.db,
                "character_updated",
                f"更新角色: {character.name}",
                {"character_id": character_id, "updated_fields": list(update_data.keys())}
            )
            
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
            character = self.db.query(Character).filter(
                Character.id == character_id
            ).first()
            
            if not character:
                raise HTTPException(status_code=404, detail="角色不存在")
            
            # 验证音频文件
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
            
            # 获取音频时长
            duration = get_audio_duration(file_path)
            
            # 更新数据库
            if audio_type == "reference":
                character.reference_audio_path = file_path
                character.reference_audio_duration = duration
            else:
                character.latent_file_path = file_path
            
            character.updated_at = datetime.now()
            self.db.commit()
            
            # 记录系统日志
            log_system_event(
                self.db,
                "character_audio_uploaded",
                f"上传角色音频: {character.name} - {audio_type}",
                {
                    "character_id": character_id,
                    "audio_type": audio_type,
                    "file_path": file_path,
                    "duration": duration
                }
            )
            
            return {
                "success": True,
                "data": {
                    "file_path": file_path,
                    "duration": duration,
                    "audio_type": audio_type
                },
                "message": f"音频文件上传成功"
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
            character = self.db.query(Character).filter(
                Character.id == character_id
            ).first()
            
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
            log_system_event(
                self.db,
                "character_avatar_uploaded",
                f"上传角色头像: {character.name}",
                {
                    "character_id": character_id,
                    "file_path": file_path
                }
            )
            
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
            character = self.db.query(Character).filter(
                Character.id == character_id
            ).first()
            
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
                    # 检查名称冲突
                    existing = self.db.query(Character).filter(
                        Character.name == char_data.name
                    ).first()
                    
                    if existing:
                        failed_characters.append({
                            "name": char_data.name,
                            "reason": "角色名称已存在"
                        })
                        continue
                    
                    # 创建角色
                    character = Character(
                        name=char_data.name,
                        description=char_data.description or "",
                        voice_type=char_data.voice_type or "custom",
                        quality_score=char_data.quality_score or 0.0,
                        status="unconfigured",
                        tags=json.dumps(char_data.tags or []),
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
            log_system_event(
                self.db,
                "characters_batch_created",
                f"批量创建角色: 成功 {len(created_characters)} 个，失败 {len(failed_characters)} 个",
                {
                    "created_count": len(created_characters),
                    "failed_count": len(failed_characters)
                }
            )
            
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