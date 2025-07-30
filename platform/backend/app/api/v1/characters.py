"""
声音角色管理API
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Form, File, UploadFile, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, or_, and_
from typing import List, Dict, Any, Optional
import os
import json
import uuid
import csv
import io
import logging
from datetime import datetime
from uuid import uuid4

from app.database import get_db
from app.models import VoiceProfile, SystemLog, UsageStats
from app.utils import log_system_event, get_audio_duration, update_usage_stats, validate_audio_file
from app.models.character import Character
from app.schemas.character import CharacterCreate, CharacterUpdate, CharacterResponse, CharacterMatchResult
from app.services.character_service import CharacterService
from app.core.auth import get_current_user
from app.models.auth import User
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/characters", tags=["Characters"])

# 音频文件存储路径 - 智能检测环境
# 检测是否在Docker环境中（检查/.dockerenv文件是Docker的标准方式）
if os.path.exists("/.dockerenv") or os.environ.get("DOCKER_ENV") == "true":
    # Docker环境
    VOICE_PROFILES_DIR = "/app/data/voice_profiles"
    AUDIO_DIR = "/app/data/audio"
else:
    # 本地开发环境 - 使用相对于backend目录的路径
    VOICE_PROFILES_DIR = "data/voice_profiles"
    AVATARS_DIR = "data/avatars"
    AUDIO_DIR = os.getenv("AUDIO_DIR", "data/audio")

# 确保路径使用正斜杠（用于URL）
def normalize_path(path):
    """将路径标准化为使用正斜杠的格式"""
    if not path:
        return None
    # 统一使用正斜杠，并清理多余的斜杠
    normalized = path.replace('\\', '/').replace('//', '/')
    return normalized

# 检查并修复文件路径
def fix_voice_file_path(voice_profile):
    """检查并修复声音文件路径"""
    if not voice_profile.reference_audio_path:
        return None, "声音文件路径为空"
    
    # 标准化路径
    original_path = voice_profile.reference_audio_path
    normalized_path = normalize_path(original_path)
    
    # 如果是相对路径，转换为绝对路径
    if not os.path.isabs(normalized_path):
        if os.path.exists("/.dockerenv"):
            # Docker环境
            full_path = f"/app/{normalized_path}"
        else:
            # 本地环境
            full_path = normalized_path
    else:
        full_path = normalized_path
    
    # 检查文件是否存在
    if os.path.exists(full_path):
        return full_path, None
    
    # 如果文件不存在，尝试在voice_profiles目录中查找
    filename = os.path.basename(full_path)
    voice_dir = "/app/data/voice_profiles" if os.path.exists("/.dockerenv") else "data/voice_profiles"
    candidate_path = os.path.join(voice_dir, filename)
    
    if os.path.exists(candidate_path):
        return candidate_path, None
    
    # 返回错误信息，包含可用的文件列表
    available_files = []
    if os.path.exists(voice_dir):
        available_files = [f for f in os.listdir(voice_dir) if f.endswith('.wav')]
    
    error_msg = f"声音文件不存在: {filename}"
    if available_files:
        error_msg += f"\n可用的声音文件: {', '.join(available_files[:5])}"
        if len(available_files) > 5:
            error_msg += f"等共{len(available_files)}个文件"
    
    return None, error_msg

class CharacterMatchRequest(BaseModel):
    book_id: int
    chapter_id: int

class CharacterMatchResponse(BaseModel):
    matched_characters: List[CharacterMatchResult]
    unmatched_characters: List[dict]
    total_count: int
    matched_count: int

class ApplyMatchesRequest(BaseModel):
    matches: List[dict]

class CharacterSyncRequest(BaseModel):
    book_id: int
    chapter_id: int

@router.get("")
async def get_characters(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query("", description="搜索关键词"),
    voice_type: str = Query("", description="声音类型过滤"),
    quality_min: float = Query(0, ge=0, le=5, description="最低质量分"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    tags: str = Query("", description="标签过滤(逗号分隔)"),
    status: str = Query("", description="状态过滤"),
    book_id: int = Query(None, description="书籍ID筛选"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取角色列表"""
    try:
        # 统一使用角色查询
        query = db.query(Character)
        
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
        
        # 标签过滤
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            for tag in tag_list:
                query = query.filter(Character.tags.like(f'%"{tag}"%'))
        
        # 排序
        sort_field = getattr(Character, sort_by, Character.created_at)
        if sort_order == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))
        
        # 统计总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        characters = query.offset(offset).limit(page_size).all()
        
        # 转换为字典格式
        character_list = []
        for character in characters:
            character_data = character.to_dict()
            character_list.append(character_data)
        
        # 🔥 修复：计算基于当前过滤条件的统计信息
        base_query = db.query(Character)
        
        # 应用相同的过滤条件
        if search:
            search_pattern = f"%{search}%"
            base_query = base_query.filter(
                or_(
                    Character.name.like(search_pattern),
                    Character.description.like(search_pattern)
                )
            )
        if voice_type and voice_type in ['male', 'female', 'child', 'elder', 'custom']:
            base_query = base_query.filter(Character.voice_type == voice_type)
        if quality_min > 0:
            base_query = base_query.filter(Character.quality_score >= quality_min)
        if book_id:
            base_query = base_query.filter(Character.book_id == book_id)
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            for tag in tag_list:
                base_query = base_query.filter(Character.tags.like(f'%"{tag}"%'))
        
        stats = {
            'total_count': total,
            'configured_count': base_query.filter(Character.status == 'configured').count(),
            'unconfigured_count': base_query.filter(Character.status == 'unconfigured').count(),
            'average_quality': base_query.with_entities(func.avg(Character.quality_score)).scalar() or 0
        }
        
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
                "tags": tags
            }
        }
        
    except Exception as e:
        logger.error(f"获取角色列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取角色列表失败: {str(e)}"
        )

