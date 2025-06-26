"""
使用统计模型
用于记录系统使用情况的统计数据
"""

from sqlalchemy import Column, Integer, String, Float
from typing import Dict, Any

from .base import Base


class UsageStats(Base):
    """
    使用统计表
    """
    __tablename__ = "usage_stats"
    
    # 基础字段
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False, unique=True, index=True)  # YYYY-MM-DD格式
    
    # 统计数据
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    total_processing_time = Column(Float, default=0.0)
    audio_files_generated = Column(Integer, default=0)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        success_rate = 0
        if self.total_requests > 0:
            success_rate = round((self.successful_requests / self.total_requests) * 100, 1)
        
        avg_processing_time = 0
        if self.successful_requests > 0:
            avg_processing_time = round(self.total_processing_time / self.successful_requests, 2)
        
        return {
            "date": self.date,
            "totalRequests": self.total_requests,
            "successfulRequests": self.successful_requests,
            "failedRequests": self.failed_requests,
            "successRate": success_rate,
            "avgProcessingTime": avg_processing_time,
            "audioFilesGenerated": self.audio_files_generated
        }