"""角色管理核心服务"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, or_, and_
from fastapi import HTTPException
import logging
import os
import json
from datetime import datetime

from app.models.character import Character
from app.models import VoiceProfile, SystemLog, UsageStats
from app.schemas.character import CharacterCreate, CharacterUpdate, CharacterResponse
from app.utils import log_system_event, get_audio_duration, update_usage_stats
from app.utils.character_utils import validate_audio_file

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
            
            # 记录系统日志（移除异步调用）
            # await log_system_event(
            #     self.db,
            #     "info",
            #     f"获取角色列表: 第{page}页，每页{page_size}条",
            #     "CHARACTER_MANAGEMENT",
            #     {
            #         "page": page,
            #         "page_size": page_size,
            #         "total": total,
            #         "filters": {
            #             "search": search,
            #             "voice_type": voice_type,
            #             "quality_min": quality_min,
            #             "status": status,
            #             "book_id": book_id,
            #             "chapter_id": chapter_id,
            #             "tags": tags
            #         }
            #     }
            # )
            
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