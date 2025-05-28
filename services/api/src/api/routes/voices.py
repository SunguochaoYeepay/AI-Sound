"""
声音管理API路由
"""

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from fastapi.responses import FileResponse
from typing import List, Optional
import logging

from ...models.voice import Voice, VoiceCreate, VoiceUpdate, VoiceGender
from ...services.voice_service import VoiceService
from ...core.dependencies import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/voices", tags=["voices"])


@router.get("/")
async def list_voices(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    engine_id: Optional[str] = Query(None, description="引擎过滤"),
    language: Optional[str] = Query(None, description="语言过滤"),
    gender: Optional[str] = Query(None, description="性别过滤"),
    db=Depends(get_db)
):
    """获取声音列表"""
    try:
        service = VoiceService(db)
        
        # 转换gender参数
        gender_enum = None
        if gender:
            try:
                gender_enum = VoiceGender(gender)
            except ValueError:
                pass  # 忽略无效的gender值
        
        voices = await service.list_voices(
            skip=skip,
            limit=limit,
            search=search,
            engine_id=engine_id,
            language=language,
            gender=gender_enum
        )
        
        # 转换为docs规范格式
        formatted_voices = []
        for voice in voices:
            formatted_voice = {
                "id": voice.id,
                "name": voice.name,
                "engine_id": voice.engine_id,
                "gender": voice.gender.value if voice.gender else "unknown",
                "language": voice.language,
                "description": voice.description,
                "preview_url": f"/api/voices/{voice.id}/preview"
            }
            formatted_voices.append(formatted_voice)
        
        return {
            "success": True,
            "data": {
                "voices": formatted_voices
            }
        }
    except Exception as e:
        logger.error(f"获取声音列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{voice_id}")
async def get_voice(voice_id: str, db=Depends(get_db)):
    """获取指定声音详情"""
    try:
        service = VoiceService(db)
        voice = await service.get_voice(voice_id)
        if not voice:
            raise HTTPException(status_code=404, detail="声音未找到")
        
        # 转换为docs规范格式
        formatted_voice = {
            "id": voice.id,
            "name": voice.name,
            "engine_id": voice.engine_id,
            "gender": voice.gender.value if voice.gender else "unknown",
            "language": voice.language,
            "description": voice.description,
            "attributes": {
                "age_group": "young",
                "style": "natural"
            },
            "preview_url": f"/api/voices/{voice.id}/preview"
        }
        
        return {
            "success": True,
            "data": formatted_voice
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取声音详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_voice(voice_data: VoiceCreate, db=Depends(get_db)):
    """创建新声音"""
    try:
        service = VoiceService(db)
        voice = await service.create_voice(voice_data)
        
        return {
            "success": True,
            "message": "声音上传成功",
            "data": {
                "voice_id": voice.id,
                "name": voice.name,
                "engine_id": voice.engine_id
            }
        }
    except Exception as e:
        logger.error(f"创建声音失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{voice_id}")
async def update_voice(
    voice_id: str, 
    voice_data: VoiceUpdate, 
    db=Depends(get_db)
):
    """更新声音"""
    try:
        service = VoiceService(db)
        voice = await service.update_voice(voice_id, voice_data)
        if not voice:
            raise HTTPException(status_code=404, detail="声音未找到")
        
        return {
            "success": True,
            "message": "声音信息更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新声音失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{voice_id}")
async def delete_voice(voice_id: str, db=Depends(get_db)):
    """删除声音"""
    try:
        service = VoiceService(db)
        success = await service.delete_voice(voice_id)
        if not success:
            raise HTTPException(status_code=404, detail="声音未找到")
        
        return {
            "success": True,
            "message": "声音删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除声音失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_voice_file(
    file: UploadFile = File(...),
    voice_id: str = Query(..., description="声音ID"),
    db=Depends(get_db)
):
    """上传声音文件"""
    try:
        # 检查文件类型
        allowed_types = ["audio/wav", "audio/mpeg", "audio/mp3", "audio/flac", "audio/ogg"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file.content_type}"
            )
        
        # 检查文件大小（限制100MB）
        if file.size and file.size > 100 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小超过限制 (100MB)")
        
        service = VoiceService(db)
        result = await service.upload_voice_file(voice_id, file)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传声音文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{voice_id}/preview")
