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
    
    # 🚀 新架构：移除旧的进度字段，改为基于AudioFile动态计算
    # total_segments, completed_segments, current_segment 已移除
    # 进度现在基于 AudioFile 实际统计

    # 任务状态
    status = Column(String(20), default='pending')  # pending, running, paused, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    
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
            # 🚀 新架构：移除旧字段，进度基于AudioFile动态计算
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
        """计算进度百分比 - 🚀 新架构：基于AudioFile动态计算"""
        # 新架构不使用存储字段，而是实时计算
        return self.progress  # 使用实时更新的progress字段
    
    def get_failed_count(self) -> int:
        """获取失败段落数量"""
        if not self.failed_segments:
            return 0
        return len(self.failed_segments)
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        # 🚀 新架构：不依赖total_segments字段
        if self.progress == 0:
            return 0.0
        
        # 🚀 新架构：基于progress字段计算成功率
        failed_count = self.get_failed_count()
        if failed_count == 0:
            return self.progress  # 使用实时progress
        else:
            return max(0.0, self.progress - (failed_count * 5))  # 考虑失败影响
    
    def get_duration(self) -> Optional[int]:
        """获取任务运行时长（秒）"""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.utcnow()
        return int((end_time - self.started_at).total_seconds())
    
    def get_estimated_remaining_time(self) -> Optional[int]:
        """估算剩余时间（秒）"""
        if not self.started_at or self.progress == 0:
            return None
        
        # 🚀 新架构：基于progress百分比估算剩余时间
        elapsed = self.get_duration() or 0
        
        if self.progress >= 100:
            return 0
        
        # 基于进度百分比估算总时间
        estimated_total_time = elapsed / (self.progress / 100)
        remaining_time = estimated_total_time - elapsed
        
        return int(max(0, remaining_time))
    
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
    
    def update_progress(self, progress: int = None):
        """更新进度信息 - 🚀 新架构：直接更新progress"""
        if progress is not None:
            self.progress = min(100, max(0, progress))
        
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
        # 🚀 新架构：不再使用current_segment字段
        self.error_message = None
        self.started_at = None
        self.completed_at = None
        self.updated_at = datetime.utcnow()
        
        return True 