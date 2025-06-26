"""
系统日志模型
用于记录系统运行时的各种事件和错误信息
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from datetime import datetime
import json
from typing import Dict, Any

from .base import Base


class SystemLog(Base):
    """
    系统日志表 - 对应 Settings.vue 功能
    """
    __tablename__ = "system_logs"
    
    # 基础字段
    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(10), nullable=False, index=True)  # 'info' | 'warn' | 'error'
    message = Column(Text, nullable=False)
    module = Column(String(50), index=True)  # 'voice_clone' | 'characters' | 'novel_reader' | 'system'
    details = Column(Text)  # JSON格式的详细信息
    
    # 时间戳
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "level": self.level,
            "message": self.message,
            "module": self.module,
            "details": json.loads(self.details) if self.details else None,
            "time": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else None
        } 