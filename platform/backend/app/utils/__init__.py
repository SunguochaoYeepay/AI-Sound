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

# 兼容性函数 - 支持新的调用方式
async def log_system_event(*args, **kwargs):
    """系统事件日志记录（兼容性函数）"""
    # 检查是否是新的调用方式 (db, level, message, module, details)
    if len(args) >= 4:
        # 新的调用方式：log_system_event(db, level, message, module, details)
        # 直接调用utils.py中的函数，避免循环导入
        import importlib
        utils_module = importlib.import_module('app.utils')
        if hasattr(utils_module, 'log_system_event'):
            # 确保调用的是utils.py中的函数
            utils_func = getattr(utils_module, 'log_system_event')
            if utils_func != log_system_event:  # 避免递归调用
                return await utils_func(*args, **kwargs)
        
        # 如果无法调用utils.py中的函数，则使用简化版本
        db, level, message, module = args[:4]
        details = args[4] if len(args) > 4 else kwargs.get('details')
        
        try:
            from ..models.system import SystemLog
            from datetime import datetime
            import json
            
            log_entry = SystemLog(
                level=level,
                message=message,
                module=module,
                details=json.dumps(details) if details else None,
                timestamp=datetime.utcnow()
            )
            
            if db and hasattr(db, 'add'):
                db.add(log_entry)
                # 不自动commit，由调用者处理
        except Exception as e:
            print(f"日志记录失败: {e}")
    else:
        # 旧的调用方式：log_system_event(message, level, **kwargs)
        from .logger import LogLevel, LogModule
        
        message = args[0] if args else kwargs.get('message', '')
        level = args[1] if len(args) > 1 else kwargs.get('level', 'info')
        
        # 映射级别
        level_map = {
            "debug": LogLevel.DEBUG,
            "info": LogLevel.INFO,
            "warning": LogLevel.WARNING,
            "error": LogLevel.ERROR,
            "critical": LogLevel.CRITICAL
        }
        
        log_level = level_map.get(level.lower(), LogLevel.INFO)
        
        # 从kwargs中移除可能冲突的参数
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ['level', 'module', 'message']}
        log_to_database(log_level, LogModule.SYSTEM, message, **filtered_kwargs)

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

async def update_usage_stats(*args, **kwargs):
    """更新使用统计（兼容性函数）"""
    # 检查是否是新的调用方式 (db, success, processing_time, audio_generated)
    if len(args) >= 1 and hasattr(args[0], 'add'):
        # 新的调用方式：update_usage_stats(db, success=True, processing_time=0.0, audio_generated=False)
        import importlib
        utils_module = importlib.import_module('app.utils')
        if hasattr(utils_module, 'update_usage_stats'):
            utils_func = getattr(utils_module, 'update_usage_stats')
            if utils_func != update_usage_stats:  # 避免递归调用
                return await utils_func(*args, **kwargs)
        
        # 如果无法调用utils.py中的函数，则跳过统计更新
        print("跳过使用统计更新")
    else:
        # 旧的调用方式：update_usage_stats(operation, **kwargs)
        operation = args[0] if args else kwargs.get('operation', 'unknown')
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