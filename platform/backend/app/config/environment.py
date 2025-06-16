"""
环境配置管理
根据运行环境自动调整配置参数
"""

import os
from typing import Dict, Any
from ..utils.path_manager import get_path_manager


class EnvironmentConfig:
    """环境配置管理器"""
    
    def __init__(self):
        self.path_manager = get_path_manager()
        self.is_docker = self.path_manager.is_docker
        self.is_windows = self.path_manager.is_windows
        
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        if self.is_docker:
            return {
                "host": os.getenv("DB_HOST", "postgres"),
                "port": int(os.getenv("DB_PORT", "5432")),
                "database": os.getenv("DB_NAME", "ai_sound"),
                "username": os.getenv("DB_USER", "postgres"),
                "password": os.getenv("DB_PASSWORD", "password"),
                "pool_size": 20,
                "max_overflow": 30
            }
        else:
            return {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", "5432")),
                "database": os.getenv("DB_NAME", "ai_sound"),
                "username": os.getenv("DB_USER", "postgres"),
                "password": os.getenv("DB_PASSWORD", "123456"),
                "pool_size": 10,
                "max_overflow": 20
            }
    
    def get_tts_config(self) -> Dict[str, Any]:
        """获取TTS服务配置"""
        base_config = {
            "timeout": 300,
            "max_retries": 3,
            "batch_size": 10
        }
        
        if self.is_docker:
            base_config.update({
                "service_url": os.getenv("TTS_SERVICE_URL", "http://tts-service:8000"),
                "max_concurrent": 5
            })
        else:
            base_config.update({
                "service_url": os.getenv("TTS_SERVICE_URL", "http://localhost:8001"),
                "max_concurrent": 3
            })
        
        return base_config
    
    def get_storage_config(self) -> Dict[str, Any]:
        """获取存储配置"""
        return {
            "base_paths": self.path_manager.base_paths,
            "max_file_size": 100 * 1024 * 1024,  # 100MB
            "allowed_audio_formats": [".wav", ".mp3", ".flac"],
            "temp_cleanup_interval": 3600,  # 1小时
            "backup_enabled": not self.is_docker  # 本地环境启用备份
        }
    
    def validate_environment(self) -> Dict[str, Any]:
        """验证环境配置"""
        issues = []
        
        # 检查必要的目录
        for path_type, path in self.path_manager.base_paths.items():
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                except Exception as e:
                    issues.append(f"无法创建目录 {path_type}: {path} - {e}")
        
        return {
            "environment": "docker" if self.is_docker else "local",
            "platform": "windows" if self.is_windows else "unix",
            "issues": issues,
            "configs": {
                "database": self.get_database_config(),
                "tts": self.get_tts_config(),
                "storage": self.get_storage_config()
            }
        }


# 全局环境配置实例
_env_config = None

def get_environment_config() -> EnvironmentConfig:
    """获取环境配置单例"""
    global _env_config
    if _env_config is None:
        _env_config = EnvironmentConfig()
    return _env_config 