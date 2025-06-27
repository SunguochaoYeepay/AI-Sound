"""
音乐生成API接口
使用重构后的简洁架构：
- SongGeneration引擎客户端（纯净生成）
- 音乐场景分析器（业务分析）  
- 音乐编排器（业务逻辑）
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import logging

from app.services.music_orchestrator import get_music_orchestrator
from app.services.music_scene_analyzer import get_music_scene_analyzer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/music-generation", tags=["音乐生成"])

# 请求模型
class MusicGenerationRequest(BaseModel):
    """音乐生成请求 - 完全匹配SongGeneration Demo参数"""
    lyrics: str = Field(..., description="歌词内容（必填）")
    genre: Optional[str] = Field("Auto", description="音乐风格")
    description: Optional[str] = Field("", description="音乐描述（可选）")
    cfg_coef: float = Field(1.5, ge=0.1, le=3.0, description="CFG系数")
    temperature: float = Field(0.9, ge=0.1, le=2.0, description="温度")
    top_k: int = Field(50, ge=1, le=100, description="Top-K")
    # AI-Sound特有参数
    chapter_id: Optional[str] = Field(None, description="章节ID")
    volume_level: float = Field(-12.0, ge=-30.0, le=0.0, description="音量级别（dB）")

# 批量音乐生成请求已移除 - 资源消耗过大，容易导致系统卡死
# class BatchMusicGenerationRequest(BaseModel):
#     """批量音乐生成请求"""
#     chapters: List[Dict] = Field(..., description="章节列表")
#     max_concurrent: int = Field(3, ge=1, le=10, description="最大并发数")

class SceneAnalysisRequest(BaseModel):
    """场景分析请求"""
    content: str = Field(..., description="要分析的文本内容")

# 响应模型
class MusicGenerationResponse(BaseModel):
    """音乐生成响应"""
    success: bool
    audio_path: Optional[str] = None
    audio_url: Optional[str] = None
    scene_analysis: Optional[Dict] = None
    music_description: Optional[str] = None
    generation_time: Optional[float] = None
    error: Optional[str] = None

class SceneAnalysisResponse(BaseModel):
    """场景分析响应"""
    success: bool
    scene_type: str
    emotion_tone: str
    intensity: float
    recommended_style: str
    recommended_duration: int
    confidence: float
    keywords: List[str]

@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        orchestrator = get_music_orchestrator()
        engine_healthy = await orchestrator.check_engine_health()
        
        return {
            "status": "healthy" if engine_healthy else "degraded",
            "engine_status": "healthy" if engine_healthy else "unhealthy",
            "message": "音乐生成服务正常" if engine_healthy else "SongGeneration引擎不可用"
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=503, detail=f"服务不可用: {str(e)}")

@router.post("/generate", response_model=MusicGenerationResponse)
async def generate_music(request: MusicGenerationRequest):
    """
    生成音乐
    新架构：场景分析 → 引擎生成 → 文件管理
    """
    try:
        logger.info(f"收到音乐生成请求，章节: {request.chapter_id}，风格: {request.genre}")
        
        orchestrator = get_music_orchestrator()
        
        # 直接使用SongGeneration Demo参数
        result = await orchestrator.generate_music_for_content(
            content=request.lyrics,
            chapter_id=request.chapter_id,
            custom_style=request.genre,
            volume_level=request.volume_level,
            advanced_params={
                "description": request.description,
                "cfg_coef": request.cfg_coef,
                "temperature": request.temperature,
                "top_k": request.top_k
            }
        )
        
        if result:
            return MusicGenerationResponse(
                success=True,
                audio_path=result["audio_path"],
                audio_url=result["audio_url"],
                scene_analysis=result["scene_analysis"],
                music_description=result["music_description"],
                generation_time=result["generation_time"]
            )
        else:
            return MusicGenerationResponse(
                success=False,
                error="音乐生成失败，请检查引擎状态"
            )
            
    except Exception as e:
        logger.error(f"音乐生成API异常: {e}")
        return MusicGenerationResponse(
            success=False,
            error=str(e)
        )

@router.post("/generate-direct", response_model=MusicGenerationResponse)
async def generate_direct_music(request: MusicGenerationRequest):
    """
    直接生成音乐（无场景分析）
    适用于基于描述的直接生成，跳过复杂的场景分析流程
    """
    try:
        logger.info(f"收到直接音乐生成请求，风格: {request.genre}，CFG: {request.cfg_coef}")
        
        orchestrator = get_music_orchestrator()
        
        # 直接使用SongGeneration Demo参数
        result = await orchestrator.generate_music_for_content(
            content=request.lyrics,
            chapter_id=request.chapter_id or f"direct_{int(__import__('time').time())}",
            custom_style=request.genre,
            volume_level=request.volume_level,
            direct_mode=True,  # 启用直接模式
            advanced_params={
                "description": request.description,
                "cfg_coef": request.cfg_coef,
                "temperature": request.temperature,
                "top_k": request.top_k
            }
        )
        
        if result:
            return MusicGenerationResponse(
                success=True,
                audio_path=result["audio_path"],
                audio_url=result["audio_url"],
                scene_analysis=result.get("scene_analysis"),
                music_description=result.get("music_description", "基于描述直接生成的音乐"),
                generation_time=result["generation_time"]
            )
        else:
            return MusicGenerationResponse(
                success=False,
                error="直接音乐生成失败，请检查引擎状态"
            )
            
    except Exception as e:
        logger.error(f"直接音乐生成API异常: {e}")
        return MusicGenerationResponse(
            success=False,
            error=str(e)
        )

@router.post("/analyze-scene", response_model=SceneAnalysisResponse)
async def analyze_scene(request: SceneAnalysisRequest):
    """
    场景分析
    独立的场景分析接口，不生成音乐
    """
    try:
        logger.info(f"收到场景分析请求，内容长度: {len(request.content)} 字符")
        
        scene_analyzer = get_music_scene_analyzer()
        analysis = scene_analyzer.analyze_content(request.content)
        
        return SceneAnalysisResponse(
            success=True,
            scene_type=analysis.scene_type,
            emotion_tone=analysis.emotion_tone,
            intensity=analysis.intensity,
            recommended_style=analysis.recommended_style,
            recommended_duration=analysis.recommended_duration,
            confidence=analysis.style_confidence,
            keywords=analysis.keywords
        )
        
    except Exception as e:
        logger.error(f"场景分析API异常: {e}")
        raise HTTPException(status_code=500, detail=f"场景分析失败: {str(e)}")

# 批量生成音乐接口已移除 - 资源消耗过大，容易导致系统卡死
# @router.post("/batch-generate")
# async def batch_generate_music(request: BatchMusicGenerationRequest, background_tasks: BackgroundTasks):
#     """
#     批量生成音乐 (已禁用)
#     单个音乐生成就需要很长时间，批量生成会导致系统资源耗尽
#     """
#     raise HTTPException(
#         status_code=501, 
#         detail="批量音乐生成功能已禁用，请使用单个生成功能避免系统过载"
#     )

