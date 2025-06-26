"""
系统模型 - 兼容性版本
用于数据库迁移前的临时支持
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float, Enum as SQLEnum, Index
import json
import enum

from .base import BaseModel


class LogLevel(enum.Enum):
    """日志级别枚举"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogModule(enum.Enum):
    """日志模块枚举"""
    SYSTEM = "system"
    TTS = "tts"
    DATABASE = "database"
    API = "api"
    WEBSOCKET = "websocket"
    AUTH = "auth"
    FILE = "file"
    SYNTHESIS = "synthesis"
    ANALYSIS = "analysis"


class SystemLogCompat(BaseModel):
    """系统日志模型 - 兼容性版本（只包含原有字段）"""
    __tablename__ = "system_logs"
    
    # 原有字段
    level = Column(SQLEnum(LogLevel), nullable=False, index=True, comment="日志级别")
    module = Column(SQLEnum(LogModule), nullable=False, index=True, comment="模块名称")
    message = Column(Text, nullable=False, comment="日志消息")
    details = Column(Text, nullable=True, comment="详细信息 JSON字符串")
    
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
        """转换为字典格式 - 兼容新字段但设为None"""
        return {
            'id': self.id,
            'level': self.level.value if self.level else None,
            'module': self.module.value if self.module else None,
            'message': self.message,
            'details': self.details,
            'source_file': None,  # 新字段默认为None
            'source_line': None,
            'function': None,
            'user_id': None,
            'session_id': None,
            'ip_address': None,
            'user_agent': None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def create_log(cls, level: LogLevel, module: LogModule, message: str, **kwargs):
        """创建日志记录的便捷方法 - 忽略新字段"""
        return cls(
            level=level,
            module=module,
            message=message,
            details=kwargs.get('details')
        )