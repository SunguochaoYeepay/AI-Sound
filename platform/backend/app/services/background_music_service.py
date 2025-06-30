"""
背景音乐服务
提供音乐库的业务逻辑处理
"""

import os
import shutil
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse
# import mutagen
# from mutagen.mp3 import MP3
# from mutagen.wave import WAVE
# from mutagen.flac import FLAC
import logging

from app.models.background_music import BackgroundMusic, MusicCategory
from app.schemas.background_music import (
    BackgroundMusicCreate, BackgroundMusicUpdate,
    MusicCategoryCreate, MusicCategoryUpdate,
    BackgroundMusicListResponse, MusicRecommendation
)
from app.utils.path_manager import get_path_manager

logger = logging.getLogger(__name__)


class BackgroundMusicService:
    """背景音乐业务服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.path_manager = get_path_manager()
        
    def _get_music_directory(self) -> str:
        """获取音乐存储目录"""
        music_dir = os.path.join(self.path_manager.get_storage_path('uploads'), 'background_music')
        os.makedirs(music_dir, exist_ok=True)
        return music_dir
    
    def _get_audio_info(self, file_path: str) -> Dict[str, Any]:
        """获取音频文件信息"""
        try:
            # TODO: 需要安装 mutagen 库来获取音频信息
            # audio_file = mutagen.File(file_path)
            # if audio_file is None:
            #     return {'duration': None, 'bitrate': None}
            # 
            # duration = getattr(audio_file, 'length', None)
            # bitrate = getattr(audio_file.info, 'bitrate', None)
            # 
            # return {
            #     'duration': duration,
            #     'bitrate': bitrate
            # }
            
            # 暂时返回空值，等待 mutagen 库安装
            return {'duration': None, 'bitrate': None}
        except Exception as e:
            logger.warning(f"无法获取音频信息 {file_path}: {e}")
            return {'duration': None, 'bitrate': None}
    
    def get_categories(self, is_active: Optional[bool] = None) -> List[MusicCategory]:
        """获取音乐分类列表"""
        query = self.db.query(MusicCategory)
        if is_active is not None:
            query = query.filter(MusicCategory.is_active == is_active)
        return query.order_by(MusicCategory.created_at.desc()).all()
    
    def create_category(self, category_data: MusicCategoryCreate) -> MusicCategory:
        """创建音乐分类"""
        category = MusicCategory(
            name=category_data.name,
            description=category_data.description,
            icon=category_data.icon
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category
    
    def update_category(self, category_id: int, category_data: MusicCategoryUpdate) -> Optional[MusicCategory]:
        """更新音乐分类"""
        category = self.db.query(MusicCategory).filter(MusicCategory.id == category_id).first()
        if not category:
            return None
        
        update_data = category_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(category, key, value)
        
        self.db.commit()
        self.db.refresh(category)
        return category
    
    def delete_category(self, category_id: int) -> bool:
        """删除音乐分类"""
        category = self.db.query(MusicCategory).filter(MusicCategory.id == category_id).first()
        if not category:
            return False
        
        # 检查是否有音乐使用此分类
        music_count = self.db.query(BackgroundMusic).filter(BackgroundMusic.category_id == category_id).count()
        if music_count > 0:
            raise HTTPException(status_code=400, detail=f"此分类下有 {music_count} 首音乐，无法删除")
        
        self.db.delete(category)
        self.db.commit()
        return True
    
    def get_music_list(
        self, skip: int = 0, limit: int = 50,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
        emotion_tag: Optional[str] = None,
        style_tag: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> BackgroundMusicListResponse:
        """获取背景音乐列表"""
        query = self.db.query(BackgroundMusic).options(joinedload(BackgroundMusic.category))
        
        # 筛选条件
        if category_id:
            query = query.filter(BackgroundMusic.category_id == category_id)
        
        if search:
            search_filter = or_(
                BackgroundMusic.name.contains(search),
                BackgroundMusic.description.contains(search)
            )
            query = query.filter(search_filter)
        
        if emotion_tag:
            query = query.filter(BackgroundMusic.emotion_tags.contains([emotion_tag]))
        
        if style_tag:
            query = query.filter(BackgroundMusic.style_tags.contains([style_tag]))
        
        if is_active is not None:
            query = query.filter(BackgroundMusic.is_active == is_active)
        
        # 获取总数
        total = query.count()
        
        # 分页和排序
        items = query.order_by(desc(BackgroundMusic.created_at)).offset(skip).limit(limit).all()
        
        return BackgroundMusicListResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit
        )
    
    def get_music_by_id(self, music_id: int) -> Optional[BackgroundMusic]:
        """根据ID获取背景音乐"""
        return self.db.query(BackgroundMusic).options(
            joinedload(BackgroundMusic.category)
        ).filter(BackgroundMusic.id == music_id).first()
    
    def create_music(self, music_data: BackgroundMusicCreate, file: UploadFile) -> BackgroundMusic:
        """创建背景音乐"""
        # 验证分类存在
        category = self.db.query(MusicCategory).filter(MusicCategory.id == music_data.category_id).first()
        if not category:
            raise HTTPException(status_code=400, detail="指定的音乐分类不存在")
        
        # 生成唯一文件名
        file_ext = os.path.splitext(music_data.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        # 保存文件
        music_dir = self._get_music_directory()
        file_path = os.path.join(music_dir, unique_filename)
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # 获取文件信息
            file_size = os.path.getsize(file_path)
            audio_info = self._get_audio_info(file_path)
            
            # 创建数据库记录
            music = BackgroundMusic(
                name=music_data.name,
                description=music_data.description,
                filename=music_data.filename,
                file_path=file_path,
                file_size=file_size,
                duration=audio_info.get('duration'),
                category_id=music_data.category_id,
                emotion_tags=music_data.emotion_tags,
                style_tags=music_data.style_tags,
                quality_rating=music_data.quality_rating
            )
            
            self.db.add(music)
            self.db.commit()
            self.db.refresh(music)
            
            # 加载关联数据
            music = self.get_music_by_id(music.id)
            return music
            
        except Exception as e:
            # 清理文件
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"保存音乐文件失败: {str(e)}")
    
    def update_music(self, music_id: int, music_data: BackgroundMusicUpdate) -> Optional[BackgroundMusic]:
        """更新背景音乐"""
        music = self.get_music_by_id(music_id)
        if not music:
            return None
        
        # 验证分类存在（如果要更新）
        if music_data.category_id:
            category = self.db.query(MusicCategory).filter(MusicCategory.id == music_data.category_id).first()
            if not category:
                raise HTTPException(status_code=400, detail="指定的音乐分类不存在")
        
        update_data = music_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(music, key, value)
        
        self.db.commit()
        self.db.refresh(music)
        return music
    
    def delete_music(self, music_id: int) -> bool:
        """删除背景音乐"""
        music = self.get_music_by_id(music_id)
        if not music:
            return False
        
        # 删除文件
        if music.file_path and os.path.exists(music.file_path):
            try:
                os.remove(music.file_path)
            except Exception as e:
                logger.warning(f"删除音乐文件失败 {music.file_path}: {e}")
        
        # 删除数据库记录
        self.db.delete(music)
        self.db.commit()
        return True
    
    def record_play(self, music_id: int) -> None:
        """记录音乐播放"""
        music = self.db.query(BackgroundMusic).filter(BackgroundMusic.id == music_id).first()
        if music:
            music.usage_count += 1
            music.last_used_at = func.now()
            self.db.commit()
    
    def recommend_by_emotion(self, emotion: str, limit: int = 10) -> List[MusicRecommendation]:
        """基于情感推荐背景音乐"""
        query = self.db.query(BackgroundMusic).filter(
            and_(
                BackgroundMusic.is_active == True,
                BackgroundMusic.emotion_tags.contains([emotion])
            )
        ).order_by(desc(BackgroundMusic.quality_rating), desc(BackgroundMusic.usage_count))
        
        music_list = query.limit(limit).all()
        
        recommendations = []
        for music in music_list:
            score = 0.5  # 基础分数
            if music.quality_rating:
                score += music.quality_rating / 10  # 质量分数
            if music.usage_count > 0:
                score += min(music.usage_count / 100, 0.3)  # 使用率分数
            
            recommendations.append(MusicRecommendation(
                music=music,
                score=round(score, 2),
                reason=f"匹配情感标签: {emotion}"
            ))
        
        return recommendations
    
    def recommend_similar(self, music_id: int, limit: int = 5) -> List[MusicRecommendation]:
        """推荐相似背景音乐"""
        reference_music = self.get_music_by_id(music_id)
        if not reference_music:
            return []
        
        # 基于相同分类和标签查找相似音乐
        query = self.db.query(BackgroundMusic).filter(
            and_(
                BackgroundMusic.id != music_id,
                BackgroundMusic.is_active == True,
                BackgroundMusic.category_id == reference_music.category_id
            )
        )
        
        candidates = query.all()
        
        recommendations = []
        for music in candidates:
            score = 0.3  # 基础分数（相同分类）
            
            # 情感标签匹配度
            common_emotions = set(music.emotion_tags or []) & set(reference_music.emotion_tags or [])
            if common_emotions:
                score += len(common_emotions) * 0.2
            
            # 风格标签匹配度
            common_styles = set(music.style_tags or []) & set(reference_music.style_tags or [])
            if common_styles:
                score += len(common_styles) * 0.2
            
            # 质量评分影响
            if music.quality_rating and reference_music.quality_rating:
                quality_diff = abs(music.quality_rating - reference_music.quality_rating)
                score += max(0, (5 - quality_diff) / 10)
            
            if score > 0.3:  # 只推荐有一定相似度的音乐
                recommendations.append(MusicRecommendation(
                    music=music,
                    score=round(score, 2),
                    reason=f"相似度: {int(score*100)}%"
                ))
        
        # 按分数排序并限制数量
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:limit]
    
    def get_music_file(self, music_id: int) -> FileResponse:
        """获取音乐文件响应"""
        music = self.get_music_by_id(music_id)
        if not music or not music.file_path or not os.path.exists(music.file_path):
            raise HTTPException(status_code=404, detail="音乐文件未找到")
        
        return FileResponse(
            path=music.file_path,
            media_type='audio/mpeg',
            filename=music.filename
        )
    
    def get_music_stats(self) -> Dict[str, Any]:
        """获取音乐库统计信息"""
        # 基础统计
        total_music = self.db.query(BackgroundMusic).count()
        active_music = self.db.query(BackgroundMusic).filter(BackgroundMusic.is_active == True).count()
        total_categories = self.db.query(MusicCategory).filter(MusicCategory.is_active == True).count()
        
        # 总时长和大小
        duration_result = self.db.query(func.sum(BackgroundMusic.duration)).scalar() or 0
        size_result = self.db.query(func.sum(BackgroundMusic.file_size)).scalar() or 0
        
        # 热门分类
        popular_categories = self.db.query(
            MusicCategory.name,
            func.count(BackgroundMusic.id).label('music_count')
        ).join(
            BackgroundMusic, MusicCategory.id == BackgroundMusic.category_id
        ).group_by(
            MusicCategory.id, MusicCategory.name
        ).order_by(
            desc('music_count')
        ).limit(5).all()
        
        # 最近上传
        recent_uploads = self.db.query(BackgroundMusic).options(
            joinedload(BackgroundMusic.category)
        ).order_by(desc(BackgroundMusic.created_at)).limit(5).all()
        
        return {
            'total_music': total_music,
            'active_music': active_music,
            'total_categories': total_categories,
            'total_duration': duration_result,
            'total_size': size_result,
            'popular_categories': [
                {'name': cat.name, 'count': cat.music_count}
                for cat in popular_categories
            ],
            'recent_uploads': recent_uploads
        }