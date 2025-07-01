"""
系统模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float, Enum as SQLEnum, Index
import json
import enum
from datetime import datetime

from .base import Base


class LogLevel(enum.Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogModule(enum.Enum):
    """日志模块枚举"""
    # 原有基础模块
    SYSTEM = "SYSTEM"
    TTS = "TTS"
    DATABASE = "DATABASE"
    API = "API"
    WEBSOCKET = "WEBSOCKET"
    AUTH = "AUTH"
    FILE = "FILE"
    SYNTHESIS = "SYNTHESIS"
    ANALYSIS = "ANALYSIS"
    ENVIRONMENT = "ENVIRONMENT"
    MUSIC = "MUSIC"
    
    # 新增专用模块（对应11个日志文件）
    BACKGROUND_MUSIC = "BACKGROUND_MUSIC"          # 背景音乐模块
    MUSIC_GENERATION = "MUSIC_GENERATION"          # 音乐生成服务
    INTELLIGENT_ANALYSIS = "INTELLIGENT_ANALYSIS"  # LLM智能分析
    TTS_VOICE = "TTS_VOICE"                       # TTS和语音合成
    ENVIRONMENT_SOUNDS = "ENVIRONMENT_SOUNDS"      # 环境音生成
    AUDIO_PROCESSING = "AUDIO_PROCESSING"          # 音频编辑和处理
    API_REQUESTS = "API_REQUESTS"                  # API请求和中间件
    DATABASE_OPS = "DATABASE_OPS"                  # 数据库操作
    WEBSOCKET_COMM = "WEBSOCKET_COMM"             # WebSocket实时通信


class SystemLog(Base):
    """系统日志模型"""
    __tablename__ = "system_logs"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    level = Column(SQLEnum(LogLevel), nullable=False, index=True, comment="日志级别")
    module = Column(SQLEnum(LogModule), nullable=False, index=True, comment="模块名称")
    message = Column(Text, nullable=False, comment="日志消息")
    
    # 详细信息  
    details = Column(Text, nullable=True, comment="详细信息 JSON字符串")
    source_file = Column(String(255), nullable=True, comment="源文件路径")
    source_line = Column(Integer, nullable=True, comment="源文件行号")
    function = Column(String(100), comment="函数名")
    
    # 用户信息
    user_id = Column(String(50), nullable=True, index=True, comment="用户ID")
    session_id = Column(String(100), nullable=True, index=True, comment="会话ID")
    ip_address = Column(String(45), nullable=True, comment="IP地址（支持IPv6）")
    user_agent = Column(String(500), nullable=True, comment="用户代理")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 性能优化索引
    __table_args__ = (
        Index('idx_log_level_time', 'level', 'created_at'),
        Index('idx_log_module_time', 'module', 'created_at'),
        Index('idx_log_user_time', 'user_id', 'created_at'),
    )
    
    def get_details(self):
        """获取详细信息"""
        try:
            return json.loads(self.details) if self.details else {}
        except json.JSONDecodeError:
            return {}
    
    def set_details(self, details):
        """设置详细信息"""
        self.details = json.dumps(details, ensure_ascii=False)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'level': self.level.value if self.level else None,
            'module': self.module.value if self.module else None,
            'message': self.message,
            'details': self.details,
            'source_file': self.source_file,
            'source_line': self.source_line,
            'function': self.function,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def create_log(cls, level: LogLevel, module: LogModule, message: str, **kwargs):
        """创建日志记录的便捷方法"""
        return cls(
            level=level,
            module=module,
            message=message,
            details=kwargs.get('details'),
            source_file=kwargs.get('source_file'),
            source_line=kwargs.get('source_line'),
            function=kwargs.get('function'),
            user_id=kwargs.get('user_id'),
            session_id=kwargs.get('session_id'),
            ip_address=kwargs.get('ip_address'),
            user_agent=kwargs.get('user_agent')
        )


class UsageStats(Base):
    """使用统计模型"""
    __tablename__ = "usage_stats"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    
    metric_name = Column(String(100), nullable=False, comment="指标名称")
    metric_value = Column(Float, nullable=False, comment="指标值")
    metric_unit = Column(String(50), comment="指标单位")
    
    # 分类信息
    category = Column(String(100), comment="分类")
    subcategory = Column(String(100), comment="子分类")
    
    # 时间范围
    period_start = Column(DateTime, comment="统计开始时间")
    period_end = Column(DateTime, comment="统计结束时间")
    
    # 额外信息
    meta_data = Column(JSON, comment="元数据")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_meta_data(self):
        """获取元数据"""
        try:
            return json.loads(self.meta_data) if self.meta_data else {}
        except json.JSONDecodeError:
            return {}
    
    def set_meta_data(self, meta_data):
        """设置元数据"""
        self.meta_data = json.dumps(meta_data, ensure_ascii=False)


class UserPreset(Base):
    """用户预设配置模型"""
    __tablename__ = "user_presets"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    
    # 预设基本信息
    name = Column(String(255), nullable=False, comment="预设名称")
    description = Column(Text, comment="预设描述")
    config_type = Column(String(50), nullable=False, comment="配置类型: voice_mapping, synthesis_params, analysis_params, analysis_complete")
    
    # 预设内容
    config_data = Column(JSON, nullable=False, comment="预设配置数据JSON")
    
    # 作用域信息
    scope = Column(String(50), default="global", comment="作用域: global, project, book")
    scope_id = Column(Integer, nullable=True, comment="作用域ID（项目ID或书籍ID）")
    
    # 用户信息
    user_id = Column(Integer, nullable=True, comment="创建用户ID")
    is_public = Column(Boolean, default=False, comment="是否公开")
    is_system = Column(Boolean, default=False, comment="是否系统预设")
    
    # 使用统计
    usage_count = Column(Integer, default=0, comment="使用次数")
    last_used = Column(DateTime, nullable=True, comment="最后使用时间")
    
    # 版本信息
    version = Column(String(20), default="1.0", comment="配置版本")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 索引优化
    __table_args__ = (
        Index('idx_preset_type_scope', 'config_type', 'scope'),
        Index('idx_preset_user_type', 'user_id', 'config_type'),
        Index('idx_preset_scope_id', 'scope', 'scope_id'),
        Index('idx_preset_usage', 'usage_count'),
    )
    
    def get_config_data(self):
        """获取配置数据"""
        try:
            return json.loads(self.config_data) if self.config_data else {}
        except json.JSONDecodeError:
            return {}
    
    def set_config_data(self, data):
        """设置配置数据"""
        self.config_data = json.dumps(data, ensure_ascii=False)
    
    def increment_usage(self):
        """增加使用次数"""
        self.usage_count = (self.usage_count or 0) + 1
        self.last_used = datetime.utcnow()
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'config_type': self.config_type,
            'config_data': self.get_config_data(),
            'scope': self.scope,
            'scope_id': self.scope_id,
            'user_id': self.user_id,
            'is_public': self.is_public,
            'is_system': self.is_system,
            'usage_count': self.usage_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def create_preset(cls, name: str, config_type: str, config_data: dict, **kwargs):
        """创建预设的便捷方法"""
        preset = cls(
            name=name,
            config_type=config_type,
            description=kwargs.get('description'),
            scope=kwargs.get('scope', 'global'),
            scope_id=kwargs.get('scope_id'),
            user_id=kwargs.get('user_id'),
            is_public=kwargs.get('is_public', False),
            is_system=kwargs.get('is_system', False),
            version=kwargs.get('version', '1.0')
        )
        preset.set_config_data(config_data)
        return preset

