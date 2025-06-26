#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份统计管理工具
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.backup import BackupTask, RestoreTask, BackupStats
from app.utils import log_system_event


class BackupStatsManager:
    """备份统计管理器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_backup_statistics(self, days: int = 30) -> Dict[str, Any]:
        """获取备份统计信息"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # 基础统计
            basic_stats = await self._get_basic_statistics(start_date, end_date)
            
            # 趋势数据
            trend_data = await self._get_trend_data(start_date, end_date)
            
            # 存储使用情况
            storage_stats = await self._get_storage_statistics()
            
            # 恢复统计
            restore_stats = await self._get_restore_statistics(start_date, end_date)
            
            # 性能统计
            performance_stats = await self._get_performance_statistics(start_date, end_date)
            
            return {
                "period": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "days": days
                },
                "basic": basic_stats,
                "trends": trend_data,
                "storage": storage_stats,
                "restore": restore_stats,
                "performance": performance_stats
            }
            
        except Exception as e:
            log_system_event(f"获取备份统计失败: {str(e)}", "error")
            return {"error": str(e)}
    
    async def _get_basic_statistics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """获取基础统计信息"""
        try:
            # 总备份数
            total_backups = self.db.query(BackupTask).filter(
                BackupTask.created_at >= start_date,
                BackupTask.created_at <= end_date
            ).count()
            
            # 成功备份数
            successful_backups = self.db.query(BackupTask).filter(
                BackupTask.created_at >= start_date,
                BackupTask.created_at <= end_date,
                BackupTask.status == "success"
            ).count()
            
            # 失败备份数
            failed_backups = self.db.query(BackupTask).filter(
                BackupTask.created_at >= start_date,
                BackupTask.created_at <= end_date,
                BackupTask.status == "failed"
            ).count()
            
            # 运行中的备份数
            running_backups = self.db.query(BackupTask).filter(
                BackupTask.status == "running"
            ).count()
            
            # 成功率
            success_rate = (successful_backups / total_backups * 100) if total_backups > 0 else 0
            
            # 最后一次备份时间
            last_backup = self.db.query(BackupTask).filter(
                BackupTask.status == "success"
            ).order_by(desc(BackupTask.end_time)).first()
            
            return {
                "total_backups": total_backups,
                "successful_backups": successful_backups,
                "failed_backups": failed_backups,
                "running_backups": running_backups,
                "success_rate": round(success_rate, 2),
                "last_backup_time": last_backup.end_time if last_backup else None
            }
            
        except Exception as e:
            log_system_event(f"获取基础统计失败: {str(e)}", "error")
            return {}
    
    async def _get_trend_data(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """获取趋势数据"""
        try:
            # 使用原生SQL避免SQLAlchemy版本兼容性问题
            from sqlalchemy import text
            
            daily_stats = self.db.execute(text("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                FROM backup_tasks 
                WHERE created_at >= :start_date AND created_at <= :end_date
                GROUP BY DATE(created_at)
                ORDER BY DATE(created_at)
            """), {
                'start_date': start_date,
                'end_date': end_date
            }).fetchall()
            
            trend_data = []
            for stat in daily_stats:
                total = int(stat.total)
                success = int(stat.success or 0)
                failed = int(stat.failed or 0)
                
                trend_data.append({
                    "date": stat.date.strftime("%Y-%m-%d") if hasattr(stat.date, 'strftime') else str(stat.date),
                    "total": total,
                    "success": success,
                    "failed": failed,
                    "success_rate": round(success / total * 100, 2) if total > 0 else 0
                })
            
            return trend_data
            
        except Exception as e:
            log_system_event(f"获取趋势数据失败: {str(e)}", "error")
            return []
    
    async def _get_storage_statistics(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            # 总存储使用量
            total_storage = self.db.query(
                func.coalesce(func.sum(BackupTask.file_size), 0)
            ).filter(
                BackupTask.status == "success",
                BackupTask.file_size.isnot(None)
            ).scalar()
            
            # 压缩后存储使用量
            compressed_storage = self.db.query(
                func.coalesce(func.sum(BackupTask.compressed_size), 0)
            ).filter(
                BackupTask.status == "success",
                BackupTask.compressed_size.isnot(None)
            ).scalar()
            
            # 按类型统计
            type_stats = self.db.query(
                BackupTask.task_type,
                func.count(BackupTask.id).label('count'),
                func.coalesce(func.sum(BackupTask.file_size), 0).label('total_size')
            ).filter(
                BackupTask.status == "success"
            ).group_by(BackupTask.task_type).all()
            
            type_breakdown = {}
            for stat in type_stats:
                type_breakdown[stat.task_type] = {
                    "count": stat.count,
                    "total_size_mb": round(stat.total_size / 1024 / 1024, 2) if stat.total_size else 0
                }
            
            return {
                "total_storage_gb": round(total_storage / 1024 / 1024 / 1024, 2),
                "compressed_storage_gb": round(compressed_storage / 1024 / 1024 / 1024, 2),
                "compression_ratio": round(
                    (1 - compressed_storage / total_storage) * 100, 2
                ) if total_storage > 0 and compressed_storage > 0 else 0,
                "type_breakdown": type_breakdown
            }
            
        except Exception as e:
            log_system_event(f"获取存储统计失败: {str(e)}", "error")
            return {}
    
    async def _get_restore_statistics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """获取恢复统计信息"""
        try:
            # 总恢复数
            total_restores = self.db.query(RestoreTask).filter(
                RestoreTask.created_at >= start_date,
                RestoreTask.created_at <= end_date
            ).count()
            
            # 成功恢复数
            successful_restores = self.db.query(RestoreTask).filter(
                RestoreTask.created_at >= start_date,
                RestoreTask.created_at <= end_date,
                RestoreTask.status == "success"
            ).count()
            
            # 失败恢复数
            failed_restores = self.db.query(RestoreTask).filter(
                RestoreTask.created_at >= start_date,
                RestoreTask.created_at <= end_date,
                RestoreTask.status == "failed"
            ).count()
            
            # 恢复成功率
            restore_success_rate = (
                successful_restores / total_restores * 100
            ) if total_restores > 0 else 0
            
            # 最近恢复
            last_restore = self.db.query(RestoreTask).filter(
                RestoreTask.status == "success"
            ).order_by(desc(RestoreTask.end_time)).first()
            
            return {
                "total_restores": total_restores,
                "successful_restores": successful_restores,
                "failed_restores": failed_restores,
                "restore_success_rate": round(restore_success_rate, 2),
                "last_restore_time": last_restore.end_time if last_restore else None
            }
            
        except Exception as e:
            log_system_event(f"获取恢复统计失败: {str(e)}", "error")
            return {}
    
    async def _get_performance_statistics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """获取性能统计信息"""
        try:
            # 平均备份时长
            avg_backup_duration = self.db.query(
                func.avg(BackupTask.duration_seconds)
            ).filter(
                BackupTask.created_at >= start_date,
                BackupTask.created_at <= end_date,
                BackupTask.status == "success",
                BackupTask.duration_seconds.isnot(None)
            ).scalar()
            
            # 平均恢复时长
            avg_restore_duration = self.db.query(
                func.avg(RestoreTask.duration_seconds)
            ).filter(
                RestoreTask.created_at >= start_date,
                RestoreTask.created_at <= end_date,
                RestoreTask.status == "success",
                RestoreTask.duration_seconds.isnot(None)
            ).scalar()
            
            # 最长和最短备份时间
            backup_duration_stats = self.db.query(
                func.min(BackupTask.duration_seconds).label('min_duration'),
                func.max(BackupTask.duration_seconds).label('max_duration')
            ).filter(
                BackupTask.created_at >= start_date,
                BackupTask.created_at <= end_date,
                BackupTask.status == "success",
                BackupTask.duration_seconds.isnot(None)
            ).first()
            
            # 平均文件大小
            avg_file_size = self.db.query(
                func.avg(BackupTask.file_size)
            ).filter(
                BackupTask.created_at >= start_date,
                BackupTask.created_at <= end_date,
                BackupTask.status == "success",
                BackupTask.file_size.isnot(None)
            ).scalar()
            
            return {
                "avg_backup_duration_minutes": round(
                    (avg_backup_duration or 0) / 60, 2
                ),
                "avg_restore_duration_minutes": round(
                    (avg_restore_duration or 0) / 60, 2
                ),
                "min_backup_duration_minutes": round(
                    (backup_duration_stats.min_duration or 0) / 60, 2
                ) if backup_duration_stats else 0,
                "max_backup_duration_minutes": round(
                    (backup_duration_stats.max_duration or 0) / 60, 2
                ) if backup_duration_stats else 0,
                "avg_file_size_mb": round(
                    (avg_file_size or 0) / 1024 / 1024, 2
                )
            }
            
        except Exception as e:
            log_system_event(f"获取性能统计失败: {str(e)}", "error")
            return {}
    
    async def update_daily_stats(self) -> bool:
        """更新每日统计（定时任务调用）"""
        try:
            today = datetime.utcnow().date()
            
            # 检查今日统计是否已存在
            existing_stat = self.db.query(BackupStats).filter(
                func.date(BackupStats.stat_date) == today
            ).first()
            
            if existing_stat:
                # 更新现有统计
                stat_record = existing_stat
            else:
                # 创建新统计记录
                stat_record = BackupStats()
                self.db.add(stat_record)
            
            # 计算今日统计
            start_of_day = datetime.combine(today, datetime.min.time())
            end_of_day = datetime.combine(today, datetime.max.time())
            
            # 总备份数
            total_backups = self.db.query(BackupTask).filter(
                BackupTask.created_at >= start_of_day,
                BackupTask.created_at <= end_of_day
            ).count()
            
            # 成功备份数
            successful_backups = self.db.query(BackupTask).filter(
                BackupTask.created_at >= start_of_day,
                BackupTask.created_at <= end_of_day,
                BackupTask.status == "success"
            ).count()
            
            # 失败备份数
            failed_backups = self.db.query(BackupTask).filter(
                BackupTask.created_at >= start_of_day,
                BackupTask.created_at <= end_of_day,
                BackupTask.status == "failed"
            ).count()
            
            # 存储使用量
            total_storage = self.db.query(
                func.coalesce(func.sum(BackupTask.file_size), 0)
            ).filter(
                BackupTask.created_at >= start_of_day,
                BackupTask.created_at <= end_of_day,
                BackupTask.status == "success"
            ).scalar()
            
            # 平均备份时长
            avg_duration = self.db.query(
                func.avg(BackupTask.duration_seconds)
            ).filter(
                BackupTask.created_at >= start_of_day,
                BackupTask.created_at <= end_of_day,
                BackupTask.status == "success",
                BackupTask.duration_seconds.isnot(None)
            ).scalar()
            
            # 按类型统计
            type_counts = self.db.query(
                BackupTask.task_type,
                func.count(BackupTask.id).label('count')
            ).filter(
                BackupTask.created_at >= start_of_day,
                BackupTask.created_at <= end_of_day
            ).group_by(BackupTask.task_type).all()
            
            full_count = 0
            incremental_count = 0
            manual_count = 0
            
            for type_count in type_counts:
                if type_count.task_type == "full":
                    full_count = type_count.count
                elif type_count.task_type == "incremental":
                    incremental_count = type_count.count
                elif type_count.task_type == "manual":
                    manual_count = type_count.count
            
            # 更新统计记录
            stat_record.stat_date = datetime.utcnow()
            stat_record.total_backups = total_backups
            stat_record.successful_backups = successful_backups
            stat_record.failed_backups = failed_backups
            stat_record.total_storage_used = total_storage or 0
            stat_record.avg_backup_duration = int(avg_duration or 0)
            stat_record.full_backup_count = full_count
            stat_record.incremental_backup_count = incremental_count
            stat_record.manual_backup_count = manual_count
            
            self.db.commit()
            
            log_system_event(f"每日备份统计更新完成: {today}", "info")
            return True
            
        except Exception as e:
            log_system_event(f"更新每日统计失败: {str(e)}", "error")
            self.db.rollback()
            return False