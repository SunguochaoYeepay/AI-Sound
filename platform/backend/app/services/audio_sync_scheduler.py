#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频同步定时调度器
提供自动化的音频文件同步任务
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import threading
import time

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("APScheduler not available, scheduler functionality disabled")

from app.database import SessionLocal
from app.services.audio_sync_service import audio_sync_service

logger = logging.getLogger(__name__)


class AudioSyncScheduler:
    """音频同步定时调度器"""
    
    def __init__(self):
        if SCHEDULER_AVAILABLE:
            self.scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
        else:
            self.scheduler = None
        self.is_running = False
        self.last_sync_time = None
        self.sync_stats = {
            'total_syncs': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'last_error': None
        }
    
    def start(self):
        """启动调度器"""
        if not SCHEDULER_AVAILABLE:
            logger.warning("调度器不可用，请安装 APScheduler")
            return
            
        if not self.is_running:
            try:
                # 添加定时任务
                self._add_sync_jobs()
                
                # 启动调度器
                self.scheduler.start()
                self.is_running = True
                
                logger.info("音频同步调度器已启动")
                
            except Exception as e:
                logger.error(f"启动音频同步调度器失败: {e}")
                raise
    
    def stop(self):
        """停止调度器"""
        if not SCHEDULER_AVAILABLE:
            return
            
        if self.is_running:
            try:
                self.scheduler.shutdown()
                self.is_running = False
                logger.info("音频同步调度器已停止")
                
            except Exception as e:
                logger.error(f"停止音频同步调度器失败: {e}")
    
    def _add_sync_jobs(self):
        """添加同步任务"""
        if not SCHEDULER_AVAILABLE:
            return
        
        # 1. 增量同步 - 每30分钟执行一次
        self.scheduler.add_job(
            func=self._incremental_sync_job,
            trigger=IntervalTrigger(minutes=30),
            id='incremental_sync',
            name='增量音频同步',
            misfire_grace_time=300,  # 5分钟宽限期
            max_instances=1,  # 最多同时运行1个实例
            replace_existing=True
        )
        
        # 2. 完整同步 - 每天凌晨2点执行
        self.scheduler.add_job(
            func=self._full_sync_job,
            trigger=CronTrigger(hour=2, minute=0),
            id='full_sync',
            name='完整音频同步',
            misfire_grace_time=1800,  # 30分钟宽限期
            max_instances=1,
            replace_existing=True
        )
        
        # 3. 文件完整性检查 - 每周一凌晨3点执行
        self.scheduler.add_job(
            func=self._integrity_check_job,
            trigger=CronTrigger(day_of_week=0, hour=3, minute=0),
            id='integrity_check',
            name='文件完整性检查',
            misfire_grace_time=3600,  # 1小时宽限期
            max_instances=1,
            replace_existing=True
        )
        
        # 4. 清理孤立记录 - 每月1号凌晨4点执行
        self.scheduler.add_job(
            func=self._cleanup_orphaned_job,
            trigger=CronTrigger(day=1, hour=4, minute=0),
            id='cleanup_orphaned',
            name='清理孤立记录',
            misfire_grace_time=7200,  # 2小时宽限期
            max_instances=1,
            replace_existing=True
        )
        
        logger.info("音频同步任务已添加到调度器")
    
    def _incremental_sync_job(self):
        """增量同步任务"""
        try:
            logger.info("开始执行增量音频同步")
            self._execute_sync_job(full_scan=False, job_name="增量同步")
            
        except Exception as e:
            logger.error(f"增量同步任务失败: {e}")
            self.sync_stats['failed_syncs'] += 1
            self.sync_stats['last_error'] = str(e)
    
    def _full_sync_job(self):
        """完整同步任务"""
        try:
            logger.info("开始执行完整音频同步")
            self._execute_sync_job(full_scan=True, job_name="完整同步")
            
        except Exception as e:
            logger.error(f"完整同步任务失败: {e}")
            self.sync_stats['failed_syncs'] += 1
            self.sync_stats['last_error'] = str(e)
    
    def _integrity_check_job(self):
        """文件完整性检查任务"""
        try:
            logger.info("开始执行文件完整性检查")
            
            db = SessionLocal()
            try:
                issues = audio_sync_service.verify_file_integrity(db)
                
                if issues:
                    logger.warning(f"发现 {len(issues)} 个文件完整性问题")
                    # 这里可以添加告警通知逻辑
                    for issue in issues[:5]:  # 只记录前5个问题
                        logger.warning(f"完整性问题: {issue}")
                else:
                    logger.info("文件完整性检查通过")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"文件完整性检查失败: {e}")
    
    def _cleanup_orphaned_job(self):
        """清理孤立记录任务"""
        try:
            logger.info("开始执行孤立记录清理")
            
            db = SessionLocal()
            try:
                # 先模拟执行，检查要清理的记录数量
                dry_run_result = audio_sync_service.cleanup_orphaned_records(db, dry_run=True)
                
                audio_count = dry_run_result['audio_files_cleaned']
                env_count = dry_run_result['environment_sounds_cleaned']
                
                if audio_count > 0 or env_count > 0:
                    logger.info(f"将清理 {audio_count} 个音频文件记录，{env_count} 个环境音记录")
                    
                    # 实际执行清理
                    result = audio_sync_service.cleanup_orphaned_records(db, dry_run=False)
                    
                    logger.info(f"孤立记录清理完成: 音频文件{result['audio_files_cleaned']}个，环境音{result['environment_sounds_cleaned']}个")
                else:
                    logger.info("没有需要清理的孤立记录")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"孤立记录清理失败: {e}")
    
    def _execute_sync_job(self, full_scan: bool, job_name: str):
        """执行同步任务的通用方法"""
        start_time = datetime.now()
        
        try:
            results = audio_sync_service.sync_all(full_scan=full_scan)
            
            # 汇总统计
            total_scanned = sum(r.scanned_files for r in results.values())
            total_new = sum(r.new_files for r in results.values())
            total_updated = sum(r.updated_files for r in results.values())
            total_orphaned = sum(r.orphaned_records for r in results.values())
            total_errors = sum(len(r.errors) for r in results.values())
            
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"{job_name}完成 - 耗时: {duration:.1f}s, "
                f"扫描: {total_scanned}, 新增: {total_new}, "
                f"更新: {total_updated}, 孤立: {total_orphaned}, 错误: {total_errors}"
            )
            
            # 更新统计
            self.sync_stats['total_syncs'] += 1
            self.sync_stats['successful_syncs'] += 1
            self.last_sync_time = datetime.now()
            
            # 如果有错误，记录但不认为是失败
            if total_errors > 0:
                logger.warning(f"{job_name}中有 {total_errors} 个错误")
                for result in results.values():
                    for error in result.errors:
                        logger.warning(f"同步错误: {error}")
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"{job_name}失败 - 耗时: {duration:.1f}s, 错误: {e}")
            
            self.sync_stats['total_syncs'] += 1
            self.sync_stats['failed_syncs'] += 1
            self.sync_stats['last_error'] = str(e)
            
            raise
    
    def get_job_status(self):
        """获取任务状态"""
        jobs = []
        
        if SCHEDULER_AVAILABLE and self.scheduler:
            for job in self.scheduler.get_jobs():
                next_run = job.next_run_time
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run': next_run.isoformat() if next_run else None,
                    'enabled': True
                })
        
        return {
            'scheduler_running': self.is_running,
            'scheduler_available': SCHEDULER_AVAILABLE,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'sync_stats': self.sync_stats,
            'jobs': jobs
        }
    
    def trigger_sync_now(self, full_scan: bool = False) -> dict:
        """立即触发同步"""
        try:
            job_name = "手动同步(完整)" if full_scan else "手动同步(增量)"
            logger.info(f"手动触发{job_name}")
            
            self._execute_sync_job(full_scan=full_scan, job_name=job_name)
            
            return {
                'success': True,
                'message': f'{job_name}完成',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'{job_name}失败: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def pause_job(self, job_id: str):
        """暂停指定任务"""
        if not SCHEDULER_AVAILABLE:
            return False
            
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"任务 {job_id} 已暂停")
            return True
        except Exception as e:
            logger.error(f"暂停任务 {job_id} 失败: {e}")
            return False
    
    def resume_job(self, job_id: str):
        """恢复指定任务"""
        if not SCHEDULER_AVAILABLE:
            return False
            
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"任务 {job_id} 已恢复")
            return True
        except Exception as e:
            logger.error(f"恢复任务 {job_id} 失败: {e}")
            return False


# 全局调度器实例
audio_sync_scheduler = AudioSyncScheduler()