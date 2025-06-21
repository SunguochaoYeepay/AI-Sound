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
from app.utils.logger import log_system_event

# 配置常量 - 使用本地开发环境路径
import os
from pathlib import Path

# 备份存储配置
BACKUP_DIR = os.getenv("BACKUP_DIR", "/app/data/backups")  # Docker环境使用容器内路径
AUDIO_DIR = os.getenv("AUDIO_DIR", "/app/data/audio")

# 确保备份目录存在
os.makedirs(BACKUP_DIR, exist_ok=True)
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
            
            # 如果找不到，尝试使用默认安装路径
            if not pg_dump_path:
                potential_paths = [
                    r"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe",
                    r"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe",
                    r"C:\Program Files (x86)\PostgreSQL\16\bin\pg_dump.exe",
                ]
                
                for path in potential_paths:
                    if os.path.exists(path):
                        pg_dump_path = path
                        log_system_event(f"✅ 使用完整路径找到 pg_dump: {pg_dump_path}", "info")
                        break
            
            if not pg_dump_path:
                error_msg = """pg_dump 工具未安装，请先安装 PostgreSQL 客户端工具

📥 安装方法：
1. 访问 https://www.postgresql.org/download/windows/
2. 下载 PostgreSQL 安装包（推荐版本 15 或 16）
3. 安装时确保选择 "Command Line Tools"
4. 安装完成后重启AI-Sound后端

💡 或者使用 Chocolatey：
   choco install postgresql

⚠️ 注意：安装后需要将 PostgreSQL/bin 目录添加到系统 PATH 环境变量中
   典型路径：C:\\Program Files\\PostgreSQL\\15\\bin

🔧 临时解决方案：如果只需要配置备份而不立即执行，可以先创建备份配置"""
                
                log_system_event("❌ pg_dump 工具检查失败", "error")
                log_system_event("📋 提供PostgreSQL客户端工具安装指导", "info")
                task.error_message = error_msg
                self.db.commit()
                return False
            
            log_system_event(f"✅ 找到 pg_dump 工具: {pg_dump_path}", "info")
            
            # 从 database_url 解析数据库连接参数
            import re
            
            # 解析 database_url
            # 格式: postgresql://username:password@host:port/database
            db_url = self.settings.database_url
            log_system_event(f"🔧 使用数据库连接: {db_url}", "info")
            print(f"DATABASE URL: {db_url}")
            match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
            
            if not match:
                raise Exception(f"无效的 database_url 格式: {db_url}")
            
            username, password, host, port, database = match.groups()
            
            print(f"HOST: {host}, PORT: {port}, USER: {username}, DB: {database}")
            log_system_event(f"🔗 连接参数: {host}:{port}/{database} (用户: {username})", "info")
            
            # 构建 pg_dump 命令
            cmd = [
                pg_dump_path,
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
            
            # Windows平台使用同步subprocess，避免asyncio问题
            import subprocess
            import threading
            import time
            
            result_container = {"process": None, "stdout": None, "stderr": None, "returncode": None}
            
            def run_pg_dump():
                """在线程中运行pg_dump"""
                try:
                    log_system_event("🔄 开始执行pg_dump进程...", "info")
                    process = subprocess.Popen(
                        cmd,
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    result_container["process"] = process
                    
                    # 等待进程完成
                    stdout, stderr = process.communicate()
                    result_container["stdout"] = stdout
                    result_container["stderr"] = stderr
                    result_container["returncode"] = process.returncode
                    
                    log_system_event(f"✅ pg_dump进程完成，退出码: {process.returncode}", "info")
                    
                except Exception as e:
                    log_system_event(f"❌ pg_dump进程异常: {str(e)}", "error")
                    result_container["returncode"] = -1
                    result_container["stderr"] = str(e)
            
            # 启动线程执行pg_dump
            dump_thread = threading.Thread(target=run_pg_dump)
            dump_thread.start()
            
            # 监控进度，每2秒更新一次
            progress = 10
            while dump_thread.is_alive():
                await asyncio.sleep(2)
                if progress < 60:
                    progress += 5
                    task.progress_percentage = progress
                    self.db.commit()
                    log_system_event(f"📊 备份进度: {progress}%", "debug")
            
            # 等待线程完成
            dump_thread.join()
            
            # 获取结果
            stdout = result_container["stdout"] or ""
            stderr = result_container["stderr"] or ""
            returncode = result_container["returncode"]
            
            if returncode == 0:
                log_system_event(f"✅ pg_dump 执行成功，退出码: {returncode}", "info")
                
                # 检查备份文件是否成功生成
                if os.path.exists(backup_path):
                    file_size = os.path.getsize(backup_path)
                    log_system_event(f"📁 备份文件已生成: {backup_path} ({file_size / 1024 / 1024:.2f} MB)", "info")
                else:
                    log_system_event(f"❌ 备份文件未生成: {backup_path}", "error")
                    return False
                    
                return True
            else:
                error_msg = stderr if stderr else "pg_dump 执行失败"
                log_system_event(f"❌ pg_dump 执行失败 (退出码: {returncode}): {error_msg}", "error")
                task.error_message = error_msg
                self.db.commit()
                return False
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            error_msg = f"pg_dump 执行异常: {str(e)}"
            
            # 记录详细错误信息
            log_system_event(f"❌ {error_msg}", "error")
            log_system_event(f"📋 错误详情: {error_details}", "error")
            print(f"BACKUP ERROR: {error_msg}")
            print(f"BACKUP ERROR DETAILS: {error_details}")
            
            # 检查具体错误类型
            error_str = str(e).lower()
            if "connection" in error_str or "connect" in error_str:
                log_system_event("🔗 可能是数据库连接问题", "error")
            elif "permission" in error_str or "access" in error_str:
                log_system_event("🔐 可能是权限问题", "error")
            elif "no such file" in error_str or "not found" in error_str:
                log_system_event("📁 可能是文件路径问题", "error")
            
            # 提供具体的修复建议
            if "No such file or directory" in str(e) or "not found" in str(e).lower():
                fix_msg = """
🔧 PostgreSQL工具路径问题修复建议:
1. 重启AI-Sound后端程序 (让环境变量生效)
2. 检查PATH环境变量是否包含: C:\\Program Files\\PostgreSQL\\16\\bin
3. 验证pg_dump.exe是否存在于该路径
4. 如果问题持续，请重启整个系统
"""
                log_system_event(fix_msg, "info")
                task.error_message = f"{error_msg}\n{fix_msg}"
            else:
                task.error_message = error_msg
            
            self.db.commit()
            return False
    

    

    
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

    def check_backup_environment(self) -> Dict[str, Any]:
        """检查备份环境状态"""
        import shutil
        
        result = {
            "pg_dump_available": False,
            "pg_dump_path": None,
            "backup_directory": False,
            "database_connection": False,
            "environment": "unknown",
            "recommendations": []
        }
        
        # 检测运行环境
        is_docker = os.path.exists('/.dockerenv') or os.getenv('DOCKER_CONTAINER', False)
        result["environment"] = "docker" if is_docker else "host"
        
        # 检查 pg_dump
        pg_dump_path = shutil.which('pg_dump')
        if pg_dump_path:
            result["pg_dump_available"] = True
            result["pg_dump_path"] = pg_dump_path
            log_system_event(f"✅ pg_dump 工具可用: {pg_dump_path} (环境: {result['environment']})", "info")
        else:
            if is_docker:
                result["recommendations"].append({
                    "type": "critical",
                    "message": "Docker容器中缺少 PostgreSQL 客户端工具",
                    "action": "重新构建Docker镜像，确保安装了 postgresql-client 包"
                })
                log_system_event("❌ Docker容器中pg_dump工具不可用", "warning")
            else:
                result["recommendations"].append({
                    "type": "critical",
                    "message": "需要安装 PostgreSQL 客户端工具",
                    "action": "访问 https://www.postgresql.org/download/windows/ 下载安装"
                })
                log_system_event("❌ 主机环境中pg_dump工具不可用", "warning")
        
        # 检查备份目录
        try:
            self._ensure_backup_directory()
            result["backup_directory"] = True
            log_system_event(f"✅ 备份目录可用: {BACKUP_DIR}", "info")
        except Exception as e:
            result["recommendations"].append({
                "type": "error", 
                "message": f"备份目录创建失败: {str(e)}",
                "action": "检查磁盘空间和权限"
            })
            log_system_event(f"❌ 备份目录检查失败: {str(e)}", "error")
        
        # 检查数据库连接（简单检查）
        try:
            # 这里只是检查数据库会话是否有效
            self.db.execute("SELECT 1")
            result["database_connection"] = True
            log_system_event("✅ 数据库连接正常", "info")
        except Exception as e:
            result["recommendations"].append({
                "type": "error",
                "message": f"数据库连接失败: {str(e)}",
                "action": "检查数据库服务状态"
            })
            log_system_event(f"❌ 数据库连接检查失败: {str(e)}", "error")
        
        # 总体状态
        result["ready"] = all([
            result["pg_dump_available"],
            result["backup_directory"], 
            result["database_connection"]
        ])
        
        if result["ready"]:
            log_system_event("🎉 备份环境检查通过，可以执行备份操作", "info")
        else:
            log_system_event("⚠️ 备份环境检查未通过，请先解决相关问题", "warning")
        
        return result