@router.get("/statistics")
async def get_voice_statistics(
    db: Session = Depends(get_db)
):
    """获取声音库统计信息"""
    try:
        # 基础统计
        total_voices = db.query(func.count(VoiceProfile.id)).filter(VoiceProfile.status == 'active').scalar()
        
        # 按类型分组统计
        type_stats = db.query(
            VoiceProfile.type,
            func.count(VoiceProfile.id).label('count'),
            func.avg(VoiceProfile.quality_score).label('avg_quality')
        ).filter(VoiceProfile.status == 'active').group_by(VoiceProfile.type).all()
        
        return {
            "success": True,
            "data": {
                "total": total_voices,
                "by_type": [{"type": t.type, "count": t.count, "avg_quality": round(t.avg_quality or 0, 2)} for t in type_stats]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")

@router.get("/check-exists")
async def check_character_exists(
    name: str = Query(..., description="角色名称"),
    db: Session = Depends(get_db)
):
    """
    检查角色是否已存在于角色库中
    用于智能角色发现功能，避免重复创建角色
    """
    try:
        existing_character = db.query(Character).filter(
            Character.name == name
        ).first()
        
        if existing_character:
            return {
                "success": True,
                "data": {
                    "exists": True,
                    "config": {
                        "id": existing_character.id,
                        "name": existing_character.name,
                        "voice_type": existing_character.voice_type,
                        "description": existing_character.description,
                        "usage_count": existing_character.usage_count,
                        "quality_score": existing_character.quality_score,
                        "color": existing_character.color,
                        "status": existing_character.status,
                        "created_at": existing_character.created_at.isoformat() if existing_character.created_at else None,
                        "reference_audio_url": existing_character.reference_audio_path,
                        "latent_file_url": existing_character.latent_file_path
                    }
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "exists": False,
                    "message": f"角色 '{name}' 不存在于角色库中"
                }
            }
            
    except Exception as e:
        logger.error(f"检查角色存在性失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"检查失败: {str(e)}")

@router.get("/{character_id}")
async def get_character_detail(
    character_id: int,
    db: Session = Depends(get_db)
):
    """获取角色详情"""
    try:
        character = db.query(Character).filter(Character.id == character_id).first()
        if not character:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        character_data = character.to_dict()
        
        # 强制修正字段名，确保返回正确的URL格式（如果to_dict()没有正确工作）
        if 'reference_audio_path' in character_data:
            # 将原始路径转换为URL
            if character_data['reference_audio_path']:
                filename = os.path.basename(character_data['reference_audio_path'])
                # 临时修复：如果是test角色且文件不存在，使用实际存在的文件
                if character.name == 'test' and not os.path.exists(f"data/voice_profiles/{filename}"):
                    filename = "test_abf44e80bb084a3d984d8072907ae6dc.wav"
                character_data['referenceAudioUrl'] = f"/voice_profiles/{filename}"
            del character_data['reference_audio_path']
        
        if 'latent_file_path' in character_data:
            if character_data['latent_file_path']:
                filename = os.path.basename(character_data['latent_file_path'])
                character_data['latentFileUrl'] = f"/voice_profiles/{filename}"
            del character_data['latent_file_path']
        
        if 'sample_audio_path' in character_data:
            if character_data['sample_audio_path']:
                filename = os.path.basename(character_data['sample_audio_path'])
                character_data['sampleAudioUrl'] = f"/voice_profiles/{filename}"
            del character_data['sample_audio_path']
        
        # 添加音频时长信息
        if character.reference_audio_path and os.path.exists(character.reference_audio_path):
            try:
                duration = get_audio_duration(character.reference_audio_path)
                character_data['audioDuration'] = duration
            except:
                pass
        
        return {
            "success": True,
            "data": character_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取详情失败: {str(e)}")

@router.post("")
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
    """创建新的声音档案"""
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
            print(f"[DEBUG] 收到音频文件: {reference_audio.filename}, 内容类型: {reference_audio.content_type}")
            
            # 验证音频文件
            if not reference_audio.content_type or not reference_audio.content_type.startswith('audio/'):
                raise HTTPException(status_code=400, detail="参考音频必须是音频文件格式")
            
            # 保存参考音频文件
            audio_content = await reference_audio.read()
            print(f"[DEBUG] 音频文件大小: {len(audio_content)} bytes")
            
            if len(audio_content) > 100 * 1024 * 1024:  # 100MB限制
                raise HTTPException(status_code=400, detail="音频文件大小不能超过100MB")
            
            # 生成文件路径
            file_ext = os.path.splitext(reference_audio.filename)[1].lower()
            if file_ext not in ['.wav', '.mp3', '.flac', '.m4a', '.ogg']:
                raise HTTPException(status_code=400, detail="不支持的音频格式")
            
            profile_ref_filename = f"{name}_{uuid.uuid4().hex}{file_ext}"
            profile_ref_path = os.path.join(VOICE_PROFILES_DIR, profile_ref_filename)
            
            print(f"[DEBUG] 准备保存到: {profile_ref_path}")
            print(f"[DEBUG] VOICE_PROFILES_DIR: {VOICE_PROFILES_DIR}")
            
            # 确保目录存在
            os.makedirs(VOICE_PROFILES_DIR, exist_ok=True)
            print(f"[DEBUG] 目录创建成功: {VOICE_PROFILES_DIR}")
            
            # 保存参考音频文件
            with open(profile_ref_path, 'wb') as f:
                f.write(audio_content)
            
            print(f"[DEBUG] 文件保存成功: {profile_ref_path}")
            print(f"[DEBUG] 文件是否存在: {os.path.exists(profile_ref_path)}")
        else:
            print(f"[DEBUG] 未收到音频文件，reference_audio: {reference_audio}")
            profile_ref_path = None
        
        # 处理latent文件（可选）
        latent_file_path = None
        if latent_file and latent_file.filename:
            if not latent_file.filename.endswith('.npy'):
                raise HTTPException(status_code=400, detail="Latent文件必须是.npy格式")
            
            latent_content = await latent_file.read()
            if len(latent_content) > 50 * 1024 * 1024:  # 50MB限制
                raise HTTPException(status_code=400, detail="Latent文件大小不能超过50MB")
            
            latent_filename = f"{name}_{uuid.uuid4().hex}.npy"
            latent_file_path = os.path.join(VOICE_PROFILES_DIR, latent_filename)
            
            with open(latent_file_path, 'wb') as f:
                f.write(latent_content)
        
        # 解析参数
        try:
            params = json.loads(parameters) if parameters else {}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="参数格式错误")
        
        # 创建声音档案
        voice_profile = VoiceProfile(
            name=name,
            description=description,
            type=voice_type,
            reference_audio_path=normalize_path(profile_ref_path),
            latent_file_path=normalize_path(latent_file_path),
            tags=tags,
            color=color,
            parameters=json.dumps(params),
            status='active',
            quality_score=3.0,  # 默认质量分
            usage_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(voice_profile)
        db.commit()
        db.refresh(voice_profile)
        
        # 记录系统日志
        await log_system_event(
            db=db,
            level="info",
            message=f"创建声音档案: {name}",
            module="characters",
            details={"voice_id": voice_profile.id}
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

@router.post("/character")
async def create_character_with_voice(
    name: str = Form(...),
    description: str = Form(""),
    voice_type: str = Form(...),
    book_id: int = Form(None),
    avatar: UploadFile = File(None),
    reference_audio: UploadFile = File(None),
    latent_file: UploadFile = File(None),
    tags: str = Form(""),
    color: str = Form("#8b5cf6"),
    parameters: str = Form("{}"),
    db: Session = Depends(get_db)
):
    """创建带声音配置的角色"""
    try:
        # 验证输入
        if not name or len(name.strip()) == 0:
            raise HTTPException(status_code=400, detail="角色名称不能为空")
        
        if voice_type not in ['male', 'female', 'child', 'elder', 'custom']:
            raise HTTPException(status_code=400, detail="声音类型必须是 male、female、child、elder 或 custom")
        
        # 检查名称是否已存在（在同一本书中）
        query = db.query(Character).filter(Character.name == name)
        if book_id:
            query = query.filter(Character.book_id == book_id)
        existing_character = query.first()
        
        if existing_character:
            raise HTTPException(status_code=400, detail="角色名称已存在")
        
        # 验证书籍是否存在
        if book_id:
            from app.models.book import Book
            book = db.query(Book).filter(Book.id == book_id).first()
            if not book:
                raise HTTPException(status_code=400, detail="所选书籍不存在")
        
        # 处理头像文件
        avatar_path = None
        if avatar and avatar.filename:
            if not avatar.content_type or not avatar.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="头像必须是图片文件格式")
            
            avatar_content = await avatar.read()
            if len(avatar_content) > 10 * 1024 * 1024:  # 10MB限制
                raise HTTPException(status_code=400, detail="头像文件大小不能超过10MB")
            
            file_ext = os.path.splitext(avatar.filename)[1].lower()
            if file_ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                raise HTTPException(status_code=400, detail="不支持的图片格式，支持jpg、png、gif、webp")
            
            avatar_filename = f"{name}_{uuid.uuid4().hex}{file_ext}"
            avatar_path = os.path.join(AVATARS_DIR, avatar_filename)
            
            os.makedirs(AVATARS_DIR, exist_ok=True)
            with open(avatar_path, 'wb') as f:
                f.write(avatar_content)
        
        # 处理参考音频文件
        ref_audio_path = None
        if reference_audio and reference_audio.filename:
            if not reference_audio.content_type or not reference_audio.content_type.startswith('audio/'):
                raise HTTPException(status_code=400, detail="参考音频必须是音频文件格式")
            
            audio_content = await reference_audio.read()
            if len(audio_content) > 100 * 1024 * 1024:  # 100MB限制
                raise HTTPException(status_code=400, detail="音频文件大小不能超过100MB")
            
            file_ext = os.path.splitext(reference_audio.filename)[1].lower()
            if file_ext not in ['.wav', '.mp3', '.flac', '.m4a', '.ogg']:
                raise HTTPException(status_code=400, detail="不支持的音频格式")
            
            ref_filename = f"{name}_{uuid.uuid4().hex}{file_ext}"
            ref_audio_path = os.path.join(VOICE_PROFILES_DIR, ref_filename)
            
            os.makedirs(VOICE_PROFILES_DIR, exist_ok=True)
            with open(ref_audio_path, 'wb') as f:
                f.write(audio_content)
        
        # 处理latent文件
        latent_path = None
        if latent_file and latent_file.filename:
            if not latent_file.filename.endswith('.npy'):
                raise HTTPException(status_code=400, detail="Latent文件必须是.npy格式")
            
            latent_content = await latent_file.read()
            if len(latent_content) > 50 * 1024 * 1024:  # 50MB限制
                raise HTTPException(status_code=400, detail="Latent文件大小不能超过50MB")
            
            latent_filename = f"{name}_{uuid.uuid4().hex}.npy"
            latent_path = os.path.join(VOICE_PROFILES_DIR, latent_filename)
            
            with open(latent_path, 'wb') as f:
                f.write(latent_content)
        
        # 解析参数
        try:
            params = json.loads(parameters) if parameters else {}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="参数格式错误")
        
        # 解析标签
        try:
            tag_list = json.loads(tags) if tags else []
        except json.JSONDecodeError:
            tag_list = []
        
        # 创建角色
        character = Character(
            name=name,
            description=description,
            book_id=book_id,
            voice_type=voice_type,
            color=color,
            avatar_path=normalize_path(avatar_path),
            reference_audio_path=normalize_path(ref_audio_path),
            latent_file_path=normalize_path(latent_path),
            voice_parameters=json.dumps(params),
            tags=json.dumps(tag_list),
            status='configured' if ref_audio_path else 'unconfigured',
            quality_score=3.0,
            usage_count=0
        )
        
        db.add(character)
        db.commit()
        db.refresh(character)
        
        # 记录日志
        await log_system_event(
            db=db,
            level="info",
            message=f"创建角色: {name}",
            module="characters",
            details={"character_id": character.id, "book_id": book_id}
        )
        
        return {
            "success": True,
            "message": "角色创建成功",
            "data": character.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")

@router.put("/character/{character_id}")
async def update_character_with_voice(
    character_id: int,
    name: str = Form(...),
    description: str = Form(""),
    voice_type: str = Form(...),
    book_id: int = Form(None),
    avatar: UploadFile = File(None),
    reference_audio: UploadFile = File(None),
    latent_file: UploadFile = File(None),
    tags: str = Form(""),
    color: str = Form("#8b5cf6"),
    parameters: str = Form("{}"),
    db: Session = Depends(get_db)
):
    """更新角色和声音配置"""
    try:
        character = db.query(Character).filter(Character.id == character_id).first()
        if not character:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        # 验证输入
        if not name or len(name.strip()) == 0:
            raise HTTPException(status_code=400, detail="角色名称不能为空")
        
        if voice_type not in ['male', 'female', 'child', 'elder', 'custom']:
            raise HTTPException(status_code=400, detail="声音类型必须是 male、female、child、elder 或 custom")
        
        # 检查名称冲突
        query = db.query(Character).filter(
            Character.name == name,
            Character.id != character_id
        )
        if book_id:
            query = query.filter(Character.book_id == book_id)
        existing_character = query.first()
        
        if existing_character:
            raise HTTPException(status_code=400, detail="角色名称已存在")
        
        # 验证书籍
        if book_id:
            from app.models.book import Book
            book = db.query(Book).filter(Book.id == book_id).first()
            if not book:
                raise HTTPException(status_code=400, detail="所选书籍不存在")
        
        # 处理新的头像文件
        if avatar and avatar.filename:
            # 删除旧头像文件
            if character.avatar_path and os.path.exists(character.avatar_path):
                try:
                    os.remove(character.avatar_path)
                except:
                    pass
            
            # 保存新头像文件
            if not avatar.content_type or not avatar.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="头像必须是图片文件格式")
            
            avatar_content = await avatar.read()
            if len(avatar_content) > 10 * 1024 * 1024:  # 10MB限制
                raise HTTPException(status_code=400, detail="头像文件大小不能超过10MB")
            
            file_ext = os.path.splitext(avatar.filename)[1].lower()
            if file_ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                raise HTTPException(status_code=400, detail="不支持的图片格式，支持jpg、png、gif、webp")
            
            avatar_filename = f"{name}_{uuid.uuid4().hex}{file_ext}"
            avatar_path = os.path.join(AVATARS_DIR, avatar_filename)
            
            os.makedirs(AVATARS_DIR, exist_ok=True)
            with open(avatar_path, 'wb') as f:
                f.write(avatar_content)
            
            character.avatar_path = normalize_path(avatar_path)
        
        # 处理新的音频文件
        if reference_audio and reference_audio.filename:
            # 删除旧文件
            if character.reference_audio_path and os.path.exists(character.reference_audio_path):
                try:
                    os.remove(character.reference_audio_path)
                except:
                    pass
            
            # 保存新文件
            audio_content = await reference_audio.read()
            if len(audio_content) > 100 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="音频文件大小不能超过100MB")
            
            file_ext = os.path.splitext(reference_audio.filename)[1].lower()
            if file_ext not in ['.wav', '.mp3', '.flac', '.m4a', '.ogg']:
                raise HTTPException(status_code=400, detail="不支持的音频格式")
            
            ref_filename = f"{name}_{uuid.uuid4().hex}{file_ext}"
            ref_audio_path = os.path.join(VOICE_PROFILES_DIR, ref_filename)
            
            os.makedirs(VOICE_PROFILES_DIR, exist_ok=True)
            with open(ref_audio_path, 'wb') as f:
                f.write(audio_content)
            
            character.reference_audio_path = normalize_path(ref_audio_path)
        
        # 处理新的latent文件
        if latent_file and latent_file.filename:
            # 删除旧文件
            if character.latent_file_path and os.path.exists(character.latent_file_path):
                try:
                    os.remove(character.latent_file_path)
                except:
                    pass
            
            latent_content = await latent_file.read()
            if len(latent_content) > 50 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Latent文件大小不能超过50MB")
            
            if not latent_file.filename.endswith('.npy'):
                raise HTTPException(status_code=400, detail="Latent文件必须是.npy格式")
            
            latent_filename = f"{name}_{uuid.uuid4().hex}.npy"
            latent_path = os.path.join(VOICE_PROFILES_DIR, latent_filename)
            
            with open(latent_path, 'wb') as f:
                f.write(latent_content)
            
            character.latent_file_path = normalize_path(latent_path)
        
        # 解析参数和标签
        try:
            params = json.loads(parameters) if parameters else {}
            tag_list = json.loads(tags) if tags else []
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="参数或标签格式错误")
        
        # 更新角色信息
        character.name = name
        character.description = description
        character.book_id = book_id
        character.voice_type = voice_type
        character.color = color
        character.voice_parameters = json.dumps(params)
        character.tags = json.dumps(tag_list)
        
        # 更新状态
        if character.reference_audio_path:
            character.status = 'configured'
        
        character.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(character)
        
        # 记录日志
        await log_system_event(
            db=db,
            level="info",
            message=f"更新角色: {name}",
            module="characters",
            details={"character_id": character_id, "book_id": book_id}
        )
        
        return {
            "success": True,
            "message": "角色更新成功",
            "data": character.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

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
    """更新声音档案"""
    try:
        voice = db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
        if not voice:
            raise HTTPException(status_code=404, detail="声音档案不存在")
        
        # 验证输入
        if not name or len(name.strip()) == 0:
            raise HTTPException(status_code=400, detail="声音名称不能为空")
        
        if voice_type not in ['male', 'female', 'child']:
            raise HTTPException(status_code=400, detail="声音类型必须是 male、female 或 child")
        
        # 检查名称是否与其他档案冲突
        existing_voice = db.query(VoiceProfile).filter(
            VoiceProfile.name == name,
            VoiceProfile.id != voice_id
        ).first()
        if existing_voice:
            raise HTTPException(status_code=400, detail="声音名称已存在")
        
        # 处理新的参考音频文件
        if reference_audio and reference_audio.filename:
            # 删除旧文件
            if voice.reference_audio_path and os.path.exists(voice.reference_audio_path):
                try:
                    os.remove(voice.reference_audio_path)
                except:
                    pass
            
            # 保存新文件
            audio_content = await reference_audio.read()
            if len(audio_content) > 100 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="音频文件大小不能超过100MB")
            
            file_ext = os.path.splitext(reference_audio.filename)[1].lower()
            if file_ext not in ['.wav', '.mp3', '.flac', '.m4a', '.ogg']:
                raise HTTPException(status_code=400, detail="不支持的音频格式")
            
            profile_ref_filename = f"{name}_{uuid.uuid4().hex}{file_ext}"
            profile_ref_path = os.path.join(VOICE_PROFILES_DIR, profile_ref_filename)
            
            os.makedirs(VOICE_PROFILES_DIR, exist_ok=True)
            
            with open(profile_ref_path, 'wb') as f:
                f.write(audio_content)
            
            voice.reference_audio_path = profile_ref_path
        
        # 处理新的latent文件
        if latent_file and latent_file.filename:
            # 删除旧文件
            if voice.latent_file_path and os.path.exists(voice.latent_file_path):
                try:
                    os.remove(voice.latent_file_path)
                except:
                    pass
            
            # 保存新文件
            latent_content = await latent_file.read()
            if len(latent_content) > 50 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Latent文件大小不能超过50MB")
            
            latent_filename = f"{name}_{uuid.uuid4().hex}.npy"
            latent_file_path = os.path.join(VOICE_PROFILES_DIR, latent_filename)
            
            with open(latent_file_path, 'wb') as f:
                f.write(latent_content)
            
            voice.latent_file_path = latent_file_path
        
        # 解析参数
        try:
            params = json.loads(parameters) if parameters else {}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="参数格式错误")
        
        # 更新字段
        voice.name = name
        voice.description = description
        voice.type = voice_type
        voice.tags = tags
        voice.color = color
        voice.parameters = json.dumps(params)
        voice.updated_at = datetime.utcnow()
        
        db.commit()
        
        # 记录系统日志
        await log_system_event(
            db=db,
            level="info",
            message=f"更新声音档案: {name}",
            module="characters",
            details={"voice_id": voice_id}
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
async def delete_character(
    voice_id: int,
    force: bool = Query(False, description="强制删除"),
    db: Session = Depends(get_db)
):
    """删除角色"""
    try:
        # 使用Character模型而不是VoiceProfile
        character = db.query(Character).filter(Character.id == voice_id).first()
        if not character:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        # 检查是否正在使用
        if not force and character.usage_count and character.usage_count > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"角色正在使用中(使用次数: {character.usage_count})，请使用强制删除"
            )
        
        # 删除关联文件
        files_to_delete = [
            character.reference_audio_path,
            character.latent_file_path
        ]
        
        for file_path in files_to_delete:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"成功删除文件: {file_path}")
                except Exception as e:
                    logger.warning(f"删除文件失败: {file_path}, {str(e)}")
        
        # 删除数据库记录
        character_name = character.name
        db.delete(character)
        db.commit()
        
        # 记录系统日志
        await log_system_event(
            db=db,
            level="info",
            message=f"删除角色: {character_name}",
            module="characters",
            details={"voice_id": voice_id, "force": force}  # 🔥 修复：正确使用voice_id而不是character_id
        )
        
        return {
            "success": True,
            "message": "角色删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@router.post("/{voice_id}/test")
async def test_voice_synthesis(
    voice_id: int,
    request: Request,
    text: str = Form("你好，这是声音测试。"),
    time_step: int = Form(32),
    p_weight: float = Form(1.4),
    t_weight: float = Form(3.0),
    db: Session = Depends(get_db)
):
    """测试声音合成 - 智能支持角色配音库和VoiceProfile两种数据源"""
    try:
        # 🔥 修复：优先查询角色配音库，回退到VoiceProfile
        voice_config = None
        data_source = None
        
        logger.info(f"🔍 [试听] 开始查找voice_id={voice_id}的配置")
        
        # 1. 优先从角色配音库获取配置
        character = db.query(Character).filter(
            Character.id == voice_id,
            Character.status.in_(['active', 'configured'])
        ).first()
        
        if character:
            logger.info(f"🎭 [试听] 在角色配音库中找到: {character.name} (ID: {character.id}, 状态: {character.status})")
            voice_config = {
                'id': character.id,
                'name': character.name,
                'reference_audio_path': character.reference_audio_path,
                'latent_file_path': character.latent_file_path,
                'voice_type': character.voice_type
            }
            data_source = 'character'
        else:
            logger.info(f"🎭 [试听] 在角色配音库中未找到voice_id={voice_id}的配置")
        
        # 2. 如果角色配音库没有找到或未配置，尝试VoiceProfile
        if not voice_config:
            voice_profile = db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
            if voice_profile:
                logger.info(f"🎤 [试听] 在VoiceProfile中找到: {voice_profile.name} (ID: {voice_profile.id}, 类型: {voice_profile.type})")
                voice_config = {
                    'id': voice_profile.id,
                    'name': voice_profile.name,
                    'reference_audio_path': voice_profile.reference_audio_path,
                    'latent_file_path': voice_profile.latent_file_path,
                    'voice_type': voice_profile.type
                }
                data_source = 'voice_profile'
            else:
                logger.info(f"🎤 [试听] 在VoiceProfile中也未找到voice_id={voice_id}的配置")
        
        # 3. 如果都没有找到，返回错误
        if not voice_config:
            raise HTTPException(status_code=404, detail=f"未找到ID为{voice_id}的声音配置")
        
        # 验证声音文件
        if not voice_config['reference_audio_path']:
            raise HTTPException(status_code=400, detail="声音文件路径为空，请重新上传")
        
        # 检查并修复音频文件路径（兼容两种数据源）
        if data_source == 'character':
            # Character的路径已经是标准化的
            fixed_audio_path = voice_config['reference_audio_path']
            if not os.path.exists(fixed_audio_path):
                raise HTTPException(status_code=400, detail=f"声音文件不存在: {fixed_audio_path}")
        else:
            # VoiceProfile使用原有的修复逻辑
            fixed_audio_path, error_msg = fix_voice_file_path(voice_profile)
            if not fixed_audio_path:
                raise HTTPException(status_code=400, detail=error_msg or "声音文件不存在，请重新上传")
        
        # 生成唯一的音频文件名
        audio_id = f"test_{voice_id}_{uuid4().hex[:32]}"
        output_path = os.path.join(AUDIO_DIR, f"{audio_id}.wav")
        
        # 确保音频输出目录存在
        os.makedirs(AUDIO_DIR, exist_ok=True)
        
        # 调用真实的TTS服务进行合成
        from app.tts_client import get_tts_client, TTSRequest
        
        # 获取TTS客户端
        tts_client = get_tts_client()
        
        # 修复latent文件路径
        latent_path = None
        if voice_config['latent_file_path']:
            latent_normalized = normalize_path(voice_config['latent_file_path'])
            if not os.path.isabs(latent_normalized):
                if os.path.exists("/.dockerenv"):
                    latent_path = f"/app/{latent_normalized}"
                else:
                    latent_path = latent_normalized
            else:
                latent_path = latent_normalized
        
        # 调试日志：确认文件路径
        logger.info(f"🎭 [TTS Test] 声音配置: {voice_config['name']} ({data_source})")
        logger.info(f"🎭 [TTS Test] 原始参考音频: {voice_config['reference_audio_path']}")
        logger.info(f"🎭 [TTS Test] 修复后参考音频: {fixed_audio_path}")
        logger.info(f"🎭 [TTS Test] Latent文件: {latent_path}")
        logger.info(f"🎭 [TTS Test] 输出路径: {output_path}")
        
        # 🔥 重要：验证音频文件是否真的存在
        if os.path.exists(fixed_audio_path):
            file_size = os.path.getsize(fixed_audio_path)
            logger.info(f"🎭 [TTS Test] ✅ 音频文件存在，大小: {file_size} 字节")
        else:
            logger.error(f"🎭 [TTS Test] ❌ 音频文件不存在: {fixed_audio_path}")
            
        # 🔥 重要：记录最终使用的配置
        logger.info(f"🎭 [TTS Test] 最终使用配置: 数据源={data_source}, 角色名={voice_config['name']}, 声音类型={voice_config['voice_type']}")
        
        # 创建TTS请求
        tts_request = TTSRequest(
            text=text,
            reference_audio_path=fixed_audio_path,
            output_audio_path=output_path,
            time_step=time_step,
            p_weight=p_weight,
            t_weight=t_weight,
            latent_file_path=latent_path  # 使用修复后的latent文件路径
        )
        
        # 执行TTS合成
        response = await tts_client.synthesize_speech(tts_request)
        
        if not response.success:
            raise HTTPException(status_code=500, detail=f"TTS合成失败: {response.message}")
        
        # 记录系统日志
        try:
            await log_system_event(
                db=db,
                level="info",
                message=f"声音测试成功: {voice_config['name']} ({data_source})",
                module="characters",
                details={
                    "voice_id": voice_id,
                    "data_source": data_source,
                    "text": text,
                    "processing_time": response.processing_time
                }
            )
        except Exception as log_error:
            logger.warning(f"记录日志失败: {str(log_error)}")
        
        # 动态生成音频URL，支持外网访问
        host = request.headers.get("host", "localhost:8000")
        scheme = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"
        audio_url = f"{scheme}://{host}/api/v1/audio/{audio_id}.wav"
        
        return {
            "success": True,
            "message": "测试合成完成",
            "audioUrl": audio_url,
            "processingTime": response.processing_time,
            "audioId": f"{audio_id}.wav"
        }
        
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
    """重新评估声音质量"""
    try:
        voice = db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
        
        if not voice:
            raise HTTPException(status_code=404, detail="声音档案不存在")
        
        old_quality = voice.quality_score
        quality_score = voice.quality_score
        
        # 如果有样本音频，重新评估
        if voice.reference_audio_path and os.path.exists(voice.reference_audio_path):
            # 简化质量评估 - 基于文件大小
            file_size = os.path.getsize(voice.reference_audio_path)
            if file_size > 50000:  # 50KB以上
                quality_score = 3.0
            if file_size > 100000:  # 100KB以上
                quality_score = 3.5
            if file_size > 200000:  # 200KB以上
                quality_score = 4.0
            
            # 更新质量分
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
    """批量操作声音档案"""
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
                        getattr(voice, 'sample_audio_path', None)
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
                    current_tags = voice.get_tags() if hasattr(voice, 'get_tags') else []
                    
                    if action == "replace":
                        final_tags = new_tags
                    elif action == "add":
                        final_tags = list(set(current_tags + new_tags))
                    elif action == "remove":
                        final_tags = [tag for tag in current_tags if tag not in new_tags]
                    else:
                        final_tags = current_tags
                    
                    # 设置标签
                    voice.tags = ','.join(final_tags) if final_tags else ''
                    voice.updated_at = datetime.utcnow()
                    
                    results.append({
                        "id": voice.id,
                        "name": voice.name,
                        "success": True,
                        "tags": final_tags
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
    """导出声音库列表"""
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
    """获取热门标签列表"""
    try:
        # 获取所有活跃声音的标签
        voices = db.query(VoiceProfile).filter(VoiceProfile.status == 'active').all()
        
        tag_count = {}
        for voice in voices:
            # 解析标签字符串
            tags = []
            if voice.tags:
                try:
                    # 支持逗号分隔的标签
                    tags = [tag.strip() for tag in voice.tags.split(',') if tag.strip()]
                except:
                    pass
            
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

@router.get("/search-similar")
async def search_similar_characters(
    name: str = Query(..., description="角色名称"),
    threshold: float = Query(0.7, description="相似度阈值"),
    db: Session = Depends(get_db)
):
    """
    搜索相似的角色名称
    用于智能角色发现，提示可能的重复角色
    """
    try:
        # 获取所有角色名称
        all_characters = db.query(VoiceProfile.name).all()
        character_names = [char.name for char in all_characters]
        
        # 简单的相似度计算（可以后续优化为更复杂的算法）
        similar_characters = []
        
        for existing_name in character_names:
            # 计算简单的字符串相似度
            similarity = calculate_similarity(name, existing_name)
            
            if similarity >= threshold and name != existing_name:
                similar_characters.append({
                    "name": existing_name,
                    "similarity": similarity
                })
        
        # 按相似度排序
        similar_characters.sort(key=lambda x: x['similarity'], reverse=True)
        
        return {
            "success": True,
            "query_name": name,
            "similar_characters": similar_characters[:5],  # 最多返回5个相似角色
            "message": f"找到 {len(similar_characters)} 个相似角色"
        }
        
    except Exception as e:
        logger.error(f"搜索相似角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.post("/match", response_model=CharacterMatchResponse)
async def match_characters(
    request: CharacterMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    根据书籍和章节匹配角色配置
    """
    try:
        character_service = CharacterService(db)
        result = character_service.match_characters_by_chapter(
            request.book_id, 
            request.chapter_id
        )
        
        return CharacterMatchResponse(
            matched_characters=result['matched'],
            unmatched_characters=result['unmatched'],
            total_count=result['total_count'],
            matched_count=result['matched_count']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匹配失败: {str(e)}")

@router.post("/apply-matches")
async def apply_matches(
    request: ApplyMatchesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    应用匹配结果
    """
    try:
        character_service = CharacterService(db)
        result = character_service.apply_character_matches(request.matches)
        
        return {
            "success": True,
            "applied_count": result['applied_count'],
            "message": f"成功应用 {result['applied_count']} 个角色配置"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"应用匹配失败: {str(e)}")

@router.post("/sync")
async def sync_characters(
    request: CharacterSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    同步角色记录与分析结果
    """
    try:
        character_service = CharacterService(db)
        result = character_service.sync_characters_with_analysis(
            request.book_id,
            request.chapter_id
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")

@router.post("/create-character")
async def create_character(
    name: str = Form(..., description="角色名称"),
    description: str = Form("", description="角色描述"),
    book_id: int = Form(..., description="所属书籍ID"),
    chapter_id: int = Form(None, description="首次出现章节ID"),
    voice_profile: str = Form("", description="语音配置"),
    voice_config: str = Form("{}", description="语音参数配置"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """创建新角色"""
    try:
        # 检查角色名称是否已存在于同一本书中
        existing = db.query(Character).filter(
            Character.name == name,
            Character.book_id == book_id
        ).first()
        
        if existing:
            return {
                "success": False,
                "message": f"角色'{name}'在该书籍中已存在"
            }
        
        # 验证书籍是否存在
        from app.models.book import Book
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            return {
                "success": False,
                "message": f"书籍ID {book_id} 不存在"
            }
        
        # 创建新角色
        new_character = Character(
            name=name,
            description=description,
            book_id=book_id,
            chapter_id=chapter_id,
            voice_profile=voice_profile,
            voice_config=voice_config
        )
        
        db.add(new_character)
        db.commit()
        db.refresh(new_character)
        
        logger.info(f"角色创建成功: {name} (书籍: {book.title})")
        
        return {
            "success": True,
            "message": f"角色'{name}'创建成功",
            "data": {
                "id": new_character.id,
                "name": new_character.name,
                "book_id": new_character.book_id,
                "book_title": book.title
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建角色失败: {str(e)}")
        return {
            "success": False,
            "message": f"创建角色失败: {str(e)}"
        }

@router.post("/batch-create-characters")
async def batch_create_characters(
    # 🔥 新增：文件上传支持
    request: Request,
    characters_data: str = Form(..., description="角色数据JSON"),
    book_id: int = Form(..., description="所属书籍ID"),
    chapter_id: int = Form(None, description="章节ID"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """批量创建角色（用于智能分析后）"""
    try:
        # 🔥 新增：处理文件上传
        form_data = await request.form()
        files_map = {}
        
        # 提取所有文件字段
        for key, value in form_data.items():
            if key.startswith('characters[') and (key.endswith('.wav_file') or key.endswith('.npy_file')):
                # 解析字段名格式：characters[0].wav_file
                try:
                    import re
                    match = re.match(r'characters\[(\d+)\]\.(wav_file|npy_file)', key)
                    if match:
                        char_index = int(match.group(1))
                        file_type = match.group(2)
                        
                        if char_index not in files_map:
                            files_map[char_index] = {}
                        files_map[char_index][file_type] = value
                        
                        logger.info(f"📁 检测到文件上传: 角色索引{char_index}, 类型{file_type}, 文件名: {value.filename}")
                except Exception as e:
                    logger.warning(f"解析文件字段失败: {key}, 错误: {e}")
        
        logger.info(f"📁 文件映射表: {list(files_map.keys())}")
        
        # 解析角色数据
        import json
        characters = json.loads(characters_data)
        
        # 验证书籍是否存在
        from app.models.book import Book
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            return {
                "success": False,
                "message": f"书籍ID {book_id} 不存在"
            }
        
        created_characters = []
        skipped_characters = []
        
        for char_index, char_data in enumerate(characters):
            name = char_data.get('name', '').strip()
            if not name:
                continue
                
            # 检查是否已存在
            existing = db.query(Character).filter(
                Character.name == name,
                Character.book_id == book_id
            ).first()
            
            # 🔥 新增：如果角色已存在，检查是否需要更新音频文件
            if existing:
                # 如果角色已存在且已有音频文件，跳过
                if existing.reference_audio_path:
                    skipped_characters.append({
                        "name": name,
                        "reason": "已存在且已配置音频"
                    })
                    continue
                
                # 如果角色已存在但没有音频文件，且用户上传了音频文件，则更新
                should_update = False
                ref_audio_path = None
                latent_file_path = None
                
                if char_index in files_map:
                    character_files = files_map[char_index]
                    
                    # 处理WAV文件
                    if 'wav_file' in character_files:
                        wav_file = character_files['wav_file']
                        if wav_file and wav_file.filename:
                            logger.info(f"📁 更新角色 {name} 的WAV文件: {wav_file.filename}")
                            
                            # 验证文件格式
                            file_ext = os.path.splitext(wav_file.filename)[1].lower()
                            if file_ext in ['.wav', '.mp3', '.flac', '.m4a', '.ogg']:
                                # 保存WAV文件
                                audio_content = await wav_file.read()
                                if len(audio_content) <= 100 * 1024 * 1024:  # 100MB限制
                                    ref_filename = f"{name}_{uuid.uuid4().hex}{file_ext}"
                                    ref_audio_path = os.path.join(VOICE_PROFILES_DIR, ref_filename)
                                    
                                    os.makedirs(VOICE_PROFILES_DIR, exist_ok=True)
                                    with open(ref_audio_path, 'wb') as f:
                                        f.write(audio_content)
                                    
                                    ref_audio_path = normalize_path(ref_audio_path)
                                    should_update = True
                                    logger.info(f"✅ 保存WAV文件: {ref_audio_path}")
                    
                    # 处理NPY文件
                    if 'npy_file' in character_files:
                        npy_file = character_files['npy_file']
                        if npy_file and npy_file.filename and npy_file.filename.lower().endswith('.npy'):
                            logger.info(f"📊 更新角色 {name} 的NPY文件: {npy_file.filename}")
                            
                            # 保存NPY文件
                            npy_content = await npy_file.read()
                            if len(npy_content) <= 50 * 1024 * 1024:  # 50MB限制
                                latent_filename = f"{name}_{uuid.uuid4().hex}.npy"
                                latent_file_path = os.path.join(VOICE_PROFILES_DIR, latent_filename)
                                
                                with open(latent_file_path, 'wb') as f:
                                    f.write(npy_content)
                                
                                latent_file_path = normalize_path(latent_file_path)
                                should_update = True
                                logger.info(f"✅ 保存NPY文件: {latent_file_path}")
                
                if should_update:
                    # 更新现有角色
                    existing.reference_audio_path = ref_audio_path
                    existing.latent_file_path = latent_file_path
                    existing.status = 'configured' if ref_audio_path else existing.status
                    
                    created_characters.append({
                        "name": name,
                        "description": existing.description,
                        "voice_type": existing.voice_type,
                        "gender": "",  # 从现有数据获取
                        "personality": "",
                        "status": existing.status,
                        "has_audio_file": ref_audio_path is not None,
                        "has_feature_file": latent_file_path is not None,
                        "audio_file_path": ref_audio_path,
                        "feature_file_path": latent_file_path,
                        "updated": True  # 标记为更新而非创建
                    })
                    logger.info(f"✅ 更新已存在角色: {name} -> {existing.status}")
                else:
                    skipped_characters.append({
                        "name": name,
                        "reason": "已存在但无音频文件上传"
                    })
                continue
            
            # 创建新角色（使用新的Character模型字段）
            description = char_data.get('description', char_data.get('personality_description', ''))
            gender = char_data.get('gender', '')
            personality = char_data.get('personality', '')
            
            # 🔥 新增：提取外貌特征信息
            appearance_info = char_data.get('recommended_config', {})
            age_range = appearance_info.get('age_range', 'young')
            build_type = appearance_info.get('build_type', 'average')
            clothing_style = appearance_info.get('clothing_style', 'ancient')
            distinctive_features = appearance_info.get('distinctive_features', '')
            appearance_description = appearance_info.get('appearance_description', '')
            avatar_prompt = appearance_info.get('avatar_prompt', '')
            consistency_tag = appearance_info.get('consistency_tag', f"{name}_{gender}_{personality}_{age_range}")
            
            # 根据性别设置默认声音类型
            voice_type = 'custom'
            if gender and gender.lower() in ['男', 'male', '男性']:
                voice_type = 'male'
            elif gender and gender.lower() in ['女', 'female', '女性']:
                voice_type = 'female'
            elif gender and gender.lower() in ['儿童', 'child', '童']:
                voice_type = 'child'
            
            # 构建声音参数
            voice_params = {
                "time_step": 20,
                "p_weight": 1.0,
                "t_weight": 1.0,
                "gender": gender,
                "personality": personality,
                "confidence": char_data.get('confidence', 0.5)
            }
            
            # 构建标签
            tags = []
            if gender:
                tags.append(gender)
            if personality:
                tags.append(personality)
            
            # 🔥 新增：处理文件上传
            ref_audio_path = None
            latent_file_path = None
            
            if char_index in files_map:
                character_files = files_map[char_index]
                
                # 处理WAV文件
                if 'wav_file' in character_files:
                    wav_file = character_files['wav_file']
                    if wav_file and wav_file.filename:
                        logger.info(f"📁 处理角色 {name} 的WAV文件: {wav_file.filename}")
                        
                        # 验证文件格式
                        file_ext = os.path.splitext(wav_file.filename)[1].lower()
                        if file_ext not in ['.wav', '.mp3', '.flac', '.m4a', '.ogg']:
                            logger.warning(f"不支持的音频格式: {wav_file.filename}")
                        else:
                            # 保存WAV文件
                            audio_content = await wav_file.read()
                            if len(audio_content) <= 100 * 1024 * 1024:  # 100MB限制
                                ref_filename = f"{name}_{uuid.uuid4().hex}{file_ext}"
                                ref_audio_path = os.path.join(VOICE_PROFILES_DIR, ref_filename)
                                
                                os.makedirs(VOICE_PROFILES_DIR, exist_ok=True)
                                with open(ref_audio_path, 'wb') as f:
                                    f.write(audio_content)
                                
                                ref_audio_path = normalize_path(ref_audio_path)
                                logger.info(f"✅ 保存WAV文件: {ref_audio_path}")
                
                # 处理NPY文件
                if 'npy_file' in character_files:
                    npy_file = character_files['npy_file']
                    if npy_file and npy_file.filename:
                        logger.info(f"📊 处理角色 {name} 的NPY文件: {npy_file.filename}")
                        
                        # 验证文件格式
                        if npy_file.filename.lower().endswith('.npy'):
                            # 保存NPY文件
                            npy_content = await npy_file.read()
                            if len(npy_content) <= 50 * 1024 * 1024:  # 50MB限制
                                latent_filename = f"{name}_{uuid.uuid4().hex}.npy"
                                latent_file_path = os.path.join(VOICE_PROFILES_DIR, latent_filename)
                                
                                with open(latent_file_path, 'wb') as f:
                                    f.write(npy_content)
                                
                                latent_file_path = normalize_path(latent_file_path)
                                logger.info(f"✅ 保存NPY文件: {latent_file_path}")
            
            # 根据是否有文件设置状态
            character_status = 'configured' if ref_audio_path else 'unconfigured'
            
            new_character = Character(
                name=name,
                description=description,
                book_id=book_id,
                chapter_id=chapter_id,
                voice_type=voice_type,
                color='#8b5cf6',
                # 🔥 新增：外貌特征字段
                age_range=age_range,
                build_type=build_type,
                clothing_style=clothing_style,
                distinctive_features=distinctive_features,
                appearance_description=appearance_description,
                avatar_prompt=avatar_prompt,
                consistency_tag=consistency_tag,
                voice_parameters=json.dumps(voice_params, ensure_ascii=False),
                tags=json.dumps(tags, ensure_ascii=False),
                # 🔥 新增：文件路径和状态
                reference_audio_path=ref_audio_path,
                latent_file_path=latent_file_path,
                status=character_status,
                quality_score=3.0,
                usage_count=0
            )
            
            db.add(new_character)
            created_characters.append({
                "name": name,
                "description": new_character.description,
                "voice_type": voice_type,
                "gender": gender,
                "personality": personality,
                "status": character_status,
                # 🔥 新增：文件信息
                "has_audio_file": ref_audio_path is not None,
                "has_feature_file": latent_file_path is not None,
                "audio_file_path": ref_audio_path,
                "feature_file_path": latent_file_path
            })
        
        db.commit()
        
        # 🔥 修复：无论创建还是更新，都需要刷新书籍角色汇总
        try:
            # 重新获取书籍的所有角色，包括刚刚更新的
            all_book_characters = db.query(Character).filter(Character.book_id == book_id).all()
            
            # 构建角色列表用于汇总更新
            character_list = []
            for char in all_book_characters:
                character_list.append({
                    "name": char.name,
                    "description": char.description or f"从第{chapter_id}章智能识别的角色",
                    "status": char.status,  # 🔥 新增：包含配音状态
                    "is_voice_configured": bool(char.reference_audio_path),  # 🔥 新增：配音配置状态
                    "character_id": char.id  # 🔥 新增：角色ID
                })
            
            # 更新书籍角色汇总JSON
            book.update_character_summary(character_list, chapter_id)
            
            # 🔥 新增：更新voice_mappings，将角色ID映射进去
            current_summary = book.get_character_summary()
            voice_mappings = current_summary.get('voice_mappings', {})
            
            # 为已配置的角色添加映射
            for char in all_book_characters:
                if char.reference_audio_path:  # 已配置音频的角色
                    voice_mappings[char.name] = str(char.id)  # 使用角色ID作为语音映射
            
            # 更新voice_mappings
            current_summary['voice_mappings'] = voice_mappings
            book.character_summary = current_summary
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(book, 'character_summary')
            
            db.commit()
            
            logger.info(f"✅ 已更新书籍角色汇总JSON: 总角色{len(character_list)}个, 已配置{len([c for c in character_list if c['is_voice_configured']])}个")
            
        except Exception as e:
            logger.error(f"❌ 更新书籍角色汇总失败: {str(e)}")
            # 不影响主流程，继续返回结果
        
        logger.info(f"批量创建角色完成: {len(created_characters)}个成功, {len(skipped_characters)}个跳过 (书籍: {book.title})")
        
        return {
            "success": True,
            "message": f"批量创建完成：{len(created_characters)}个角色创建成功",
            "data": {
                "created": created_characters,
                "skipped": skipped_characters,
                "book_id": book_id,
                "book_title": book.title,
                "total_created": len(created_characters),
                "total_skipped": len(skipped_characters)
            }
        }
        
    except json.JSONDecodeError:
        return {
            "success": False,
            "message": "角色数据格式错误"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"批量创建角色失败: {str(e)}")
        return {
            "success": False,
            "message": f"批量创建角色失败: {str(e)}"
        }

# 角色管理相关函数
async def get_character_list(
    db: Session, 
    page: int, 
    page_size: int, 
    search: str, 
    book_id: int, 
    sort_by: str, 
    sort_order: str
) -> Dict[str, Any]:
    """获取角色列表（Character模型）"""
    try:
        from app.models.book import Book
        
        # 构建基础查询，包含书籍信息
        query = db.query(Character).join(Book, Character.book_id == Book.id, isouter=True)
        
        # 书籍筛选
        if book_id:
            query = query.filter(Character.book_id == book_id)
        
        # 搜索过滤
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Character.name.like(search_pattern),
                    Character.description.like(search_pattern),
                    Book.title.like(search_pattern)
                )
            )
        
        # 排序
        if sort_by == "book_title":
            sort_field = Book.title
        else:
            sort_field = getattr(Character, sort_by, Character.created_at)
        
        if sort_order == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))
        
        # 统计总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        characters = query.offset(offset).limit(page_size).all()
        
        # 转换为字典格式，包含书籍信息
        character_list = []
        for character in characters:
            character_data = {
                "id": character.id,
                "name": character.name,
                "description": character.description or "",
                "voice_profile": character.voice_profile,
                "voice_config": character.voice_config,
                "book_id": character.book_id,
                "chapter_id": character.chapter_id,
                "created_at": character.created_at.isoformat() if character.created_at else None,
                "updated_at": character.updated_at.isoformat() if character.updated_at else None,
                
                # 添加书籍信息
                "book": {
                    "id": character.book.id if character.book else None,
                    "title": character.book.title if character.book else "未知书籍",
                    "author": character.book.author if character.book else "",
                } if character.book else None
            }
            character_list.append(character_data)
        
        # 获取书籍统计信息
        book_stats = db.query(
            Book.id,
            Book.title,
            func.count(Character.id).label('character_count')
        ).outerjoin(Character).group_by(Book.id, Book.title).all()
        
        books_summary = [
            {
                "book_id": stat.id,
                "book_title": stat.title,
                "character_count": stat.character_count
            }
            for stat in book_stats if stat.character_count > 0
        ]
        
        return {
            "success": True,
            "data": {
                "items": character_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "books_summary": books_summary,  # 书籍汇总信息
                "management_type": "character"
            }
        }
        
    except Exception as e:
        logger.error(f"获取角色列表失败: {str(e)}")
        return {
            "success": False,
            "message": f"获取角色列表失败: {str(e)}",
            "data": {"items": [], "total": 0}
        }

def calculate_similarity(str1: str, str2: str) -> float:
    """
    计算两个字符串的相似度
    使用简单的编辑距离算法
    """
    if not str1 or not str2:
        return 0.0
    
    # 计算编辑距离
    len1, len2 = len(str1), len(str2)
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    
    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j
    
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            if str1[i-1] == str2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1
    
    # 转换为相似度（0-1之间）
    max_len = max(len1, len2)
    if max_len == 0:
        return 1.0
    
    similarity = 1.0 - (dp[len1][len2] / max_len)
    return similarity

@router.post("/generate-avatar/{character_id}")
async def generate_character_avatar(
    character_id: int,
    custom_prompt: str = Form("", description="自定义提示词（可选）"),
    style_preference: str = Form("realistic", description="风格偏好: realistic, anime, cartoon, artistic"),
    image_size: str = Form("512x512", description="图片尺寸: 512x512, 768x768, 1024x1024"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """🔥 新增：为指定角色生成头像"""
    try:
        # 获取角色信息
        character = db.query(Character).filter(Character.id == character_id).first()
        if not character:
            return {
                "success": False,
                "message": f"角色ID {character_id} 不存在"
            }
        
        # 构建头像生成提示词
        if custom_prompt:
            # 使用自定义提示词
            avatar_prompt = custom_prompt
        elif character.avatar_prompt:
            # 使用预设的头像提示词
            avatar_prompt = character.avatar_prompt
        else:
            # 基于角色信息生成提示词
            avatar_prompt = _build_avatar_prompt_from_character(character)
        
        # 根据风格偏好调整提示词
        avatar_prompt = _enhance_prompt_with_style(avatar_prompt, style_preference)
        
        logger.info(f"🎨 为角色 {character.name} 生成头像，提示词: {avatar_prompt}")
        
        # 调用图片生成服务
        try:
            from app.clients.comfyui_client import ComfyUIClient
            comfyui = ComfyUIClient()
            
            # 解析图片尺寸
            width, height = map(int, image_size.split('x'))
            
            # 生成图片
            image_path = await comfyui.generate_image(
                prompt=avatar_prompt,
                negative_prompt="blurry, low quality, distorted, deformed, ugly, bad anatomy",
                width=width,
                height=height,
                steps=20,
                cfg=7.0,
                seed=None  # 随机种子
            )
            
            if image_path:
                # 保存生成的头像到角色专用目录
                avatar_filename = f"avatar_{character.name}_{character.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                avatar_dir = os.path.join("platform", "storage", "avatars")
                os.makedirs(avatar_dir, exist_ok=True)
                avatar_path = os.path.join(avatar_dir, avatar_filename)
                
                # 复制生成的图片到头像目录
                import shutil
                shutil.copy2(image_path, avatar_path)
                
                # 更新角色的头像路径
                character.avatar_path = avatar_path
                db.commit()
                
                return {
                    "success": True,
                    "message": f"成功为角色 {character.name} 生成头像",
                    "data": {
                        "character_name": character.name,
                        "avatar_path": avatar_path,
                        "avatar_url": f"/api/v1/characters/avatar/{character.id}",
                        "prompt_used": avatar_prompt,
                        "style": style_preference,
                        "size": image_size,
                        "consistency_tag": character.consistency_tag
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "图片生成返回空路径"
                }
                
        except Exception as e:
            logger.error(f"调用图片生成服务失败: {str(e)}")
            return {
                "success": False,
                "message": f"图片生成服务不可用: {str(e)}"
            }
            
    except Exception as e:
        logger.error(f"生成角色头像失败: {str(e)}")
        return {
            "success": False,
            "message": f"生成头像失败: {str(e)}"
        }

@router.get("/avatar/{character_id}")
async def get_character_avatar(
    character_id: int,
    db: Session = Depends(get_db)
):
    """获取角色头像"""
    try:
        character = db.query(Character).filter(Character.id == character_id).first()
        if not character or not character.avatar_path:
            # 返回默认头像或404
            raise HTTPException(status_code=404, detail="头像不存在")
        
        # 检查文件是否存在
        if not os.path.exists(character.avatar_path):
            raise HTTPException(status_code=404, detail="头像文件不存在")
        
        from fastapi.responses import FileResponse
        return FileResponse(
            character.avatar_path,
            media_type="image/png",
            filename=f"{character.name}_avatar.png"
        )
        
    except Exception as e:
        logger.error(f"获取角色头像失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取头像失败: {str(e)}")

def _build_avatar_prompt_from_character(character: Character) -> str:
    """基于角色信息构建头像生成提示词"""
    prompt_parts = [
        f"portrait of {character.name}",
        "professional headshot",
        "high quality",
        "detailed face"
    ]
    
    # 添加年龄特征
    if character.age_range:
        age_prompts = {
            'child': 'child, young face, innocent expression',
            'young': 'young adult, youthful appearance',
            'middle': 'middle-aged, mature features',
            'elder': 'elderly, aged features, wise expression'
        }
        prompt_parts.append(age_prompts.get(character.age_range, 'young adult'))
    
    # 添加身材特征
    if character.build_type:
        build_prompts = {
            'slim': 'slim build, delicate features',
            'average': 'average build, balanced proportions',
            'sturdy': 'strong build, robust features', 
            'plump': 'full figure, rounded features'
        }
        prompt_parts.append(build_prompts.get(character.build_type, 'average build'))
    
    # 添加服装风格
    if character.clothing_style:
        clothing_prompts = {
            'ancient': 'traditional Chinese clothing, hanfu, ancient style',
            'modern': 'modern clothing, contemporary style',
            'formal': 'formal attire, elegant dress',
            'casual': 'casual wear, comfortable clothing'
        }
        prompt_parts.append(clothing_prompts.get(character.clothing_style, 'traditional clothing'))
    
    # 添加特殊特征
    if character.distinctive_features:
        # 将中文特征转换为英文描述
        features_cn_to_en = {
            '美貌': 'beautiful', '俊美': 'handsome', '英俊': 'handsome',
            '美丽': 'beautiful', '漂亮': 'pretty',
            '长发': 'long hair', '短发': 'short hair', '白发': 'white hair', 
            '黑发': 'black hair', '卷发': 'curly hair',
            '大眼': 'large eyes', '小眼': 'small eyes', '明眸': 'bright eyes',
            '高鼻': 'high nose', '挺鼻': 'straight nose',
            '红唇': 'red lips', '薄唇': 'thin lips', '厚唇': 'full lips',
            '白皮': 'fair skin', '黑皮': 'dark skin', '古铜色': 'bronze skin'
        }
        
        features_en = []
        for feature in character.distinctive_features.split('，'):
            feature = feature.strip()
            if feature in features_cn_to_en:
                features_en.append(features_cn_to_en[feature])
        
        if features_en:
            prompt_parts.extend(features_en)
    
    return ', '.join(prompt_parts)

def _enhance_prompt_with_style(prompt: str, style: str) -> str:
    """根据风格偏好增强提示词"""
    style_enhancements = {
        'realistic': 'photorealistic, professional photography, studio lighting',
        'anime': 'anime style, manga style, clean line art, vibrant colors',
        'cartoon': 'cartoon style, colorful, friendly, stylized',
        'artistic': 'artistic style, painterly, expressive, creative'
    }
    
    enhancement = style_enhancements.get(style, style_enhancements['realistic'])
    return f"{prompt}, {enhancement}"