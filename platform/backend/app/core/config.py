import os

class Settings:
    """应用配置"""
    
    def __init__(self):
        # 数据库配置
        self.database_url = "sqlite:///./app.db"
        
        # API配置
        self.api_v1_str = "/api/v1"
        self.project_name = "AI-Sound Platform"
        
        # 文件路径配置
        self.voice_profiles_dir = "data/voice_profiles"
        self.avatars_dir = "data/avatars"
        self.temp_dir = "data/temp"
        self.UPLOAD_DIR = "data/uploads"
        
        # AI服务配置
        self.AVATAR_GENERATION_API_URL = os.getenv("AVATAR_GENERATION_API_URL", "http://localhost:7860")
        self.AVATAR_GENERATION_ENABLED = os.getenv("AVATAR_GENERATION_ENABLED", "false").lower() == "true"
        self.AVATAR_GENERATION_API_KEY = os.getenv("AVATAR_GENERATION_API_KEY", "")
    
    # Docker环境检测
    @property
    def is_docker(self) -> bool:
        return os.path.exists("/.dockerenv")
    
    # 根据环境调整路径
    @property
    def voice_profiles_path(self) -> str:
        if self.is_docker:
            return "/app/data/voice_profiles"
        return self.voice_profiles_dir
    
    @property
    def avatars_path(self) -> str:
        if self.is_docker:
            return "/app/data/avatars"
        return self.avatars_dir
    
    @property
    def temp_path(self) -> str:
        if self.is_docker:
            return "/app/data/temp"
        return self.temp_dir

settings = Settings()