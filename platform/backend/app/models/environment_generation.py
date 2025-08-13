"""
环境音生成相关的数据库模型
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class EnvironmentProject(Base):
    """环境音效项目模型"""
    __tablename__ = 'environment_projects'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="项目名称")
    description = Column(Text, comment="项目描述")
    status = Column(String(50), default='analyzed', comment="项目状态: analyzed, generating, completed, failed")
    
    # 分析结果
    analysis_result = Column(JSON, comment="分析结果")
    matching_result = Column(JSON, comment="匹配结果")
    chapter_ids = Column(JSON, comment="章节ID列表")
    analysis_options = Column(JSON, comment="分析选项")
    
    # 统计信息
    analysis_tracks = Column(Integer, default=0, comment="分析轨道数量")
    generation_count = Column(Integer, default=0, comment="生成数量")
    matched_count = Column(Integer, default=0, comment="匹配数量")
    
    # 书籍信息
    book_name = Column(String(255), comment="书籍名称")
    chapter_name = Column(String(255), comment="章节名称")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "analysis_result": self.analysis_result,
            "matching_result": self.matching_result,
            "chapter_ids": self.chapter_ids,
            "analysis_options": self.analysis_options,
            "analysis_tracks": self.analysis_tracks,
            "generation_count": self.generation_count,
            "matched_count": self.matched_count,
            "book_name": self.book_name,
            "chapter_name": self.chapter_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_simple_dict(self):
        """转换为简化的字典格式（不包含分析结果和匹配结果）"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "chapter_ids": self.chapter_ids,
            "analysis_options": self.analysis_options,
            "analysis_tracks": self.analysis_tracks,
            "generation_count": self.generation_count,
            "matched_count": self.matched_count,
            "book_name": self.book_name,
            "chapter_name": self.chapter_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class EnvironmentGenerationSession(Base):
    """环境音生成会话"""
    __tablename__ = 'environment_generation_sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=True, index=True)  # 移除外键约束，改为普通字段
    chapter_id = Column(String(50), nullable=False, index=True)
    session_status = Column(String(20), default='active', index=True)  # active, completed, cancelled
    
    # 分析阶段数据
    analysis_result = Column(JSON, nullable=True)
    analysis_stats = Column(JSON, nullable=True)
    analysis_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # 校对阶段数据
    validation_data = Column(JSON, nullable=True)
    validation_summary = Column(JSON, nullable=True)
    validation_timestamp = Column(DateTime, nullable=True)
    
    # 持久化数据
    persistence_data = Column(JSON, nullable=True)
    persistence_summary = Column(JSON, nullable=True)
    persistence_timestamp = Column(DateTime, nullable=True)
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    tracks = relationship("EnvironmentTrackConfig", back_populates="session", cascade="all, delete-orphan")


class EnvironmentTrackConfig(Base):
    """环境音轨道配置"""
    __tablename__ = 'environment_track_configs'
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('environment_generation_sessions.id'), nullable=False, index=True)
    
    # 轨道基本信息
    segment_id = Column(String(50), nullable=False, index=True)
    track_index = Column(Integer, nullable=False)
    start_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    
    # 分析结果
    scene_description = Column(Text, nullable=True)
    environment_keywords = Column(JSON, nullable=True)  # List[str]
    confidence = Column(Float, nullable=True)
    
    # 场景继承
    inheritance_applied = Column(Boolean, default=False)
    inherited_environment = Column(JSON, nullable=True)
    previous_track_id = Column(Integer, ForeignKey('environment_track_configs.id'), nullable=True)
    
    # 人工编辑
    manual_edits = Column(JSON, nullable=True)
    validation_status = Column(String(20), default='pending')  # pending, edited, approved, rejected
    validation_notes = Column(Text, nullable=True)
    validation_timestamp = Column(DateTime, nullable=True)
    
    # TangoFlux配置
    matching_suggestions = Column(JSON, nullable=True)  # List[TangoFluxSuggestion]
    selected_tangoflux_config = Column(JSON, nullable=True)
    final_prompt = Column(Text, nullable=True)
    
    # 渐变设置
    fade_in = Column(Float, default=3.0)
    fade_out = Column(Float, default=2.0)
    volume = Column(Float, default=0.6)
    loop_enabled = Column(Boolean, default=True)
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    session = relationship("EnvironmentGenerationSession", back_populates="tracks")
    previous_track = relationship("EnvironmentTrackConfig", remote_side=[id])


class EnvironmentAudioMixingJob(Base):
    """环境音混合任务"""
    __tablename__ = 'environment_audio_mixing_jobs'
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('environment_generation_sessions.id'), nullable=False, index=True)
    project_id = Column(Integer, nullable=True, index=True)  # 移除外键约束，改为普通字段
    chapter_id = Column(String(50), nullable=False, index=True)
    
    # 任务状态
    job_status = Column(String(20), default='pending', index=True)  # pending, running, completed, failed
    progress = Column(Float, default=0.0)
    
    # 混合配置
    mixing_config = Column(JSON, nullable=True)
    total_tracks = Column(Integer, default=0)
    completed_tracks = Column(Integer, default=0)
    failed_tracks = Column(Integer, default=0)
    
    # 输出信息
    output_file_path = Column(String(500), nullable=True)
    output_duration = Column(Float, nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # 错误信息
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # 时间戳
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EnvironmentGenerationLog(Base):
    """环境音生成日志"""
    __tablename__ = 'environment_generation_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('environment_generation_sessions.id'), nullable=False, index=True)
    
    # 日志信息
    log_level = Column(String(10), nullable=False, index=True)  # DEBUG, INFO, WARNING, ERROR
    log_message = Column(Text, nullable=False)
    log_details = Column(JSON, nullable=True)
    
    # 操作信息
    operation = Column(String(50), nullable=True, index=True)  # analyze, validate, edit, approve, finalize
    user_id = Column(String(50), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow) 