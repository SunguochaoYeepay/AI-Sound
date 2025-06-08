"""
系统监控API模块
对应 Settings.vue 功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, text, and_, or_
from typing import Dict, List, Any, Optional
import os
import json
import time
import logging
import asyncio
import psutil
import shutil
from datetime import datetime, timedelta
import zipfile
import csv

from database import get_db, engine
from models import SystemLog, UsageStats, VoiceProfile, NovelProject, TextSegment
from tts_client import MegaTTS3Client, get_tts_client
from utils import log_system_event, save_upload_file

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/monitor", tags=["系统监控"])

# 备份存储路径
BACKUP_DIR = "../data/backups"
CONFIG_DIR = "../data/config"

@router.get("/system-status")
async def get_system_status(db: Session = Depends(get_db)):
    """
    获取系统状态
    对应前端系统状态面板
    """
    try:
        # 系统基础信息
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('../data')
        
        # 网络连接统计
        network = psutil.net_io_counters()
        
        # 进程信息
        current_process = psutil.Process()
        process_info = {
            "pid": current_process.pid,
            "memoryUsage": current_process.memory_info().rss / 1024 / 1024,  # MB
            "cpuPercent": current_process.cpu_percent(),
            "createTime": datetime.fromtimestamp(current_process.create_time()).isoformat(),
            "numThreads": current_process.num_threads()
        }
        
        # 数据库统计
        voice_count = db.query(VoiceProfile).count()
        project_count = db.query(NovelProject).count()
        active_projects = db.query(NovelProject).filter(
            NovelProject.status.in_(['processing', 'paused'])
        ).count()
        
        # 最近24小时的系统日志统计
        yesterday = datetime.utcnow() - timedelta(days=1)
        log_stats = db.query(
            SystemLog.level,
            func.count(SystemLog.id).label('count')
        ).filter(
            SystemLog.created_at >= yesterday
        ).group_by(SystemLog.level).all()
        
        log_summary = {level: 0 for level in ['info', 'warning', 'error', 'critical']}
        for level, count in log_stats:
            log_summary[level] = count
        
        # 磁盘使用详情
        data_dirs = {
            "audio": "../data/audio",
            "uploads": "../data/uploads", 
            "voice_profiles": "../data/voice_profiles",
            "projects": "../data/projects",
            "backups": "../data/backups"
        }
        
        disk_usage = {}
        for name, path in data_dirs.items():
            if os.path.exists(path):
                size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(path)
                    for filename in filenames
                ) / 1024 / 1024  # MB
                disk_usage[name] = round(size, 2)
            else:
                disk_usage[name] = 0
        
        return {
            "success": True,
            "data": {
                "timestamp": datetime.utcnow().isoformat(),
                "system": {
                    "cpuPercent": round(cpu_percent, 1),
                    "memoryPercent": round(memory.percent, 1),
                    "memoryUsed": round(memory.used / 1024 / 1024 / 1024, 2),  # GB
                    "memoryTotal": round(memory.total / 1024 / 1024 / 1024, 2),  # GB
                    "diskPercent": round(disk.percent, 1),
                    "diskUsed": round(disk.used / 1024 / 1024 / 1024, 2),  # GB
                    "diskTotal": round(disk.total / 1024 / 1024 / 1024, 2),  # GB
                    "networkSent": round(network.bytes_sent / 1024 / 1024, 2),  # MB
                    "networkRecv": round(network.bytes_recv / 1024 / 1024, 2)   # MB
                },
                "process": process_info,
                "database": {
                    "voiceProfiles": voice_count,
                    "projects": project_count,
                    "activeProjects": active_projects
                },
                "logs": log_summary,
                "diskUsage": disk_usage
            }
        }
        
    except Exception as e:
        logger.error(f"获取系统状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")

@router.get("/performance-history")
async def get_performance_history(
    hours: int = Query(24, ge=1, le=168, description="历史小时数"),
    db: Session = Depends(get_db)
):
    """
    获取性能历史数据
    对应前端性能图表展示
    """
    try:
        # 获取历史性能数据（从usage_stats表）
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        stats = db.query(UsageStats).filter(
            UsageStats.created_at >= start_time
        ).order_by(UsageStats.created_at).all()
        
        # 按小时聚合数据
        hourly_data = {}
        for stat in stats:
            hour_key = stat.created_at.strftime('%Y-%m-%d %H:00:00')
            if hour_key not in hourly_data:
                hourly_data[hour_key] = {
                    "timestamp": hour_key,
                    "ttsRequests": 0,
                    "audioGenerated": 0,
                    "storageUsed": 0,
                    "errors": 0
                }
            
            # 聚合统计数据
            details = stat.get_details()
            hourly_data[hour_key]["ttsRequests"] += details.get("requests", 1)
            hourly_data[hour_key]["audioGenerated"] += details.get("audio_duration", 0)
            hourly_data[hour_key]["storageUsed"] += details.get("file_size", 0)
            if details.get("success", True) == False:
                hourly_data[hour_key]["errors"] += 1
        
        # 转换为列表并排序
        performance_data = list(hourly_data.values())
        performance_data.sort(key=lambda x: x["timestamp"])
        
        # 计算趋势
        total_requests = sum(item["ttsRequests"] for item in performance_data)
        total_audio = round(sum(item["audioGenerated"] for item in performance_data) / 60, 2)  # 分钟
        total_storage = round(sum(item["storageUsed"] for item in performance_data) / 1024 / 1024, 2)  # MB
        total_errors = sum(item["errors"] for item in performance_data)
        
        success_rate = 100.0
        if total_requests > 0:
            success_rate = round((total_requests - total_errors) / total_requests * 100, 1)
        
        return {
            "success": True,
            "data": {
                "timeRange": f"最近{hours}小时",
                "summary": {
                    "totalRequests": total_requests,
                    "totalAudioMinutes": total_audio,
                    "totalStorageMB": total_storage,
                    "successRate": success_rate,
                    "errorCount": total_errors
                },
                "history": performance_data
            }
        }
        
    except Exception as e:
        logger.error(f"获取性能历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取性能历史失败: {str(e)}")

@router.get("/service-health")
async def check_service_health():
    """
    检查服务健康状态
    对应前端服务状态监控
    """
    try:
        health_results = {}
        overall_status = "healthy"
        
        # 检查MegaTTS3服务
        try:
            tts_client = get_tts_client()
            megatts3_health = await tts_client.health_check()
            health_results["megatts3"] = {
                "status": "healthy" if megatts3_health.get("status") == "ok" else "unhealthy",
                "responseTime": megatts3_health.get("response_time", 0),
                "version": megatts3_health.get("version", "unknown"),
                "lastCheck": datetime.utcnow().isoformat()
            }
            if health_results["megatts3"]["status"] == "unhealthy":
                overall_status = "degraded"
        except Exception as e:
            health_results["megatts3"] = {
                "status": "unhealthy",
                "error": str(e),
                "lastCheck": datetime.utcnow().isoformat()
            }
            overall_status = "unhealthy"
        
        # 检查数据库连接
        try:
            from database import get_db
            db = next(get_db())
            db.execute(text("SELECT 1"))
            health_results["database"] = {
                "status": "healthy",
                "connectionPool": "active",
                "lastCheck": datetime.utcnow().isoformat()
            }
        except Exception as e:
            health_results["database"] = {
                "status": "unhealthy",
                "error": str(e),
                "lastCheck": datetime.utcnow().isoformat()
            }
            overall_status = "unhealthy"
        
        # 检查磁盘空间
        try:
            disk = psutil.disk_usage('../data')
            disk_status = "healthy"
            if disk.percent > 90:
                disk_status = "critical"
                overall_status = "critical"
            elif disk.percent > 80:
                disk_status = "warning"
                if overall_status == "healthy":
                    overall_status = "degraded"
            
            health_results["storage"] = {
                "status": disk_status,
                "usedPercent": round(disk.percent, 1),
                "freeGB": round(disk.free / 1024 / 1024 / 1024, 2),
                "lastCheck": datetime.utcnow().isoformat()
            }
        except Exception as e:
            health_results["storage"] = {
                "status": "unhealthy",
                "error": str(e),
                "lastCheck": datetime.utcnow().isoformat()
            }
            overall_status = "unhealthy"
        
        # 检查内存使用
        try:
            memory = psutil.virtual_memory()
            memory_status = "healthy"
            if memory.percent > 90:
                memory_status = "critical"
                overall_status = "critical"
            elif memory.percent > 80:
                memory_status = "warning"
                if overall_status == "healthy":
                    overall_status = "degraded"
            
            health_results["memory"] = {
                "status": memory_status,
                "usedPercent": round(memory.percent, 1),
                "availableGB": round(memory.available / 1024 / 1024 / 1024, 2),
                "lastCheck": datetime.utcnow().isoformat()
            }
        except Exception as e:
            health_results["memory"] = {
                "status": "unhealthy",
                "error": str(e),
                "lastCheck": datetime.utcnow().isoformat()
            }
            overall_status = "unhealthy"
        
        return {
            "success": True,
            "data": {
                "overallStatus": overall_status,
                "timestamp": datetime.utcnow().isoformat(),
                "services": health_results
            }
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")

@router.get("/logs")
async def get_system_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    level: str = Query("", description="日志级别过滤"),
    module: str = Query("", description="模块过滤"),
    search: str = Query("", description="搜索关键词"),
    start_date: str = Query("", description="开始日期"),
    end_date: str = Query("", description="结束日期"),
    db: Session = Depends(get_db)
):
    """
    获取系统日志
    对应前端日志查看功能
    """
    try:
        # 构建查询
        query = db.query(SystemLog)
        
        # 级别过滤
        if level and level in ['info', 'warning', 'error', 'critical']:
            query = query.filter(SystemLog.level == level)
        
        # 模块过滤
        if module:
            query = query.filter(SystemLog.module == module)
        
        # 搜索过滤
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    SystemLog.message.like(search_pattern),
                    SystemLog.details_json.like(search_pattern)
                )
            )
        
        # 日期过滤
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                query = query.filter(SystemLog.created_at >= start_dt)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                query = query.filter(SystemLog.created_at <= end_dt)
            except ValueError:
                pass
        
        # 排序（最新的在前）
        query = query.order_by(desc(SystemLog.created_at))
        
        # 统计总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        logs = query.offset(offset).limit(page_size).all()
        
        # 转换为字典格式
        log_list = []
        for log in logs:
            log_dict = {
                "id": log.id,
                "level": log.level,
                "message": log.message,
                "module": log.module,
                "createdAt": log.created_at.isoformat(),
                "details": log.get_details()
            }
            log_list.append(log_dict)
        
        # 分页信息
        total_pages = (total + page_size - 1) // page_size
        
        # 日志级别统计
        level_stats = db.query(
            SystemLog.level,
            func.count(SystemLog.id).label('count')
        ).group_by(SystemLog.level).all()
        
        level_summary = {level: 0 for level in ['info', 'warning', 'error', 'critical']}
        for level_name, count in level_stats:
            level_summary[level_name] = count
        
        return {
            "success": True,
            "data": log_list,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": total_pages,
                "hasMore": page < total_pages
            },
            "filters": {
                "level": level,
                "module": module,
                "search": search,
                "startDate": start_date,
                "endDate": end_date
            },
            "summary": level_summary
        }
        
    except Exception as e:
        logger.error(f"获取系统日志失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取日志失败: {str(e)}")

@router.delete("/logs/cleanup")
async def cleanup_old_logs(
    days: int = Form(30, description="保留天数"),
    level: str = Form("", description="清理特定级别"),
    db: Session = Depends(get_db)
):
    """
    清理旧日志
    对应前端日志清理功能
    """
    try:
        # 计算清理时间点
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 构建删除查询
        query = db.query(SystemLog).filter(SystemLog.created_at < cutoff_date)
        
        if level and level in ['info', 'warning', 'error', 'critical']:
            query = query.filter(SystemLog.level == level)
        
        # 统计要删除的数量
        delete_count = query.count()
        
        # 执行删除
        query.delete()
        db.commit()
        
        # 记录清理日志
        await log_system_event(
            db=db,
            level="info",
            message=f"日志清理完成",
            module="monitor",
            details={
                "deleted_count": delete_count,
                "cutoff_days": days,
                "level_filter": level or "all"
            }
        )
        
        return {
            "success": True,
            "message": f"清理完成，删除了 {delete_count} 条日志",
            "deletedCount": delete_count
        }
        
    except Exception as e:
        logger.error(f"清理日志失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")

@router.get("/settings")
async def get_system_settings():
    """
    获取系统设置
    对应前端设置管理功能
    """
    try:
        # 读取配置文件
        settings_file = os.path.join(CONFIG_DIR, "settings.json")
        default_settings = {
            "tts": {
                "default_time_step": 20,
                "default_p_weight": 1.0,
                "default_t_weight": 1.0,
                "max_text_length": 1000,
                "concurrent_limit": 3
            },
            "storage": {
                "max_audio_file_size": 100,  # MB
                "max_upload_file_size": 50,  # MB
                "auto_cleanup_days": 30,
                "backup_retention_days": 90
            },
            "security": {
                "allowed_audio_formats": ["wav", "mp3", "flac", "m4a", "ogg"],
                "max_requests_per_minute": 60,
                "enable_rate_limiting": True
            },
            "monitoring": {
                "log_level": "info",
                "enable_performance_tracking": True,
                "health_check_interval": 60,  # seconds
                "alert_thresholds": {
                    "cpu_percent": 80,
                    "memory_percent": 80,
                    "disk_percent": 90
                }
            }
        }
        
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                # 合并默认设置（确保所有字段都存在）
                for category, defaults in default_settings.items():
                    if category not in settings:
                        settings[category] = defaults
                    else:
                        for key, default_value in defaults.items():
                            if key not in settings[category]:
                                settings[category][key] = default_value
            except json.JSONDecodeError:
                settings = default_settings
        else:
            settings = default_settings
            # 创建配置目录和默认配置文件
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "data": settings
        }
        
    except Exception as e:
        logger.error(f"获取系统设置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取设置失败: {str(e)}")

@router.put("/settings")
async def update_system_settings(
    settings_data: str = Form(..., description="设置JSON数据"),
    db: Session = Depends(get_db)
):
    """
    更新系统设置
    对应前端设置保存功能
    """
    try:
        # 解析设置数据
        try:
            new_settings = json.loads(settings_data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="设置数据格式错误")
        
        # 验证设置数据
        required_categories = ["tts", "storage", "security", "monitoring"]
        for category in required_categories:
            if category not in new_settings:
                raise HTTPException(status_code=400, detail=f"缺少设置分类: {category}")
        
        # 保存到配置文件
        os.makedirs(CONFIG_DIR, exist_ok=True)
        settings_file = os.path.join(CONFIG_DIR, "settings.json")
        
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(new_settings, f, indent=2, ensure_ascii=False)
        
        # 记录设置更新日志
        await log_system_event(
            db=db,
            level="info",
            message="系统设置已更新",
            module="monitor",
            details={
                "updated_categories": list(new_settings.keys()),
                "updated_by": "admin"  # 实际应用中应该是当前用户
            }
        )
        
        return {
            "success": True,
            "message": "系统设置更新成功",
            "data": new_settings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新系统设置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新设置失败: {str(e)}")

@router.post("/backup/create")
async def create_backup(
    background_tasks: BackgroundTasks,
    include_audio: bool = Form(False, description="包含音频文件"),
    include_logs: bool = Form(True, description="包含日志文件"),
    backup_name: str = Form("", description="备份名称"),
    db: Session = Depends(get_db)
):
    """
    创建系统备份
    对应前端数据备份功能
    """
    try:
        # 生成备份名称
        if not backup_name:
            backup_name = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # 启动后台备份任务
        background_tasks.add_task(
            perform_backup_task,
            backup_name,
            include_audio,
            include_logs
        )
        
        # 记录备份开始日志
        await log_system_event(
            db=db,
            level="info",
            message=f"备份任务已启动: {backup_name}",
            module="monitor",
            details={
                "backup_name": backup_name,
                "include_audio": include_audio,
                "include_logs": include_logs
            }
        )
        
        return {
            "success": True,
            "message": f"备份任务 '{backup_name}' 已启动",
            "backupName": backup_name
        }
        
    except Exception as e:
        logger.error(f"创建备份失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建备份失败: {str(e)}")

@router.get("/backup/list")
async def list_backups():
    """
    获取备份列表
    对应前端备份管理功能
    """
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        backups = []
        for filename in os.listdir(BACKUP_DIR):
            if filename.endswith('.zip'):
                file_path = os.path.join(BACKUP_DIR, filename)
                file_stat = os.stat(file_path)
                
                backup_info = {
                    "name": filename.replace('.zip', ''),
                    "filename": filename,
                    "size": round(file_stat.st_size / 1024 / 1024, 2),  # MB
                    "createdAt": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                    "modifiedAt": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                }
                backups.append(backup_info)
        
        # 按创建时间倒序排列
        backups.sort(key=lambda x: x["createdAt"], reverse=True)
        
        return {
            "success": True,
            "data": backups
        }
        
    except Exception as e:
        logger.error(f"获取备份列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取备份列表失败: {str(e)}")

@router.get("/backup/download/{backup_name}")
async def download_backup(backup_name: str):
    """
    下载备份文件
    对应前端备份下载功能
    """
    try:
        backup_file = os.path.join(BACKUP_DIR, f"{backup_name}.zip")
        
        if not os.path.exists(backup_file):
            raise HTTPException(status_code=404, detail="备份文件不存在")
        
        return FileResponse(
            path=backup_file,
            filename=f"{backup_name}.zip",
            media_type="application/zip"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载备份失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")

@router.delete("/backup/{backup_name}")
async def delete_backup(
    backup_name: str,
    db: Session = Depends(get_db)
):
    """
    删除备份文件
    对应前端备份删除功能
    """
    try:
        backup_file = os.path.join(BACKUP_DIR, f"{backup_name}.zip")
        
        if not os.path.exists(backup_file):
            raise HTTPException(status_code=404, detail="备份文件不存在")
        
        # 获取文件大小用于日志
        file_size = os.path.getsize(backup_file) / 1024 / 1024  # MB
        
        # 删除文件
        os.remove(backup_file)
        
        # 记录删除日志
        await log_system_event(
            db=db,
            level="info",
            message=f"备份文件已删除: {backup_name}",
            module="monitor",
            details={
                "backup_name": backup_name,
                "file_size_mb": round(file_size, 2)
            }
        )
        
        return {
            "success": True,
            "message": f"备份文件 '{backup_name}' 删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除备份失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@router.post("/maintenance/cleanup")
async def perform_maintenance(
    background_tasks: BackgroundTasks,
    cleanup_temp_files: bool = Form(True, description="清理临时文件"),
    cleanup_old_logs: bool = Form(True, description="清理旧日志"),
    optimize_database: bool = Form(True, description="优化数据库"),
    days_to_keep: int = Form(30, description="保留天数"),
    db: Session = Depends(get_db)
):
    """
    执行系统维护
    对应前端系统维护功能
    """
    try:
        # 启动后台维护任务
        background_tasks.add_task(
            perform_maintenance_task,
            cleanup_temp_files,
            cleanup_old_logs,
            optimize_database,
            days_to_keep
        )
        
        # 记录维护开始日志
        await log_system_event(
            db=db,
            level="info",
            message="系统维护任务已启动",
            module="monitor",
            details={
                "cleanup_temp_files": cleanup_temp_files,
                "cleanup_old_logs": cleanup_old_logs,
                "optimize_database": optimize_database,
                "days_to_keep": days_to_keep
            }
        )
        
        return {
            "success": True,
            "message": "系统维护任务已启动",
            "operations": {
                "cleanupTempFiles": cleanup_temp_files,
                "cleanupOldLogs": cleanup_old_logs,
                "optimizeDatabase": optimize_database
            }
        }
        
    except Exception as e:
        logger.error(f"启动维护任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动维护失败: {str(e)}")

# 后台任务函数

async def perform_backup_task(backup_name: str, include_audio: bool, include_logs: bool):
    """执行备份任务"""
    try:
        from database import SessionLocal
        db = SessionLocal()
        
        try:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            backup_path = os.path.join(BACKUP_DIR, f"{backup_name}.zip")
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 备份数据库
                db_file = "../data/ai_sound.db"
                if os.path.exists(db_file):
                    zipf.write(db_file, "database/ai_sound.db")
                
                # 备份配置文件
                config_files = ["../data/config/settings.json"]
                for config_file in config_files:
                    if os.path.exists(config_file):
                        zipf.write(config_file, f"config/{os.path.basename(config_file)}")
                
                # 备份声音档案
                voice_profiles_dir = "../data/voice_profiles"
                if os.path.exists(voice_profiles_dir):
                    for root, dirs, files in os.walk(voice_profiles_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = file_path.replace("../data/", "")
                            zipf.write(file_path, arcname)
                
                # 可选：备份音频文件
                if include_audio:
                    audio_dirs = ["../data/audio", "../data/uploads"]
                    for audio_dir in audio_dirs:
                        if os.path.exists(audio_dir):
                            for root, dirs, files in os.walk(audio_dir):
                                for file in files:
                                    file_path = os.path.join(root, file)
                                    arcname = file_path.replace("../data/", "")
                                    zipf.write(file_path, arcname)
                
                # 可选：备份日志文件
                if include_logs:
                    logs_dir = "../data/logs"
                    if os.path.exists(logs_dir):
                        for root, dirs, files in os.walk(logs_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = file_path.replace("../data/", "")
                                zipf.write(file_path, arcname)
            
            # 记录备份完成日志
            backup_size = os.path.getsize(backup_path) / 1024 / 1024  # MB
            await log_system_event(
                db=db,
                level="info",
                message=f"备份任务完成: {backup_name}",
                module="monitor",
                details={
                    "backup_name": backup_name,
                    "backup_size_mb": round(backup_size, 2),
                    "include_audio": include_audio,
                    "include_logs": include_logs
                }
            )
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"备份任务失败: {str(e)}")

async def perform_maintenance_task(
    cleanup_temp_files: bool,
    cleanup_old_logs: bool, 
    optimize_database: bool,
    days_to_keep: int
):
    """执行维护任务"""
    try:
        from database import SessionLocal
        db = SessionLocal()
        
        try:
            maintenance_results = {}
            
            # 清理临时文件
            if cleanup_temp_files:
                temp_cleaned = 0
                temp_dirs = ["../data/temp", "../data/cache"]
                for temp_dir in temp_dirs:
                    if os.path.exists(temp_dir):
                        for root, dirs, files in os.walk(temp_dir):
                            for file in files:
                                try:
                                    os.remove(os.path.join(root, file))
                                    temp_cleaned += 1
                                except:
                                    pass
                maintenance_results["temp_files_cleaned"] = temp_cleaned
            
            # 清理旧日志
            if cleanup_old_logs:
                cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
                deleted_logs = db.query(SystemLog).filter(
                    SystemLog.created_at < cutoff_date
                ).count()
                
                db.query(SystemLog).filter(
                    SystemLog.created_at < cutoff_date
                ).delete()
                
                maintenance_results["logs_cleaned"] = deleted_logs
            
            # 优化数据库
            if optimize_database:
                try:
                    db.execute(text("VACUUM"))
                    db.execute(text("ANALYZE"))
                    maintenance_results["database_optimized"] = True
                except Exception as e:
                    maintenance_results["database_optimized"] = False
                    maintenance_results["database_error"] = str(e)
            
            db.commit()
            
            # 记录维护完成日志
            await log_system_event(
                db=db,
                level="info",
                message="系统维护任务完成",
                module="monitor",
                details=maintenance_results
            )
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"维护任务失败: {str(e)}") 