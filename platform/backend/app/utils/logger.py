#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志工具函数
提供统一的日志记录功能
"""

import json
import logging
import inspect
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from ..models.system import SystemLog, LogLevel, LogModule
from ..database import get_db

logger = logging.getLogger(__name__)


def log_to_database(
    level: LogLevel,
    module: LogModule,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    db: Optional[Session] = None
):
    """
    记录日志到数据库
    
    Args:
        level: 日志级别
        module: 模块名称
        message: 日志消息
        details: 额外详情
        user_id: 用户ID
        session_id: 会话ID
        ip_address: IP地址
        user_agent: 用户代理
        db: 数据库会话
    """
    try:
        # 获取调用者信息
        frame = inspect.currentframe().f_back
        source_file = frame.f_code.co_filename if frame else None
        source_line = frame.f_lineno if frame else None
        
        # 创建日志记录
        log_entry = SystemLog(
            level=level,
            module=module,
            message=message,
            details=json.dumps(details, ensure_ascii=False) if details else None,
            source_file=source_file,
            source_line=source_line,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now()
        )
        
        # 保存到数据库
        if db is None:
            # 如果没有传入数据库会话，创建一个新的
            from ..database import SessionLocal
            db = SessionLocal()
            try:
                db.add(log_entry)
                db.commit()
            finally:
                db.close()
        else:
            db.add(log_entry)
            db.commit()
            
    except Exception as e:
        # 记录到文件日志，避免循环依赖
        logger.error(f"记录数据库日志失败: {e}", exc_info=True)


def log_debug(message: str, module: LogModule = LogModule.SYSTEM, **kwargs):
    """记录调试日志"""
    log_to_database(LogLevel.DEBUG, module, message, **kwargs)


def log_info(message: str, module: LogModule = LogModule.SYSTEM, **kwargs):
    """记录信息日志"""
    log_to_database(LogLevel.INFO, module, message, **kwargs)


def log_warning(message: str, module: LogModule = LogModule.SYSTEM, **kwargs):
    """记录警告日志"""
    log_to_database(LogLevel.WARNING, module, message, **kwargs)


def log_error(message: str, module: LogModule = LogModule.SYSTEM, **kwargs):
    """记录错误日志"""
    log_to_database(LogLevel.ERROR, module, message, **kwargs)


def log_critical(message: str, module: LogModule = LogModule.SYSTEM, **kwargs):
    """记录严重错误日志"""
    log_to_database(LogLevel.CRITICAL, module, message, **kwargs)


def log_api_request(
    method: str,
    path: str,
    status_code: int,
    response_time: float,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    **kwargs
):
    """记录API请求日志"""
    message = f"{method} {path} - {status_code} ({response_time:.2f}ms)"
    details = {
        "method": method,
        "path": path,
        "status_code": status_code,
        "response_time": response_time,
        **kwargs
    }
    
    # 根据状态码确定日志级别
    if status_code >= 500:
        level = LogLevel.ERROR
    elif status_code >= 400:
        level = LogLevel.WARNING
    else:
        level = LogLevel.INFO
    
    log_to_database(
        level=level,
        module=LogModule.API,
        message=message,
        details=details,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent
    )


def log_tts_operation(
    operation: str,
    status: str,
    duration: Optional[float] = None,
    text_length: Optional[int] = None,
    voice_model: Optional[str] = None,
    error_message: Optional[str] = None,
    **kwargs
):
    """记录TTS操作日志"""
    message = f"TTS {operation}: {status}"
    if duration:
        message += f" ({duration:.2f}s)"
    
    details = {
        "operation": operation,
        "status": status,
        "duration": duration,
        "text_length": text_length,
        "voice_model": voice_model,
        "error_message": error_message,
        **kwargs
    }
    
    # 根据状态确定日志级别
    if status == "failed" or error_message:
        level = LogLevel.ERROR
    elif status == "warning":
        level = LogLevel.WARNING
    else:
        level = LogLevel.INFO
    
    log_to_database(
        level=level,
        module=LogModule.TTS,
        message=message,
        details=details
    )


def log_synthesis_operation(
    project_id: str,
    operation: str,
    status: str,
    progress: Optional[float] = None,
    chapters_count: Optional[int] = None,
    estimated_time: Optional[float] = None,
    error_message: Optional[str] = None,
    **kwargs
):
    """记录合成操作日志"""
    message = f"合成项目 {project_id}: {operation} - {status}"
    if progress is not None:
        message += f" ({progress:.1f}%)"
    
    details = {
        "project_id": project_id,
        "operation": operation,
        "status": status,
        "progress": progress,
        "chapters_count": chapters_count,
        "estimated_time": estimated_time,
        "error_message": error_message,
        **kwargs
    }
    
    # 根据状态确定日志级别
    if status == "failed" or error_message:
        level = LogLevel.ERROR
    elif status == "warning":
        level = LogLevel.WARNING
    else:
        level = LogLevel.INFO
    
    log_to_database(
        level=level,
        module=LogModule.SYNTHESIS,
        message=message,
        details=details
    )


def log_database_operation(
    operation: str,
    table: str,
    status: str,
    affected_rows: Optional[int] = None,
    duration: Optional[float] = None,
    error_message: Optional[str] = None,
    **kwargs
):
    """记录数据库操作日志"""
    message = f"数据库 {operation} {table}: {status}"
    if affected_rows is not None:
        message += f" ({affected_rows} rows)"
    
    details = {
        "operation": operation,
        "table": table,
        "status": status,
        "affected_rows": affected_rows,
        "duration": duration,
        "error_message": error_message,
        **kwargs
    }
    
    # 根据状态确定日志级别
    if status == "failed" or error_message:
        level = LogLevel.ERROR
    elif status == "warning":
        level = LogLevel.WARNING
    else:
        level = LogLevel.INFO
    
    log_to_database(
        level=level,
        module=LogModule.DATABASE,
        message=message,
        details=details
    )


def log_file_operation(
    operation: str,
    file_path: str,
    status: str,
    file_size: Optional[int] = None,
    duration: Optional[float] = None,
    error_message: Optional[str] = None,
    **kwargs
):
    """记录文件操作日志"""
    message = f"文件 {operation} {file_path}: {status}"
    if file_size is not None:
        message += f" ({file_size} bytes)"
    
    details = {
        "operation": operation,
        "file_path": file_path,
        "status": status,
        "file_size": file_size,
        "duration": duration,
        "error_message": error_message,
        **kwargs
    }
    
    # 根据状态确定日志级别
    if status == "failed" or error_message:
        level = LogLevel.ERROR
    elif status == "warning":
        level = LogLevel.WARNING
    else:
        level = LogLevel.INFO
    
    log_to_database(
        level=level,
        module=LogModule.FILE,
        message=message,
        details=details
    )


def log_websocket_event(
    event_type: str,
    connection_id: str,
    status: str,
    message_data: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    **kwargs
):
    """记录WebSocket事件日志"""
    message = f"WebSocket {event_type} {connection_id}: {status}"
    
    details = {
        "event_type": event_type,
        "connection_id": connection_id,
        "status": status,
        "message_data": message_data,
        "error_message": error_message,
        **kwargs
    }
    
    # 根据状态确定日志级别
    if status == "failed" or error_message:
        level = LogLevel.ERROR
    elif status == "warning":
        level = LogLevel.WARNING
    else:
        level = LogLevel.INFO
    
    log_to_database(
        level=level,
        module=LogModule.WEBSOCKET,
        message=message,
        details=details
    )


def log_system_event(
    message: str,
    level_str: str = "info",
    module: LogModule = LogModule.SYSTEM,
    **kwargs
):
    """
    记录系统事件日志（兼容原有接口）
    
    Args:
        message: 日志消息
        level_str: 日志级别字符串 ('debug', 'info', 'warning', 'error', 'critical')
        module: 模块名称
        **kwargs: 其他参数
    """
    # 转换字符串级别到LogLevel枚举
    level_mapping = {
        "debug": LogLevel.DEBUG,
        "info": LogLevel.INFO,
        "warning": LogLevel.WARNING,
        "error": LogLevel.ERROR,
        "critical": LogLevel.CRITICAL
    }
    
    level = level_mapping.get(level_str.lower(), LogLevel.INFO)
    
    # 同时输出到控制台和数据库
    print(f"[{level_str.upper()}] {message}")
    
    log_to_database(
        level=level,
        module=module,
        message=message,
        **kwargs
    )