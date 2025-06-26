"""
音乐生成相关的数据库模型
包括生成任务、场景分析、音乐文件管理等
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime

from .base import BaseModel


class MusicGenerationStatus(enum.Enum):
    """音乐生成任务状态"""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MusicSceneType(enum.Enum):
    """音乐场景类型"""
    BATTLE = "battle"
    ROMANCE = "romance"
    MYSTERY = "mystery"
    PEACEFUL = "peaceful"
    SAD = "sad"
    CUSTOM = "custom"


class FadeMode(enum.Enum):
    """淡入淡出模式"""
    STANDARD = "standard"
    SMOOTH = "smooth"
    QUICK = "quick"


class MusicGenerationTask(BaseModel):
    """音乐生成任务"""
    __tablename__ = "music_generation_tasks"
    
    # 任务基本信息
    task_id = Column(String(64), unique=True, nullable=False, index=True, comment="任务唯一标识")
    chapter_id = Column(String(64), nullable=True, index=True, comment="关联章节ID")
    novel_project_id = Column(Integer, ForeignKey("novel_projects.id"), nullable=True, comment="关联小说项目ID")
    
    # 生成参数
    content = Column(Text, nullable=False, comment="生成音乐的文本内容")
    target_duration = Column(Integer, default=30, comment="目标时长（秒）")
    custom_style = Column(String(100), nullable=True, comment="自定义音乐风格")
    volume_level = Column(Float, default=-12.0, comment="音量等级（dB）")
    fade_mode = Column(Enum(FadeMode), default=FadeMode.STANDARD, comment="淡入淡出模式")
    fade_in = Column(Float, default=2.0, comment="淡入时间（秒）")
    fade_out = Column(Float, default=2.0, comment="淡出时间（秒）")
    
    # 任务状态
    status = Column(Enum(MusicGenerationStatus), default=MusicGenerationStatus.PENDING, comment="任务状态")
    progress = Column(Float, default=0.0, comment="任务进度（0.0-1.0）")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 生成结果
    audio_path = Column(String(500), nullable=True, comment="生成的音频文件路径")
    audio_url = Column(String(500), nullable=True, comment="音频访问URL")
    actual_duration = Column(Float, nullable=True, comment="实际音频时长（秒）")
    file_size = Column(Integer, nullable=True, comment="文件大小（字节）")
    
    # 性能指标
    generation_time = Column(Float, nullable=True, comment="生成耗时（秒）")
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    
    # 用户信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="用户ID")
    user_preferences = Column(JSON, nullable=True, comment="用户偏好设置")
    
    # 关联关系
    scene_analysis = relationship("MusicSceneAnalysis", back_populates="generation_task", uselist=False)
    music_files = relationship("GeneratedMusicFile", back_populates="generation_task")
    novel_project = relationship("NovelProject", back_populates="music_generation_tasks")
    user = relationship("User", back_populates="music_generation_tasks")
    
    def __repr__(self):
        return f"<MusicGenerationTask(task_id={self.task_id}, status={self.status.value})>"


class MusicSceneAnalysis(BaseModel):
    """音乐场景分析结果"""
    __tablename__ = "music_scene_analyses"
    
    # 关联任务
    generation_task_id = Column(Integer, ForeignKey("music_generation_tasks.id"), nullable=False, comment="关联生成任务ID")
    
    # 场景分析结果
    primary_scene_type = Column(Enum(MusicSceneType), nullable=False, comment="主要场景类型")
    emotion_tone = Column(String(100), nullable=False, comment="情绪基调")
    intensity = Column(Float, nullable=False, comment="强度（0.0-1.0）")
    confidence = Column(Float, nullable=False, comment="置信度（0.0-1.0）")
    
    # 分析详情
    keywords = Column(JSON, nullable=True, comment="关键词列表")
    secondary_scenes = Column(JSON, nullable=True, comment="次要场景信息")
    transition_points = Column(JSON, nullable=True, comment="场景转换点")
    
    # 音乐建议
    overall_mood = Column(String(100), nullable=True, comment="整体氛围")
    tempo_preference = Column(Integer, nullable=True, comment="节奏偏好（BPM）")
    volume_suggestion = Column(Float, nullable=True, comment="音量建议（dB）")
    duration_hint = Column(Integer, nullable=True, comment="时长建议（秒）")
    
    # 风格推荐
    style_recommendations = Column(JSON, nullable=True, comment="风格推荐列表")
    
    # 分析元数据
    content_length = Column(Integer, nullable=True, comment="分析文本长度")
    analysis_version = Column(String(20), default="1.0", comment="分析算法版本")
    analysis_time = Column(Float, nullable=True, comment="分析耗时（秒）")
    
    # 关联关系
    generation_task = relationship("MusicGenerationTask", back_populates="scene_analysis")
    
    def __repr__(self):
        return f"<MusicSceneAnalysis(scene_type={self.primary_scene_type.value}, intensity={self.intensity})>"


class GeneratedMusicFile(BaseModel):
    """生成的音乐文件记录"""
    __tablename__ = "generated_music_files"
    
    # 关联任务
    generation_task_id = Column(Integer, ForeignKey("music_generation_tasks.id"), nullable=False, comment="关联生成任务ID")
    
    # 文件信息
    filename = Column(String(255), nullable=False, comment="文件名")
    file_path = Column(String(500), nullable=False, comment="文件路径")
    file_url = Column(String(500), nullable=True, comment="访问URL")
    file_size = Column(Integer, nullable=True, comment="文件大小（字节）")
    file_format = Column(String(10), default="wav", comment="文件格式")
    
    # 音频属性
    duration = Column(Float, nullable=True, comment="音频时长（秒）")
    sample_rate = Column(Integer, nullable=True, comment="采样率")
    bit_depth = Column(Integer, nullable=True, comment="位深度")
    channels = Column(Integer, default=2, comment="声道数")
    
    # 音乐属性
    volume_level = Column(Float, nullable=True, comment="音量等级（dB）")
    tempo = Column(Integer, nullable=True, comment="节奏（BPM）")
    key_signature = Column(String(10), nullable=True, comment="调性")
    
    # 质量评估
    quality_score = Column(Float, nullable=True, comment="质量评分（0.0-1.0）")
    noise_level = Column(Float, nullable=True, comment="噪音水平")
    dynamic_range = Column(Float, nullable=True, comment="动态范围")
    
    # 使用统计
    download_count = Column(Integer, default=0, comment="下载次数")
    play_count = Column(Integer, default=0, comment="播放次数")
    last_accessed = Column(DateTime, nullable=True, comment="最后访问时间")
    
    # 状态管理
    is_active = Column(Boolean, default=True, comment="是否可用")
    is_public = Column(Boolean, default=False, comment="是否公开")
    
    # 关联关系
    generation_task = relationship("MusicGenerationTask", back_populates="music_files")
    
    def __repr__(self):
        return f"<GeneratedMusicFile(filename={self.filename}, duration={self.duration})>"


class MusicGenerationBatch(BaseModel):
    """音乐生成批处理任务"""
    __tablename__ = "music_generation_batches"
    
    # 批处理信息
    batch_id = Column(String(64), unique=True, nullable=False, index=True, comment="批处理唯一标识")
    batch_name = Column(String(200), nullable=True, comment="批处理名称")
    description = Column(Text, nullable=True, comment="批处理描述")
    
    # 批处理参数
    total_chapters = Column(Integer, nullable=False, comment="总章节数")
    default_duration = Column(Integer, default=30, comment="默认时长（秒）")
    default_volume_level = Column(Float, default=-12.0, comment="默认音量等级（dB）")
    max_concurrent = Column(Integer, default=2, comment="最大并发数")
    
    # 批处理状态
    status = Column(String(20), default="pending", comment="批处理状态")
    success_count = Column(Integer, default=0, comment="成功数量")
    failed_count = Column(Integer, default=0, comment="失败数量")
    progress = Column(Float, default=0.0, comment="整体进度（0.0-1.0）")
    
    # 时间记录
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    estimated_completion = Column(DateTime, nullable=True, comment="预计完成时间")
    
    # 用户信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="用户ID")
    novel_project_id = Column(Integer, ForeignKey("novel_projects.id"), nullable=True, comment="关联小说项目ID")
    
    # 配置和结果
    batch_config = Column(JSON, nullable=True, comment="批处理配置")
    batch_results = Column(JSON, nullable=True, comment="批处理结果")
    error_summary = Column(JSON, nullable=True, comment="错误汇总")
    
    # 关联关系
    user = relationship("User", back_populates="music_generation_batches")
    novel_project = relationship("NovelProject", back_populates="music_generation_batches")
    
    def __repr__(self):
        return f"<MusicGenerationBatch(batch_id={self.batch_id}, status={self.status})>"


class MusicStyleTemplate(BaseModel):
    """音乐风格模板"""
    __tablename__ = "music_style_templates"
    
    # 模板基本信息
    name = Column(String(100), nullable=False, unique=True, comment="风格名称")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    description = Column(Text, nullable=True, comment="风格描述")
    category = Column(String(50), nullable=True, comment="风格分类")
    
    # 风格参数
    default_tempo = Column(Integer, nullable=True, comment="默认节奏（BPM）")
    tempo_range_min = Column(Integer, nullable=True, comment="节奏范围最小值")
    tempo_range_max = Column(Integer, nullable=True, comment="节奏范围最大值")
    
    default_volume = Column(Float, nullable=True, comment="默认音量（dB）")
    volume_range_min = Column(Float, nullable=True, comment="音量范围最小值")
    volume_range_max = Column(Float, nullable=True, comment="音量范围最大值")
    
    default_intensity = Column(Float, nullable=True, comment="默认强度")
    intensity_range_min = Column(Float, nullable=True, comment="强度范围最小值")
    intensity_range_max = Column(Float, nullable=True, comment="强度范围最大值")
    
    # 风格特征
    keywords = Column(JSON, nullable=True, comment="关键词列表")
    emotion_tags = Column(JSON, nullable=True, comment="情绪标签")
    scene_types = Column(JSON, nullable=True, comment="适用场景类型")
    
    # 生成参数
    generation_params = Column(JSON, nullable=True, comment="生成参数配置")
    post_processing_params = Column(JSON, nullable=True, comment="后处理参数")
    
    # 使用统计
    usage_count = Column(Integer, default=0, comment="使用次数")
    success_rate = Column(Float, nullable=True, comment="成功率")
    average_rating = Column(Float, nullable=True, comment="平均评分")
    
    # 状态管理
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_system = Column(Boolean, default=False, comment="是否系统内置")
    is_public = Column(Boolean, default=True, comment="是否公开")
    
    # 创建者信息
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建者ID")
    
    # 关联关系
    creator = relationship("User", back_populates="music_style_templates")
    
    def __repr__(self):
        return f"<MusicStyleTemplate(name={self.name}, category={self.category})>"


class MusicGenerationUsageLog(BaseModel):
    """音乐生成使用日志"""
    __tablename__ = "music_generation_usage_logs"
    
    # 关联信息
    task_id = Column(String(64), nullable=False, index=True, comment="任务ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="用户ID")
    
    # 使用详情
    action = Column(String(50), nullable=False, comment="操作类型")
    content_length = Column(Integer, nullable=True, comment="内容长度")
    generation_duration = Column(Float, nullable=True, comment="生成时长（秒）")
    
    # 参数记录
    style_used = Column(String(100), nullable=True, comment="使用的风格")
    target_duration = Column(Integer, nullable=True, comment="目标时长")
    volume_level = Column(Float, nullable=True, comment="音量等级")
    
    # 结果记录
    success = Column(Boolean, nullable=False, comment="是否成功")
    error_code = Column(String(50), nullable=True, comment="错误代码")
    quality_score = Column(Float, nullable=True, comment="质量评分")
    
    # 系统信息
    api_version = Column(String(20), nullable=True, comment="API版本")
    client_info = Column(JSON, nullable=True, comment="客户端信息")
    
    # 关联关系
    user = relationship("User", back_populates="music_generation_usage_logs")
    
    def __repr__(self):
        return f"<MusicGenerationUsageLog(task_id={self.task_id}, action={self.action})>"


class MusicGenerationSettings(BaseModel):
    """音乐生成系统设置"""
    __tablename__ = "music_generation_settings"
    
    # 设置基本信息
    setting_key = Column(String(100), nullable=False, unique=True, comment="设置键名")
    setting_value = Column(Text, nullable=True, comment="设置值")
    setting_type = Column(String(20), default="string", comment="设置类型")
    
    # 设置描述
    display_name = Column(String(200), nullable=True, comment="显示名称")
    description = Column(Text, nullable=True, comment="设置描述")
    category = Column(String(50), nullable=True, comment="设置分类")
    
    # 验证规则
    validation_rules = Column(JSON, nullable=True, comment="验证规则")
    default_value = Column(Text, nullable=True, comment="默认值")
    
    # 状态管理
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_system = Column(Boolean, default=False, comment="是否系统设置")
    requires_restart = Column(Boolean, default=False, comment="是否需要重启")
    
    # 修改记录
    last_modified_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="最后修改者")
    
    # 关联关系
    modifier = relationship("User", back_populates="music_generation_settings")
    
    def __repr__(self):
        return f"<MusicGenerationSettings(key={self.setting_key}, value={self.setting_value})>" 