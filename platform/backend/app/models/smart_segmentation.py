"""
智能分段数据模型 - 独立服务
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.models.base import Base


class SmartSegmentation(Base):
    """智能分段结果表 - 按分析项目独立存储"""
    __tablename__ = "smart_segmentations"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=False, index=True, comment="分析项目ID")
    chapter_id = Column(Integer, nullable=False, index=True, comment="章节ID")
    
    # 分段基本信息
    original_content = Column(Text, nullable=False, comment="原始章节内容")
    segments = Column(JSON, nullable=False, comment="分段结果列表")
    segment_count = Column(Integer, nullable=False, comment="分段数量")
    
    # 分段统计信息
    total_length = Column(Integer, nullable=False, comment="原文总长度")
    segments_length = Column(JSON, nullable=True, comment="各分段长度列表")
    
    # 模型信息
    model_used = Column(String(100), nullable=False, comment="使用的LLM模型")
    validation_passed = Column(Boolean, default=True, comment="验证是否通过")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "chapter_id": self.chapter_id,
            "original_content": self.original_content,
            "segments": self.segments,
            "segment_count": self.segment_count,
            "total_length": self.total_length,
            "segments_length": self.segments_length,
            "model_used": self.model_used,
            "validation_passed": self.validation_passed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
