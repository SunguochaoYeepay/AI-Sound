"""角色相关工具函数"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
import logging
import os
import json
import re
from datetime import datetime
import mimetypes
from pathlib import Path

from app.models.character import Character
from app.core.config import settings

logger = logging.getLogger(__name__)

def validate_character_name(name: str) -> Tuple[bool, str]:
    """验证角色名称"""
    if not name or not name.strip():
        return False, "角色名称不能为空"
    
    name = name.strip()
    
    if len(name) < 1:
        return False, "角色名称至少需要1个字符"
    
    if len(name) > 100:
        return False, "角色名称不能超过100个字符"
    
    # 检查特殊字符
    if re.search(r'[<>:"/\\|?*]', name):
        return False, "角色名称不能包含特殊字符 < > : \" / \\ | ? *"
    
    return True, ""

def validate_voice_type(voice_type: str) -> Tuple[bool, str]:
    """验证声音类型"""
    valid_types = ["male", "female", "child", "elder", "custom"]
    
    if voice_type not in valid_types:
        return False, f"无效的声音类型，支持的类型: {', '.join(valid_types)}"
    
    return True, ""

def validate_quality_score(score: float) -> Tuple[bool, str]:
    """验证质量分数"""
    if not isinstance(score, (int, float)):
        return False, "质量分数必须是数字"
    
    if score < 0 or score > 100:
        return False, "质量分数必须在0-100之间"
    
    return True, ""

def validate_tags(tags: List[str]) -> Tuple[bool, str]:
    """验证标签列表"""
    if not isinstance(tags, list):
        return False, "标签必须是列表格式"
    
    if len(tags) > 20:
        return False, "标签数量不能超过20个"
    
    for tag in tags:
        if not isinstance(tag, str):
            return False, "标签必须是字符串"
        
        if len(tag.strip()) == 0:
            return False, "标签不能为空"
        
        if len(tag) > 50:
            return False, "单个标签长度不能超过50个字符"
    
    return True, ""

def validate_audio_file(file: UploadFile) -> Tuple[bool, str]:
    """验证音频文件"""
    import logging
    logger = logging.getLogger(__name__)
    
    if not file:
        logger.warning("音频文件验证失败: 文件为空")
        return False, "文件不能为空"
    
    if not file.filename:
        logger.warning("音频文件验证失败: 文件名为空")
        return False, "文件名不能为空"
    
    # 检查文件扩展名
    allowed_extensions = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
    file_extension = Path(file.filename).suffix.lower()
    
    logger.info(f"音频文件验证: 文件名={file.filename}, 扩展名={file_extension}")
    
    if file_extension not in allowed_extensions:
        logger.warning(f"音频文件验证失败: 不支持的扩展名 {file_extension}")
        return False, f"不支持的音频格式，支持的格式: {', '.join(allowed_extensions)}"
    
    # 检查MIME类型
    mime_type, _ = mimetypes.guess_type(file.filename)
    logger.info(f"音频文件验证: MIME类型={mime_type}")
    
    if mime_type and not mime_type.startswith('audio/'):
        logger.warning(f"音频文件验证失败: MIME类型不是audio/ {mime_type}")
        return False, "文件类型不是音频文件"
    
    # 检查文件大小（假设最大50MB）
    if hasattr(file, 'size') and file.size:
        max_size = 50 * 1024 * 1024  # 50MB
        logger.info(f"音频文件验证: 文件大小={file.size}, 最大大小={max_size}")
        if file.size > max_size:
            logger.warning(f"音频文件验证失败: 文件过大 {file.size} > {max_size}")
            return False, f"文件大小不能超过{max_size // (1024*1024)}MB"
    
    logger.info(f"音频文件验证成功: {file.filename}")
    return True, ""

def validate_image_file(file: UploadFile) -> Tuple[bool, str]:
    """验证图片文件"""
    if not file:
        return False, "文件不能为空"
    
    if not file.filename:
        return False, "文件名不能为空"
    
    # 检查文件扩展名
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        return False, f"不支持的图片格式，支持的格式: {', '.join(allowed_extensions)}"
    
    # 检查MIME类型
    mime_type, _ = mimetypes.guess_type(file.filename)
    if mime_type and not mime_type.startswith('image/'):
        return False, "文件类型不是图片文件"
    
    # 检查文件大小（假设最大10MB）
    if hasattr(file, 'size') and file.size:
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            return False, f"文件大小不能超过{max_size // (1024*1024)}MB"
    
    return True, ""

def sanitize_filename(filename: str) -> str:
    """清理文件名，移除不安全字符"""
    # 移除路径分隔符和其他不安全字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # 移除控制字符
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    
    # 限制长度
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename

def generate_character_file_path(character_id: int, file_type: str, extension: str) -> str:
    """生成角色文件路径"""
    base_dir = os.path.join(settings.UPLOAD_DIR, "characters", str(character_id))
    
    if file_type == "avatar":
        subdir = "avatar"
        filename = f"avatar{extension}"
    elif file_type == "reference_audio":
        subdir = "audio"
        filename = f"reference{extension}"
    elif file_type == "latent":
        subdir = "audio"
        filename = f"latent{extension}"
    else:
        subdir = "misc"
        filename = f"{file_type}{extension}"
    
    file_dir = os.path.join(base_dir, subdir)
    os.makedirs(file_dir, exist_ok=True)
    
    return os.path.join(file_dir, filename)

def normalize_file_path(file_path: str) -> str:
    """标准化文件路径"""
    if not file_path:
        return ""
    
    # 转换为绝对路径
    abs_path = os.path.abspath(file_path)
    
    # 标准化路径分隔符
    normalized_path = abs_path.replace('\\', '/')
    
    return normalized_path

def check_file_exists(file_path: str) -> bool:
    """检查文件是否存在"""
    if not file_path:
        return False
    
    return os.path.exists(file_path) and os.path.isfile(file_path)

def get_file_size(file_path: str) -> int:
    """获取文件大小（字节）"""
    if not check_file_exists(file_path):
        return 0
    
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0

def format_file_size(size_bytes: int) -> str:
    """格式化文件大小显示"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"