@router.get("/styles")
async def get_supported_styles():
    """获取支持的音乐风格列表"""
    try:
        orchestrator = get_music_orchestrator()
        styles = orchestrator.get_supported_styles()
        
        return {
            "success": True,
            "styles": styles,
            "total": len(styles)
        }
        
    except Exception as e:
        logger.error(f"获取风格列表异常: {e}")
        raise HTTPException(status_code=500, detail=f"获取风格失败: {str(e)}")

@router.get("/scenes")
async def get_supported_scenes():
    """获取支持的场景类型列表"""
    try:
        orchestrator = get_music_orchestrator()
        scenes = orchestrator.get_supported_scenes()
        
        return {
            "success": True,
            "scenes": scenes,
            "total": len(scenes)
        }
        
    except Exception as e:
        logger.error(f"获取场景列表异常: {e}")
        raise HTTPException(status_code=500, detail=f"获取场景失败: {str(e)}")

@router.post("/cleanup")
async def cleanup_old_files(max_age_hours: int = 24):
    """清理旧的音乐文件"""
    try:
        orchestrator = get_music_orchestrator()
        cleaned_count = await orchestrator.cleanup_old_files(max_age_hours)
        
        return {
            "success": True,
            "cleaned_files": cleaned_count,
            "message": f"清理了 {cleaned_count} 个旧文件"
        }
        
    except Exception as e:
        logger.error(f"清理文件异常: {e}")
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")

@router.get("/info")
async def get_service_info():
    """获取服务信息"""
    try:
        orchestrator = get_music_orchestrator()
        engine_healthy = await orchestrator.check_engine_health()
        
        return {
            "service_name": "AI-Sound Music Generation Service",
            "version": "2.0.0",
            "architecture": "简洁分离式架构",
            "components": {
                "songgeneration_engine": "引擎客户端（纯净生成）",
                "scene_analyzer": "场景分析器（业务分析）",
                "orchestrator": "编排器（业务逻辑）"
            },
            "engine_status": "healthy" if engine_healthy else "unhealthy",
            "supported_styles": orchestrator.get_supported_styles(),
            "supported_scenes": orchestrator.get_supported_scenes()
        }
        
    except Exception as e:
        logger.error(f"获取服务信息异常: {e}")
        raise HTTPException(status_code=500, detail=f"获取信息失败: {str(e)}") 