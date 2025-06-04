"""
声音库管理API模块
对应 Characters.vue 功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, or_, and_
from typing import Dict, List, Any, Optional
import os
import json
import time
import logging
from datetime import datetime, timedelta
from uuid import uuid4

from database import get_db
from models import VoiceProfile, SystemLog, UsageStats
from tts_client import MegaTTS3Client, TTSRequest, get_tts_client
from utils import log_system_event, update_usage_stats, validate_audio_file, get_audio_duration

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/characters", tags=["声音库管理"])

# 音频文件存储路径
VOICE_PROFILES_DIR = "../data/voice_profiles"
AUDIO_DIR = "../data/audio"

@router.get("/")
async def get_voice_profiles(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query("", description="搜索关键词"),
    voice_type: str = Query("", description="声音类型过滤"),
    quality_min: float = Query(0, ge=0, le=5, description="最低质量分"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    tags: str = Query("", description="标签过滤(逗号分隔)"),
    status: str = Query("", description="状态过滤"),
    db: Session = Depends(get_db)
):
    """
    获取声音档案列表
    对应前端 Characters.vue 的列表显示功能
    """
    try:
        # 构建查询
        query = db.query(VoiceProfile)
        
        # 搜索过滤
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    VoiceProfile.name.like(search_pattern),
                    VoiceProfile.description.like(search_pattern)
                )
            )
        
        # 声音类型过滤
        if voice_type and voice_type in ['male', 'female', 'child']:
            query = query.filter(VoiceProfile.type == voice_type)
        
        # 质量分过滤
        if quality_min > 0:
            query = query.filter(VoiceProfile.quality_score >= quality_min)
        
        # 状态过滤
        if status:
            query = query.filter(VoiceProfile.status == status)
        else:
            # 默认只显示激活的声音
            query = query.filter(VoiceProfile.status == 'active')
        
        # 标签过滤
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            for tag in tag_list:
                query = query.filter(VoiceProfile.tags.like(f'%"{tag}"%'))
        
        # 排序
        sort_field = getattr(VoiceProfile, sort_by, VoiceProfile.created_at)
        if sort_order == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))
        
        # 统计总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        voices = query.offset(offset).limit(page_size).all()
        
        # 转换为字典格式
        voice_list = []
        for voice in voices:
            voice_data = voice.to_dict()
            
            # 添加音频时长信息
            if voice.reference_audio_path and os.path.exists(voice.reference_audio_path):
                duration = get_audio_duration(voice.reference_audio_path)
                voice_data['audioDuration'] = duration
            
            voice_list.append(voice_data)
        
        # 分页信息
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "success": True,
            "data": voice_list,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": total_pages,
                "hasMore": page < total_pages
            },
            "filters": {
                "search": search,
                "voiceType": voice_type,
                "qualityMin": quality_min,
                "tags": tags,
                "status": status
            }
        }
        
    except Exception as e:
        logger.error(f"获取声音档案列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取列表失败: {str(e)}")

@router.post("/")
async def create_voice_profile(
    name: str = Form(...),
    description: str = Form(""),
    voice_type: str = Form(...),
    reference_audio: UploadFile = File(None),
    latent_file: UploadFile = File(None),
    tags: str = Form(""),
    color: str = Form("#06b6d4"),
    parameters: str = Form("{}"),
    db: Session = Depends(get_db)
):
    """
    创建新的声音档案
    对应前端 Characters.vue 的创建功能
    """
    try:
        # 验证输入
        if not name or len(name.strip()) == 0:
            raise HTTPException(status_code=400, detail="声音名称不能为空")
        
        if voice_type not in ['male', 'female', 'child']:
            raise HTTPException(status_code=400, detail="声音类型必须是 male、female 或 child")
        
        # 检查名称是否已存在
        existing_voice = db.query(VoiceProfile).filter(VoiceProfile.name == name).first()
        if existing_voice:
            raise HTTPException(status_code=400, detail="声音名称已存在")
        
        profile_ref_path = None
        
        # 处理参考音频文件（可选）
        if reference_audio and reference_audio.filename:
            # 验证音频文件
            if not reference_audio.content_type or not reference_audio.content_type.startswith('audio/'):
                raise HTTPException(status_code=400, detail="参考音频必须是音频文件格式")
            
            # 保存参考音频文件
            audio_content = await reference_audio.read()
            if len(audio_content) > 100 * 1024 * 1024:  # 100MB限制
                raise HTTPException(status_code=400, detail="音频文件大小不能超过100MB")
            
            # 生成文件路径
            import uuid
            file_ext = os.path.splitext(reference_audio.filename)[1].lower()
            if file_ext not in ['.wav', '.mp3', '.flac', '.m4a', '.ogg']:
                raise HTTPException(status_code=400, detail="不支持的音频格式")
            
            profile_ref_filename = f"{name}_{uuid.uuid4().hex}{file_ext}"
            profile_ref_path = os.path.join(VOICE_PROFILES_DIR, profile_ref_filename)
            
            # 确保目录存在
            os.makedirs(VOICE_PROFILES_DIR, exist_ok=True)
            
            # 保存参考音频文件
            with open(profile_ref_path, 'wb') as f:
                f.write(audio_content)
        
        # 处理latent文件（可选）
        latent_file_path = None
        if latent_file and latent_file.filename:
            if not latent_file.filename.endswith('.npy'):
                raise HTTPException(status_code=400, detail="Latent文件必须是.npy格式")
            
            latent_content = await latent_file.read()
            if len(latent_content) > 50 * 1024 * 1024:  # 50MB限制
                raise HTTPException(status_code=400, detail="Latent文件大小不能超过50MB")
            
            import uuid
            latent_filename = f"{name}_latent_{uuid.uuid4().hex}.npy"
            latent_file_path = os.path.join(VOICE_PROFILES_DIR, latent_filename)
            
            # 确保目录存在
            os.makedirs(VOICE_PROFILES_DIR, exist_ok=True)
            
            with open(latent_file_path, 'wb') as f:
                f.write(latent_content)
        
        # 处理标签
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # 处理参数
        params_dict = {"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}
        if parameters:
            try:
                params_dict.update(json.loads(parameters))
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="参数格式错误")
        
        # 创建声音档案记录
        voice_profile = VoiceProfile(
            name=name,
            description=description,
            type=voice_type,
            reference_audio_path=profile_ref_path,
            latent_file_path=latent_file_path,
            color=color,
            status='active'
        )
        
        voice_profile.set_tags(tag_list)
        voice_profile.set_parameters(params_dict)
        
        db.add(voice_profile)
        db.commit()
        db.refresh(voice_profile)
        
        # 记录创建日志
        await log_system_event(
            db=db,
            level="info",
            message=f"声音档案创建: {name}",
            module="characters",
            details={
                "voice_id": voice_profile.id,
                "voice_type": voice_type,
                "has_audio": reference_audio is not None and reference_audio.filename is not None,
                "has_latent": latent_file is not None and latent_file.filename is not None,
                "tags": tag_list
            }
        )
        
        return {
            "success": True,
            "message": "声音档案创建成功",
            "data": voice_profile.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建声音档案失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")

@router.get("/statistics")
async def get_voice_statistics(
    db: Session = Depends(get_db)
):
    """
    获取声音库统计信息
    对应前端统计面板功能
    """
    try:
        # 基础统计
        total_voices = db.query(VoiceProfile).filter(VoiceProfile.status == 'active').count()
        
        # 按类型统计
        type_stats = db.query(
            VoiceProfile.type,
            func.count(VoiceProfile.id).label('count')
        ).filter(VoiceProfile.status == 'active').group_by(VoiceProfile.type).all()
        
        type_distribution = {stat.type: stat.count for stat in type_stats}
        
        # 质量分布统计
        quality_ranges = [
            (0, 2, "低质量"),
            (2, 3.5, "中等质量"), 
            (3.5, 4.5, "高质量"),
            (4.5, 5, "极高质量")
        ]
        
        quality_distribution = {}
        for min_score, max_score, label in quality_ranges:
            count = db.query(VoiceProfile).filter(
                and_(
                    VoiceProfile.status == 'active',
                    VoiceProfile.quality_score >= min_score,
                    VoiceProfile.quality_score < max_score
                )
            ).count()
            quality_distribution[label] = count
        
        # 使用频率统计
        most_used = db.query(VoiceProfile).filter(
            VoiceProfile.status == 'active'
        ).order_by(desc(VoiceProfile.usage_count)).limit(5).all()
        
        top_voices = [
            {
                "name": voice.name,
                "usageCount": voice.usage_count,
                "quality": voice.quality_score
            }
            for voice in most_used
        ]
        
        # 最近添加
        recent_voices = db.query(VoiceProfile).filter(
            VoiceProfile.status == 'active'
        ).order_by(desc(VoiceProfile.created_at)).limit(5).all()
        
        recent_list = [
            {
                "name": voice.name,
                "type": voice.type,
                "quality": voice.quality_score,
                "createdAt": voice.created_at.strftime("%Y-%m-%d")
            }
            for voice in recent_voices
        ]
        
        # 平均质量分
        avg_quality = db.query(func.avg(VoiceProfile.quality_score)).filter(
            VoiceProfile.status == 'active'
        ).scalar() or 0
        
        return {
            "success": True,
            "statistics": {
                "totalVoices": total_voices,
                "averageQuality": round(avg_quality, 2),
                "typeDistribution": type_distribution,
                "qualityDistribution": quality_distribution,
                "topVoices": top_voices,
                "recentVoices": recent_list
            }
        }
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")

@router.get("/{voice_id}")
async def get_voice_profile(
    voice_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个声音档案详情
    对应前端详情面板功能
    """
    try:
        voice = db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
        
        if not voice:
            raise HTTPException(status_code=404, detail="声音档案不存在")
        
        voice_data = voice.to_dict()
        
        # 添加额外信息
        if voice.reference_audio_path and os.path.exists(voice.reference_audio_path):
            # 音频时长
            duration = get_audio_duration(voice.reference_audio_path)
            voice_data['audioDuration'] = duration
            
            # 文件大小
            file_size = os.path.getsize(voice.reference_audio_path)
            voice_data['fileSize'] = file_size
            voice_data['fileSizeMB'] = round(file_size / (1024 * 1024), 2)
        
        # 最近使用记录
        recent_usage = db.query(SystemLog).filter(
            and_(
                SystemLog.module == 'voice_clone',
                SystemLog.details.like(f'%"voice_id": {voice_id}%')
            )
        ).order_by(desc(SystemLog.timestamp)).limit(10).all()
        
        usage_history = []
        for log in recent_usage:
            try:
                details = json.loads(log.details) if log.details else {}
                usage_history.append({
                    "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "message": log.message,
                    "processingTime": details.get("processing_time", 0)
                })
            except:
                continue
        
        voice_data['usageHistory'] = usage_history
        
        return {
            "success": True,
            "data": voice_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取声音档案详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取详情失败: {str(e)}")

@router.put("/{voice_id}")
async def update_voice_profile(
    voice_id: int,
    name: str = Form(...),
    description: str = Form(""),
    voice_type: str = Form(...),
    reference_audio: UploadFile = File(None),
    latent_file: UploadFile = File(None),
    tags: str = Form(""),
    color: str = Form("#06b6d4"),
    parameters: str = Form("{}"),
    db: Session = Depends(get_db)
):
    """
    更新声音档案信息
    对应前端编辑功能
    """
    try:
        voice = db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
        
        if not voice:
            raise HTTPException(status_code=404, detail="声音档案不存在")
        
        # 验证输入
        if voice_type not in ['male', 'female', 'child']:
            raise HTTPException(status_code=400, detail="声音类型必须是 male、female 或 child")
        
        # 检查名称重复（排除自己）
        existing = db.query(VoiceProfile).filter(
            and_(
                VoiceProfile.name == name,
                VoiceProfile.id != voice_id
            )
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="声音名称已存在")
        
        # 处理新上传的参考音频文件（可选）
        if reference_audio and reference_audio.filename:
            # 验证音频文件
            if not reference_audio.content_type or not reference_audio.content_type.startswith('audio/'):
                raise HTTPException(status_code=400, detail="参考音频必须是音频文件格式")
            
            # 保存新的参考音频文件
            audio_content = await reference_audio.read()
            if len(audio_content) > 100 * 1024 * 1024:  # 100MB限制
                raise HTTPException(status_code=400, detail="音频文件大小不能超过100MB")
            
            # 删除旧的参考音频文件
            if voice.reference_audio_path and os.path.exists(voice.reference_audio_path):
                try:
                    os.remove(voice.reference_audio_path)
                except Exception as e:
                    logger.warning(f"删除旧参考音频文件失败: {str(e)}")
            
            # 生成新文件路径
            import uuid
            file_ext = os.path.splitext(reference_audio.filename)[1].lower()
            if file_ext not in ['.wav', '.mp3', '.flac', '.m4a', '.ogg']:
                raise HTTPException(status_code=400, detail="不支持的音频格式")
            
            profile_ref_filename = f"{name}_{uuid.uuid4().hex}{file_ext}"
            profile_ref_path = os.path.join(VOICE_PROFILES_DIR, profile_ref_filename)
            
            # 确保目录存在
            os.makedirs(VOICE_PROFILES_DIR, exist_ok=True)
            
            # 保存新参考音频文件
            with open(profile_ref_path, 'wb') as f:
                f.write(audio_content)
            
            voice.reference_audio_path = profile_ref_path

        # 处理新上传的latent文件（可选）
        if latent_file and latent_file.filename:
            if not latent_file.filename.endswith('.npy'):
                raise HTTPException(status_code=400, detail="Latent文件必须是.npy格式")
            
            latent_content = await latent_file.read()
            if len(latent_content) > 50 * 1024 * 1024:  # 50MB限制
                raise HTTPException(status_code=400, detail="Latent文件大小不能超过50MB")
            
            # 删除旧的latent文件
            if voice.latent_file_path and os.path.exists(voice.latent_file_path):
                try:
                    os.remove(voice.latent_file_path)
                except Exception as e:
                    logger.warning(f"删除旧Latent文件失败: {str(e)}")
            
            # 生成新文件路径
            import uuid
            latent_filename = f"{name}_{uuid.uuid4().hex}.npy"
            latent_path = os.path.join(VOICE_PROFILES_DIR, latent_filename)
            
            # 保存新latent文件
            with open(latent_path, 'wb') as f:
                f.write(latent_content)
            
            voice.latent_file_path = latent_path
        
        # 处理标签
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # 处理参数
        params_dict = {}
        if parameters:
            try:
                params_dict = json.loads(parameters)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="参数格式错误")
        
        # 更新字段
        old_name = voice.name
        voice.name = name
        voice.description = description
        voice.type = voice_type
        voice.color = color
        voice.set_tags(tag_list)
        voice.set_parameters(params_dict)
        voice.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(voice)
        
        # 记录更新日志
        await log_system_event(
            db=db,
            level="info",
            message=f"声音档案更新: {old_name} -> {name}",
            module="characters",
            details={
                "voice_id": voice_id,
                "old_name": old_name,
                "new_name": name,
                "changes": {
                    "description": description,
                    "type": voice_type,
                    "tags": tag_list,
                    "color": color,
                    "parameters": params_dict,
                    "files_updated": {
                        "reference_audio": bool(reference_audio and reference_audio.filename),
                        "latent_file": bool(latent_file and latent_file.filename)
                    }
                }
            }
        )
        
        return {
            "success": True,
            "message": "声音档案更新成功",
            "data": voice.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新声音档案失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

@router.delete("/{voice_id}")
async def delete_voice_profile(
    voice_id: int,
    force: bool = Query(False, description="强制删除"),
    db: Session = Depends(get_db)
):
    """
    删除声音档案
    对应前端删除功能
    """
    try:
        voice = db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
        
        if not voice:
            raise HTTPException(status_code=404, detail="声音档案不存在")
        
        # 检查是否正在使用中
        if not force and voice.usage_count > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"声音档案正在使用中(使用次数: {voice.usage_count})，请使用强制删除"
            )
        
        voice_name = voice.name
        
        # 删除相关文件
        files_to_delete = []
        if voice.reference_audio_path and os.path.exists(voice.reference_audio_path):
            files_to_delete.append(voice.reference_audio_path)
        
        if voice.latent_file_path and os.path.exists(voice.latent_file_path):
            files_to_delete.append(voice.latent_file_path)
        
        if voice.sample_audio_path and os.path.exists(voice.sample_audio_path):
            files_to_delete.append(voice.sample_audio_path)
        
        # 删除数据库记录
        db.delete(voice)
        db.commit()
        
        # 删除文件
        deleted_files = []
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
                deleted_files.append(file_path)
            except Exception as e:
                logger.warning(f"删除文件失败 {file_path}: {str(e)}")
        
        # 记录删除日志
        await log_system_event(
            db=db,
            level="info",
            message=f"声音档案删除: {voice_name}",
            module="characters",
            details={
                "voice_id": voice_id,
                "voice_name": voice_name,
                "deleted_files": deleted_files,
                "force": force
            }
        )
        
        return {
            "success": True,
            "message": f"声音档案 '{voice_name}' 删除成功",
            "deletedFiles": len(deleted_files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除声音档案失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@router.post("/{voice_id}/test")
async def test_voice_synthesis(
    voice_id: int,
    request: Request,  # 移到前面避免语法错误
    text: str = Form("你好，这是声音测试。"),
    time_step: int = Form(32),
    p_weight: float = Form(1.4),
    t_weight: float = Form(3.0),
    db: Session = Depends(get_db)
):
    """测试声音合成"""
    try:
        voice_profile = db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
        if not voice_profile:
            raise HTTPException(status_code=404, detail="声音档案不存在")
        
        # 检查音频文件是否存在
        if not voice_profile.reference_audio_path or not os.path.exists(voice_profile.reference_audio_path):
            raise HTTPException(status_code=400, detail="声音文件不存在，请重新上传")
        
        # 生成唯一的音频文件名
        audio_id = f"test_{voice_id}_{uuid4().hex[:32]}"
        output_path = os.path.join("../data/audio", f"{audio_id}.wav")  # 修复：使用os.path.join确保跨平台兼容
        
        # 确保音频输出目录存在
        os.makedirs("../data/audio", exist_ok=True)
        
        # 创建TTS请求
        tts_request = TTSRequest(
            text=text,
            reference_audio_path=voice_profile.reference_audio_path,  # 修复：使用正确字段名
            output_audio_path=output_path,
            time_step=time_step,     # 修复：使用新默认值
            p_weight=p_weight,       # 修复：使用新默认值
            t_weight=t_weight,       # 修复：使用新默认值
            latent_file_path=voice_profile.latent_file_path
        )
        
        # 执行合成
        tts_client = get_tts_client()
        response = await tts_client.synthesize_speech(tts_request)
        
        if response.success:
            # 修复：使用正确的log_system_event调用方式
            try:
                await log_system_event(
                    db=db,
                    level="info",
                    message=f"声音测试成功: {voice_profile.name}",
                    module="characters",
                    details={
                        "voice_id": voice_id,
                        "text": text,
                        "processing_time": response.processing_time
                    }
                )
            except Exception as log_error:
                logger.warning(f"记录日志失败: {str(log_error)}")
            
            # 动态生成音频URL，支持外网访问
            host = request.headers.get("host", "localhost:8000")
            scheme = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"
            audio_url = f"{scheme}://{host}/audio/{audio_id}.wav"
            
            return {
                "success": True,
                "message": "测试合成完成",
                "audioUrl": audio_url,  # 使用动态URL
                "processingTime": response.processing_time,
                "audioId": f"{audio_id}.wav"
            }
        else:
            raise HTTPException(status_code=500, detail=f"合成失败: {response.message}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"声音测试失败: {str(e)}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"声音测试失败: {str(e)}")

@router.post("/{voice_id}/evaluate-quality")
async def evaluate_voice_quality(
    voice_id: int,
    db: Session = Depends(get_db)
):
    """
    重新评估声音质量
    对应前端质量评估功能
    """
    tts_client = get_tts_client()
    
    try:
        voice = db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
        
        if not voice:
            raise HTTPException(status_code=404, detail="声音档案不存在")
        
        quality_score = voice.quality_score
        
        # 如果有样本音频，重新评估
        if voice.sample_audio_path and os.path.exists(voice.sample_audio_path):
            # 简化质量评估 - 基于文件大小
            file_size = os.path.getsize(voice.sample_audio_path)
            if file_size > 50000:  # 50KB以上
                quality_score = 3.0
            if file_size > 100000:  # 100KB以上
                quality_score = 3.5
            if file_size > 200000:  # 200KB以上
                quality_score = 4.0
            
            # 更新质量分
            old_quality = voice.quality_score
            voice.quality_score = quality_score
            voice.updated_at = datetime.utcnow()
            db.commit()
            
            # 记录评估日志
            await log_system_event(
                db=db,
                level="info",
                message=f"质量评估更新: {voice.name}",
                module="characters",
                details={
                    "voice_id": voice_id,
                    "old_quality": old_quality,
                    "new_quality": quality_score,
                    "file_size": file_size
                }
            )
        
        return {
            "success": True,
            "message": "质量评估完成",
            "qualityScore": voice.quality_score,
            "updated": voice.quality_score != old_quality
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"质量评估失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"评估失败: {str(e)}")

@router.post("/batch-operations")
async def batch_operations(
    operation: str = Form(...),
    voice_ids: str = Form(...),
    parameters: str = Form("{}"),
    db: Session = Depends(get_db)
):
    """
    批量操作声音档案
    对应前端批量管理功能
    """
    try:
        # 解析声音ID列表
        try:
            id_list = [int(id.strip()) for id in voice_ids.split(',') if id.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="声音ID格式错误")
        
        if not id_list:
            raise HTTPException(status_code=400, detail="未选择任何声音档案")
        
        # 解析参数
        params = {}
        if parameters:
            try:
                params = json.loads(parameters)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="参数格式错误")
        
        # 获取声音档案
        voices = db.query(VoiceProfile).filter(VoiceProfile.id.in_(id_list)).all()
        
        if len(voices) != len(id_list):
            raise HTTPException(status_code=404, detail="部分声音档案不存在")
        
        results = []
        
        if operation == "delete":
            # 批量删除
            force = params.get("force", False)
            
            for voice in voices:
                try:
                    if not force and voice.usage_count > 0:
                        results.append({
                            "id": voice.id,
                            "name": voice.name,
                            "success": False,
                            "error": f"正在使用中(使用次数: {voice.usage_count})"
                        })
                        continue
                    
                    # 删除文件
                    files_to_delete = [
                        voice.reference_audio_path,
                        voice.latent_file_path,
                        voice.sample_audio_path
                    ]
                    
                    db.delete(voice)
                    
                    # 删除关联文件
                    for file_path in files_to_delete:
                        if file_path and os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                            except:
                                pass
                    
                    results.append({
                        "id": voice.id,
                        "name": voice.name,
                        "success": True
                    })
                    
                except Exception as e:
                    results.append({
                        "id": voice.id,
                        "name": voice.name,
                        "success": False,
                        "error": str(e)
                    })
        
        elif operation == "update_tags":
            # 批量更新标签
            new_tags = params.get("tags", [])
            action = params.get("action", "replace")  # replace, add, remove
            
            for voice in voices:
                try:
                    current_tags = voice.get_tags()
                    
                    if action == "replace":
                        voice.set_tags(new_tags)
                    elif action == "add":
                        combined_tags = list(set(current_tags + new_tags))
                        voice.set_tags(combined_tags)
                    elif action == "remove":
                        remaining_tags = [tag for tag in current_tags if tag not in new_tags]
                        voice.set_tags(remaining_tags)
                    
                    voice.updated_at = datetime.utcnow()
                    
                    results.append({
                        "id": voice.id,
                        "name": voice.name,
                        "success": True,
                        "tags": voice.get_tags()
                    })
                    
                except Exception as e:
                    results.append({
                        "id": voice.id,
                        "name": voice.name,
                        "success": False,
                        "error": str(e)
                    })
        
        elif operation == "update_status":
            # 批量更新状态
            new_status = params.get("status", "active")
            
            if new_status not in ['active', 'inactive', 'training']:
                raise HTTPException(status_code=400, detail="无效的状态值")
            
            for voice in voices:
                try:
                    voice.status = new_status
                    voice.updated_at = datetime.utcnow()
                    
                    results.append({
                        "id": voice.id,
                        "name": voice.name,
                        "success": True,
                        "status": new_status
                    })
                    
                except Exception as e:
                    results.append({
                        "id": voice.id,
                        "name": voice.name,
                        "success": False,
                        "error": str(e)
                    })
        
        else:
            raise HTTPException(status_code=400, detail=f"不支持的操作: {operation}")
        
        # 提交所有更改
        db.commit()
        
        # 统计结果
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful
        
        # 记录批量操作日志
        await log_system_event(
            db=db,
            level="info",
            message=f"批量操作完成: {operation}",
            module="characters",
            details={
                "operation": operation,
                "total": len(results),
                "successful": successful,
                "failed": failed,
                "parameters": params
            }
        )
        
        return {
            "success": True,
            "message": f"批量操作完成: 成功 {successful}，失败 {failed}",
            "results": results,
            "summary": {
                "total": len(results),
                "successful": successful,
                "failed": failed
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量操作失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量操作失败: {str(e)}")

@router.get("/export/list")
async def export_voice_list(
    format: str = Query("json", description="导出格式"),
    include_files: bool = Query(False, description="是否包含音频文件"),
    db: Session = Depends(get_db)
):
    """
    导出声音库列表
    对应前端导出功能
    """
    try:
        voices = db.query(VoiceProfile).filter(VoiceProfile.status == 'active').all()
        
        if format == "json":
            voice_list = []
            for voice in voices:
                voice_data = voice.to_dict()
                
                if not include_files:
                    # 移除文件路径信息
                    voice_data.pop('referenceAudioUrl', None)
                    voice_data.pop('latentFileUrl', None)
                    voice_data.pop('sampleAudioUrl', None)
                
                voice_list.append(voice_data)
            
            return {
                "success": True,
                "format": "json",
                "count": len(voice_list),
                "data": voice_list,
                "exportTime": datetime.now().isoformat()
            }
        
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入表头
            headers = ['ID', '名称', '描述', '类型', '质量分', '使用次数', '状态', '创建时间']
            writer.writerow(headers)
            
            # 写入数据
            for voice in voices:
                row = [
                    voice.id,
                    voice.name,
                    voice.description or '',
                    voice.type,
                    voice.quality_score,
                    voice.usage_count,
                    voice.status,
                    voice.created_at.strftime('%Y-%m-%d %H:%M:%S') if voice.created_at else ''
                ]
                writer.writerow(row)
            
            csv_content = output.getvalue()
            output.close()
            
            return {
                "success": True,
                "format": "csv",
                "count": len(voices),
                "data": csv_content,
                "exportTime": datetime.now().isoformat()
            }
        
        else:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出声音库失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

@router.get("/tags/popular")
async def get_popular_tags(
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db)
):
    """
    获取热门标签列表
    对应前端标签选择功能
    """
    try:
        # 获取所有活跃声音的标签
        voices = db.query(VoiceProfile).filter(VoiceProfile.status == 'active').all()
        
        tag_count = {}
        for voice in voices:
            tags = voice.get_tags()
            for tag in tags:
                tag_count[tag] = tag_count.get(tag, 0) + 1
        
        # 按使用频率排序
        popular_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        tag_list = [
            {
                "tag": tag,
                "count": count,
                "percentage": round((count / len(voices)) * 100, 1) if voices else 0
            }
            for tag, count in popular_tags
        ]
        
        return {
            "success": True,
            "tags": tag_list,
            "total": len(tag_count)
        }
        
    except Exception as e:
        logger.error(f"获取热门标签失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取标签失败: {str(e)}") 