def parse_tags_string(tags_str: str) -> List[str]:
    """解析标签字符串"""
    if not tags_str:
        return []
    
    try:
        # 尝试解析JSON格式
        tags = json.loads(tags_str)
        if isinstance(tags, list):
            return [str(tag).strip() for tag in tags if str(tag).strip()]
    except (json.JSONDecodeError, TypeError):
        pass
    
    # 如果不是JSON，按逗号分割
    tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
    return tags

def format_tags_for_storage(tags: List[str]) -> str:
    """格式化标签用于存储"""
    if not tags:
        return "[]"
    
    # 清理和去重
    clean_tags = list(set(tag.strip() for tag in tags if tag.strip()))
    
    return json.dumps(clean_tags, ensure_ascii=False)

def build_character_search_query(db: Session, search_params: Dict[str, Any]):
    """构建角色搜索查询"""
    query = db.query(Character)
    
    # 基础搜索
    if search_params.get('search'):
        search_term = f"%{search_params['search']}%"
        query = query.filter(
            Character.name.like(search_term) |
            Character.description.like(search_term)
        )
    
    # 声音类型过滤
    if search_params.get('voice_type'):
        query = query.filter(Character.voice_type == search_params['voice_type'])
    
    # 质量分数过滤
    if search_params.get('quality_min') is not None:
        query = query.filter(Character.quality_score >= search_params['quality_min'])
    
    if search_params.get('quality_max') is not None:
        query = query.filter(Character.quality_score <= search_params['quality_max'])
    
    # 状态过滤
    if search_params.get('status'):
        query = query.filter(Character.status == search_params['status'])
    
    # 书籍过滤
    if search_params.get('book_id'):
        query = query.filter(Character.book_id == search_params['book_id'])
    
    # 章节过滤
    if search_params.get('chapter_id'):
        query = query.filter(Character.chapter_id == search_params['chapter_id'])
    
    # 标签过滤
    if search_params.get('tags'):
        tags = search_params['tags']
        if isinstance(tags, str):
            tags = parse_tags_string(tags)
        
        for tag in tags:
            query = query.filter(Character.tags.like(f'%"{tag}"%'))
    
    return query

