"""角色基础CRUD路由"""

import os
import json
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.character import Character
from app.schemas.character import (
    CharacterCreate, CharacterUpdate, CharacterResponse, CharacterListResponse
)
from app.services.character_management_service import CharacterManagementService
from app.services.character_crud_service import CharacterCRUDService
from app.utils.character_utils import (
    validate_character_name, validate_voice_type, validate_quality_score, validate_tags, validate_audio_file, validate_image_file
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/characters", tags=["角色管理-CRUD"])

@router.get("/")
async def get_characters(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query("", description="搜索关键词"),
    voice_type: str = Query("", description="声音类型"),
    quality_min: float = Query(0, ge=0, le=100, description="最低质量分"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    tags: str = Query("", description="标签过滤（逗号分隔）"),
    status: str = Query("", description="状态过滤"),
    book_id: Optional[int] = Query(None, description="书籍ID"),
    chapter_id: Optional[int] = Query(None, description="章节ID"),
    avatar_filter: str = Query("", description="头像过滤"),
    audio_filter: str = Query("", description="音频过滤"),
    db: Session = Depends(get_db)
):
    """获取角色列表"""
    try:
        service = CharacterManagementService(db)
        result = service.get_characters_with_filters(
            page=page,
            page_size=page_size,
            search=search,
            voice_type=voice_type,
            quality_min=quality_min,
            sort_by=sort_by,
            sort_order=sort_order,
            tags=tags,
            status=status,
            book_id=book_id,
            chapter_id=chapter_id,
            avatar_filter=avatar_filter,
            audio_filter=audio_filter
        )
        
        # 🔧 修复：转换为CharacterListResponse格式
        if result.get("success"):
            pagination = result.get("pagination", {})
            return CharacterListResponse(
                characters=result.get("data", []),
                total=pagination.get("total", 0),
                page=pagination.get("page", page),
                size=pagination.get("page_size", page_size),
                has_next=pagination.get("page", page) < pagination.get("pages", 1),
                has_prev=pagination.get("page", page) > 1
            )
        else:
            raise HTTPException(status_code=500, detail="获取角色列表失败")
            
    except Exception as e:
        logger.error(f"获取角色列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_characters_stats(db: Session = Depends(get_db)):
    """获取角色统计信息"""
    try:
        service = CharacterManagementService(db)
        return service.get_voice_statistics()
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check-exists")
async def check_character_exists(
    name: str = Query(..., description="角色名称"),
    db: Session = Depends(get_db)
):
    """检查角色是否存在"""
    try:
        # 验证角色名称
        is_valid, error_msg = validate_character_name(name)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        service = CharacterManagementService(db)
        return service.check_character_exists(name)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检查角色存在性失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{character_id}")
async def get_character(
    character_id: int,
    db: Session = Depends(get_db)
):
    """获取角色详情"""
    try:
        service = CharacterManagementService(db)
        character = service.get_character_by_id(character_id)
        
        if not character:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        return {
            "success": True,
            "data": character.to_dict(),
            "message": "获取角色详情成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取角色详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_character(
    character_data: CharacterCreate,
    db: Session = Depends(get_db)
):
    """创建新角色"""
    try:
        # 验证输入数据
        is_valid, error_msg = validate_character_name(character_data.name)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 检查字段是否存在再验证
        if hasattr(character_data, 'voice_type') and character_data.voice_type:
            is_valid, error_msg = validate_voice_type(character_data.voice_type)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
        
        if hasattr(character_data, 'quality_score') and character_data.quality_score is not None:
            is_valid, error_msg = validate_quality_score(character_data.quality_score)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
        
        if hasattr(character_data, 'tags') and character_data.tags:
            is_valid, error_msg = validate_tags(character_data.tags)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
        
        service = CharacterCRUDService(db)
        return service.create_character(character_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{character_id}")
async def update_character(
    character_id: int,
    name: str = Form(None),
    description: str = Form(None),
    voice_type: str = Form(None),
    color: str = Form(None),
    parameters: str = Form(None),
    tags: str = Form(None),
    book_id: int = Form(None),
    avatar: UploadFile = File(None),
    remove_avatar: str = Form(None),
    reference_audio: UploadFile = File(None),
    latent_file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """更新角色信息（支持FormData）"""
    try:
        # 构建更新数据
        update_data = {}
        
        if name is not None:
            update_data['name'] = name
        if description is not None:
            update_data['description'] = description
        if voice_type is not None:
            update_data['voice_type'] = voice_type
        if color is not None:
            update_data['color'] = color
        if parameters is not None:
            try:
                update_data['voice_parameters'] = json.loads(parameters)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="参数格式错误")
        if tags is not None:
            try:
                # 尝试解析为JSON数组，如果失败则按逗号分割
                if tags.startswith('[') and tags.endswith(']'):
                    update_data['tags'] = json.loads(tags)
                else:
                    update_data['tags'] = tags.split(',') if tags else []
            except json.JSONDecodeError:
                # 如果JSON解析失败，按逗号分割
                update_data['tags'] = tags.split(',') if tags else []
        if book_id is not None:
            update_data['book_id'] = book_id
        
        # 验证输入数据
        if update_data.get('name'):
            is_valid, error_msg = validate_character_name(update_data['name'])
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
        
        if update_data.get('voice_type'):
            is_valid, error_msg = validate_voice_type(update_data['voice_type'])
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
        
        service = CharacterCRUDService(db)
        
        # 处理文件上传
        if avatar:
            is_valid, error_msg = validate_image_file(avatar)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
            service.upload_character_avatar(character_id, avatar)
        
        if reference_audio:
            is_valid, error_msg = validate_audio_file(reference_audio)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
            service.upload_character_audio(character_id, reference_audio, "reference")
        
        if latent_file:
            is_valid, error_msg = validate_audio_file(latent_file)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
            service.upload_character_audio(character_id, latent_file, "latent")
        
        # 处理头像移除
        if remove_avatar == 'true':
            service.remove_character_avatar(character_id)
        
        # 更新角色信息
        character_update = CharacterUpdate(**update_data)
        return service.update_character(character_id, character_update)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{character_id}")
async def delete_character(
    character_id: int,
    force: bool = Query(False, description="是否强制删除（包括关联文件）"),
    db: Session = Depends(get_db)
):
    """删除角色"""
    try:
        service = CharacterManagementService(db)
        return service.delete_character(character_id, force)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{character_id}/upload-audio")
async def upload_character_audio(
    character_id: int,
    audio_file: UploadFile = File(...),
    audio_type: str = Query("reference", regex="^(reference|latent)$", description="音频类型"),
    db: Session = Depends(get_db)
):
    """上传角色音频文件"""
    try:
        # 验证音频文件
        is_valid, error_msg = validate_audio_file(audio_file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        service = CharacterCRUDService(db)
        return service.upload_character_audio(character_id, audio_file, audio_type)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传音频文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{character_id}/upload-avatar")
async def upload_character_avatar(
    character_id: int,
    avatar_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传角色头像"""
    try:
        # 验证图片文件
        is_valid, error_msg = validate_image_file(avatar_file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        service = CharacterCRUDService(db)
        return service.upload_character_avatar(character_id, avatar_file)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传头像失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/avatar/default")
async def get_default_avatar(
    name: str = Query(..., description="角色名称"),
    voice_type: str = Query("custom", description="声音类型")
):
    """获取默认头像（基于角色名称生成）"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io
        from urllib.parse import unquote
        
        # 🔧 修复：解码URL编码的角色名称
        decoded_name = unquote(name)
        
        # 创建默认头像
        size = (200, 200)
        img = Image.new('RGB', size, color='#8b5cf6')
        draw = ImageDraw.Draw(img)
        
        # 尝试加载字体，如果失败则使用默认字体
        try:
            font = ImageFont.truetype("arial.ttf", 80)
        except:
            font = ImageFont.load_default()
        
        # 获取角色名称的第一个字符
        first_char = decoded_name[0] if decoded_name else "?"
        
        # 计算文字位置（居中）
        bbox = draw.textbbox((0, 0), first_char, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2
        
        # 绘制文字
        draw.text((x, y), first_char, fill='white', font=font)
        
        # 转换为字节流
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        return Response(
            content=img_byte_arr.getvalue(),
            media_type="image/jpeg"
        )
    except Exception as e:
        logger.error(f"生成默认头像失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/avatar/{character_id}")
async def get_character_avatar(
    character_id: int,
    db: Session = Depends(get_db)
):
    """获取角色头像"""
    try:
        service = CharacterManagementService(db)
        character = service.get_character_by_id(character_id)
        
        if not character:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        if not character.avatar_path:
            raise HTTPException(status_code=404, detail="角色没有头像")
        
        # 🔧 修复：处理头像路径
        avatar_path = character.avatar_path
        
        # 如果是相对路径，转换为绝对路径
        if not os.path.isabs(avatar_path):
            # 使用当前工作目录作为基准
            current_working_dir = os.getcwd()
            # 直接使用当前工作目录，因为文件就在backend目录下
            avatar_path = os.path.join(current_working_dir, avatar_path)
        
        # 🔧 调试：输出路径信息
        logger.info(f"头像路径解析: 原始={character.avatar_path}, 解析后={avatar_path}, 存在={os.path.exists(avatar_path)}")
        
        # 检查文件是否存在
        if not os.path.exists(avatar_path):
            logger.error(f"头像文件不存在: {avatar_path}")
            raise HTTPException(status_code=404, detail="头像文件不存在")
        
        # 根据文件扩展名确定媒体类型
        file_ext = os.path.splitext(avatar_path)[1].lower()
        if file_ext == '.png':
            media_type = "image/png"
            filename = f"avatar_{character_id}.png"
        elif file_ext == '.jpg' or file_ext == '.jpeg':
            media_type = "image/jpeg"
            filename = f"avatar_{character_id}.jpg"
        else:
            media_type = "image/png"  # 默认使用PNG
            filename = f"avatar_{character_id}.png"
        
        # 返回头像文件
        return FileResponse(
            avatar_path,
            media_type=media_type,
            filename=filename
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取头像失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-create")
async def batch_create_characters(
    characters_data: List[CharacterCreate],
    db: Session = Depends(get_db)
):
    """批量创建角色"""
    try:
        if not characters_data:
            raise HTTPException(status_code=400, detail="角色数据不能为空")
        
        if len(characters_data) > 100:
            raise HTTPException(status_code=400, detail="单次最多创建100个角色")
        
        # 验证所有角色数据
        for i, char_data in enumerate(characters_data):
            is_valid, error_msg = validate_character_name(char_data.name)
            if not is_valid:
                raise HTTPException(
                    status_code=400, 
                    detail=f"第{i+1}个角色名称无效: {error_msg}"
                )
            
            if char_data.voice_type:
                is_valid, error_msg = validate_voice_type(char_data.voice_type)
                if not is_valid:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"第{i+1}个角色声音类型无效: {error_msg}"
                    )
            
            if char_data.quality_score is not None:
                is_valid, error_msg = validate_quality_score(char_data.quality_score)
                if not is_valid:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"第{i+1}个角色质量分数无效: {error_msg}"
                    )
            
            if char_data.tags:
                is_valid, error_msg = validate_tags(char_data.tags)
                if not is_valid:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"第{i+1}个角色标签无效: {error_msg}"
                    )
        
        service = CharacterCRUDService(db)
        return service.batch_create_characters(characters_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量创建角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))