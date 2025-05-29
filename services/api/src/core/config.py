"""
核心配置管理模块
使用Pydantic Settings进行配置管理
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
import os


class DatabaseConfig(BaseSettings):
    """数据库配置"""
    host: str = Field(default="localhost", description="MongoDB主机地址")
    port: int = Field(default=27017, description="MongoDB端口")
    database: str = Field(default="ai_sound", description="数据库名称")
    username: Optional[str] = Field(default="ai_sound_user", description="用户名")
    password: Optional[str] = Field(default="ai_sound_pass_2024", description="密码")
    
    @property
    def url(self) -> str:
        """获取数据库连接URL"""
        if self.username and self.password:
            return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?authSource=admin"
        return f"mongodb://{self.host}:{self.port}/{self.database}"
    
    class Config:
        env_prefix = "DB_"


class RedisConfig(BaseSettings):
    """Redis配置"""
    host: str = Field(default="localhost", description="Redis主机地址")
    port: int = Field(default=6379, description="Redis端口")
    db: int = Field(default=0, description="Redis数据库编号")
    password: Optional[str] = Field(default=None, description="Redis密码")
    
    @property
    def url(self) -> str:
        """获取Redis连接URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"
    
    class Config:
        env_prefix = "REDIS_"


class APIConfig(BaseSettings):
    """API服务配置"""
    host: str = Field(default="0.0.0.0", description="API服务主机")
    port: int = Field(default=9930, description="API服务端口")
    reload: bool = Field(default=False, description="是否启用热重载")
    workers: int = Field(default=1, description="工作进程数")
    cors_origins: List[str] = Field(default=["*"], description="CORS允许的源")
    
    class Config:
        env_prefix = "API_"


class TTSConfig(BaseSettings):
    """TTS引擎配置"""
    model_path: str = Field(default="data/models", description="模型文件路径")
    output_path: str = Field(default="data/output", description="输出文件路径")
    cache_path: str = Field(default="data/cache", description="缓存文件路径")
    max_text_length: int = Field(default=1000, description="最大文本长度")
    default_engine: str = Field(default="megatts3", description="默认TTS引擎")
    
    class Config:
        env_prefix = "TTS_"


class EngineConfig(BaseSettings):
    """TTS引擎服务配置"""
    megatts3_url: str = Field(default="http://localhost:7931", description="MegaTTS3服务URL")
    espnet_url: str = Field(default="http://localhost:9001", description="ESPnet服务URL")
    bertvits2_url: str = Field(default="http://localhost:9932", description="Bert-VITS2服务URL")
    
    class Config:
        env_prefix = ""  # 直接使用环境变量名


class LoggingConfig(BaseSettings):
    """日志配置"""
    level: str = Field(default="INFO", description="日志级别")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    file_path: Optional[str] = Field(default=None, description="日志文件路径")
    max_file_size: int = Field(default=10485760, description="日志文件最大大小(字节)")
    backup_count: int = Field(default=5, description="日志文件备份数量")
    
    class Config:
        env_prefix = "LOG_"


class Settings(BaseSettings):
    """应用主配置"""
    app_name: str = Field(default="AI-Sound TTS System", description="应用名称")
    version: str = Field(default="2.0.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    
    # 子配置
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    api: APIConfig = APIConfig()
    tts: TTSConfig = TTSConfig()
    logging: LoggingConfig = LoggingConfig()
    engines: EngineConfig = EngineConfig()
    
    class Config:
        # 移除env_file配置，只从环境变量读取
        extra = "ignore"  # 忽略额外的环境变量


# 全局配置实例
settings = Settings()