def calculate_character_completeness(character: Character) -> Dict[str, Any]:
    """计算角色完整度"""
    completeness = 0
    total_fields = 0
    missing_fields = []
    
    # 基础信息
    fields_check = [
        ('name', character.name, '角色名称'),
        ('description', character.description, '角色描述'),
        ('voice_type', character.voice_type, '声音类型'),
        ('reference_audio_path', character.reference_audio_path, '参考音频'),
        ('avatar_path', character.avatar_path, '角色头像')
    ]
    
    for field_name, field_value, field_desc in fields_check:
        total_fields += 1
        if field_value:
            if field_name in ['reference_audio_path', 'avatar_path']:
                # 检查文件是否存在
                if check_file_exists(field_value):
                    completeness += 1
                else:
                    missing_fields.append(f"{field_desc}（文件不存在）")
            else:
                completeness += 1
        else:
            missing_fields.append(field_desc)
    
    # 可选字段
    optional_fields = [
        ('latent_file_path', character.latent_file_path, '潜在特征文件'),
        ('tags', character.tags, '角色标签')
    ]
    
    for field_name, field_value, field_desc in optional_fields:
        if field_value:
            if field_name == 'latent_file_path':
                if check_file_exists(field_value):
                    completeness += 0.5
            elif field_name == 'tags':
                tags = parse_tags_string(field_value)
                if tags:
                    completeness += 0.5
    
    completeness_percentage = (completeness / total_fields) * 100
    
    return {
        'completeness_percentage': min(completeness_percentage, 100),
        'completed_fields': total_fields - len(missing_fields),
        'total_fields': total_fields,
        'missing_fields': missing_fields,
        'is_complete': len(missing_fields) == 0
    }

def get_character_file_info(character: Character) -> Dict[str, Any]:
    """获取角色文件信息"""
    file_info = {
        'reference_audio': None,
        'latent_file': None,
        'avatar': None,
        'total_size': 0
    }
    
    # 参考音频信息
    if character.reference_audio_path:
        if check_file_exists(character.reference_audio_path):
            size = get_file_size(character.reference_audio_path)
            file_info['reference_audio'] = {
                'path': character.reference_audio_path,
                'exists': True,
                'size': size,
                'size_formatted': format_file_size(size),
                'duration': getattr(character, 'reference_audio_duration', None)
            }
            file_info['total_size'] += size
        else:
            file_info['reference_audio'] = {
                'path': character.reference_audio_path,
                'exists': False,
                'size': 0,
                'size_formatted': '0 B'
            }
    
    # 潜在文件信息
    if character.latent_file_path:
        if check_file_exists(character.latent_file_path):
            size = get_file_size(character.latent_file_path)
            file_info['latent_file'] = {
                'path': character.latent_file_path,
                'exists': True,
                'size': size,
                'size_formatted': format_file_size(size)
            }
            file_info['total_size'] += size
        else:
            file_info['latent_file'] = {
                'path': character.latent_file_path,
                'exists': False,
                'size': 0,
                'size_formatted': '0 B'
            }
    
    # 头像信息
    if character.avatar_path:
        if check_file_exists(character.avatar_path):
            size = get_file_size(character.avatar_path)
            file_info['avatar'] = {
                'path': character.avatar_path,
                'exists': True,
                'size': size,
                'size_formatted': format_file_size(size)
            }
            file_info['total_size'] += size
        else:
            file_info['avatar'] = {
                'path': character.avatar_path,
                'exists': False,
                'size': 0,
                'size_formatted': '0 B'
            }
    
    file_info['total_size_formatted'] = format_file_size(file_info['total_size'])
    
    return file_info