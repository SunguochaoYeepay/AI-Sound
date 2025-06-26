#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置文件
管理日志系统的各种配置选项
"""

import os
from typing import List, Dict, Any

class LogConfig:
    """日志系统配置类"""
    
    # 数据库日志配置
    DATABASE_LOG_ENABLED: bool = True
    DATABASE_LOG_LEVEL: str = "INFO"
    
    # 文件日志配置
    FILE_LOG_ENABLED: bool = True
    FILE_LOG_LEVEL: str = "DEBUG"
    FILE_LOG_PATH: str = "data/logs"
    FILE_LOG_MAX_SIZE: int = 100 * 1024 * 1024  # 100MB
    FILE_LOG_BACKUP_COUNT: int = 5
    
    # API日志中间件配置
    API_LOG_ENABLED: bool = True
    API_LOG_SKIP_PATHS: List[str] = [
        "/health",
        "/docs",
        "/redoc", 
        "/openapi.json",
        "/favicon.ico",
        "/static/",
        "/ws"  # WebSocket连接
    ]
    
    # 日志清理配置
    AUTO_CLEANUP_ENABLED: bool = True
    AUTO_CLEANUP_DAYS: int = 30
    AUTO_CLEANUP_INTERVAL: int = 24 * 60 * 60  # 24小时（秒）
    
    # 性能相关配置
    ASYNC_LOG_ENABLED: bool = False  # 异步日志写入
    BATCH_LOG_SIZE: int = 100  # 批量写入大小
    BATCH_LOG_TIMEOUT: int = 5  # 批量写入超时（秒）
    
    # 敏感信息过滤配置
    SENSITIVE_FIELDS: List[str] = [
        "password", "passwd", "pwd",
        "token", "api_key", "secret",
        "private_key", "access_token",
        "refresh_token", "auth_token",
        ""
    ]
    
    # 监控配置
    ERROR_RATE_THRESHOLD: float = 5.0  # 错误率阈值（百分比）
    ERROR_COUNT_THRESHOLD: int = 50  # 错误数量阈值
    MONITOR_INTERVAL: int = 300  # 监控间隔（秒）
    
    # 导出配置
    EXPORT_MAX_RECORDS: int = 10000  # 最大导出记录数
    EXPORT_TIMEOUT: int = 300  # 导出超时（秒）
    
    @classmethod
    def from_env(cls) -> 'LogConfig':
        """从环境变量加载配置"""
        config = cls()
        
        # 从环境变量读取配置
        config.DATABASE_LOG_ENABLED = os.getenv("LOG_DATABASE_ENABLED", "true").lower() == "true"
        config.DATABASE_LOG_LEVEL = os.getenv("LOG_DATABASE_LEVEL", "INFO")
        
        config.FILE_LOG_ENABLED = os.getenv("LOG_FILE_ENABLED", "true").lower() == "true"
        config.FILE_LOG_LEVEL = os.getenv("LOG_FILE_LEVEL", "DEBUG")
        config.FILE_LOG_PATH = os.getenv("LOG_FILE_PATH", "data/logs")
        
        config.API_LOG_ENABLED = os.getenv("LOG_API_ENABLED", "true").lower() == "true"
        
        config.AUTO_CLEANUP_ENABLED = os.getenv("LOG_AUTO_CLEANUP", "true").lower() == "true"
        config.AUTO_CLEANUP_DAYS = int(os.getenv("LOG_CLEANUP_DAYS", "30"))
        
        config.ASYNC_LOG_ENABLED = os.getenv("LOG_ASYNC_ENABLED", "false").lower() == "true"
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "database_log": {
                "enabled": self.DATABASE_LOG_ENABLED,
                "level": self.DATABASE_LOG_LEVEL
            },
            "file_log": {
                "enabled": self.FILE_LOG_ENABLED,
                "level": self.FILE_LOG_LEVEL,
                "path": self.FILE_LOG_PATH,
                "max_size": self.FILE_LOG_MAX_SIZE,
                "backup_count": self.FILE_LOG_BACKUP_COUNT
            },
            "api_log": {
                "enabled": self.API_LOG_ENABLED,
                "skip_paths": self.API_LOG_SKIP_PATHS
            },
            "cleanup": {
                "enabled": self.AUTO_CLEANUP_ENABLED,
                "days": self.AUTO_CLEANUP_DAYS,
                "interval": self.AUTO_CLEANUP_INTERVAL
            },
            "performance": {
                "async_enabled": self.ASYNC_LOG_ENABLED,
                "batch_size": self.BATCH_LOG_SIZE,
                "batch_timeout": self.BATCH_LOG_TIMEOUT
            },
            "monitoring": {
                "error_rate_threshold": self.ERROR_RATE_THRESHOLD,
                "error_count_threshold": self.ERROR_COUNT_THRESHOLD,
                "monitor_interval": self.MONITOR_INTERVAL
            }
        }


# 全局配置实例
log_config = LogConfig.from_env()