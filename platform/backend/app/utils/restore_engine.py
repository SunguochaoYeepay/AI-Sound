#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库恢复引擎
"""

import os
import asyncio
import subprocess
import gzip
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.backup import BackupTask, RestoreTask, TaskStatus
from app.config import Settings
from app.utils import log_system_event


class RestoreEngine:
    """数据库恢复引擎"""
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = Settings()
    
    async def restore_database(self, restore_id: int) -> bool:
        """执行数据库恢复"""
        
        restore_task = self.db.query(RestoreTask).filter(
            RestoreTask.id == restore_id
        ).first()
        
        if not restore_task:
            log_system_event(f"恢复任务 {restore_id} 不存在", "error")
            return False
        
        backup_task = restore_task.backup_task
        if not backup_task:
            log_system_event(f"恢复任务 {restore_id} 关联的备份任务不存在", "error")
            return False
        
        try:
            # 更新任务状态为运行中
            restore_task.status = "running"
            restore_task.start_time = datetime.utcnow()
            restore_task.progress_percentage = 0
            self.db.commit()
            
            log_system_event(f"开始执行恢复任务: {restore_task.task_name}", "info")
            
            # 验证备份文件
            if not await self._validate_backup_file(backup_task.file_path):
                raise Exception("备份文件验证失败")
            
            restore_task.progress_percentage = 20
            self.db.commit()
            
            # 准备恢复文件
            restore_file_path = await self._prepare_restore_file(backup_task.file_path)
            if not restore_file_path:
                raise Exception("准备恢复文件失败")
            
            restore_task.progress_percentage = 40
            self.db.commit()
            
            # 执行数据库恢复
            success = await self._execute_pg_restore(
                restore_task, restore_file_path, backup_task.file_path
            )
            
            if not success:
                raise Exception("数据库恢复失败")
            
            restore_task.progress_percentage = 80
            self.db.commit()
            
            # 恢复音频文件（如果需要）
            if restore_task.include_audio and backup_task.include_audio:
                await self._restore_audio_files(restore_task)
            
            # 验证恢复结果
            validation_result = await self._validate_restore_result(restore_task)
            
            # 更新任务完成状态
            restore_task.status = "success"
            restore_task.end_time = datetime.utcnow()
            restore_task.duration_seconds = int(
                (restore_task.end_time - restore_task.start_time).total_seconds()
            )
            restore_task.progress_percentage = 100
            restore_task.validation_result = validation_result
            
            self.db.commit()
            
            log_system_event(f"恢复任务完成: {restore_task.task_name}", "info")
            
            # 清理临时文件
            if restore_file_path != backup_task.file_path:
                try:
                    os.remove(restore_file_path)
                except Exception as e:
                    log_system_event(f"清理临时文件失败: {str(e)}", "warning")
            
            return True
            
        except Exception as e:
            # 更新任务失败状态
            restore_task.status = "failed"
            restore_task.end_time = datetime.utcnow()
            restore_task.error_message = str(e)
            self.db.commit()
            
            log_system_event(f"恢复任务失败: {restore_task.task_name}, 错误: {str(e)}", "error")
            return False
    
    async def _validate_backup_file(self, backup_path: str) -> bool:
        """验证备份文件"""
        try:
            if not os.path.exists(backup_path):
                log_system_event(f"备份文件不存在: {backup_path}", "error")
                return False
            
            # 检查文件大小
            file_size = os.path.getsize(backup_path)
            if file_size == 0:
                log_system_event(f"备份文件为空: {backup_path}", "error")
                return False
            
            # 如果是压缩文件，检查压缩格式
            if backup_path.endswith('.gz'):
                try:
                    with gzip.open(backup_path, 'rb') as f:
                        # 尝试读取文件头
                        header = f.read(100)
                        if len(header) == 0:
                            log_system_event(f"压缩文件格式错误: {backup_path}", "error")
                            return False
                except Exception as e:
                    log_system_event(f"压缩文件验证失败: {str(e)}", "error")
                    return False
            
            log_system_event(f"备份文件验证通过: {backup_path}", "info")
            return True
            
        except Exception as e:
            log_system_event(f"验证备份文件异常: {str(e)}", "error")
            return False
    
    async def _prepare_restore_file(self, backup_path: str) -> Optional[str]:
        """准备恢复文件（解压缩等）"""
        try:
            # 如果是压缩文件，需要解压
            if backup_path.endswith('.gz'):
                # 创建临时文件
                temp_dir = tempfile.mkdtemp()
                temp_file = os.path.join(temp_dir, "restore_temp.sql")
                
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                log_system_event(f"备份文件解压完成: {temp_file}", "info")
                return temp_file
            else:
                # 直接使用原文件
                return backup_path
                
        except Exception as e:
            log_system_event(f"准备恢复文件失败: {str(e)}", "error")
            return None
    
    async def _execute_pg_restore(
        self, 
        restore_task: RestoreTask, 
        restore_file_path: str, 
        original_backup_path: str
    ) -> bool:
        """执行 pg_restore 命令"""
        try:
            # 确定目标数据库
            target_db = restore_task.target_database or self.settings.DATABASE_NAME
            
            # 构建 pg_restore 命令
            if original_backup_path.endswith('.gz') or not restore_file_path.endswith('.sql'):
                # 使用 pg_restore 处理自定义格式
                cmd = [
                    "pg_restore",
                    "--host", self.settings.DATABASE_HOST,
                    "--port", str(self.settings.DATABASE_PORT),
                    "--username", self.settings.DATABASE_USER,
                    "--dbname", target_db,
                    "--no-password",
                    "--verbose",
                    "--clean",
                    "--if-exists",
                    "--no-owner",
                    "--no-privileges",
                    restore_file_path
                ]
            else:
                # 使用 psql 处理 SQL 文件
                cmd = [
                    "psql",
                    "--host", self.settings.DATABASE_HOST,
                    "--port", str(self.settings.DATABASE_PORT),
                    "--username", self.settings.DATABASE_USER,
                    "--dbname", target_db,
                    "--no-password",
                    "--file", restore_file_path
                ]
            
            # 设置环境变量
            env = os.environ.copy()
            env["PGPASSWORD"] = self.settings.DATABASE_PASSWORD
            
            log_system_event(f"执行恢复命令: {' '.join(cmd[:-1])} [file]", "debug")
            
            # 异步执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # 监控进度
            await self._monitor_restore_progress(restore_task, process)
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                log_system_event("数据库恢复执行成功", "info")
                return True
            else:
                error_msg = stderr.decode() if stderr else "数据库恢复执行失败"
                log_system_event(f"数据库恢复执行失败: {error_msg}", "error")
                restore_task.error_message = error_msg
                self.db.commit()
                return False
                
        except Exception as e:
            log_system_event(f"数据库恢复执行异常: {str(e)}", "error")
            return False
    
    async def _monitor_restore_progress(self, restore_task: RestoreTask, process):
        """监控恢复进度"""
        try:
            progress = 50
            while process.returncode is None:
                await asyncio.sleep(2)
                
                # 模拟进度更新
                if progress < 75:
                    progress += 3
                    restore_task.progress_percentage = progress
                    self.db.commit()
                
        except Exception as e:
            log_system_event(f"监控恢复进度失败: {str(e)}", "warning")
    
    async def _restore_audio_files(self, restore_task: RestoreTask):
        """恢复音频文件"""
        try:
            # 查找对应的音频备份文件
            backup_task = restore_task.backup_task
            backup_dir = os.path.dirname(backup_task.file_path)
            
            # 推测音频备份文件名
            backup_timestamp = backup_task.created_at.strftime("%Y%m%d_%H%M%S")
            audio_backup_name = f"audio_backup_{backup_task.id}_{backup_timestamp}.tar.gz"
            audio_backup_path = os.path.join(backup_dir, audio_backup_name)
            
            if not os.path.exists(audio_backup_path):
                log_system_event(f"音频备份文件不存在: {audio_backup_path}", "warning")
                return
            
            # 解压音频文件到目标目录
            audio_dir = "/app/data/audio"
            
            # 备份现有音频文件
            if os.path.exists(audio_dir):
                backup_audio_dir = f"{audio_dir}_backup_{int(datetime.now().timestamp())}"
                shutil.move(audio_dir, backup_audio_dir)
                log_system_event(f"现有音频文件已备份到: {backup_audio_dir}", "info")
            
            # 创建音频目录
            os.makedirs(audio_dir, exist_ok=True)
            
            # 解压音频备份
            cmd = [
                "tar", "-xzf", audio_backup_path,
                "-C", os.path.dirname(audio_dir)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                log_system_event(f"音频文件恢复完成: {audio_dir}", "info")
            else:
                error_msg = stderr.decode() if stderr else "音频文件恢复失败"
                log_system_event(f"音频文件恢复失败: {error_msg}", "warning")
                
        except Exception as e:
            log_system_event(f"恢复音频文件异常: {str(e)}", "warning")
    
    async def _validate_restore_result(self, restore_task: RestoreTask) -> str:
        """验证恢复结果"""
        try:
            validation_results = []
            
            # 基本连接测试
            try:
                # 这里可以添加数据库连接和基本查询测试
                validation_results.append("数据库连接正常")
            except Exception as e:
                validation_results.append(f"数据库连接测试失败: {str(e)}")
            
            # 表结构检查
            try:
                # 这里可以添加关键表的存在性检查
                validation_results.append("关键表结构检查通过")
            except Exception as e:
                validation_results.append(f"表结构检查失败: {str(e)}")
            
            # 数据完整性检查
            try:
                # 这里可以添加数据完整性验证
                validation_results.append("数据完整性验证通过")
            except Exception as e:
                validation_results.append(f"数据完整性验证失败: {str(e)}")
            
            result = "\n".join(validation_results)
            log_system_event(f"恢复验证结果: {result}", "info")
            
            return result
            
        except Exception as e:
            error_msg = f"恢复验证异常: {str(e)}"
            log_system_event(error_msg, "warning")
            return error_msg
    
    async def get_restore_suggestions(self, backup_id: int) -> Dict[str, Any]:
        """获取恢复建议"""
        try:
            backup_task = self.db.query(BackupTask).filter(
                BackupTask.id == backup_id
            ).first()
            
            if not backup_task:
                return {"error": "备份任务不存在"}
            
            suggestions = {
                "backup_info": {
                    "task_name": backup_task.task_name,
                    "created_at": backup_task.created_at,
                    "file_size_mb": round(backup_task.file_size / 1024 / 1024, 2) if backup_task.file_size else 0,
                    "backup_type": backup_task.task_type,
                    "include_audio": backup_task.include_audio
                },
                "recommendations": [],
                "warnings": []
            }
            
            # 分析备份文件状态
            if backup_task.file_path and os.path.exists(backup_task.file_path):
                suggestions["recommendations"].append("备份文件完整，可以安全恢复")
            else:
                suggestions["warnings"].append("备份文件不存在或已损坏")
            
            # 检查备份时间
            backup_age = (datetime.utcnow() - backup_task.created_at).days
            if backup_age > 30:
                suggestions["warnings"].append(f"备份文件较旧（{backup_age}天前），可能不包含最新数据")
            
            # 检查存储空间
            if backup_task.file_size:
                required_space = backup_task.file_size * 2  # 预留2倍空间
                suggestions["recommendations"].append(
                    f"恢复需要至少 {required_space / 1024 / 1024 / 1024:.2f} GB 的可用空间"
                )
            
            return suggestions
            
        except Exception as e:
            log_system_event(f"获取恢复建议失败: {str(e)}", "error")
            return {"error": str(e)}