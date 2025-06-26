"""
分析会话模型
管理LLM智能分析的会话和配置
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, Optional

from .base import Base


class AnalysisSession(Base):
    """分析会话模型"""
    
    __tablename__ = 'analysis_sessions'
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('novel_projects.id', ondelete='CASCADE'), nullable=True)
    session_name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # 分析配置
    target_type = Column(String(20), nullable=False)  # 'full_book', 'single_chapter', 'chapter_range'
    target_config = Column(JSON)  # 目标配置：章节ID列表等
    llm_config = Column(JSON)  # LLM配置：模型、参数等
    analysis_params = Column(JSON)  # 分析参数：选项、规则等
    
    # 处理状态
    status = Column(String(20), default='pending')  # pending, running, completed, failed, cancelled
    progress = Column(Integer, default=0)  # 0-100
    current_step = Column(String(100))  # 当前处理步骤描述
    
    # 结果统计
    total_chapters = Column(Integer, default=0)
    completed_chapters = Column(Integer, default=0)
    failed_chapters = Column(Integer, default=0)
    
    # 错误信息
    error_message = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    project = relationship("NovelProject", back_populates="analysis_sessions")
    analysis_results = relationship("AnalysisResult", back_populates="session", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_analysis_sessions_project_id', 'project_id'),
        Index('idx_analysis_sessions_status', 'status'),
        Index('idx_analysis_sessions_target_type', 'target_type'),
        Index('idx_analysis_sessions_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AnalysisSession(id={self.id}, project_id={self.project_id}, name='{self.session_name}', status='{self.status}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'session_name': self.session_name,
            'description': self.description,
            'target_type': self.target_type,
            'target_config': self.target_config,
            'llm_config': self.llm_config,
            'analysis_params': self.analysis_params,
            'status': self.status,
            'progress': self.progress,
            'current_step': self.current_step,
            'total_chapters': self.total_chapters,
            'completed_chapters': self.completed_chapters,
            'failed_chapters': self.failed_chapters,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_progress_percentage(self) -> int:
        """获取进度百分比"""
        if self.total_chapters == 0:
            return 0
        return min(100, int((self.completed_chapters / self.total_chapters) * 100))
    
    def get_duration(self) -> Optional[int]:
        """获取运行时长（秒）"""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.utcnow()
        return int((end_time - self.started_at).total_seconds())
    
    def is_active(self) -> bool:
        """检查会话是否处于活跃状态"""
        return self.status in ['pending', 'running']
    
    def is_completed(self) -> bool:
        """检查会话是否已完成"""
        return self.status == 'completed'
    
    def is_failed(self) -> bool:
        """检查会话是否失败"""
        return self.status == 'failed'
    
    def update_progress(self, completed: int = None, current_step: str = None):
        """更新进度信息"""
        if completed is not None:
            self.completed_chapters = completed
            self.progress = self.get_progress_percentage()
        
        if current_step is not None:
            self.current_step = current_step
        
        self.updated_at = datetime.utcnow()
    
    def mark_started(self):
        """标记会话开始"""
        self.status = 'running'
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self):
        """标记会话完成"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self.progress = 100
        self.current_step = '分析完成'
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error_message: str):
        """标记会话失败"""
        self.status = 'failed'
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
    
    def mark_cancelled(self):
        """标记会话取消"""
        self.status = 'cancelled'
        self.updated_at = datetime.utcnow() 