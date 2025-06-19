#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频文件同步服务
提供统一的音频文件同步、校验和清理功能
"""

import os
import hashlib
import logging
import asyncio
import wave
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.database import SessionLocal


logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """同步结果数据类"""
    scanned_files: int = 0
    new_files: int = 0
    updated_files: int = 0
    orphaned_records: int = 0
    invalid_files: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


@dataclass
class FileInfo:
    """文件信息数据类"""
    path: str
    size: int
    md5: str
    duration: float
    sample_rate: int
    channels: int
    modified_time: datetime


class AudioSyncService:
    """音频文件同步服务"""
    
    def __init__(self):
        self.audio_dir = os.getenv("AUDIO_DIR", "platform/backend/uploads")
        self.environment_sounds_dir = os.getenv("ENVIRONMENT_SOUNDS_DIR", "platform/backend/uploads/environment_sounds")
        
        # 确保目录存在
        os.makedirs(self.audio_dir, exist_ok=True)
        os.makedirs(self.environment_sounds_dir, exist_ok=True)
        
        # 支持的音频格式
        self.supported_formats = {'.wav', '.mp3', '.flac', '.m4a', '.ogg'}
    
    def calculate_file_md5(self, file_path: str) -> str:
        """计算文件MD5哈希值"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"计算文件MD5失败 {file_path}: {e}")
            return ""
    
    def get_audio_info(self, file_path: str) -> Optional[FileInfo]:
        """获取音频文件信息"""
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            size = stat.st_size
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            
            # 计算MD5
            md5 = self.calculate_file_md5(file_path)
            
            # 获取音频属性
            duration = 0.0
            sample_rate = 44100
            channels = 2
            
            if file_path.lower().endswith('.wav'):
                try:
                    with wave.open(file_path, 'r') as wav_file:
                        frames = wav_file.getnframes()
                        sample_rate = wav_file.getframerate()
                        channels = wav_file.getnchannels()
                        duration = frames / float(sample_rate)
                except Exception as e:
                    logger.warning(f"无法读取WAV文件信息 {file_path}: {e}")
            
            return FileInfo(
                path=file_path,
                size=size,
                md5=md5,
                duration=duration,
                sample_rate=sample_rate,
                channels=channels,
                modified_time=modified_time
            )
            
        except Exception as e:
            logger.error(f"获取文件信息失败 {file_path}: {e}")
            return None
    
    def scan_directory(self, directory: str) -> List[FileInfo]:
        """扫描目录中的音频文件"""
        files = []
        
        if not os.path.exists(directory):
            logger.warning(f"目录不存在: {directory}")
            return files
        
        try:
            for root, dirs, filenames in os.walk(directory):
                for filename in filenames:
                    if Path(filename).suffix.lower() in self.supported_formats:
                        file_path = os.path.join(root, filename)
                        file_info = self.get_audio_info(file_path)
                        if file_info:
                            files.append(file_info)
                        
        except Exception as e:
            logger.error(f"扫描目录失败 {directory}: {e}")
        
        return files
    
    def sync_audio_files(self, db: Session, full_scan: bool = False) -> SyncResult:
        """同步音频库文件"""
        result = SyncResult()
        
        try:
            # 导入模型（避免循环导入）
            from app.models import AudioFile
            
            # 扫描音频目录
            scanned_files = self.scan_directory(self.audio_dir)
            result.scanned_files = len(scanned_files)
            
            # 获取数据库中的所有记录
            db_files = db.query(AudioFile).filter(AudioFile.status != 'deleted').all()
            db_file_paths = {f.file_path: f for f in db_files}
            
            # 检测新文件和更新文件
            for file_info in scanned_files:
                try:
                    if file_info.path in db_file_paths:
                        # 文件已存在，检查是否需要更新
                        db_file = db_file_paths[file_info.path]
                        
                        # 检查文件是否发生变化
                        if (db_file.file_size != file_info.size):
                            
                            # 更新文件信息
                            db_file.file_size = file_info.size
                            db_file.duration = file_info.duration
                            db_file.updated_at = datetime.now()
                            
                            result.updated_files += 1
                            logger.info(f"更新音频文件: {file_info.path}")
                    else:
                        # 新文件，创建记录
                        filename = os.path.basename(file_info.path)
                        
                        # 解析文件类型和关联信息
                        audio_type = self._parse_audio_type(filename)
                        project_id = self._extract_project_id(filename)
                        
                        audio_file = AudioFile(
                            filename=filename,
                            original_name=filename,
                            file_path=file_info.path,
                            file_size=file_info.size,
                            duration=file_info.duration,
                            audio_type=audio_type,
                            project_id=project_id,
                            status='active',
                            created_at=file_info.modified_time
                        )
                        
                        db.add(audio_file)
                        result.new_files += 1
                        logger.info(f"添加新音频文件: {file_info.path}")
                        
                except Exception as e:
                    result.errors.append(f"处理文件失败 {file_info.path}: {str(e)}")
                    logger.error(f"处理文件失败 {file_info.path}: {e}")
            
            # 检查孤立记录（数据库有记录但文件不存在）
            scanned_paths = {f.path for f in scanned_files}
            for db_file in db_files:
                if db_file.file_path not in scanned_paths:
                    if os.path.exists(db_file.file_path):
                        # 文件存在但不在扫描目录中，可能移动了位置
                        continue
                    
                    # 文件不存在，标记为已删除
                    db_file.status = 'deleted'
                    db_file.updated_at = datetime.now()
                    result.orphaned_records += 1
                    logger.info(f"标记孤立记录: {db_file.file_path}")
            
            db.commit()
            logger.info(f"音频文件同步完成: 扫描{result.scanned_files}个，新增{result.new_files}个，更新{result.updated_files}个，孤立{result.orphaned_records}个")
            
        except Exception as e:
            db.rollback()
            result.errors.append(f"同步过程失败: {str(e)}")
            logger.error(f"音频文件同步失败: {e}")
        
        return result
    
    def sync_environment_sounds(self, db: Session, full_scan: bool = False) -> SyncResult:
        """同步环境音文件"""
        result = SyncResult()
        
        try:
            # 导入模型（避免循环导入）
            from app.models.environment_sound import EnvironmentSound
            
            # 扫描环境音目录
            scanned_files = self.scan_directory(self.environment_sounds_dir)
            result.scanned_files = len(scanned_files)
            
            # 获取数据库中的所有环境音记录
            db_sounds = db.query(EnvironmentSound).filter(
                EnvironmentSound.generation_status != 'deleted'
            ).all()
            db_sound_paths = {s.file_path: s for s in db_sounds if s.file_path}
            
            # 检测新文件和更新文件
            for file_info in scanned_files:
                try:
                    if file_info.path in db_sound_paths:
                        # 文件已存在，检查是否需要更新
                        db_sound = db_sound_paths[file_info.path]
                        
                        # 检查文件是否发生变化
                        if (db_sound.file_size != file_info.size):
                            
                            # 更新文件信息
                            db_sound.file_size = file_info.size
                            db_sound.duration = file_info.duration
                            db_sound.updated_at = datetime.now()
                            
                            result.updated_files += 1
                            logger.info(f"更新环境音文件: {file_info.path}")
                    else:
                        # 新文件，但需要谨慎处理，因为环境音通常通过生成创建
                        # 只有在明确是环境音文件时才创建记录
                        if self._is_environment_sound_file(file_info.path):
                            filename = os.path.basename(file_info.path)
                            
                            # 尝试从文件名解析信息
                            name = self._extract_sound_name(filename)
                            category = self._extract_sound_category(file_info.path)
                            
                            environment_sound = EnvironmentSound(
                                name=name,
                                description=f"从文件同步: {filename}",
                                file_path=file_info.path,
                                file_size=file_info.size,
                                duration=file_info.duration,
                                category=category,
                                generation_status='completed',
                                created_at=file_info.modified_time
                            )
                            
                            db.add(environment_sound)
                            result.new_files += 1
                            logger.info(f"添加新环境音文件: {file_info.path}")
                        
                except Exception as e:
                    result.errors.append(f"处理环境音文件失败 {file_info.path}: {str(e)}")
                    logger.error(f"处理环境音文件失败 {file_info.path}: {e}")
            
            # 检查孤立记录
            scanned_paths = {f.path for f in scanned_files}
            for db_sound in db_sounds:
                if db_sound.file_path and db_sound.file_path not in scanned_paths:
                    if not os.path.exists(db_sound.file_path):
                        # 文件不存在，根据状态处理
                        if db_sound.generation_status == 'completed':
                            db_sound.generation_status = 'failed'
                            db_sound.error_message = "音频文件丢失"
                        db_sound.updated_at = datetime.now()
                        result.orphaned_records += 1
                        logger.info(f"标记环境音孤立记录: {db_sound.file_path}")
            
            db.commit()
            logger.info(f"环境音同步完成: 扫描{result.scanned_files}个，新增{result.new_files}个，更新{result.updated_files}个，孤立{result.orphaned_records}个")
            
        except Exception as e:
            db.rollback()
            result.errors.append(f"环境音同步过程失败: {str(e)}")
            logger.error(f"环境音同步失败: {e}")
        
        return result
    
    def sync_all(self, db: Session = None, full_scan: bool = False) -> Dict[str, SyncResult]:
        """同步所有音频文件"""
        if db is None:
            db = SessionLocal()
        
        try:
            results = {
                'audio_files': self.sync_audio_files(db, full_scan),
                'environment_sounds': self.sync_environment_sounds(db, full_scan)
            }
            
            # 汇总统计
            total_scanned = sum(r.scanned_files for r in results.values())
            total_new = sum(r.new_files for r in results.values())
            total_updated = sum(r.updated_files for r in results.values())
            total_orphaned = sum(r.orphaned_records for r in results.values())
            
            logger.info(f"音频同步总计: 扫描{total_scanned}个，新增{total_new}个，更新{total_updated}个，孤立{total_orphaned}个")
            
            return results
            
        finally:
            if db:
                db.close()
    
    def verify_file_integrity(self, db: Session) -> List[Dict]:
        """验证文件完整性"""
        issues = []
        
        try:
            # 导入模型（避免循环导入）
            from app.models import AudioFile
            from app.models.environment_sound import EnvironmentSound
            
            # 检查音频文件
            audio_files = db.query(AudioFile).filter(AudioFile.status == 'active').all()
            for audio_file in audio_files:
                if not os.path.exists(audio_file.file_path):
                    issues.append({
                        'type': 'missing_file',
                        'model': 'AudioFile',
                        'id': audio_file.id,
                        'path': audio_file.file_path,
                        'message': '文件不存在'
                    })
                else:
                    # 检查文件大小
                    actual_size = os.path.getsize(audio_file.file_path)
                    if actual_size != audio_file.file_size:
                        issues.append({
                            'type': 'size_mismatch',
                            'model': 'AudioFile',
                            'id': audio_file.id,
                            'path': audio_file.file_path,
                            'message': f'文件大小不匹配: 期望{audio_file.file_size}，实际{actual_size}'
                        })
            
            # 检查环境音文件
            environment_sounds = db.query(EnvironmentSound).filter(
                EnvironmentSound.generation_status == 'completed'
            ).all()
            for sound in environment_sounds:
                if sound.file_path and not os.path.exists(sound.file_path):
                    issues.append({
                        'type': 'missing_file',
                        'model': 'EnvironmentSound',
                        'id': sound.id,
                        'path': sound.file_path,
                        'message': '环境音文件不存在'
                    })
                elif sound.file_path:
                    # 检查文件大小
                    actual_size = os.path.getsize(sound.file_path)
                    if actual_size != sound.file_size:
                        issues.append({
                            'type': 'size_mismatch',
                            'model': 'EnvironmentSound',
                            'id': sound.id,
                            'path': sound.file_path,
                            'message': f'文件大小不匹配: 期望{sound.file_size}，实际{actual_size}'
                        })
            
        except Exception as e:
            logger.error(f"文件完整性验证失败: {e}")
            issues.append({
                'type': 'verification_error',
                'message': f'验证过程出错: {str(e)}'
            })
        
        return issues
    
    def cleanup_orphaned_records(self, db: Session, dry_run: bool = True) -> Dict:
        """清理孤立记录"""
        result = {
            'audio_files_cleaned': 0,
            'environment_sounds_cleaned': 0,
            'errors': []
        }
        
        try:
            # 导入模型（避免循环导入）
            from app.models import AudioFile
            from app.models.environment_sound import EnvironmentSound
            
            # 清理音频文件孤立记录
            orphaned_audio = db.query(AudioFile).filter(
                and_(
                    AudioFile.status == 'deleted',
                    AudioFile.updated_at < datetime.now() - timedelta(days=7)  # 删除超过7天的记录
                )
            ).all()
            
            for audio_file in orphaned_audio:
                if not dry_run:
                    db.delete(audio_file)
                result['audio_files_cleaned'] += 1
            
            # 清理环境音孤立记录
            orphaned_sounds = db.query(EnvironmentSound).filter(
                and_(
                    EnvironmentSound.generation_status == 'failed',
                    EnvironmentSound.error_message.like('%文件丢失%'),
                    EnvironmentSound.updated_at < datetime.now() - timedelta(days=7)
                )
            ).all()
            
            for sound in orphaned_sounds:
                if not dry_run:
                    db.delete(sound)
                result['environment_sounds_cleaned'] += 1
            
            if not dry_run:
                db.commit()
                logger.info(f"清理孤立记录完成: 音频文件{result['audio_files_cleaned']}个，环境音{result['environment_sounds_cleaned']}个")
            else:
                logger.info(f"模拟清理孤立记录: 音频文件{result['audio_files_cleaned']}个，环境音{result['environment_sounds_cleaned']}个")
            
        except Exception as e:
            if not dry_run:
                db.rollback()
            result['errors'].append(f"清理过程失败: {str(e)}")
            logger.error(f"清理孤立记录失败: {e}")
        
        return result
    
    # 辅助方法
    def _parse_audio_type(self, filename: str) -> str:
        """从文件名解析音频类型"""
        filename_lower = filename.lower()
        
        if filename_lower.startswith('segment_'):
            return 'segment'
        elif filename_lower.startswith('project_'):
            return 'project'
        elif filename_lower.startswith('tts_'):
            return 'single'
        elif filename_lower.startswith('test_'):
            return 'test'
        elif filename_lower.startswith('env_'):
            return 'environment'
        else:
            return 'unknown'
    
    def _extract_project_id(self, filename: str) -> Optional[int]:
        """从文件名提取项目ID"""
        try:
            if filename.startswith('project_'):
                parts = filename.split('_')
                if len(parts) >= 2 and parts[1].isdigit():
                    return int(parts[1])
        except:
            pass
        return None
    
    def _is_environment_sound_file(self, file_path: str) -> bool:
        """判断是否为环境音文件"""
        # 检查文件路径是否在环境音目录中
        try:
            return str(Path(file_path)).startswith(str(Path(self.environment_sounds_dir)))
        except:
            return False
    
    def _extract_sound_name(self, filename: str) -> str:
        """从文件名提取环境音名称"""
        # 移除扩展名和常见前缀
        name = Path(filename).stem
        
        # 移除常见前缀
        prefixes = ['env_sound_', 'environment_', 'env_']
        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break
        
        # 移除时间戳等后缀
        import re
        name = re.sub(r'_\d{8}_\w+$', '', name)
        name = re.sub(r'_\d{10,}$', '', name)
        
        return name or "未知环境音"
    
    def _extract_sound_category(self, file_path: str) -> str:
        """从文件路径提取环境音分类"""
        try:
            relative_path = os.path.relpath(file_path, self.environment_sounds_dir)
            parts = relative_path.split(os.sep)
            
            # 如果有子目录，使用第一级子目录作为分类
            if len(parts) > 1:
                return parts[0]
        except:
            pass
        
        return "general"


# 全局实例
audio_sync_service = AudioSyncService()