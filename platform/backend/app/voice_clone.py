"""
声音克隆API模块
对应 BasicTTS.vue 功能
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Dict, List, Any, Optional
import os
import uuid
import json
import time
import logging
from datetime import datetime

from .database import get_db
from .models import VoiceProfile, SystemLog, UsageStats
from .tts_client import MegaTTS3Client, TTSRequest, get_tts_client
from .utils import save_upload_file, log_system_event, update_usage_stats

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/voice-clone", tags=["声音克隆"])

# 音频文件存储路径
AUDIO_DIR = "../data/audio"
UPLOAD_DIR = "../data/uploads"
VOICE_PROFILES_DIR = "../data/voice_profiles"

@router.post("/upload-reference")
async def upload_reference_audio(
    file: UploadFile = File(...),
    latent_file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """
    上传参考音频文件和可选的latent文件
    对应前端 BasicTTS.vue 的文件上传功能
    """
    try:
        # 验证音频文件类型
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="只支持音频文件格式")
        
        # 验证音频文件大小 (限制为100MB)
        audio_content = await file.read()
        if len(audio_content) > 100 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="音频文件大小不能超过100MB")
        
        # 生成唯一文件名
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ['.wav', '.mp3', '.flac', '.m4a', '.ogg']:
            raise HTTPException(status_code=400, detail="不支持的音频格式")
        
        unique_filename = f"ref_{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # 确保目录存在
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # 保存音频文件
        with open(file_path, 'wb') as f:
            f.write(audio_content)
        
        # 处理latent文件（可选）
        latent_file_path = None
        latent_filename = None
        if latent_file:
            # 验证latent文件
            if not latent_file.filename.endswith('.npy'):
                raise HTTPException(status_code=400, detail="Latent文件必须是.npy格式")
            
            latent_content = await latent_file.read()
            if len(latent_content) > 50 * 1024 * 1024:  # 限制50MB
                raise HTTPException(status_code=400, detail="Latent文件大小不能超过50MB")
            
            latent_filename = f"latent_{uuid.uuid4().hex}.npy"
            latent_file_path = os.path.join(UPLOAD_DIR, latent_filename)
            
            with open(latent_file_path, 'wb') as f:
                f.write(latent_content)
        
        # 获取音频文件信息
        file_size_mb = len(audio_content) / (1024 * 1024)
        
        # 记录系统日志
        await log_system_event(
            db=db,
            level="info",
            message=f"参考音频上传成功: {file.filename}" + (f" (含latent: {latent_file.filename})" if latent_file else ""),
            module="voice_clone",
            details={
                "filename": file.filename,
                "size_mb": round(file_size_mb, 2),
                "file_path": file_path,
                "latent_file": latent_file.filename if latent_file else None,
                "latent_path": latent_file_path
            }
        )
        
        return {
            "success": True,
            "message": "文件上传成功",
            "fileId": unique_filename,
            "filePath": file_path,
            "fileName": file.filename,
            "fileSize": round(file_size_mb, 2),
            "url": f"/uploads/{unique_filename}",
            "latentFileId": latent_filename,
            "latentFilePath": latent_file_path,
            "latentFileName": latent_file.filename if latent_file else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"参考音频上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.post("/synthesize")
async def synthesize_speech(
    text: str = Form(...),
    reference_file_id: str = Form(...),
    time_step: int = Form(20),
    p_weight: float = Form(1.0),
    t_weight: float = Form(1.0),
    latent_file_id: str = Form(...),
    voice_name: Optional[str] = Form("临时测试"),
    db: Session = Depends(get_db)
):
    """
    实时语音合成
    对应前端 BasicTTS.vue 的合成功能
    注意：MegaTTS3采用WaveVAE decoder-only架构，必须同时提供音频文件和latent文件
    """
    start_time = time.time()
    tts_client = get_tts_client()
    
    try:
        # 验证输入
        if not text or len(text.strip()) == 0:
            raise HTTPException(status_code=400, detail="合成文本不能为空")
        
        if len(text) > 1000:
            raise HTTPException(status_code=400, detail="文本长度不能超过1000字符")
        
        # 验证参考音频文件
        reference_audio_path = os.path.join(UPLOAD_DIR, reference_file_id)
        if not os.path.exists(reference_audio_path):
            raise HTTPException(status_code=404, detail="参考音频文件不存在")
        
        # 验证latent文件（必需）
        latent_file_path = os.path.join(UPLOAD_DIR, latent_file_id)
        if not os.path.exists(latent_file_path):
            raise HTTPException(status_code=404, detail="Latent特征文件不存在。MegaTTS3采用decoder-only架构，必须同时提供音频文件和latent文件")
        
        # 生成输出文件路径
        output_filename = f"tts_{uuid.uuid4().hex}.wav"
        output_path = os.path.join(AUDIO_DIR, output_filename)
        
        # 确保输出目录存在
        os.makedirs(AUDIO_DIR, exist_ok=True)
        
        # 构建TTS请求
        tts_request = TTSRequest(
            text=text,
            reference_audio_path=reference_audio_path,
            output_audio_path=output_path,
            time_step=time_step,
            p_weight=p_weight,
            t_weight=t_weight,
            latent_file_path=latent_file_path
        )
        
        # 调用MegaTTS3进行合成
        response = await tts_client.synthesize_speech(tts_request)
        
        processing_time = time.time() - start_time
        
        if response.success:
            # 记录成功日志
            await log_system_event(
                db=db,
                level="info",
                message=f"语音合成成功: {voice_name}",
                module="voice_clone",
                details={
                    "text_length": len(text),
                    "processing_time": processing_time,
                    "parameters": {
                        "time_step": time_step,
                        "p_weight": p_weight,
                        "t_weight": t_weight
                    }
                }
            )
            
            # 更新使用统计
            await update_usage_stats(db, success=True, processing_time=processing_time)
            
            return {
                "success": True,
                "message": "合成完成",
                "audioUrl": f"/audio/{output_filename}",
                "processingTime": round(processing_time, 2),
                "audioId": output_filename,
                "parameters": {
                    "timeStep": time_step,
                    "pWeight": p_weight,
                    "tWeight": t_weight
                }
            }
        else:
            # 记录失败日志
            await log_system_event(
                db=db,
                level="error",
                message=f"语音合成失败: {response.message}",
                module="voice_clone",
                details={
                    "error_code": response.error_code,
                    "processing_time": processing_time,
                    "text_length": len(text)
                }
            )
            
            # 更新使用统计
            await update_usage_stats(db, success=False, processing_time=processing_time)
            
            raise HTTPException(status_code=500, detail=response.message)
    
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"语音合成异常: {str(e)}")
        
        # 记录异常日志
        await log_system_event(
            db=db,
            level="error",
            message=f"语音合成异常: {str(e)}",
            module="voice_clone",
            details={"processing_time": processing_time}
        )
        
        # 更新使用统计
        await update_usage_stats(db, success=False, processing_time=processing_time)
        
        raise HTTPException(status_code=500, detail=f"合成异常: {str(e)}")

@router.post("/clone-voice")
async def clone_voice(
    voice_name: str = Form(...),
    reference_file_id: str = Form(...),
    description: str = Form(""),
    voice_type: str = Form("female"),
    latent_file_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    声音克隆 - 生成潜向量文件并保存到声音库
    对应前端保存到声音库功能
    支持用户上传预训练的latent文件来提升克隆质量
    """
    start_time = time.time()
    tts_client = get_tts_client()
    
    try:
        # 验证输入
        if not voice_name or len(voice_name.strip()) == 0:
            raise HTTPException(status_code=400, detail="声音名称不能为空")
        
        if voice_type not in ['male', 'female', 'child']:
            raise HTTPException(status_code=400, detail="声音类型必须是 male、female 或 child")
        
        # 检查名称是否已存在
        existing_voice = db.query(VoiceProfile).filter(VoiceProfile.name == voice_name).first()
        if existing_voice:
            raise HTTPException(status_code=400, detail="声音名称已存在")
        
        # 验证参考音频文件
        reference_audio_path = os.path.join(UPLOAD_DIR, reference_file_id)
        if not os.path.exists(reference_audio_path):
            raise HTTPException(status_code=404, detail="参考音频文件不存在")
        
        # 处理用户上传的latent文件（可选）
        user_latent_file_path = None
        if latent_file_id:
            user_latent_file_path = os.path.join(UPLOAD_DIR, latent_file_id)
            if not os.path.exists(user_latent_file_path):
                logger.warning(f"用户上传的latent文件不存在，将使用系统生成: {user_latent_file_path}")
                user_latent_file_path = None
        
        # 调用MegaTTS3进行声音克隆
        clone_result = await tts_client.clone_voice(reference_audio_path, voice_name)
        
        if not clone_result.get("success", False):
            raise HTTPException(status_code=500, detail=clone_result.get("message", "声音克隆失败"))
        
        # 移动参考音频到voice_profiles目录
        profile_ref_filename = f"{voice_name}_reference{os.path.splitext(reference_audio_path)[1]}"
        profile_ref_path = os.path.join(VOICE_PROFILES_DIR, profile_ref_filename)
        
        os.makedirs(VOICE_PROFILES_DIR, exist_ok=True)
        import shutil
        shutil.copy2(reference_audio_path, profile_ref_path)
        
        # 确定最终使用的latent文件路径
        final_latent_file_path = None
        if user_latent_file_path:
            # 使用用户上传的latent文件
            profile_latent_filename = f"{voice_name}_latent.npy"
            final_latent_file_path = os.path.join(VOICE_PROFILES_DIR, profile_latent_filename)
            shutil.copy2(user_latent_file_path, final_latent_file_path)
            logger.info(f"使用用户上传的latent文件: {final_latent_file_path}")
        else:
            # 使用系统生成的latent文件
            final_latent_file_path = clone_result.get("latent_file_path")
            logger.info(f"使用系统生成的latent文件: {final_latent_file_path}")
        
        # 生成测试音频（使用固定测试文本）
        test_text = "这是声音克隆的测试音频，用于验证克隆效果。"
        sample_filename = f"{voice_name}_sample.wav"
        sample_path = os.path.join(VOICE_PROFILES_DIR, sample_filename)
        
        # 使用克隆的声音合成测试音频
        test_request = TTSRequest(
            text=test_text,
            reference_audio_path=profile_ref_path,
            output_audio_path=sample_path,
            time_step=20,
            p_weight=1.0,
            t_weight=1.0,
            latent_file_path=final_latent_file_path
        )
        
        sample_result = await tts_client.synthesize_speech(test_request)
        if not sample_result.success:
            logger.warning(f"生成测试音频失败: {sample_result.message}")
            sample_path = None
        
        # 评估音质
        quality_score = 3.0  # 默认值
        if sample_path and os.path.exists(sample_path):
            quality_result = await tts_client.get_voice_quality_score(sample_path)
            if quality_result.get("success", False):
                quality_score = quality_result.get("quality_score", 3.0)
        
        # 创建声音档案记录
        voice_profile = VoiceProfile(
            name=voice_name,
            description=description,
            type=voice_type,
            reference_audio_path=profile_ref_path,
            latent_file_path=final_latent_file_path,
            sample_audio_path=sample_path,
            parameters=json.dumps({"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}),
            quality_score=quality_score,
            status='active'
        )
        
        db.add(voice_profile)
        db.commit()
        db.refresh(voice_profile)
        
        processing_time = time.time() - start_time
        
        # 记录成功日志
        await log_system_event(
            db=db,
            level="info",
            message=f"声音克隆成功: {voice_name}" + (f" (使用用户latent文件)" if user_latent_file_path else ""),
            module="voice_clone",
            details={
                "voice_id": voice_profile.id,
                "processing_time": processing_time,
                "quality_score": quality_score,
                "user_latent_used": bool(user_latent_file_path)
            }
        )
        
        return {
            "success": True,
            "message": "声音克隆完成",
            "voiceProfile": voice_profile.to_dict(),
            "processingTime": round(processing_time, 2),
            "userLatentUsed": bool(user_latent_file_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"声音克隆异常: {str(e)}")
        
        # 记录异常日志
        await log_system_event(
            db=db,
            level="error",
            message=f"声音克隆异常: {str(e)}",
            module="voice_clone",
            details={"processing_time": processing_time}
        )
        
        raise HTTPException(status_code=500, detail=f"克隆异常: {str(e)}")

@router.post("/optimize-parameters")
async def optimize_parameters(
    text: str = Form(...),
    reference_file_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    参数优化 - 自动寻找最佳的time_step、p_weight、t_weight参数
    对应前端参数优化功能
    """
    start_time = time.time()
    tts_client = get_tts_client()
    
    try:
        # 验证输入
        if not text or len(text.strip()) == 0:
            raise HTTPException(status_code=400, detail="测试文本不能为空")
        
        # 验证参考音频文件
        reference_audio_path = os.path.join(UPLOAD_DIR, reference_file_id)
        if not os.path.exists(reference_audio_path):
            raise HTTPException(status_code=404, detail="参考音频文件不存在")
        
        # 参数优化范围
        time_steps = [15, 20, 25]
        p_weights = [0.8, 1.0, 1.2]
        t_weights = [0.8, 1.0, 1.2]
        
        best_params = {"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}
        best_quality = 0.0
        optimization_results = []
        
        # 测试不同参数组合
        for time_step in time_steps:
            for p_weight in p_weights:
                for t_weight in t_weights:
                    try:
                        # 生成测试音频
                        test_filename = f"opt_{uuid.uuid4().hex}.wav"
                        test_path = os.path.join(AUDIO_DIR, test_filename)
                        
                        test_request = TTSRequest(
                            text=text,
                            reference_audio_path=reference_audio_path,
                            output_audio_path=test_path,
                            time_step=time_step,
                            p_weight=p_weight,
                            t_weight=t_weight
                        )
                        
                        synthesis_result = await tts_client.synthesize_speech(test_request)
                        
                        if synthesis_result.success:
                            # 评估音质
                            quality_result = await tts_client.get_voice_quality_score(test_path)
                            quality_score = quality_result.get("quality_score", 0.0) if quality_result.get("success") else 0.0
                            
                            optimization_results.append({
                                "timeStep": time_step,
                                "pWeight": p_weight,
                                "tWeight": t_weight,
                                "qualityScore": quality_score,
                                "processingTime": synthesis_result.processing_time
                            })
                            
                            # 更新最佳参数
                            if quality_score > best_quality:
                                best_quality = quality_score
                                best_params = {
                                    "timeStep": time_step,
                                    "pWeight": p_weight,
                                    "tWeight": t_weight
                                }
                            
                            # 清理测试文件
                            try:
                                os.remove(test_path)
                            except:
                                pass
                    
                    except Exception as e:
                        logger.warning(f"参数测试失败 ({time_step}, {p_weight}, {t_weight}): {str(e)}")
                        continue
        
        processing_time = time.time() - start_time
        
        # 记录优化结果
        await log_system_event(
            db=db,
            level="info",
            message="参数优化完成",
            module="voice_clone",
            details={
                "best_params": best_params,
                "best_quality": best_quality,
                "total_tests": len(optimization_results),
                "processing_time": processing_time
            }
        )
        
        return {
            "success": True,
            "message": "参数优化完成",
            "bestParameters": best_params,
            "bestQuality": best_quality,
            "allResults": optimization_results,
            "processingTime": round(processing_time, 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"参数优化异常: {str(e)}")
        
        # 记录异常日志
        await log_system_event(
            db=db,
            level="error",
            message=f"参数优化异常: {str(e)}",
            module="voice_clone",
            details={"processing_time": processing_time}
        )
        
        raise HTTPException(status_code=500, detail=f"优化异常: {str(e)}")

@router.get("/templates")
async def get_voice_templates(
    db: Session = Depends(get_db)
):
    """
    获取声音模板列表
    对应前端模板选择功能
    """
    try:
        # 获取质量较高的声音档案作为模板
        templates = db.query(VoiceProfile)\
                     .filter(VoiceProfile.status == 'active')\
                     .filter(VoiceProfile.quality_score >= 3.5)\
                     .order_by(desc(VoiceProfile.quality_score))\
                     .limit(10)\
                     .all()
        
        template_list = []
        for template in templates:
            template_data = template.to_dict()
            template_data['isTemplate'] = True
            template_list.append(template_data)
        
        return {
            "success": True,
            "templates": template_list,
            "total": len(template_list)
        }
        
    except Exception as e:
        logger.error(f"获取模板列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模板失败: {str(e)}")

@router.get("/recent-synthesis")
async def get_recent_synthesis(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    获取最近的合成记录
    对应前端历史记录功能
    """
    try:
        # 从系统日志中获取最近的合成记录
        recent_logs = db.query(SystemLog)\
                       .filter(SystemLog.module == 'voice_clone')\
                       .filter(SystemLog.message.contains('语音合成成功'))\
                       .order_by(desc(SystemLog.timestamp))\
                       .limit(limit)\
                       .all()
        
        synthesis_history = []
        for log in recent_logs:
            details = json.loads(log.details) if log.details else {}
            synthesis_history.append({
                "id": log.id,
                "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "textLength": details.get("text_length", 0),
                "processingTime": details.get("processing_time", 0),
                "parameters": details.get("parameters", {})
            })
        
        return {
            "success": True,
            "history": synthesis_history,
            "total": len(synthesis_history)
        }
        
    except Exception as e:
        logger.error(f"获取合成历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}")

@router.delete("/cleanup-temp-files")
async def cleanup_temp_files():
    """
    清理临时文件
    对应前端清理功能
    """
    try:
        cleanup_count = 0
        
        # 清理超过24小时的上传文件
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                file_age = time.time() - os.path.getctime(file_path)
                if file_age > 24 * 3600:  # 24小时
                    try:
                        os.remove(file_path)
                        cleanup_count += 1
                    except Exception as e:
                        logger.warning(f"清理文件失败 {filename}: {str(e)}")
        
        # 清理超过1小时的临时TTS文件
        for filename in os.listdir(AUDIO_DIR):
            if filename.startswith('tts_') or filename.startswith('opt_'):
                file_path = os.path.join(AUDIO_DIR, filename)
                if os.path.isfile(file_path):
                    file_age = time.time() - os.path.getctime(file_path)
                    if file_age > 3600:  # 1小时
                        try:
                            os.remove(file_path)
                            cleanup_count += 1
                        except Exception as e:
                            logger.warning(f"清理文件失败 {filename}: {str(e)}")
        
        return {
            "success": True,
            "message": f"清理完成，删除了 {cleanup_count} 个文件",
            "cleanedFiles": cleanup_count
        }
        
    except Exception as e:
        logger.error(f"清理临时文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")

@router.post("/synthesize-from-library")
async def synthesize_from_library(
    text: str = Form(...),
    voice_profile_id: int = Form(...),
    time_step: int = Form(20),
    p_weight: float = Form(1.0),
    t_weight: float = Form(1.0),
    voice_name: Optional[str] = Form("声音库合成"),
    db: Session = Depends(get_db)
):
    """
    使用声音库中的声音进行合成
    对应前端从声音库选择声音的功能
    无需重新上传文件，直接使用已保存的音频文件和latent文件
    """
    start_time = time.time()
    tts_client = get_tts_client()
    
    try:
        # 验证输入
        if not text or len(text.strip()) == 0:
            raise HTTPException(status_code=400, detail="合成文本不能为空")
        
        if len(text) > 1000:
            raise HTTPException(status_code=400, detail="文本长度不能超过1000字符")
        
        # 获取声音档案
        voice_profile = db.query(VoiceProfile).filter(VoiceProfile.id == voice_profile_id).first()
        if not voice_profile:
            raise HTTPException(status_code=404, detail="声音档案不存在")
        
        if voice_profile.status != 'active':
            raise HTTPException(status_code=400, detail="该声音档案不可用")
        
        # 验证声音库中的文件是否存在
        if not voice_profile.reference_audio_path or not os.path.exists(voice_profile.reference_audio_path):
            raise HTTPException(status_code=404, detail="声音库中的音频文件不存在")
        
        if not voice_profile.latent_file_path or not os.path.exists(voice_profile.latent_file_path):
            raise HTTPException(status_code=404, detail="声音库中的latent文件不存在")
        
        # 生成输出文件路径
        output_filename = f"library_tts_{uuid.uuid4().hex}.wav"
        output_path = os.path.join(AUDIO_DIR, output_filename)
        
        # 确保输出目录存在
        os.makedirs(AUDIO_DIR, exist_ok=True)
        
        # 构建TTS请求 - 直接使用声音库中的文件
        tts_request = TTSRequest(
            text=text,
            reference_audio_path=voice_profile.reference_audio_path,
            output_audio_path=output_path,
            time_step=time_step,
            p_weight=p_weight,
            t_weight=t_weight,
            latent_file_path=voice_profile.latent_file_path
        )
        
        # 调用MegaTTS3进行合成
        response = await tts_client.synthesize_speech(tts_request)
        
        processing_time = time.time() - start_time
        
        if response.success:
            # 更新声音档案的使用统计
            voice_profile.usage_count = (voice_profile.usage_count or 0) + 1
            voice_profile.last_used = datetime.utcnow()
            db.commit()
            
            # 记录成功日志
            await log_system_event(
                db=db,
                level="info",
                message=f"声音库合成成功: {voice_profile.name}",
                module="voice_clone",
                details={
                    "voice_profile_id": voice_profile_id,
                    "voice_name": voice_profile.name,
                    "text_length": len(text),
                    "processing_time": processing_time,
                    "parameters": {
                        "time_step": time_step,
                        "p_weight": p_weight,
                        "t_weight": t_weight
                    }
                }
            )
            
            # 更新使用统计
            await update_usage_stats(db, success=True, processing_time=processing_time)
            
            return {
                "success": True,
                "message": "声音库合成完成",
                "audioUrl": f"/audio/{output_filename}",
                "processingTime": round(processing_time, 2),
                "audioId": output_filename,
                "voiceProfile": {
                    "id": voice_profile.id,
                    "name": voice_profile.name,
                    "usageCount": voice_profile.usage_count
                },
                "parameters": {
                    "timeStep": time_step,
                    "pWeight": p_weight,
                    "tWeight": t_weight
                }
            }
        else:
            # 记录失败日志
            await log_system_event(
                db=db,
                level="error",
                message=f"声音库合成失败: {response.message}",
                module="voice_clone",
                details={
                    "voice_profile_id": voice_profile_id,
                    "error_code": response.error_code,
                    "processing_time": processing_time,
                    "text_length": len(text)
                }
            )
            
            # 更新使用统计
            await update_usage_stats(db, success=False, processing_time=processing_time)
            
            raise HTTPException(status_code=500, detail=response.message)
    
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"声音库合成异常: {str(e)}")
        
        # 记录异常日志
        await log_system_event(
            db=db,
            level="error",
            message=f"声音库合成异常: {str(e)}",
            module="voice_clone",
            details={
                "voice_profile_id": voice_profile_id,
                "processing_time": processing_time
            }
        )
        
        # 更新使用统计
        await update_usage_stats(db, success=False, processing_time=processing_time)
        
        raise HTTPException(status_code=500, detail=f"合成异常: {str(e)}") 