async def preview_voice(
    voice_id: str,
    text: str = Query("你好，这是声音预览。", description="预览文本"),
    db=Depends(get_db)
):
    """预览声音"""
    try:
        service = VoiceService(db)
        result = await service.preview_voice(voice_id, text)
        if not result:
            raise HTTPException(status_code=404, detail="声音未找到或预览失败")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预览声音失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{voice_id}/sample")
async def get_voice_sample(voice_id: str, db=Depends(get_db)):
    """获取声音样本文件"""
    try:
        service = VoiceService(db)
        sample_path = await service.get_voice_sample(voice_id)
        if not sample_path:
            raise HTTPException(status_code=404, detail="声音样本未找到")
        
        return FileResponse(
            path=sample_path,
            media_type="audio/wav",
            filename=f"voice_{voice_id}_sample.wav"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取声音样本失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{voice_id}/analyze")
async def analyze_voice(voice_id: str, db=Depends(get_db)):
    """分析声音特征"""
    try:
        service = VoiceService(db)
        analysis = await service.analyze_voice(voice_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="声音未找到或分析失败")
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析声音特征失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/similar")
async def search_similar_voices(
    voice_id: str = Query(..., description="参考声音ID"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db=Depends(get_db)
):
    """搜索相似声音"""
    try:
        service = VoiceService(db)
        similar_voices = await service.search_similar_voices(voice_id, limit)
        return {"similar_voices": similar_voices}
    except Exception as e:
        logger.error(f"搜索相似声音失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/languages")
async def get_language_stats(db=Depends(get_db)):
    """获取语言统计"""
    try:
        service = VoiceService(db)
        stats = await service.get_language_stats()
        return stats
    except Exception as e:
        logger.error(f"获取语言统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/engines")
async def get_engine_stats(db=Depends(get_db)):
    """获取引擎统计"""
    try:
        service = VoiceService(db)
        stats = await service.get_engine_stats()
        return stats
    except Exception as e:
        logger.error(f"获取引擎统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch/import")
async def batch_import_voices(
    voices_data: List[VoiceCreate],
    db=Depends(get_db)
):
    """批量导入声音"""
    try:
        if len(voices_data) > 100:
            raise HTTPException(status_code=400, detail="批量导入数量超过限制 (100)")
        
        service = VoiceService(db)
        result = await service.batch_import_voices(voices_data)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量导入声音失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch/export")
async def batch_export_voices(
    voice_ids: List[str],
    db=Depends(get_db)
):
    """批量导出声音"""
    try:
        if len(voice_ids) > 100:
            raise HTTPException(status_code=400, detail="批量导出数量超过限制 (100)")
        
        service = VoiceService(db)
        export_path = await service.batch_export_voices(voice_ids)
        
        return FileResponse(
            path=export_path,
            media_type="application/zip",
            filename="voices_export.zip"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量导出声音失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{voice_id}/clone")
async def clone_voice(voice_id: str, new_name: str, db=Depends(get_db)):
    """克隆声音"""
    try:
        service = VoiceService(db)
        cloned_voice = await service.clone_voice(voice_id, new_name)
        if not cloned_voice:
            raise HTTPException(status_code=404, detail="声音未找到或克隆失败")
        return cloned_voice
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"克隆声音失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/from-engine")
async def sync_voices_from_engine(
    engine_id: str = Query(..., description="引擎ID"),
    db=Depends(get_db)
):
    """从引擎同步声音"""
    try:
        service = VoiceService(db)
        result = await service.sync_voices_from_engine(engine_id)
        return result
    except Exception as e:
        logger.error(f"从引擎同步声音失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))