"""
工具函数模块
提供通用的文件处理、日志记录、统计更新等功能
"""

import os
import uuid
import json
import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session

from models import SystemLog, UsageStats

logger = logging.getLogger(__name__)

async def save_upload_file(
    file: UploadFile, 
    upload_dir: str, 
    allowed_extensions: List[str] = None,
    max_size_mb: int = 100
) -> Dict[str, Any]:
    """
    保存上传文件
    
    Args:
        file: FastAPI上传文件对象
        upload_dir: 上传目录
        allowed_extensions: 允许的文件扩展名列表
        max_size_mb: 最大文件大小(MB)
    
    Returns:
        包含文件信息的字典
    """
    try:
        # 读取文件内容
        content = await file.read()
        
        # 验证文件大小
        file_size_mb = len(content) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            raise ValueError(f"文件大小不能超过{max_size_mb}MB")
        
        # 验证文件扩展名
        if allowed_extensions:
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in allowed_extensions:
                raise ValueError(f"不支持的文件格式: {file_ext}")
        
        # 生成唯一文件名
        file_ext = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # 确保目录存在
        os.makedirs(upload_dir, exist_ok=True)
        
        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return {
            "success": True,
            "filename": unique_filename,
            "original_name": file.filename,
            "file_path": file_path,
            "file_size_mb": round(file_size_mb, 2),
            "content_type": file.content_type
        }
        
    except Exception as e:
        logger.error(f"保存文件失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

async def log_system_event(
    db: Session,
    level: str,
    message: str,
    module: str,
    details: Dict[str, Any] = None
):
    """
    记录系统事件到数据库
    
    Args:
        db: 数据库会话
        level: 日志级别 ('info', 'warn', 'error')
        message: 日志消息
        module: 模块名称
        details: 详细信息字典
    """
    try:
        # 检查数据库会话状态
        if not db or not hasattr(db, 'add'):
            logger.warning("无效的数据库会话，跳过日志记录")
            return
        
        # 创建系统日志记录
        log_entry = SystemLog(
            level=level,
            message=message,
            module=module,
            details=json.dumps(details) if details else None,
            timestamp=datetime.utcnow()
        )
        
        # 只添加到会话，不进行commit/rollback操作
        # 让调用者决定何时提交事务
        db.add(log_entry)
        
        # 同时记录到应用日志
        if level == "info":
            logger.info(f"[{module}] {message}")
        elif level == "warn":
            logger.warning(f"[{module}] {message}")
        elif level == "error":
            logger.error(f"[{module}] {message}")
            
    except Exception as e:
        logger.error(f"记录系统日志失败: {str(e)}")
        # 日志记录失败不应该影响主要业务逻辑
        pass

async def update_usage_stats(
    db: Session,
    success: bool = True,
    processing_time: float = 0.0,
    audio_generated: bool = False
):
    """
    更新使用统计
    
    Args:
        db: 数据库会话
        success: 是否成功
        processing_time: 处理时间(秒)
        audio_generated: 是否生成了音频文件
    """
    try:
        # 检查数据库会话状态
        if not db or not hasattr(db, 'query'):
            logger.warning("无效的数据库会话，跳过统计更新")
            return
        
        today = date.today().strftime("%Y-%m-%d")
        
        # 查找或创建今天的统计记录
        stats = db.query(UsageStats).filter(UsageStats.date == today).first()
        if not stats:
            stats = UsageStats(date=today)
            db.add(stats)
            # 使用flush而不是commit，让调用者决定何时提交
            db.flush()
        
        # 更新统计数据，确保处理None值
        stats.total_requests = (stats.total_requests or 0) + 1
        
        if success:
            stats.successful_requests = (stats.successful_requests or 0) + 1
            stats.total_processing_time = (stats.total_processing_time or 0.0) + processing_time
        else:
            stats.failed_requests = (stats.failed_requests or 0) + 1
        
        if audio_generated:
            stats.audio_files_generated = (stats.audio_files_generated or 0) + 1
        
    except Exception as e:
        logger.error(f"更新使用统计失败: {str(e)}")
        # 统计更新失败不应该影响主要业务逻辑
        pass

def validate_audio_file(file_path: str) -> Dict[str, Any]:
    """
    验证音频文件
    
    Args:
        file_path: 音频文件路径
    
    Returns:
        验证结果字典
    """
    try:
        if not os.path.exists(file_path):
            return {"valid": False, "error": "文件不存在"}
        
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return {"valid": False, "error": "文件为空"}
        
        if file_size > 100 * 1024 * 1024:  # 100MB
            return {"valid": False, "error": "文件过大"}
        
        # 检查文件扩展名
        file_ext = os.path.splitext(file_path)[1].lower()
        supported_formats = ['.wav', '.mp3', '.flac', '.m4a', '.ogg']
        if file_ext not in supported_formats:
            return {"valid": False, "error": f"不支持的音频格式: {file_ext}"}
        
        return {
            "valid": True,
            "file_size": file_size,
            "format": file_ext,
            "size_mb": round(file_size / (1024 * 1024), 2)
        }
        
    except Exception as e:
        return {"valid": False, "error": f"验证失败: {str(e)}"}

def get_audio_duration(file_path: str) -> Optional[float]:
    """
    获取音频文件时长（秒）
    需要安装 librosa 或 pydub
    
    Args:
        file_path: 音频文件路径
    
    Returns:
        音频时长(秒)，失败返回None
    """
    # 添加环境变量控制开关
    if os.getenv('DISABLE_AUDIO_DURATION', 'false').lower() == 'true':
        return None
        
    try:
        # 尝试使用 librosa
        try:
            import librosa
            duration = librosa.get_duration(filename=file_path)
            return duration
        except ImportError:
            pass
        
        # 尝试使用 pydub
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(file_path)
            return len(audio) / 1000.0  # 转换为秒
        except ImportError:
            pass
        
        # 只在第一次导入失败时显示警告
        if not hasattr(get_audio_duration, '_warning_shown'):
            logger.warning("无法获取音频时长：未安装 librosa 或 pydub")
            get_audio_duration._warning_shown = True
        return None
        
    except Exception as e:
        logger.error(f"获取音频时长失败: {str(e)}")
        return None

def cleanup_old_files(directory: str, max_age_hours: int = 24) -> int:
    """
    清理过期文件
    
    Args:
        directory: 目录路径
        max_age_hours: 最大文件年龄(小时)
    
    Returns:
        清理的文件数量
    """
    try:
        if not os.path.exists(directory):
            return 0
        
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        cleanup_count = 0
        
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getctime(file_path)
                if file_age > max_age_seconds:
                    try:
                        os.remove(file_path)
                        cleanup_count += 1
                        logger.info(f"清理过期文件: {filename}")
                    except Exception as e:
                        logger.warning(f"清理文件失败 {filename}: {str(e)}")
        
        return cleanup_count
        
    except Exception as e:
        logger.error(f"清理目录失败 {directory}: {str(e)}")
        return 0

def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小显示
    
    Args:
        size_bytes: 文件大小(字节)
    
    Returns:
        格式化的文件大小字符串
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不安全字符
    
    Args:
        filename: 原始文件名
    
    Returns:
        清理后的文件名
    """
    import re
    
    # 移除路径分隔符和其他不安全字符
    unsafe_chars = r'[<>:"/\\|?*\x00-\x1f]'
    filename = re.sub(unsafe_chars, '_', filename)
    
    # 移除开头和结尾的点和空格
    filename = filename.strip('. ')
    
    # 限制长度
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:100-len(ext)] + ext
    
    return filename or "unnamed"

def get_system_info() -> Dict[str, Any]:
    """
    获取系统信息
    
    Returns:
        系统信息字典
    """
    try:
        import psutil
        import platform
        
        # CPU信息
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # 内存信息
        memory = psutil.virtual_memory()
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        
        return {
            "platform": platform.system(),
            "architecture": platform.architecture()[0],
            "python_version": platform.python_version(),
            "cpu_count": cpu_count,
            "cpu_percent": cpu_percent,
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_percent": memory.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_percent": round((disk.used / disk.total) * 100, 1)
        }
        
    except ImportError:
        # 如果psutil未安装，返回基本信息
        import platform
        return {
            "platform": platform.system(),
            "architecture": platform.architecture()[0],
            "python_version": platform.python_version(),
            "note": "安装 psutil 以获取更详细的系统信息"
        }
    except Exception as e:
        logger.error(f"获取系统信息失败: {str(e)}")
        return {"error": str(e)}

def validate_parameters(
    time_step: int,
    p_weight: float,
    t_weight: float
) -> Dict[str, Any]:
    """
    验证TTS参数
    
    Args:
        time_step: 时间步长
        p_weight: P权重
        t_weight: T权重
    
    Returns:
        验证结果字典
    """
    errors = []
    
    # 验证time_step
    if not isinstance(time_step, int) or time_step < 1 or time_step > 100:
        errors.append("time_step必须是1-100之间的整数")
    
    # 验证p_weight
    if not isinstance(p_weight, (int, float)) or p_weight < 0.1 or p_weight > 3.0:
        errors.append("p_weight必须是0.1-3.0之间的数值")
    
    # 验证t_weight
    if not isinstance(t_weight, (int, float)) or t_weight < 0.1 or t_weight > 3.0:
        errors.append("t_weight必须是0.1-3.0之间的数值")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    } 