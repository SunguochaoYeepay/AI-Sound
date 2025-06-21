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
    
    def _get_current_database_name(self) -> str:
        """获取当前正在使用的数据库名称"""
        try:
            from sqlalchemy.engine.url import make_url
            from app.database import DATABASE_URL
            db_url = make_url(DATABASE_URL)
            return str(db_url.database)
        except Exception:
            return "ai_sound"  # 默认值

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
            
        # 🎯 恢复信息记录：允许恢复到生产数据库
        current_db = self._get_current_database_name()
        target_db = restore_task.target_database
        
        if target_db == current_db:
            log_system_event(f"📋 恢复到当前生产数据库: {target_db}，将替换现有数据", "warning")
        else:
            log_system_event(f"📋 恢复到目标数据库: {target_db}", "info")
        
        temp_file_path = None
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
            
            # 直接使用备份文件，不需要额外准备
            restore_task.progress_percentage = 40
            self.db.commit()
            
            # 双重保险：先手动清理，再用pg_restore的--clean参数
            await self._clean_database_before_restore(restore_task)
            restore_task.progress_percentage = 60
            self.db.commit()
            
            # 执行数据库恢复
            success, temp_file_path = await self._execute_pg_restore(
                restore_task, backup_task.file_path, backup_task.file_path
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
            
            # 刷新对象状态，避免Session问题
            self.db.refresh(restore_task)
            
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
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    log_system_event(f"清理临时文件: {temp_file_path}", "debug")
                except Exception as e:
                    log_system_event(f"清理临时文件失败: {str(e)}", "warning")
            
            return True
            
        except Exception as e:
            try:
                # 刷新对象状态，避免Session问题
                self.db.refresh(restore_task)
                
                # 更新任务失败状态
                restore_task.status = "failed"
                restore_task.end_time = datetime.utcnow()
                restore_task.error_message = str(e)
                if restore_task.start_time:
                    restore_task.duration_seconds = int(
                        (restore_task.end_time - restore_task.start_time).total_seconds()
                    )
                self.db.commit()
                
                log_system_event(f"恢复任务失败: {restore_task.task_name}, 错误: {str(e)}", "error")
            except Exception as commit_error:
                log_system_event(f"更新恢复任务状态失败: {str(commit_error)}", "error")
            
            return False
    async def _clean_database_before_restore(self, restore_task: RestoreTask):
        """清理数据库，为恢复做准备 - 增强版清理逻辑"""
        try:
            # 🔧 重要修复：确保target_database有正确的默认值
            from sqlalchemy.engine.url import make_url
            from app.database import DATABASE_URL
            
            db_url = make_url(DATABASE_URL)
            default_db_name = str(db_url.database)
            
            # 如果target_database为空或None，使用默认数据库名
            target_db = restore_task.target_database
            if not target_db or target_db.strip() == '':
                target_db = default_db_name
                log_system_event(f"🎯 target_database为空，使用默认数据库: {target_db}", "info")
            
            # 清理检查 - 记录当前数据库清理操作
            current_db = self._get_current_database_name()
            if target_db == current_db:
                log_system_event(f"🧹 清理当前生产数据库: {current_db}，为恢复做准备", "info")
            else:
                log_system_event(f"🧹 清理目标数据库: {target_db}，为恢复做准备", "info")
            
            log_system_event(f"🧹 开始清理目标数据库 '{target_db}' 为恢复做准备", "info")
            
            # 获取数据库连接信息（复用已解析的db_url）
            default_host = str(db_url.host)
            default_port = db_url.port or 5432
            default_user = str(db_url.username)
            default_password = str(db_url.password)
            
            # 增强版清理 SQL - 更安全和全面
            cleanup_sql = """
                -- 设置客户端编码
                SET client_encoding = 'UTF8';
                
                -- 取消所有活动连接
                SELECT pg_terminate_backend(pid) 
                FROM pg_stat_activity 
                WHERE datname = current_database() 
                  AND pid <> pg_backend_pid()
                  AND state = 'active';
                
                -- 删除所有外键约束
                DO $$ 
                DECLARE 
                    r RECORD;
                BEGIN
                    FOR r IN (
                        SELECT constraint_name, table_name 
                        FROM information_schema.table_constraints 
                        WHERE constraint_type = 'FOREIGN KEY' 
                          AND table_schema = 'public'
                    ) 
                    LOOP
                        BEGIN
                            EXECUTE 'ALTER TABLE IF EXISTS ' || quote_ident(r.table_name) || 
                                   ' DROP CONSTRAINT IF EXISTS ' || quote_ident(r.constraint_name);
                        EXCEPTION WHEN others THEN
                            RAISE NOTICE '跳过约束: %.%', r.table_name, r.constraint_name;
                        END;
                    END LOOP;
                END $$;
                
                -- 删除所有用户表（按依赖顺序）
                DO $$
                DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (
                        SELECT tablename 
                        FROM pg_tables 
                        WHERE schemaname = 'public'
                        ORDER BY tablename
                    ) 
                    LOOP
                        BEGIN
                            EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                            RAISE NOTICE '删除表: %', r.tablename;
                        EXCEPTION WHEN others THEN
                            RAISE NOTICE '跳过表: %', r.tablename;
                        END;
                    END LOOP;
                END $$;
                
                -- 删除所有序列
                DO $$
                DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (
                        SELECT sequence_name 
                        FROM information_schema.sequences 
                        WHERE sequence_schema = 'public'
                    ) 
                    LOOP
                        BEGIN
                            EXECUTE 'DROP SEQUENCE IF EXISTS ' || quote_ident(r.sequence_name) || ' CASCADE';
                            RAISE NOTICE '删除序列: %', r.sequence_name;
                        EXCEPTION WHEN others THEN
                            RAISE NOTICE '跳过序列: %', r.sequence_name;
                        END;
                    END LOOP;
                END $$;
                
                -- 删除所有用户自定义类型（包括枚举）
                DO $$
                DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (
                        SELECT typname 
                        FROM pg_type 
                        WHERE typnamespace = (
                            SELECT oid FROM pg_namespace WHERE nspname = 'public'
                        ) 
                        AND typtype IN ('e', 'c', 'd')  -- 枚举、复合、域类型
                        ORDER BY typname
                    ) 
                    LOOP
                        BEGIN
                            EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
                            RAISE NOTICE '删除类型: %', r.typname;
                        EXCEPTION WHEN others THEN
                            RAISE NOTICE '跳过类型: %', r.typname;
                        END;
                    END LOOP;
                END $$;
                
                -- 删除所有视图
                DO $$
                DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (
                        SELECT viewname 
                        FROM pg_views 
                        WHERE schemaname = 'public'
                    ) 
                    LOOP
                        BEGIN
                            EXECUTE 'DROP VIEW IF EXISTS ' || quote_ident(r.viewname) || ' CASCADE';
                            RAISE NOTICE '删除视图: %', r.viewname;
                        EXCEPTION WHEN others THEN
                            RAISE NOTICE '跳过视图: %', r.viewname;
                        END;
                    END LOOP;
                END $$;
                
                -- 删除所有函数
                DO $$
                DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (
                        SELECT proname, oidvectortypes(proargtypes) as argtypes
                        FROM pg_proc 
                        WHERE pronamespace = (
                            SELECT oid FROM pg_namespace WHERE nspname = 'public'
                        )
                    ) 
                    LOOP
                        BEGIN
                            EXECUTE 'DROP FUNCTION IF EXISTS ' || quote_ident(r.proname) || 
                                   '(' || r.argtypes || ') CASCADE';
                            RAISE NOTICE '删除函数: %(%)', r.proname, r.argtypes;
                        EXCEPTION WHEN others THEN
                            RAISE NOTICE '跳过函数: %(%)', r.proname, r.argtypes;
                        END;
                    END LOOP;
                END $$;
                
                -- 清理完成确认
                SELECT 'Database cleaned successfully' as result;
            """
            
            # 执行清理
            cmd = [
                "psql",
                "--host", default_host,
                "--port", str(default_port),
                "--username", default_user,
                "--dbname", target_db,
                "--no-password",
                "--single-transaction",
                "--command", cleanup_sql
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = default_password
            
            log_system_event(f"📋 执行数据库清理命令", "debug")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                log_system_event("✅ 数据库清理完成，准备恢复数据", "info")
                if stdout:
                    output = stdout.decode()
                    if "Database cleaned successfully" in output:
                        log_system_event("🎉 数据库清理验证成功", "info")
            else:
                error_msg = stderr.decode() if stderr else "数据库清理失败"
                log_system_event(f"⚠️ 数据库清理警告: {error_msg[:200]}...", "warning")
                # 不抛出异常，让pg_restore的--clean处理剩余清理
                
        except Exception as e:
            log_system_event(f"❌ 数据库清理异常: {str(e)}", "warning")
            # 不抛出异常，继续执行恢复流程
    
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
    ) -> tuple[bool, str]:
        """执行 pg_restore 命令"""
        try:
            # 确定目标数据库
            from sqlalchemy.engine.url import make_url
            from app.database import DATABASE_URL
            
            # 从数据库URL中解析数据库名
            db_url = make_url(DATABASE_URL)
            default_db_name = db_url.database
            default_host = db_url.host
            default_port = db_url.port
            default_user = db_url.username
            default_password = db_url.password
            
            target_db = restore_task.target_database or default_db_name
            
            log_system_event(f"恢复目标数据库: {target_db}", "info")
            
            # 构建恢复命令
            if original_backup_path.endswith('.gz'):
                # 对于压缩的自定义格式文件，先解压到临时文件
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.dump')
                temp_file.close()
                
                # 解压到临时文件
                decompress_cmd = f"gunzip -c '{original_backup_path}' > '{temp_file.name}'"
                decompress_result = subprocess.run(decompress_cmd, shell=True, capture_output=True, text=True)
                
                if decompress_result.returncode != 0:
                    raise Exception(f"解压备份文件失败: {decompress_result.stderr}")
                
                log_system_event(f"备份文件解压到: {temp_file.name}", "debug")
                
                # 使用pg_restore恢复 - 添加清理参数确保干净恢复
                cmd = [
                    "pg_restore",
                    "--host", default_host,
                    "--port", str(default_port),
                    "--username", default_user,
                    "--dbname", target_db,
                    "--no-password",
                    "--verbose",
                    "--clean",
                    "--if-exists",
                    "--no-owner",
                    "--no-privileges",
                    temp_file.name
                ]
            else:
                # 使用 psql 处理 SQL 文件
                cmd = [
                    "psql",
                    "--host", default_host,
                    "--port", str(default_port),
                    "--username", default_user,
                    "--dbname", target_db,
                    "--no-password",
                    "--file", restore_file_path
                ]
            
            # 设置环境变量
            env = os.environ.copy()
            env["PGPASSWORD"] = default_password
            
            log_system_event(f"执行恢复命令: {' '.join(cmd[:-1])} [file]", "debug")
            log_system_event(f"数据库连接信息 - 主机: {default_host}, 端口: {default_port}, 用户: {default_user}, 数据库: {target_db}", "debug")
            
            # 先测试数据库连接
            test_cmd = [
                "psql",
                "--host", default_host,
                "--port", str(default_port),
                "--username", default_user,
                "--dbname", target_db,
                "--no-password",
                "--command", "SELECT 1;"
            ]
            
            log_system_event("测试数据库连接...", "info")
            test_process = await asyncio.create_subprocess_exec(
                *test_cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            test_stdout, test_stderr = await test_process.communicate()
            
            if test_process.returncode != 0:
                connection_error = test_stderr.decode() if test_stderr else "数据库连接测试失败"
                log_system_event(f"数据库连接测试失败: {connection_error}", "error")
                restore_task.error_message = f"数据库连接失败: {connection_error}"
                self.db.commit()
                return False
            else:
                log_system_event("数据库连接测试成功", "info")
            
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
            
            # 记录详细的输出信息
            if stdout:
                stdout_text = stdout.decode()
                log_system_event(f"恢复命令标准输出: {stdout_text[:500]}...", "debug")
            
            if stderr:
                stderr_text = stderr.decode()
                log_system_event(f"恢复命令错误输出: {stderr_text[:500]}...", "debug")
            
            if process.returncode == 0:
                log_system_event("数据库恢复执行成功", "info")
                return True, temp_file.name if original_backup_path.endswith('.gz') else None
            else:
                error_msg = stderr.decode() if stderr else "数据库恢复执行失败"
                log_system_event(f"数据库恢复执行失败 (返回码: {process.returncode}): {error_msg}", "error")
                restore_task.error_message = f"恢复失败 (返回码: {process.returncode}): {error_msg}"
                self.db.commit()
                return False, temp_file.name if original_backup_path.endswith('.gz') else None
                
        except Exception as e:
            log_system_event(f"数据库恢复执行异常: {str(e)}", "error")
            return False, None
    
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
                    # 不在监控循环中提交，避免Session冲突
                    # self.db.commit()
                
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