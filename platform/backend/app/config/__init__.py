"""
配置模块
"""

from .environment import get_environment_config, EnvironmentConfig
import os

# 创建settings对象以保持向后兼容
class Settings:
    """设置类，提供配置访问"""
    
    def __init__(self):
        self.env_config = get_environment_config()
    
    @property
    def database_url(self):
        db_config = self.env_config.get_database_config()
        return f"postgresql://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    
    @property
    def tts_service_url(self):
        tts_config = self.env_config.get_tts_config()
        return tts_config['service_url']
    
    @property
    def SONGGENERATION_URL(self):
        """SongGeneration服务URL"""
        return os.getenv("SONGGENERATION_URL", "http://localhost:8081")

# 创建全局settings实例
settings = Settings()

__all__ = ['get_environment_config', 'EnvironmentConfig', 'settings'] 