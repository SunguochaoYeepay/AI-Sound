"""
合成任务模型
管理TTS音频合成的批量任务
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, Optional

from .base import Base


class SynthesisTask(Base):
    """合成任务模型"""
    
    __tablename__ = 'synthesis_tasks'
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('novel_projects.id', ondelete='CASCADE'), nullable=False)
    analysis_result_id = Column(Integer, ForeignKey('analysis_results.id', ondelete='SET NULL'))
    chapter_id = Column(Integer, ForeignKey('book_chapters.id', ondelete='SET NULL'))
    
    # 任务配置
    synthesis_plan = Column(JSON)  # 合成计划配置
    batch_size = Column(Integer, default=10)  # 批处理大小
    
    # 任务状态
    status = Column(String(20), default='pending')  # pending, running, paused, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    
    # 进度统计
    total_segments = Column(Integer, default=0)
    completed_segments = Column(Integer, default=0)
    current_segment = Column(Integer)  # 当前处理的段落ID
    
    # 错误处理
    failed_segments = Column(JSON)  # 失败的段落列表
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # 输出文件
    output_files = Column(JSON)  # 生成的音频文件列表
    final_audio_path = Column(String(500))  # 最终合并的音频文件路径
    
    # 时间统计
    processing_time = Column(Integer)  # 总处理时间（秒）
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    project = relationship("NovelProject", back_populates="synthesis_tasks")
    analysis_result = relationship("AnalysisResult", back_populates="synthesis_tasks")
    chapter = relationship("BookChapter", back_populates="synthesis_tasks")
    
    # 索引
    __table_args__ = (
        Index('idx_synthesis_tasks_project_id', 'project_id'),
        Index('idx_synthesis_tasks_status', 'status'),
        Index('idx_synthesis_tasks_analysis_result_id', 'analysis_result_id'),
        Index('idx_synthesis_tasks_chapter_id', 'chapter_id'),
        Index('idx_synthesis_tasks_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<SynthesisTask(id={self.id}, project_id={self.project_id}, status='{self.status}', progress={self.progress}%)>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'analysis_result_id': self.analysis_result_id,
            'chapter_id': self.chapter_id,
            'synthesis_plan': self.synthesis_plan,
            'batch_size': self.batch_size,
            'status': self.status,
            'progress': self.progress,
            'total_segments': self.total_segments,
            'completed_segments': self.completed_segments,
            'current_segment': self.current_segment,
            'failed_segments': self.failed_segments,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'output_files': self.output_files,
            'final_audio_path': self.final_audio_path,
            'processing_time': self.processing_time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_progress_percentage(self) -> int:
        """计算进度百分比"""
        if self.total_segments == 0:
            return 0
        return min(100, int((self.completed_segments / self.total_segments) * 100))
    
    def get_failed_count(self) -> int:
        """获取失败段落数量"""
        if not self.failed_segments:
            return 0
        return len(self.failed_segments)
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_segments == 0:
            return 0.0
        
        processed = self.completed_segments + self.get_failed_count()
        if processed == 0:
            return 0.0
        
        return (self.completed_segments / processed) * 100
    
    def get_duration(self) -> Optional[int]:
        """获取任务运行时长（秒）"""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.utcnow()
        return int((end_time - self.started_at).total_seconds())
    
    def get_estimated_remaining_time(self) -> Optional[int]:
        """估算剩余时间（秒）"""
        if not self.started_at or self.completed_segments == 0:
            return None
        
        # 基于已完成的平均处理时间估算
        elapsed = self.get_duration() or 0
        remaining_segments = self.total_segments - self.completed_segments
        
        if remaining_segments <= 0:
            return 0
        
        avg_time_per_segment = elapsed / self.completed_segments
        return int(avg_time_per_segment * remaining_segments)
    
    def is_active(self) -> bool:
        """检查任务是否处于活跃状态"""
        return self.status in ['pending', 'running']
    
    def is_completed(self) -> bool:
        """检查任务是否已完成"""
        return self.status == 'completed'
    
    def is_failed(self) -> bool:
        """检查任务是否失败"""
        return self.status == 'failed'
    
    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return self.retry_count < self.max_retries and self.status == 'failed'
    
    def update_progress(self, completed: int = None, current_segment: int = None):
        """更新进度信息"""
        if completed is not None:
            self.completed_segments = completed
            self.progress = self.get_progress_percentage()
        
        if current_segment is not None:
            self.current_segment = current_segment
        
        self.updated_at = datetime.utcnow()
    
    def add_failed_segment(self, segment_id: int, error: str):
        """添加失败的段落"""
        if not self.failed_segments:
            self.failed_segments = []
        
        self.failed_segments.append({
            'segment_id': segment_id,
            'error': error,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        self.updated_at = datetime.utcnow()
    
    def mark_started(self):
        """标记任务开始"""
        self.status = 'running'
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self):
        """标记任务完成"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self.progress = 100
        
        if self.started_at:
            self.processing_time = self.get_duration()
        
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error_message: str):
        """标记任务失败"""
        self.status = 'failed'
        self.error_message = error_message
        self.retry_count += 1
        self.updated_at = datetime.utcnow()
    
    def mark_paused(self):
        """标记任务暂停"""
        self.status = 'paused'
        self.updated_at = datetime.utcnow()
    
    def mark_cancelled(self):
        """标记任务取消"""
        self.status = 'failed'
        self.error_message = '用户取消'
        self.updated_at = datetime.utcnow()
    
    def reset_for_retry(self):
        """重置任务以便重试"""
        if not self.can_retry():
            return False
        
        self.status = 'pending'
        self.progress = 0
        self.completed_segments = 0
        self.current_segment = None
        self.error_message = None
        self.started_at = None
        self.completed_at = None
        self.updated_at = datetime.utcnow()
        
        return True 