"""
TTS API模块
提供TTS试听和合成功能
"""

from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import os
import uuid
import time
import logging
from datetime import datetime

from app.database import get_db
from app.models import VoiceProfile, Character
from app.tts_client import TTSRequest, get_tts_client
from app.utils import log_system_event, update_usage_stats

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tts", tags=["TTS"])

# 音频文件存储路径
AUDIO_DIR = os.getenv("AUDIO_DIR", "data/audio")
AVATARS_DIR = os.getenv("AVATARS_DIR", "data/avatars")

@router.post("/preview")
async def tts_preview(
    text: str = Form(...),
    voice_id: str = Form(...),
    time_step: int = Form(20),
    p_weight: float = Form(1.0),
    t_weight: float = Form(1.0),
    db: Session = Depends(get_db)
):
    """
    TTS试听功能 - 智能支持角色配音库和VoiceProfile两种数据源
    根据voice_id自动判断是使用Character表还是VoiceProfile表的数据
    """
    start_time = time.time()
    tts_client = get_tts_client()
    
    try:
        # 验证输入
        if not text or len(text.strip()) == 0:
            raise HTTPException(status_code=400, detail="试听文本不能为空")
        
        if len(text) > 200:
            raise HTTPException(status_code=400, detail="试听文本长度不能超过200字符")
        
        # 🔥 分离ID空间：根据前端传递的参数类型判断数据源
        voice_config = None
        data_source = None
        
        # 检查是否为角色配音库ID（通常前端会传递额外的标识）
        # 但由于当前前端可能混用ID，我们需要智能判断
        
        # 1. 先尝试从角色配音库获取配置
        character_found = False
        try:
            character = db.query(Character).filter(
                Character.id == int(voice_id),
                Character.status.in_(['active', 'configured'])
            ).first()
            
            if character and character.is_voice_configured:
                voice_config = {
                    'id': character.id,
                    'name': character.name,
                    'reference_audio_path': character.reference_audio_path,
                    'latent_file_path': character.latent_file_path,
                    'voice_type': character.voice_type,
                    'avatar_path': character.avatar_path
                }
                data_source = 'character'
                character_found = True
                logger.info(f"🎭 [试听] 使用角色配音库数据: {character.name} (ID: {character.id})")
        except (ValueError, TypeError):
            # voice_id不是有效的整数，跳过Character查询
            pass
        
        # 2. 如果角色配音库没有找到或未配置，且不是角色ID，尝试VoiceProfile
        if not voice_config and not character_found:
            try:
                voice_profile = db.query(VoiceProfile).filter(
                    VoiceProfile.id == int(voice_id),
                    VoiceProfile.status == 'active'
                ).first()
                
                if voice_profile:
                    voice_config = {
                        'id': voice_profile.id,
                        'name': voice_profile.name,
                        'reference_audio_path': voice_profile.reference_audio_path,
                        'latent_file_path': voice_profile.latent_file_path,
                        'voice_type': voice_profile.type,
                        'avatar_path': None  # VoiceProfile没有avatar_path
                    }
                    data_source = 'voice_profile'
                    logger.info(f"🎤 [试听] 使用VoiceProfile数据: {voice_profile.name} (ID: {voice_profile.id})")
            except (ValueError, TypeError):
                pass
        elif character_found and not voice_config:
            # 角色存在但未配置声音
            raise HTTPException(status_code=400, detail=f"角色配音库中的角色'{character.name}'尚未配置声音文件，请先上传音频")
        
        # 3. 如果都没有找到，返回错误
        if not voice_config:
            raise HTTPException(status_code=404, detail=f"未找到voice_id为{voice_id}的声音配置")
        
        # 验证声音文件是否存在
        if not voice_config['reference_audio_path'] or not os.path.exists(voice_config['reference_audio_path']):
            raise HTTPException(status_code=404, detail=f"声音配置'{voice_config['name']}'的音频文件不存在")
        
        if not voice_config['latent_file_path'] or not os.path.exists(voice_config['latent_file_path']):
            raise HTTPException(status_code=404, detail=f"声音配置'{voice_config['name']}'的latent文件不存在")
        
        # 生成输出文件路径
        output_filename = f"preview_{uuid.uuid4().hex}.wav"
        output_path = os.path.join(AUDIO_DIR, output_filename)
        
        # 确保输出目录存在
        os.makedirs(AUDIO_DIR, exist_ok=True)
        
        # 构建TTS请求
        tts_request = TTSRequest(
            text=text,
            reference_audio_path=voice_config['reference_audio_path'],
            output_audio_path=output_path,
            time_step=time_step,
            p_weight=p_weight,
            t_weight=t_weight,
            latent_file_path=voice_config['latent_file_path']
        )
        
        # 调用MegaTTS3进行合成
        response = await tts_client.synthesize_speech(tts_request)
        
        processing_time = time.time() - start_time
        
        if response.success:
            # 获取生成的音频文件信息
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            
            # 获取音频时长
            try:
                from utils import get_audio_duration
                duration = get_audio_duration(output_path)
            except:
                duration = 0.0
            
            # 更新使用统计
            if data_source == 'character':
                # 更新角色配音库的使用统计
                character = db.query(Character).filter(Character.id == int(voice_id)).first()
                if character:
                    character.usage_count = (character.usage_count or 0) + 1
                    db.commit()
            elif data_source == 'voice_profile':
                # 更新VoiceProfile的使用统计
                voice_profile = db.query(VoiceProfile).filter(VoiceProfile.id == int(voice_id)).first()
                if voice_profile:
                    voice_profile.usage_count = (voice_profile.usage_count or 0) + 1
                    voice_profile.last_used = datetime.utcnow()
                    db.commit()
            
            # 记录成功日志
            await log_system_event(
                db,
                "info",
                f"TTS试听成功: {voice_config['name']} (数据源: {data_source})",
                "tts",
                {
                    "voice_id": voice_id,
                    "voice_name": voice_config['name'],
                    "data_source": data_source,
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
                "message": "试听生成完成",
                "audioUrl": f"/audio/{output_filename}",
                "processingTime": round(processing_time, 2),
                "audioId": output_filename,
                "voiceConfig": {
                    "id": voice_config['id'],
                    "name": voice_config['name'],
                    "voice_type": voice_config['voice_type'],
                    "data_source": data_source,
                    "avatar_path": voice_config['avatar_path']
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
                db,
                "error",
                f"TTS试听失败: {response.message}",
                "tts",
                {
                    "voice_id": voice_id,
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
        logger.error(f"TTS试听异常: {str(e)}")
        
        # 记录异常日志
        await log_system_event(
            db,
            "error",
            f"TTS试听异常: {str(e)}",
            "tts",
            {
                "voice_id": voice_id,
                "processing_time": processing_time
            }
        )
        
        # 更新使用统计
        await update_usage_stats(db, success=False, processing_time=processing_time)
        
        raise HTTPException(status_code=500, detail=f"试听异常: {str(e)}") 