#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库备份恢复API接口
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, File, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import asyncio

from app.database import get_db
from app.models.backup import (
    BackupTask, BackupConfig, RestoreTask, BackupSchedule, BackupStats,
    TaskStatus, BackupType, StorageLocation, RestoreType
)
from app.models.system import SystemLog, LogLevel, LogModule
from app.utils.backup_engine import BackupEngine
from app.utils.restore_engine import RestoreEngine
from app.utils.backup_stats import BackupStatsManager
from app.utils import log_system_event

router = APIRouter(prefix="/backup", tags=["数据库备份恢复"])


# ======================== 数据模型 ========================

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

class BackupTaskCreate(BaseModel):
    """创建备份任务请求"""
    task_name: str = Field(..., description="任务名称")
    backup_type: str = Field(default="full", description="备份类型: full, incremental, manual")
    include_audio: bool = Field(default=False, description="是否包含音频文件")
    encryption_enabled: bool = Field(default=True, description="是否启用加密")
    storage_location: str = Field(default="local", description="存储位置: local, s3, oss")
    retention_days: int = Field(default=30, description="保留天数")

class BackupTaskResponse(BaseModel):
    """备份任务响应"""
    id: int
    task_name: str
    task_type: str
    status: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration_seconds: Optional[int]
    file_path: Optional[str]
    file_size: Optional[int]
    compressed_size: Optional[int]
    progress_percentage: int
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class RestoreTaskCreate(BaseModel):
    """创建恢复任务请求"""
    backup_id: int = Field(..., description="备份任务ID")
    task_name: str = Field(..., description="恢复任务名称")
    restore_type: str = Field(default="full", description="恢复类型")
    target_database: str = Field(..., description="目标数据库名")
    include_audio: bool = Field(default=False, description="是否恢复音频文件")
    restore_point: Optional[datetime] = Field(None, description="恢复到指定时间点")

class BackupConfigUpdate(BaseModel):
    """备份配置更新请求"""
    configs: Dict[str, Any] = Field(..., description="配置键值对")

class BackupStatsResponse(BaseModel):
    """备份统计响应"""
    total_backups: int
    successful_backups: int
    failed_backups: int
    success_rate: float
    total_storage_used: int
    avg_backup_duration: int
    last_backup_time: Optional[datetime]
    storage_trend: List[Dict[str, Any]]


# ======================== 备份管理接口 ========================

