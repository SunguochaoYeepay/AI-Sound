from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import asyncio
import json
from pydantic import BaseModel

from app.database import get_db
from app.services.smart_editing_service import SmartEditingService

logger = logging.getLogger(__name__)
router = APIRouter()

# 请求模型
class ChapterSplitRequest(BaseModel):
    audio_url: str
    silence_threshold: float = -30.0
    min_silence_duration: float = 1.0
    min_chapter_length: float = 30.0

class SpeechRecognitionRequest(BaseModel):
    audio_url: str
    language: str = "zh-CN"
    accuracy: str = "balanced"

class EmotionAnalysisRequest(BaseModel):
    audio_url: str
    intensity: float = 0.7
    adjustments: List[str] = ["pitch", "volume"]

class MusicRecommendationRequest(BaseModel):
    audio_url: str
    style: str = "ambient"
    intensity: float = 0.5

class BatchProcessingRequest(BaseModel):
    audio_urls: List[str]
    tasks: List[str]

# 响应模型
class ChapterInfo(BaseModel):
    start_time: float
    end_time: float
    duration: float
    confidence: float = 0.8

class SpeechResult(BaseModel):
    start_time: float
    text: str
    confidence: float

class EmotionResult(BaseModel):
    start_time: float
    duration: float
    emotion_type: str
    intensity: float

class MusicRecommendation(BaseModel):
    name: str
    description: str
    style: str
    url: Optional[str] = None
    preview_url: Optional[str] = None

@router.post("/chapter-split", response_model=List[ChapterInfo])
async def analyze_chapters(
    request: ChapterSplitRequest,
    db: Session = Depends(get_db)
):
    """自动章节分割分析"""
    try:
        service = SmartEditingService(db)
        chapters = await service.analyze_chapters(
            audio_url=request.audio_url,
            silence_threshold=request.silence_threshold,
            min_silence_duration=request.min_silence_duration,
            min_chapter_length=request.min_chapter_length
        )
        
        return chapters
        
    except Exception as e:
        logger.error(f"章节分割分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"章节分割分析失败: {str(e)}")

@router.post("/speech-recognition", response_model=List[SpeechResult])
async def recognize_speech(
    request: SpeechRecognitionRequest,
    db: Session = Depends(get_db)
):
    """语音识别"""
    try:
        service = SmartEditingService(db)
        results = await service.recognize_speech(
            audio_url=request.audio_url,
            language=request.language,
            accuracy=request.accuracy
        )
        
        return results
        
    except Exception as e:
        logger.error(f"语音识别失败: {e}")
        raise HTTPException(status_code=500, detail=f"语音识别失败: {str(e)}")

@router.post("/emotion-analysis", response_model=List[EmotionResult])
async def analyze_emotions(
    request: EmotionAnalysisRequest,
    db: Session = Depends(get_db)
):
    """情感分析"""
    try:
        service = SmartEditingService(db)
        results = await service.analyze_emotions(
            audio_url=request.audio_url,
            intensity=request.intensity,
            adjustments=request.adjustments
        )
        
        return results
        
    except Exception as e:
        logger.error(f"情感分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"情感分析失败: {str(e)}")

@router.post("/music-recommendation", response_model=List[MusicRecommendation])
async def recommend_music(
    request: MusicRecommendationRequest,
    db: Session = Depends(get_db)
):
    """背景音乐推荐"""
    try:
        service = SmartEditingService(db)
        recommendations = await service.recommend_music(
            audio_url=request.audio_url,
            style=request.style,
            intensity=request.intensity
        )
        
        return recommendations
        
    except Exception as e:
        logger.error(f"音乐推荐失败: {e}")
        raise HTTPException(status_code=500, detail=f"音乐推荐失败: {str(e)}")

@router.post("/batch-processing")
async def batch_process(
    request: BatchProcessingRequest,
    db: Session = Depends(get_db)
):
    """批量处理"""
    try:
        service = SmartEditingService(db)
        results = await service.batch_process(
            audio_urls=request.audio_urls,
            tasks=request.tasks
        )
        
        return {"success": True, "results": results}
        
    except Exception as e:
        logger.error(f"批量处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量处理失败: {str(e)}")

@router.get("/test-audio")
async def get_test_audio():
    """获取测试音频文件"""
    try:
        # 返回一个测试音频文件的URL
        test_audio_url = "/static/test/sample_audio.mp3"
        return {"audio_url": test_audio_url}
        
    except Exception as e:
        logger.error(f"获取测试音频失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取测试音频失败: {str(e)}")

@router.get("/supported-languages")
async def get_supported_languages():
    """获取支持的语音识别语言"""
    languages = [
        {"code": "zh-CN", "name": "中文", "supported": True},
        {"code": "en-US", "name": "英语", "supported": True},
        {"code": "ja-JP", "name": "日语", "supported": False},
        {"code": "ko-KR", "name": "韩语", "supported": False}
    ]
    return {"languages": languages}

@router.get("/music-styles")
async def get_music_styles():
    """获取支持的音乐风格"""
    styles = [
        {"code": "ambient", "name": "环境音乐", "description": "轻柔的背景音乐"},
        {"code": "classical", "name": "古典音乐", "description": "优雅的古典乐曲"},
        {"code": "electronic", "name": "电子音乐", "description": "现代电子音效"},
        {"code": "cinematic", "name": "电影配乐", "description": "戏剧性的配乐"},
        {"code": "nature", "name": "自然音效", "description": "自然环境声音"}
    ]
    return {"styles": styles} 