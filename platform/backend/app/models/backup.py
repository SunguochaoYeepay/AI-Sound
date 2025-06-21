#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份相关数据库模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Enum as SQLEnum
from datetime import datetime
from enum import Enum
from .base import Base


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BackupType(str, Enum):
    """备份类型枚举"""
    FULL = "full"
    INCREMENTAL = "incremental"
    MANUAL = "manual"


class StorageLocation(str, Enum):
    """存储位置枚举"""
    LOCAL = "local"
    S3 = "s3"
    OSS = "oss"


class RestoreType(str, Enum):
    """恢复类型枚举"""
    FULL = "full"
    PARTIAL = "partial"
    POINT_IN_TIME = "point_in_time"


class BackupTask(Base):
    """备份任务模型"""
    __tablename__ = 'backup_tasks'
    
    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(255), nullable=False)
    task_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    compressed_size = Column(Integer, nullable=True)
    progress_percentage = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    include_audio = Column(Boolean, default=False)
    encryption_enabled = Column(Boolean, default=True)
    storage_location = Column(String(50), default="local")
    retention_days = Column(Integer, default=30)
    created_by = Column(String(100), nullable=True)
    backup_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BackupConfig(Base):
    """备份配置模型"""
    __tablename__ = 'backup_configs'
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RestoreTask(Base):
    """恢复任务模型"""
    __tablename__ = 'restore_tasks'
    
    id = Column(Integer, primary_key=True, index=True)
    backup_id = Column(Integer, nullable=False)
    task_name = Column(String(255), nullable=False)
    restore_type = Column(String(50), nullable=False)
    target_database = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    progress_percentage = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    include_audio = Column(Boolean, default=False)
    restore_point = Column(DateTime, nullable=True)
    created_by = Column(String(100), nullable=True)
    restore_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BackupSchedule(Base):
    """备份计划模型"""
    __tablename__ = 'backup_schedules'
    
    id = Column(Integer, primary_key=True, index=True)
    schedule_name = Column(String(255), nullable=False)
    backup_type = Column(String(50), nullable=False)
    cron_expression = Column(String(100), nullable=False)
    is_enabled = Column(Boolean, default=True)
    include_audio = Column(Boolean, default=False)
    encryption_enabled = Column(Boolean, default=True)
    storage_location = Column(String(50), default="local")
    retention_days = Column(Integer, default=30)
    last_run_time = Column(DateTime, nullable=True)
    next_run_time = Column(DateTime, nullable=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BackupStats(Base):
    """备份统计模型"""
    __tablename__ = 'backup_stats'
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False)
    total_backups = Column(Integer, default=0)
    successful_backups = Column(Integer, default=0)
    failed_backups = Column(Integer, default=0)
    total_storage_used = Column(Integer, default=0)
    avg_backup_duration = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow) 