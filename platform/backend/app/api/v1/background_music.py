"""
背景音乐管理API
提供音乐库的完整CRUD操作
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import os
import shutil

from app.database import get_db
from app.models.background_music import BackgroundMusic, MusicCategory
from app.schemas.background_music import (
    BackgroundMusicCreate, BackgroundMusicUpdate, BackgroundMusicResponse,
    MusicCategoryCreate, MusicCategoryUpdate, MusicCategoryResponse,
    BackgroundMusicListResponse, MusicRecommendation
)
from app.services.background_music_service import BackgroundMusicService
from app.utils.path_manager import get_path_manager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/categories", response_model=List[MusicCategoryResponse])
async def get_music_categories(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """获取音乐分类列表"""
    try:
        service = BackgroundMusicService(db)
        categories = service.get_categories(is_active=is_active)
        return categories
    except Exception as e:
        logger.error(f"获取音乐分类失败: {e}")
        raise HTTPException(status_code=500, detail="获取音乐分类失败")

@router.post("/categories", response_model=MusicCategoryResponse)
async def create_music_category(
    category: MusicCategoryCreate,
    db: Session = Depends(get_db)
):
    """创建音乐分类"""
    try:
        service = BackgroundMusicService(db)
        new_category = service.create_category(category)
        return new_category
    except Exception as e:
        logger.error(f"创建音乐分类失败: {e}")
        raise HTTPException(status_code=500, detail="创建音乐分类失败")

@router.put("/categories/{category_id}", response_model=MusicCategoryResponse)
async def update_music_category(
    category_id: int,
    category: MusicCategoryUpdate,
    db: Session = Depends(get_db)
):
    """更新音乐分类"""
    try:
        service = BackgroundMusicService(db)
        updated_category = service.update_category(category_id, category)
        if not updated_category:
            raise HTTPException(status_code=404, detail="音乐分类未找到")
        return updated_category
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新音乐分类失败: {e}")
        raise HTTPException(status_code=500, detail="更新音乐分类失败")

@router.delete("/categories/{category_id}")
async def delete_music_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """删除音乐分类"""
    try:
        service = BackgroundMusicService(db)
        success = service.delete_category(category_id)
        if not success:
            raise HTTPException(status_code=404, detail="音乐分类未找到")
        return {"message": "音乐分类删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除音乐分类失败: {e}")
        raise HTTPException(status_code=500, detail="删除音乐分类失败")

@router.get("/music", response_model=BackgroundMusicListResponse)
async def get_background_music_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    emotion_tags: Optional[List[str]] = Query(None),
    style_tags: Optional[List[str]] = Query(None),
    active_only: Optional[bool] = None,
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc"),
    db: Session = Depends(get_db)
):
    """获取背景音乐列表"""
    try:
        service = BackgroundMusicService(db)
        # 计算skip值
        skip = (page - 1) * page_size
        result = service.get_music_list(
            skip=skip, limit=page_size,
            category_id=category_id, search=search,
            emotion_tag=emotion_tags[0] if emotion_tags else None,
            style_tag=style_tags[0] if style_tags else None,
            is_active=active_only
        )
        return result
    except Exception as e:
        logger.error(f"获取背景音乐列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取背景音乐列表失败")

@router.get("/music/{music_id}", response_model=BackgroundMusicResponse)
async def get_background_music(
    music_id: int,
    db: Session = Depends(get_db)
):
    """获取单个背景音乐详情"""
    try:
        service = BackgroundMusicService(db)
        music = service.get_music_by_id(music_id)
        if not music:
            raise HTTPException(status_code=404, detail="背景音乐未找到")
        return music
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取背景音乐详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取背景音乐详情失败")

@router.post("/music", response_model=BackgroundMusicResponse)
async def upload_background_music(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    category_id: int = Form(...),
    emotion_tags: Optional[str] = Form(None),
    style_tags: Optional[str] = Form(None),
    quality_rating: Optional[float] = Form(None),
    db: Session = Depends(get_db)
):
    """上传背景音乐文件"""
    try:
        # 验证文件类型
        allowed_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.aac'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="不支持的音频文件格式")
        
        # 解析标签
        emotion_tags_list = []
        style_tags_list = []
        if emotion_tags:
            emotion_tags_list = [tag.strip() for tag in emotion_tags.split(',') if tag.strip()]
        if style_tags:
            style_tags_list = [tag.strip() for tag in style_tags.split(',') if tag.strip()]
        
        # 创建音乐数据
        music_data = BackgroundMusicCreate(
            name=name,
            description=description,
            filename=file.filename,
            category_id=category_id,
            emotion_tags=emotion_tags_list,
            style_tags=style_tags_list,
            quality_rating=quality_rating
        )
        
        service = BackgroundMusicService(db)
        new_music = service.create_music(music_data, file)
        return new_music
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传背景音乐失败: {e}")
        raise HTTPException(status_code=500, detail="上传背景音乐失败")

@router.put("/music/{music_id}", response_model=BackgroundMusicResponse)
async def update_background_music(
    music_id: int,
    music: BackgroundMusicUpdate,
    db: Session = Depends(get_db)
):
    """更新背景音乐信息"""
    try:
        service = BackgroundMusicService(db)
        updated_music = service.update_music(music_id, music)
        if not updated_music:
            raise HTTPException(status_code=404, detail="背景音乐未找到")
        return updated_music
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新背景音乐失败: {e}")
        raise HTTPException(status_code=500, detail="更新背景音乐失败")

@router.delete("/music/{music_id}")
async def delete_background_music(
    music_id: int,
    db: Session = Depends(get_db)
):
    """删除背景音乐"""
    try:
        service = BackgroundMusicService(db)
        success = service.delete_music(music_id)
        if not success:
            raise HTTPException(status_code=404, detail="背景音乐未找到")
        return {"message": "背景音乐删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除背景音乐失败: {e}")
        raise HTTPException(status_code=500, detail="删除背景音乐失败")

@router.post("/music/{music_id}/play")
async def play_music(
    music_id: int,
    db: Session = Depends(get_db)
):
    """记录音乐播放"""
    try:
        service = BackgroundMusicService(db)
        service.record_play(music_id)
        return {"message": "播放记录成功"}
    except Exception as e:
        logger.error(f"记录播放失败: {e}")
        raise HTTPException(status_code=500, detail="记录播放失败")

@router.get("/recommend/by-emotion")
async def recommend_by_emotion(
    emotion: str = Query(..., description="情感类型"),
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """基于情感推荐背景音乐"""
    try:
        service = BackgroundMusicService(db)
        recommendations = service.recommend_by_emotion(emotion, limit)
        return {"recommendations": recommendations}
    except Exception as e:
        logger.error(f"情感推荐失败: {e}")
        raise HTTPException(status_code=500, detail="情感推荐失败")

@router.get("/music/{music_id}/similar")
async def recommend_similar(
    music_id: int,
    limit: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db)
):
    """推荐相似背景音乐"""
    try:
        service = BackgroundMusicService(db)
        recommendations = service.recommend_similar(music_id, limit)
        return {"recommendations": recommendations}
    except Exception as e:
        logger.error(f"相似推荐失败: {e}")
        raise HTTPException(status_code=500, detail="相似推荐失败")

@router.get("/music/{music_id}/download")
async def download_music(
    music_id: int,
    db: Session = Depends(get_db)
):
    """下载背景音乐文件"""
    try:
        service = BackgroundMusicService(db)
        file_response = service.get_music_file(music_id)
        return file_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载音乐文件失败: {e}")
        raise HTTPException(status_code=500, detail="下载音乐文件失败")

@router.get("/stats/overview")
async def get_music_stats(db: Session = Depends(get_db)):
    """获取音乐库统计信息"""
    try:
        service = BackgroundMusicService(db)
        stats = service.get_music_stats()
        return stats
    except Exception as e:
        logger.error(f"获取音乐统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取音乐统计失败")