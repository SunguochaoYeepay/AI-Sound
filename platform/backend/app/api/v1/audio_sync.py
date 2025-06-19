#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频同步API模块
提供改进的音频文件同步功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import logging
from datetime import datetime

from app.database import get_db
from app.services.audio_sync_service import audio_sync_service
from app.services.audio_sync_scheduler import audio_sync_scheduler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audio-sync", tags=["Audio Sync"])


@router.post("/sync-all", summary="同步所有音频文件")
async def sync_all_audio_files(
    full_scan: bool = Query(False, description="是否执行完整扫描"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    同步所有音频文件（音频库 + 环境音）
    """
    try:
        if background_tasks:
            # 后台执行
            background_tasks.add_task(
                sync_all_background_task,
                full_scan=full_scan
            )
            return {
                "success": True,
                "message": "音频同步任务已启动，将在后台执行",
                "task_status": "started"
            }
        else:
            # 同步执行
            results = audio_sync_service.sync_all(db, full_scan=full_scan)
            
            # 汇总结果
            total_scanned = sum(r.scanned_files for r in results.values())
            total_new = sum(r.new_files for r in results.values())
            total_updated = sum(r.updated_files for r in results.values())
            total_orphaned = sum(r.orphaned_records for r in results.values())
            total_errors = sum(len(r.errors) for r in results.values())
            
            return {
                "success": True,
                "message": "音频同步完成",
                "summary": {
                    "scanned_files": total_scanned,
                    "new_files": total_new,
                    "updated_files": total_updated,
                    "orphaned_records": total_orphaned,
                    "errors": total_errors
                },
                "details": {
                    "audio_files": {
                        "scanned": results["audio_files"].scanned_files,
                        "new": results["audio_files"].new_files,
                        "updated": results["audio_files"].updated_files,
                        "orphaned": results["audio_files"].orphaned_records,
                        "errors": results["audio_files"].errors
                    },
                    "environment_sounds": {
                        "scanned": results["environment_sounds"].scanned_files,
                        "new": results["environment_sounds"].new_files,
                        "updated": results["environment_sounds"].updated_files,
                        "orphaned": results["environment_sounds"].orphaned_records,
                        "errors": results["environment_sounds"].errors
                    }
                }
            }
            
    except Exception as e:
        logger.error(f"音频同步失败: {e}")
        raise HTTPException(status_code=500, detail=f"音频同步失败: {str(e)}")


@router.post("/sync-audio-library", summary="同步音频库文件")
async def sync_audio_library(
    full_scan: bool = Query(False, description="是否执行完整扫描"),
    db: Session = Depends(get_db)
):
    """
    仅同步音频库文件
    """
    try:
        result = audio_sync_service.sync_audio_files(db, full_scan=full_scan)
        
        return {
            "success": True,
            "message": "音频库同步完成",
            "data": {
                "scanned_files": result.scanned_files,
                "new_files": result.new_files,
                "updated_files": result.updated_files,
                "orphaned_records": result.orphaned_records,
                "invalid_files": result.invalid_files,
                "errors": result.errors
            }
        }
        
    except Exception as e:
        logger.error(f"音频库同步失败: {e}")
        raise HTTPException(status_code=500, detail=f"音频库同步失败: {str(e)}")


@router.post("/sync-environment-sounds", summary="同步环境音文件")
async def sync_environment_sounds(
    full_scan: bool = Query(False, description="是否执行完整扫描"),
    db: Session = Depends(get_db)
):
    """
    仅同步环境音文件
    """
    try:
        result = audio_sync_service.sync_environment_sounds(db, full_scan=full_scan)
        
        return {
            "success": True,
            "message": "环境音同步完成",
            "data": {
                "scanned_files": result.scanned_files,
                "new_files": result.new_files,
                "updated_files": result.updated_files,
                "orphaned_records": result.orphaned_records,
                "invalid_files": result.invalid_files,
                "errors": result.errors
            }
        }
        
    except Exception as e:
        logger.error(f"环境音同步失败: {e}")
        raise HTTPException(status_code=500, detail=f"环境音同步失败: {str(e)}")


@router.get("/verify-integrity", summary="验证文件完整性")
async def verify_file_integrity(
    db: Session = Depends(get_db)
):
    """
    验证音频文件完整性
    """
    try:
        issues = audio_sync_service.verify_file_integrity(db)
        
        # 分类问题
        missing_files = [i for i in issues if i.get('type') == 'missing_file']
        size_mismatches = [i for i in issues if i.get('type') == 'size_mismatch']
        other_issues = [i for i in issues if i.get('type') not in ['missing_file', 'size_mismatch']]
        
        return {
            "success": True,
            "message": f"文件完整性检查完成，发现 {len(issues)} 个问题",
            "summary": {
                "total_issues": len(issues),
                "missing_files": len(missing_files),
                "size_mismatches": len(size_mismatches),
                "other_issues": len(other_issues)
            },
            "details": {
                "missing_files": missing_files,
                "size_mismatches": size_mismatches,
                "other_issues": other_issues
            }
        }
        
    except Exception as e:
        logger.error(f"文件完整性验证失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件完整性验证失败: {str(e)}")


@router.post("/cleanup-orphaned", summary="清理孤立记录")
async def cleanup_orphaned_records(
    dry_run: bool = Query(True, description="是否只模拟执行"),
    db: Session = Depends(get_db)
):
    """
    清理孤立的数据库记录
    """
    try:
        result = audio_sync_service.cleanup_orphaned_records(db, dry_run=dry_run)
        
        action = "模拟清理" if dry_run else "清理"
        
        return {
            "success": True,
            "message": f"{action}完成",
            "data": {
                "audio_files_cleaned": result["audio_files_cleaned"],
                "environment_sounds_cleaned": result["environment_sounds_cleaned"],
                "errors": result["errors"],
                "dry_run": dry_run
            }
        }
        
    except Exception as e:
        logger.error(f"清理孤立记录失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理孤立记录失败: {str(e)}")


@router.get("/status", summary="获取同步状态")
async def get_sync_status(
    db: Session = Depends(get_db)
):
    """
    获取音频同步状态概览
    """
    try:
        # 检查文件完整性
        issues = audio_sync_service.verify_file_integrity(db)
        
        # 获取目录信息
        audio_files_count = len(audio_sync_service.scan_directory(audio_sync_service.audio_dir))
        env_sounds_count = len(audio_sync_service.scan_directory(audio_sync_service.environment_sounds_dir))
        
        # 数据库统计
        from app.models.audio_file import AudioFile
        from app.models.environment_sound import EnvironmentSound
        
        db_audio_count = db.query(AudioFile).filter(AudioFile.status != 'deleted').count()
        db_env_count = db.query(EnvironmentSound).filter(
            EnvironmentSound.generation_status != 'deleted'
        ).count()
        
        return {
            "success": True,
            "data": {
                "directories": {
                    "audio_dir": audio_sync_service.audio_dir,
                    "environment_sounds_dir": audio_sync_service.environment_sounds_dir
                },
                "file_counts": {
                    "audio_files_on_disk": audio_files_count,
                    "audio_files_in_db": db_audio_count,
                    "environment_sounds_on_disk": env_sounds_count,
                    "environment_sounds_in_db": db_env_count
                },
                "integrity": {
                    "total_issues": len(issues),
                    "has_issues": len(issues) > 0
                },
                "last_check": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"获取同步状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取同步状态失败: {str(e)}")


@router.get("/scheduler/status", summary="获取调度器状态")
async def get_scheduler_status():
    """
    获取音频同步调度器状态
    """
    try:
        status = audio_sync_scheduler.get_job_status()
        return {
            "success": True,
            "data": status
        }
        
    except Exception as e:
        logger.error(f"获取调度器状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取调度器状态失败: {str(e)}")


@router.post("/scheduler/start", summary="启动调度器")
async def start_scheduler():
    """
    启动音频同步调度器
    """
    try:
        if audio_sync_scheduler.is_running:
            return {
                "success": True,
                "message": "调度器已在运行中"
            }
        
        audio_sync_scheduler.start()
        
        return {
            "success": True,
            "message": "调度器已启动"
        }
        
    except Exception as e:
        logger.error(f"启动调度器失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动调度器失败: {str(e)}")


@router.post("/scheduler/stop", summary="停止调度器")
async def stop_scheduler():
    """
    停止音频同步调度器
    """
    try:
        if not audio_sync_scheduler.is_running:
            return {
                "success": True,
                "message": "调度器已停止"
            }
        
        audio_sync_scheduler.stop()
        
        return {
            "success": True,
            "message": "调度器已停止"
        }
        
    except Exception as e:
        logger.error(f"停止调度器失败: {e}")
        raise HTTPException(status_code=500, detail=f"停止调度器失败: {str(e)}")


@router.post("/scheduler/trigger", summary="手动触发同步")
async def trigger_sync_now(
    full_scan: bool = Query(False, description="是否执行完整扫描")
):
    """
    立即手动触发音频同步
    """
    try:
        result = audio_sync_scheduler.trigger_sync_now(full_scan=full_scan)
        
        return {
            "success": result["success"],
            "message": result["message"],
            "timestamp": result["timestamp"]
        }
        
    except Exception as e:
        logger.error(f"手动触发同步失败: {e}")
        raise HTTPException(status_code=500, detail=f"手动触发同步失败: {str(e)}")


@router.post("/scheduler/jobs/{job_id}/pause", summary="暂停任务")
async def pause_job(job_id: str):
    """
    暂停指定的调度任务
    """
    try:
        success = audio_sync_scheduler.pause_job(job_id)
        
        if success:
            return {
                "success": True,
                "message": f"任务 {job_id} 已暂停"
            }
        else:
            raise HTTPException(status_code=400, detail=f"暂停任务 {job_id} 失败")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"暂停任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"暂停任务失败: {str(e)}")


@router.post("/scheduler/jobs/{job_id}/resume", summary="恢复任务")
async def resume_job(job_id: str):
    """
    恢复指定的调度任务
    """
    try:
        success = audio_sync_scheduler.resume_job(job_id)
        
        if success:
            return {
                "success": True,
                "message": f"任务 {job_id} 已恢复"
            }
        else:
            raise HTTPException(status_code=400, detail=f"恢复任务 {job_id} 失败")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"恢复任务失败: {str(e)}")


# 后台任务函数
async def sync_all_background_task(full_scan: bool = False):
    """后台同步任务"""
    try:
        logger.info(f"开始后台音频同步任务，完整扫描: {full_scan}")
        results = audio_sync_service.sync_all(full_scan=full_scan)
        
        # 汇总统计
        total_scanned = sum(r.scanned_files for r in results.values())
        total_new = sum(r.new_files for r in results.values())
        total_updated = sum(r.updated_files for r in results.values())
        total_orphaned = sum(r.orphaned_records for r in results.values())
        
        logger.info(f"后台音频同步完成: 扫描{total_scanned}，新增{total_new}，更新{total_updated}，孤立{total_orphaned}")
        
    except Exception as e:
        logger.error(f"后台音频同步失败: {e}") 