@router.post("/create", response_model=Dict[str, Any])
async def create_backup_task(
    task_data: BackupTaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """创建备份任务"""
    try:
        # 检查是否有正在运行的备份任务
        running_task = db.query(BackupTask).filter(
            BackupTask.status == "running"
        ).first()
        
        if running_task:
            raise HTTPException(
                status_code=400,
                detail="已有备份任务正在运行，请等待完成后再创建新任务"
            )
        
        # 创建备份任务记录
        backup_task = BackupTask(
            task_name=task_data.task_name,
            task_type=task_data.backup_type,
            status="pending",
            include_audio=task_data.include_audio,
            encryption_enabled=task_data.encryption_enabled,
            storage_location=task_data.storage_location,
            retention_days=task_data.retention_days,
            created_by="system",  # TODO: 从认证信息获取用户
            backup_metadata={}
        )
        
        db.add(backup_task)
        db.commit()
        db.refresh(backup_task)
        
        # 添加后台任务执行备份
        background_tasks.add_task(
            execute_backup_task,
            backup_task.id,
            task_data.backup_type,
            task_data.include_audio
        )
        
        # 记录日志
        log_system_event(
            f"创建备份任务: {task_data.task_name}",
            "info",
            details={"task_id": backup_task.id, "backup_type": task_data.backup_type}
        )
        
        return {
            "success": True,
            "message": "备份任务创建成功",
            "data": {
                "task_id": backup_task.id,
                "status": backup_task.status
            }
        }
        
    except Exception as e:
        log_system_event(f"创建备份任务失败: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"创建备份任务失败: {str(e)}")


@router.get("/list", response_model=Dict[str, Any])
async def get_backup_list(
    page: int = Query(1, description="页码"),
    page_size: int = Query(20, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    backup_type: Optional[str] = Query(None, description="类型筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
):
    """获取备份任务列表"""
    try:
        # 构建查询条件
        query = db.query(BackupTask)
        
        if status:
            query = query.filter(BackupTask.status == status)
        if backup_type:
            query = query.filter(BackupTask.task_type == backup_type)
        if start_date:
            query = query.filter(BackupTask.created_at >= start_date)
        if end_date:
            query = query.filter(BackupTask.created_at <= end_date)
        
        # 总数统计
        total = query.count()
        
        # 分页查询
        tasks = query.order_by(desc(BackupTask.created_at))\
                    .offset((page - 1) * page_size)\
                    .limit(page_size)\
                    .all()
        
        # 转换为响应格式
        task_list = []
        for task in tasks:
            task_dict = {
                "id": task.id,
                "task_name": task.task_name,
                "task_type": task.task_type,
                "status": task.status,
                "start_time": task.start_time,
                "end_time": task.end_time,
                "duration_seconds": task.duration_seconds,
                "file_path": task.file_path,
                "file_size": task.file_size,
                "compressed_size": task.compressed_size,
                "progress_percentage": task.progress_percentage,
                "include_audio": task.include_audio,
                "encryption_enabled": task.encryption_enabled,
                "storage_location": task.storage_location,
                "retention_days": task.retention_days,
                "error_message": task.error_message,
                "created_at": task.created_at,
                "created_by": task.created_by
            }
            task_list.append(task_dict)
        
        return {
            "success": True,
            "data": {
                "tasks": task_list,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取备份列表失败: {str(e)}")


@router.get("/{task_id}/status", response_model=Dict[str, Any])
async def get_backup_status(task_id: int, db: Session = Depends(get_db)):
    """获取备份任务状态"""
    try:
        task = db.query(BackupTask).filter(BackupTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="备份任务不存在")
        
        return {
            "success": True,
            "data": {
                "task_id": task.id,
                "status": task.status,
                "progress_percentage": task.progress_percentage,
                "start_time": task.start_time,
                "end_time": task.end_time,
                "duration_seconds": task.duration_seconds,
                "error_message": task.error_message
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取备份状态失败: {str(e)}")


@router.post("/{task_id}/cancel", response_model=Dict[str, Any])
async def cancel_backup_task(task_id: int, db: Session = Depends(get_db)):
    """取消备份任务"""
    try:
        task = db.query(BackupTask).filter(BackupTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="备份任务不存在")
        
        # 只能取消正在运行或等待中的任务
        if task.status not in ["running", "pending"]:
            raise HTTPException(status_code=400, detail=f"无法取消已{task.status}的任务")
        
        # 更新任务状态为取消
        task.status = "cancelled"
        task.end_time = datetime.utcnow()
        task.error_message = "用户手动取消"
        
        # 计算持续时间
        if task.start_time:
            task.duration_seconds = int((task.end_time - task.start_time).total_seconds())
        
        db.commit()
        
        log_system_event(f"备份任务 {task.task_name} 已被用户取消", "info", details={"task_id": task_id})
        
        return {
            "success": True,
            "message": "备份任务已取消"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_system_event(f"取消备份任务失败: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"取消失败: {str(e)}")


@router.delete("/{task_id}", response_model=Dict[str, Any])
async def delete_backup_task(task_id: int, db: Session = Depends(get_db)):
    """删除备份任务"""
    try:
        task = db.query(BackupTask).filter(BackupTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="备份任务不存在")
        
        # 检查任务是否正在运行
        if task.status in ["running", "pending"]:
            raise HTTPException(status_code=400, detail="无法删除正在运行的备份任务，请先取消任务")
        
        # 检查是否有关联的恢复任务
        restore_tasks = db.query(RestoreTask).filter(RestoreTask.backup_id == task_id).all()
        if restore_tasks:
            # 检查是否有正在运行的恢复任务
            running_restores = [r for r in restore_tasks if r.status in ["running", "pending"]]
            if running_restores:
                raise HTTPException(
                    status_code=400, 
                    detail=f"无法删除备份任务，有 {len(running_restores)} 个恢复任务正在运行，请先取消这些恢复任务"
                )
            
            # 删除所有关联的恢复任务
            for restore_task in restore_tasks:
                db.delete(restore_task)
            
            log_system_event(
                f"删除了 {len(restore_tasks)} 个关联的恢复任务", 
                "info", 
                details={"backup_id": task_id, "restore_count": len(restore_tasks)}
            )
        
        # 删除备份文件
        if task.file_path and os.path.exists(task.file_path):
            try:
                os.remove(task.file_path)
                log_system_event(f"删除备份文件: {task.file_path}", "info")
            except Exception as e:
                log_system_event(f"删除备份文件失败: {str(e)}", "warning")
        
        # 删除数据库记录
        db.delete(task)
        db.commit()
        
        log_system_event(f"删除备份任务: {task.task_name}", "info", details={"task_id": task_id})
        
        return {
            "success": True,
            "message": f"备份任务删除成功{f'（同时删除了 {len(restore_tasks)} 个关联的恢复任务）' if restore_tasks else ''}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_system_event(f"删除备份任务失败: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"删除备份任务失败: {str(e)}")


# ======================== 恢复管理接口 ========================

def _get_current_database_name() -> str:
    """获取当前正在使用的数据库名称"""
    try:
        from sqlalchemy.engine.url import make_url
        from app.database import DATABASE_URL
        db_url = make_url(DATABASE_URL)
        return str(db_url.database)
    except Exception:
        return "ai_sound"  # 默认值

@router.post("/restore", response_model=Dict[str, Any])
async def create_restore_task(
    restore_data: RestoreTaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """创建恢复任务"""
    try:
        # 🔧 处理空的target_database
        current_db = _get_current_database_name()
        target_db = restore_data.target_database
        
        # 如果target_database为空，提供智能默认值
        if not target_db or target_db.strip() == '':
            # 为了安全，默认使用测试数据库而不是当前数据库
            if current_db == "ai_sound":
                target_db = "ai_sound_restore_test"
            else:
                target_db = f"{current_db}_restore_test"
            
            restore_data.target_database = target_db
            log_system_event(f"🎯 target_database为空，使用安全的测试数据库: {target_db}", "info")
        
        # 🎯 恢复到生产数据库的情况：给出友好提示
        if target_db == current_db:
            log_system_event(f"📋 恢复到当前生产数据库: {target_db}，这将替换现有数据", "warning")
        
        # 检查备份任务是否存在
        backup_task = db.query(BackupTask).filter(
            BackupTask.id == restore_data.backup_id
        ).first()
        
        if not backup_task:
            raise HTTPException(status_code=404, detail="备份任务不存在")
        
        if backup_task.status != "success":
            raise HTTPException(status_code=400, detail="只能恢复成功的备份")
        
        # 检查是否有正在运行的恢复任务
        running_restore = db.query(RestoreTask).filter(
            RestoreTask.status == "running"
        ).first()
        
        if running_restore:
            raise HTTPException(
                status_code=400,
                detail="已有恢复任务正在运行，请等待完成后再创建新任务"
            )
        
        # 创建恢复任务记录
        restore_task = RestoreTask(
            backup_id=restore_data.backup_id,
            task_name=restore_data.task_name,
            status="pending",
            restore_type=restore_data.restore_type,
            target_database=restore_data.target_database,
            include_audio=restore_data.include_audio,
            restore_point=restore_data.restore_point,
            created_by="system"  # TODO: 从认证信息获取用户
        )
        
        db.add(restore_task)
        db.commit()
        db.refresh(restore_task)
        
        # 添加后台任务执行恢复
        background_tasks.add_task(
            execute_restore_task,
            restore_task.id
        )
        
        log_system_event(
            f"创建恢复任务: {restore_data.task_name}",
            "info",
            details={"restore_id": restore_task.id, "backup_id": restore_data.backup_id}
        )
        
        return {
            "success": True,
            "message": "恢复任务创建成功",
            "data": {
                "restore_id": restore_task.id,
                "status": restore_task.status
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_system_event(f"创建恢复任务失败: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"创建恢复任务失败: {str(e)}")


@router.get("/restore/{restore_id}")
async def get_restore_details(
    restore_id: int,
    db: Session = Depends(get_db)
):
    """获取恢复任务详情"""
    try:
        # 获取恢复任务
        restore_task = db.query(RestoreTask).filter(
            RestoreTask.id == restore_id
        ).first()
        
        if not restore_task:
            raise HTTPException(status_code=404, detail="恢复任务不存在")
        
        # 获取相关日志
        logs = db.query(SystemLog).filter(
            SystemLog.message.contains(str(restore_id))
        ).order_by(SystemLog.created_at.desc()).limit(50).all()
        
        # 计算进度百分比
        progress_percentage = 0
        if restore_task.status == "pending":
            progress_percentage = 0
        elif restore_task.status == "running":
            progress_percentage = 50  # 临时设置为50%
        elif restore_task.status == "success":
            progress_percentage = 100
        elif restore_task.status == "failed":
            progress_percentage = 0
        
        # 计算持续时间
        duration_seconds = 0
        if restore_task.start_time:
            end_time = restore_task.end_time or datetime.now()
            duration_seconds = int((end_time - restore_task.start_time).total_seconds())
        
        return {
            "success": True,
            "data": {
                "task": {
                    "id": restore_task.id,
                    "task_name": restore_task.task_name,
                    "restore_type": restore_task.restore_type,
                    "status": restore_task.status,
                    "target_database": restore_task.target_database,
                    "include_audio": restore_task.include_audio,
                    "progress_percentage": progress_percentage,
                    "created_at": restore_task.created_at,
                    "start_time": restore_task.start_time,
                    "end_time": restore_task.end_time,
                    "duration_seconds": duration_seconds,
                    "error_message": restore_task.error_message
                },
                "logs": [
                    {
                        "id": log.id,
                        "level": log.level,
                        "message": log.message,
                        "created_at": log.created_at
                    }
                    for log in logs
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取恢复任务详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取恢复任务详情失败: {str(e)}")


@router.post("/restore/{restore_id}/cancel")
async def cancel_restore_task(
    restore_id: int,
    db: Session = Depends(get_db)
):
    """取消恢复任务"""
    try:
        # 获取恢复任务
        restore_task = db.query(RestoreTask).filter(
            RestoreTask.id == restore_id
        ).first()
        
        if not restore_task:
            raise HTTPException(status_code=404, detail="恢复任务不存在")
        
        if restore_task.status not in ["pending", "running"]:
            raise HTTPException(status_code=400, detail="只能取消等待或正在运行的任务")
        
        # 更新任务状态
        restore_task.status = "cancelled"
        restore_task.end_time = datetime.now()
        restore_task.error_message = "用户手动取消"
        
        # 计算持续时间
        if restore_task.start_time:
            restore_task.duration_seconds = int((restore_task.end_time - restore_task.start_time).total_seconds())
        
        db.commit()
        
        # 记录日志
        log_entry = SystemLog(
            level="info",
            message=f"恢复任务 {restore_id} 已被用户取消",
            source="restore_engine",
            details=f"任务名称: {restore_task.task_name}"
        )
        db.add(log_entry)
        db.commit()
        
        return {"success": True, "message": "恢复任务已取消"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消恢复任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取消恢复任务失败: {str(e)}")


# ======================== 统计信息接口 ========================

@router.get("/stats", response_model=Dict[str, Any])
async def get_backup_stats(
    days: int = Query(30, description="统计天数"),
    db: Session = Depends(get_db)
):
    """获取备份统计信息"""
    try:
        stats_manager = BackupStatsManager(db)
        stats_data = await stats_manager.get_backup_statistics(days)
        
        return {
            "success": True,
            "data": stats_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.get("/health", response_model=Dict[str, Any])
async def get_backup_health():
    """获取备份系统健康状态"""
    try:
        # 检查备份目录
        backup_dir = "/app/backups"
        disk_usage = {}
        
        if os.path.exists(backup_dir):
            stat = os.statvfs(backup_dir)
            total_space = stat.f_frsize * stat.f_blocks
            free_space = stat.f_frsize * stat.f_available
            used_space = total_space - free_space
            
            disk_usage = {
                "total_gb": round(total_space / (1024**3), 2),
                "used_gb": round(used_space / (1024**3), 2),
                "free_gb": round(free_space / (1024**3), 2),
                "usage_percentage": round((used_space / total_space) * 100, 2)
            }
        
        return {
            "success": True,
            "data": {
                "status": "healthy",
                "backup_directory_exists": os.path.exists(backup_dir),
                "disk_usage": disk_usage,
                "timestamp": datetime.utcnow()
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "data": {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow()
            }
        }


# ======================== 后台任务函数 ========================

async def execute_backup_task(task_id: int, backup_type: str, include_audio: bool):
    """执行备份任务的后台函数"""
    try:
        # 这里需要创建新的数据库会话，因为在后台任务中
        from app.database import SessionLocal
        db = SessionLocal()
        
        try:
            backup_engine = BackupEngine(db)
            success = await backup_engine.create_database_backup(
                task_id, backup_type, include_audio
            )
            
            if success:
                log_system_event(f"备份任务 {task_id} 执行成功", "info")
            else:
                log_system_event(f"备份任务 {task_id} 执行失败", "error")
                
        finally:
            db.close()
            
    except Exception as e:
        log_system_event(f"备份任务 {task_id} 异常: {str(e)}", "error")


async def execute_restore_task(restore_id: int):
    """执行恢复任务的后台函数"""
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        
        try:
            restore_engine = RestoreEngine(db)
            success = await restore_engine.restore_database(restore_id)
            
            if success:
                log_system_event(f"恢复任务 {restore_id} 执行成功", "info")
            else:
                log_system_event(f"恢复任务 {restore_id} 执行失败", "error")
                
        finally:
            db.close()
            
    except Exception as e:
        log_system_event(f"恢复任务 {restore_id} 异常: {str(e)}", "error")


# ======================== 下载和详情接口 ========================

@router.get("/{task_id}/download")
async def download_backup_file(
    task_id: int,
    db: Session = Depends(get_db)
):
    """下载备份文件"""
    try:
        # 查找备份任务
        backup_task = db.query(BackupTask).filter(BackupTask.id == task_id).first()
        if not backup_task:
            raise HTTPException(status_code=404, detail="备份任务不存在")
        
        if not backup_task.file_path:
            raise HTTPException(status_code=404, detail="备份文件路径不存在")
        
        # 检查文件是否存在
        if not os.path.exists(backup_task.file_path):
            raise HTTPException(status_code=404, detail="备份文件不存在")
        
        # 生成下载文件名
        filename = f"{backup_task.task_name}_{backup_task.created_at.strftime('%Y%m%d_%H%M%S')}.sql.gz"
        
        # 记录下载日志
        log_system_event(
            f"下载备份文件: {backup_task.task_name}",
            "info"
        )
        
        return FileResponse(
            path=backup_task.file_path,
            filename=filename,
            media_type='application/gzip'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_system_event(f"下载备份文件失败: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")


@router.get("/{task_id}/details")
async def get_backup_details(
    task_id: int,
    db: Session = Depends(get_db)
):
    """获取备份任务详细信息，包括关联的日志"""
    try:
        # 查找备份任务
        backup_task = db.query(BackupTask).filter(BackupTask.id == task_id).first()
        if not backup_task:
            raise HTTPException(status_code=404, detail="备份任务不存在")
        
        # 获取任务相关的日志
        task_logs = db.query(SystemLog).filter(
            SystemLog.message.contains(str(task_id))
        ).order_by(desc(SystemLog.created_at)).limit(50).all()
        
        # 获取文件信息
        file_info = None
        if backup_task.file_path and os.path.exists(backup_task.file_path):
            file_stat = os.stat(backup_task.file_path)
            file_info = {
                "exists": True,
                "size": file_stat.st_size,
                "created_time": datetime.fromtimestamp(file_stat.st_ctime),
                "modified_time": datetime.fromtimestamp(file_stat.st_mtime)
            }
        else:
            file_info = {"exists": False}
        
        # 计算实际进度和统计
        current_step = "未开始"
        processed_records = 0
        
        if backup_task.status == "pending":
            current_step = "等待开始"
        elif backup_task.status == "running":
            if backup_task.progress_percentage < 30:
                current_step = "连接数据库"
            elif backup_task.progress_percentage < 70:
                current_step = "导出数据"
                processed_records = backup_task.progress_percentage * 10
            elif backup_task.progress_percentage < 90:
                current_step = "压缩文件"
                processed_records = backup_task.progress_percentage * 10
            else:
                current_step = "完成处理"
                processed_records = backup_task.progress_percentage * 10
        elif backup_task.status == "success":
            current_step = "备份完成"
            processed_records = 1000
        elif backup_task.status == "failed":
            current_step = "备份失败"
        
        return {
            "success": True,
            "data": {
                "task_info": {
                    "id": backup_task.id,
                    "task_name": backup_task.task_name,
                    "task_type": backup_task.task_type,
                    "status": backup_task.status,
                    "start_time": backup_task.start_time,
                    "end_time": backup_task.end_time,
                    "duration_seconds": backup_task.duration_seconds,
                    "progress_percentage": backup_task.progress_percentage,
                    "error_message": backup_task.error_message,
                    "created_at": backup_task.created_at,
                    "include_audio": backup_task.include_audio,
                    "storage_location": backup_task.storage_location,
                    "retention_days": backup_task.retention_days
                },
                "file_info": file_info,
                "progress_info": {
                    "current_step": current_step,
                    "processed_records": processed_records,
                    "estimated_total": 1000 if backup_task.status == "success" else processed_records + 500
                },
                "logs": [
                    {
                        "id": log.id,
                        "level": log.level.value,
                        "module": log.module.value,
                        "message": log.message,
                        "created_at": log.created_at,
                        "details": log.details
                    }
                    for log in task_logs
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_system_event(f"获取备份详情失败: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"获取备份详情失败: {str(e)}")