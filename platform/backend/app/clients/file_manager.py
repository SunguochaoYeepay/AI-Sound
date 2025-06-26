"""
文件管理器
处理文件上传、存储和管理
"""

import os
import shutil
import aiofiles
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
import hashlib
from datetime import datetime
import mimetypes
import logging

logger = logging.getLogger(__name__)


class FileManager:
    """文件管理器"""
    
    def __init__(self, base_path: str = "./storage"):
        from app.utils.path_manager import PathManager
        path_manager = PathManager()
        self.base_path = Path(path_manager.get_storage_path('storage'))
        self.base_path.mkdir(exist_ok=True)
        
        # 创建子目录
        self.uploads_dir = self.base_path / "uploads"
        self.books_dir = self.base_path / "books"
        self.audio_dir = self.base_path / "audio"
        self.temp_dir = self.base_path / "temp"
        
        for directory in [self.uploads_dir, self.books_dir, self.audio_dir, self.temp_dir]:
            directory.mkdir(exist_ok=True)
    
    async def save_uploaded_file(
        self,
        file_data: bytes,
        filename: str,
        category: str = "uploads"
    ) -> Dict[str, Any]:
        """
        保存上传的文件
        
        Args:
            file_data: 文件数据
            filename: 文件名
            category: 文件分类 (uploads, books, audio, temp)
        
        Returns:
            文件信息字典
        """
        try:
            # 选择保存目录
            if category == "books":
                save_dir = self.books_dir
            elif category == "audio":
                save_dir = self.audio_dir
            elif category == "temp":
                save_dir = self.temp_dir
            else:
                save_dir = self.uploads_dir
            
            # 生成唯一文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(filename)
            safe_filename = f"{timestamp}_{self._sanitize_filename(name)}{ext}"
            
            file_path = save_dir / safe_filename
            
            # 异步写入文件
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_data)
            
            # 计算文件信息
            file_size = len(file_data)
            file_hash = hashlib.md5(file_data).hexdigest()
            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            
            file_info = {
                "filename": safe_filename,
                "original_filename": filename,
                "file_path": str(file_path),
                "relative_path": str(file_path.relative_to(self.base_path)),
                "file_size": file_size,
                "content_type": content_type,
                "file_hash": file_hash,
                "category": category,
                "created_at": datetime.now().isoformat()
            }
            
            logger.info(f"文件保存成功: {file_path}")
            return file_info
            
        except Exception as e:
            logger.error(f"文件保存失败: {e}")
            raise
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除非法字符
        
        Args:
            filename: 原始文件名
        
        Returns:
            清理后的文件名
        """
        # 移除或替换非法字符
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        
        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename
    
    async def read_text_file(
        self,
        file_path: str,
        encoding: str = "utf-8"
    ) -> Optional[str]:
        """
        读取文本文件内容
        
        Args:
            file_path: 文件路径
            encoding: 文件编码
        
        Returns:
            文件内容或None
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"文件不存在: {file_path}")
                return None
            
            async with aiofiles.open(path, 'r', encoding=encoding) as f:
                content = await f.read()
            
            return content
            
        except UnicodeDecodeError:
            # 尝试其他编码
            encodings = ['gbk', 'gb2312', 'latin1']
            for enc in encodings:
                try:
                    async with aiofiles.open(path, 'r', encoding=enc) as f:
                        content = await f.read()
                    logger.info(f"文件编码检测成功: {enc}")
                    return content
                except UnicodeDecodeError:
                    continue
            
            logger.error(f"无法解码文件: {file_path}")
            return None
            
        except Exception as e:
            logger.error(f"文本文件读取失败: {e}")
            return None
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
        
        Returns:
            文件信息字典或None
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            stat = path.stat()
            content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
            
            return {
                "filename": path.name,
                "file_path": str(path),
                "file_size": stat.st_size,
                "content_type": content_type,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_file": path.is_file(),
                "is_dir": path.is_dir()
            }
            
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return None

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Returns:
            存储统计信息字典
        """
        try:
            stats = {
                "base_path": str(self.base_path),
                "directories": {},
                "total_files": 0,
                "total_size": 0
            }
            
            # 统计各目录信息
            directories = {
                "uploads": self.uploads_dir,
                "books": self.books_dir,
                "audio": self.audio_dir,
                "temp": self.temp_dir
            }
            
            for name, directory in directories.items():
                if directory.exists():
                    dir_stats = self._get_directory_stats(directory)
                    stats["directories"][name] = dir_stats
                    stats["total_files"] += dir_stats["file_count"]
                    stats["total_size"] += dir_stats["total_size"]
                else:
                    stats["directories"][name] = {
                        "exists": False,
                        "file_count": 0,
                        "total_size": 0,
                        "path": str(directory)
                    }
            
            # 添加可读性大小
            stats["total_size_human"] = self._format_bytes(stats["total_size"])
            
            return stats
            
        except Exception as e:
            logger.error(f"获取存储统计失败: {e}")
            return {
                "error": str(e),
                "total_files": 0,
                "total_size": 0,
                "total_size_human": "0 B"
            }
    
    def _get_directory_stats(self, directory: Path) -> Dict[str, Any]:
        """
        获取目录统计信息
        
        Args:
            directory: 目录路径
        
        Returns:
            目录统计信息
        """
        try:
            file_count = 0
            total_size = 0
            
            for item in directory.rglob("*"):
                if item.is_file():
                    file_count += 1
                    total_size += item.stat().st_size
            
            return {
                "exists": True,
                "path": str(directory),
                "file_count": file_count,
                "total_size": total_size,
                "total_size_human": self._format_bytes(total_size)
            }
            
        except Exception as e:
            logger.error(f"获取目录统计失败: {e}")
            return {
                "exists": False,
                "error": str(e),
                "file_count": 0,
                "total_size": 0,
                "total_size_human": "0 B"
            }
    
    def _format_bytes(self, bytes_size: int) -> str:
        """
        格式化字节大小为可读格式
        
        Args:
            bytes_size: 字节大小
        
        Returns:
            格式化后的大小字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"


    async def save_audio_file(
        self,
        audio_data: bytes,
        filename: str,
        subfolder: str = "environment_sounds"
    ) -> str:
        """
        保存音频文件到指定子文件夹
        
        Args:
            audio_data: 音频数据
            filename: 文件名
            subfolder: 子文件夹名称
        
        Returns:
            保存的文件路径
        """
        try:
            # 创建子文件夹
            audio_subfolder = self.audio_dir / subfolder
            audio_subfolder.mkdir(exist_ok=True)
            
            # 生成唯一文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(filename)
            if not ext:
                ext = ".wav"  # 默认wav格式
            safe_filename = f"{timestamp}_{self._sanitize_filename(name)}{ext}"
            
            file_path = audio_subfolder / safe_filename
            
            # 异步写入文件
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(audio_data)
            
            logger.info(f"音频文件保存成功: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"音频文件保存失败: {e}")
            raise
    
    def get_audio_file_path(self, filename: str, subfolder: str = "environment_sounds") -> str:
        """
        获取音频文件的完整路径
        
        Args:
            filename: 文件名
            subfolder: 子文件夹名称
        
        Returns:
            文件完整路径
        """
        audio_subfolder = self.audio_dir / subfolder
        return str(audio_subfolder / filename)


# 全局文件管理器实例
file_manager = FileManager() 

# 导出函数供其他模块使用
async def save_audio_file(audio_data: bytes, filename: str, subfolder: str = "environment_sounds") -> str:
    """保存音频文件的便捷函数"""
    return await file_manager.save_audio_file(audio_data, filename, subfolder)

def get_audio_file_path(filename: str, subfolder: str = "environment_sounds") -> str:
    """获取音频文件路径的便捷函数"""
    return file_manager.get_audio_file_path(filename, subfolder) 