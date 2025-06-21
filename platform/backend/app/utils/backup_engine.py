#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库备份引擎
"""

import os
import asyncio
import subprocess
import time
import gzip
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.backup import BackupTask, TaskStatus
from app.config import settings
from app.utils import log_system_event

# 配置常量 - 使用本地开发环境路径
import os
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKUP_DIR = os.path.join(PROJECT_ROOT, "storage", "backups")
AUDIO_DIR = os.path.join(PROJECT_ROOT, "storage", "audio")
MAX_BACKUP_SIZE = 10 * 1024 * 1024 * 1024  # 10GB


class BackupEngine:
    """数据库备份引擎"""
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = settings
        self._ensure_backup_directory()
    
    def _ensure_backup_directory(self):
        """确保备份目录存在"""
        Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
        log_system_event(f"备份目录检查完成: {BACKUP_DIR}", "debug")
    
    async def create_database_backup(
        self, 
        task_id: int, 
        backup_type: str = "full",
        include_audio: bool = False
    ) -> bool:
        """创建数据库备份"""
        
        task = self.db.query(BackupTask).filter(BackupTask.id == task_id).first()
        if not task:
            log_system_event(f"备份任务 {task_id} 不存在", "error")
            return False
        
        try:
            # 更新任务状态为运行中
            task.status = "running"
            task.start_time = datetime.utcnow()
            task.progress_percentage = 0
            self.db.commit()
            
            log_system_event(f"🚀 开始执行备份任务: {task.task_name} (ID: {task_id})", "info")
            log_system_event(f"📝 备份类型: {backup_type}, 包含音频: {include_audio}", "info")
            
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{backup_type}_{timestamp}.sql"
            backup_path = os.path.join(BACKUP_DIR, backup_filename)
            
            log_system_event(f"📁 备份文件路径: {backup_path}", "info")
            
            # 执行数据库备份
            log_system_event(f"⏳ 开始数据库备份...", "info")
            success = await self._execute_pg_dump(task, backup_path)
            
            if not success:
                return False
            

            
            # 压缩备份文件
            log_system_event(f"🗜️ 开始压缩备份文件...", "info")
            task.progress_percentage = 70
            self.db.commit()
            
            compressed_path = await self._compress_backup_file(backup_path)
            if compressed_path:
                backup_path = compressed_path
                log_system_event(f"✅ 压缩完成: {compressed_path}", "info")
            
            # 包含音频文件（如果需要）
            if include_audio:
                task.progress_percentage = 80
                self.db.commit()
                
                audio_backup_path = await self._backup_audio_files(task_id, timestamp)
                if audio_backup_path:
                    log_system_event(f"音频文件备份完成: {audio_backup_path}", "info")
            
            # 计算文件大小
            file_size = os.path.getsize(backup_path)
            
            # 更新任务完成状态
            task.status = "success"
            task.end_time = datetime.utcnow()
            task.duration_seconds = int((task.end_time - task.start_time).total_seconds())
            task.file_path = backup_path
            task.file_size = file_size
            task.compressed_size = file_size if compressed_path else None
            task.progress_percentage = 100
            
            self.db.commit()
            
            log_system_event(
                f"🎉 备份任务完成: {task.task_name}", "info"
            )
            log_system_event(
                f"📊 备份统计: 文件大小 {file_size / 1024 / 1024:.2f} MB, 耗时 {task.duration_seconds}秒", "info"
            )
            
            # 清理旧备份文件
            await self._cleanup_old_backups(task.retention_days)
            
            return True
            
        except Exception as e:
            # 更新任务失败状态
            task.status = "failed"
            task.end_time = datetime.utcnow()
            task.error_message = str(e)
            self.db.commit()
            
            log_system_event(f"备份任务失败: {task.task_name}, 错误: {str(e)}", "error")
            return False
    
    async def _execute_pg_dump(self, task: BackupTask, backup_path: str) -> bool:
        """执行 pg_dump 命令"""
        try:
            # 检查 pg_dump 是否可用
            import shutil
            pg_dump_path = shutil.which('pg_dump')
            
            if not pg_dump_path:
                error_msg = "pg_dump 工具未安装，请先安装 PostgreSQL 客户端工具"
                log_system_event(error_msg, "error")
                task.error_message = error_msg
                self.db.commit()
                return False
            
            # 从 database_url 解析数据库连接参数
            import re
            
            # 解析 database_url
            # 格式: postgresql://username:password@host:port/database
            db_url = self.settings.database_url
            log_system_event(f"🔧 使用数据库连接: {db_url}", "debug")
            match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
            
            if not match:
                raise Exception(f"无效的 database_url 格式: {db_url}")
            
            username, password, host, port, database = match.groups()
            
            # 构建 pg_dump 命令
            cmd = [
                "pg_dump",
                "--host", host,
                "--port", port,
                "--username", username,
                "--dbname", database,
                "--no-password",
                "--verbose",
                "--clean",
                "--if-exists",
                "--format=custom",
                "--file", backup_path
            ]
            
            # 设置环境变量
            env = os.environ.copy()
            env["PGPASSWORD"] = password
            
            log_system_event(f"🔧 执行 pg_dump 命令: {' '.join(cmd[:-1])} [file]", "info")
            log_system_event(f"🔗 连接数据库: {host}:{port}/{database}", "info")
            
            # 异步执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # 监控进度
            await self._monitor_backup_progress(task, process)
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                log_system_event(f"✅ pg_dump 执行成功，退出码: {process.returncode}", "info")
                
                # 检查备份文件是否成功生成
                if os.path.exists(backup_path):
                    file_size = os.path.getsize(backup_path)
                    log_system_event(f"📁 备份文件已生成: {backup_path} ({file_size / 1024 / 1024:.2f} MB)", "info")
                else:
                    log_system_event(f"❌ 备份文件未生成: {backup_path}", "error")
                    return False
                    
                return True
            else:
                error_msg = stderr.decode() if stderr else "pg_dump 执行失败"
                log_system_event(f"❌ pg_dump 执行失败 (退出码: {process.returncode}): {error_msg}", "error")
                task.error_message = error_msg
                self.db.commit()
                return False
                
        except Exception as e:
            error_msg = f"pg_dump 执行异常: {str(e)}"
            log_system_event(error_msg, "error")
            task.error_message = error_msg
            self.db.commit()
            return False
    

    
    async def _monitor_backup_progress(self, task: BackupTask, process):
        """监控备份进度"""
        try:
            progress = 10
            start_time = time.time()
            
            log_system_event(f"📈 开始监控备份进度...", "info")
            
            while process.returncode is None:
                await asyncio.sleep(3)  # 增加到3秒，减少日志频率
                
                current_time = time.time()
                elapsed = int(current_time - start_time)
                
                # 模拟进度更新
                if progress < 60:
                    progress += 5
                    task.progress_percentage = progress
                    self.db.commit()
                    
                    log_system_event(
                        f"⏳ 备份进度: {progress}% (已耗时 {elapsed}秒)", 
                        "info"
                    )
                
        except Exception as e:
            log_system_event(f"⚠️ 监控备份进度失败: {str(e)}", "warning")
    
    async def _compress_backup_file(self, backup_path: str) -> Optional[str]:
        """压缩备份文件"""
        try:
            compressed_path = f"{backup_path}.gz"
            
            # 记录原始文件大小
            original_size = os.path.getsize(backup_path)
            
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 记录压缩后文件大小
            compressed_size = os.path.getsize(compressed_path)
            
            # 删除原始文件
            os.remove(backup_path)
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            log_system_event(
                f"🗜️ 备份文件压缩完成: {compressed_path}", "info"
            )
            log_system_event(
                f"📊 压缩统计: {original_size / 1024 / 1024:.2f} MB → {compressed_size / 1024 / 1024:.2f} MB (压缩率: {compression_ratio:.1f}%)", 
                "info"
            )
            return compressed_path
            
        except Exception as e:
            log_system_event(f"压缩备份文件失败: {str(e)}", "warning")
            return None
    
    async def _backup_audio_files(self, task_id: int, timestamp: str) -> Optional[str]:
        """备份音频文件"""
        try:
            if not os.path.exists(AUDIO_DIR):
                log_system_event("音频目录不存在，跳过音频备份", "warning")
                return None
            
            audio_backup_name = f"audio_backup_{task_id}_{timestamp}.tar.gz"
            audio_backup_path = os.path.join(BACKUP_DIR, audio_backup_name)
            
            # 使用 tar 命令压缩音频目录
            cmd = [
                "tar", "-czf", audio_backup_path,
                "-C", os.path.dirname(AUDIO_DIR),
                os.path.basename(AUDIO_DIR)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                log_system_event(f"音频文件备份完成: {audio_backup_path}", "info")
                return audio_backup_path
            else:
                error_msg = stderr.decode() if stderr else "音频备份失败"
                log_system_event(f"音频文件备份失败: {error_msg}", "warning")
                return None
                
        except Exception as e:
            log_system_event(f"备份音频文件异常: {str(e)}", "warning")
            return None
    
    async def _cleanup_old_backups(self, retention_days: int):
        """清理过期的备份文件"""
        try:
            cutoff_time = time.time() - (retention_days * 24 * 60 * 60)
            deleted_count = 0
            
            for filename in os.listdir(BACKUP_DIR):
                file_path = os.path.join(BACKUP_DIR, filename)
                if os.path.isfile(file_path):
                    if os.path.getmtime(file_path) < cutoff_time:
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                            log_system_event(f"删除过期备份文件: {filename}", "debug")
                        except Exception as e:
                            log_system_event(f"删除备份文件失败: {filename}, {str(e)}", "warning")
            
            if deleted_count > 0:
                log_system_event(f"清理完成，删除了 {deleted_count} 个过期备份文件", "info")
                
        except Exception as e:
            log_system_event(f"清理旧备份文件失败: {str(e)}", "warning")
    
    async def get_backup_file_info(self, backup_path: str) -> Dict[str, Any]:
        """获取备份文件信息"""
        try:
            if not os.path.exists(backup_path):
                return {"exists": False}
            
            stat = os.stat(backup_path)
            
            return {
                "exists": True,
                "size": stat.st_size,
                "created_time": datetime.fromtimestamp(stat.st_ctime),
                "modified_time": datetime.fromtimestamp(stat.st_mtime),
                "readable": os.access(backup_path, os.R_OK)
            }
            
        except Exception as e:
            log_system_event(f"获取备份文件信息失败: {str(e)}", "warning")
            return {"exists": False, "error": str(e)}
    
    async def validate_backup_file(self, backup_path: str) -> bool:
        """验证备份文件完整性"""
        try:
            # 检查文件是否存在
            if not os.path.exists(backup_path):
                return False
            
            # 检查文件大小
            file_size = os.path.getsize(backup_path)
            if file_size == 0:
                return False
            
            # 如果是压缩文件，尝试解压验证
            if backup_path.endswith('.gz'):
                try:
                    with gzip.open(backup_path, 'rb') as f:
                        # 读取文件头验证格式
                        header = f.read(100)
                        if len(header) == 0:
                            return False
                except Exception:
                    return False
            
            return True
            
        except Exception as e:
            log_system_event(f"验证备份文件失败: {str(e)}", "warning")
            return False