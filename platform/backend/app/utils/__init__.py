# 工具包

# 导出日志功能
from .logger import (
    log_to_database,
    log_debug,
    log_info,
    log_warning,
    log_error,
    log_critical,
    log_api_request,
    log_tts_operation,
    log_synthesis_operation,
    log_database_operation,
    log_file_operation,
    log_websocket_event
)

# 兼容性函数
def log_system_event(message: str, level: str = "info", **kwargs):
    """系统事件日志记录（兼容性函数）"""
    from .logger import LogLevel, LogModule
    
    # 映射级别
    level_map = {
        "debug": LogLevel.DEBUG,
        "info": LogLevel.INFO,
        "warning": LogLevel.WARNING,
        "error": LogLevel.ERROR,
        "critical": LogLevel.CRITICAL
    }
    
    log_level = level_map.get(level.lower(), LogLevel.INFO)
    log_to_database(log_level, LogModule.SYSTEM, message, **kwargs)

# 其他工具函数（为兼容性保留）
def get_audio_duration(file_path: str) -> float:
    """获取音频文件时长"""
    try:
        import librosa
        duration = librosa.get_duration(filename=file_path)
        return duration
    except Exception as e:
        log_error(f"获取音频时长失败: {e}", details={"file_path": file_path})
        return 0.0

def update_usage_stats(operation: str, **kwargs):
    """更新使用统计"""
    log_info(f"使用统计: {operation}", details=kwargs)

def validate_audio_file(file_path: str) -> bool:
    """验证音频文件"""
    try:
        import os
        if not os.path.exists(file_path):
            return False
        # 简单的文件大小检查
        file_size = os.path.getsize(file_path)
        return file_size > 0
    except Exception:
        return False

def save_upload_file(file, upload_dir: str, filename: str = None) -> str:
    """保存上传文件"""
    import os
    import uuid
    from pathlib import Path
    
    try:
        # 确保上传目录存在
        Path(upload_dir).mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        if not filename:
            file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'tmp'
            filename = f"{uuid.uuid4().hex}.{file_ext}"
        
        file_path = os.path.join(upload_dir, filename)
        
        # 保存文件
        with open(file_path, 'wb') as f:
            content = file.file.read()
            f.write(content)
        
        log_file_operation("upload", file_path, "success", file_size=len(content))
        return file_path
        
    except Exception as e:
        log_file_operation("upload", filename or "unknown", "failed", error_message=str(e))
        raise