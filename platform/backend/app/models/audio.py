"""
音频文件模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship

from .base import BaseModel


class AudioFile(BaseModel):
    """音频文件模型"""
    __tablename__ = "audio_files"
    
    filename = Column(String(255), nullable=False, comment="文件名")
    original_name = Column(String(255), comment="原始文件名")
    file_path = Column(Text, nullable=False, comment="文件路径")
    file_size = Column(Integer, comment="文件大小(字节)")
    duration = Column(Float, comment="音频时长(秒)")
    type = Column(String(50), comment="音频类型")
    
    # 项目关联
    project_id = Column(Integer, ForeignKey("novel_projects.id"), comment="项目ID")
    chapter_id = Column(Integer, ForeignKey("book_chapters.id"), comment="章节ID")
    chapter_number = Column(Integer, comment="章节号")
    segment_id = Column(Integer, comment="段落ID")
    
    # 角色信息
    character_name = Column(String(100), comment="角色名")
    speaker = Column(String(100), comment="说话人")
    paragraph_index = Column(Integer, comment="段落索引")
    voice_profile_id = Column(Integer, ForeignKey("voice_profiles.id"), comment="声音档案ID")
    
    # 内容信息
    text_content = Column(Text, comment="文本内容")
    audio_type = Column(String(50), default="segment", comment="音频类型: segment, final, environment")
    
    # 音频技术信息
    sample_rate = Column(Integer, comment="采样率")
    channels = Column(Integer, comment="声道数")
    file_metadata = Column(Text, comment="文件元数据")
    
    # 用户交互
    is_favorite = Column(Boolean, default=False, comment="是否收藏")
    tags = Column(Text, comment="标签")
    
    # 处理信息
    processing_time = Column(Float, comment="处理时间(秒)")
    model_used = Column(String(100), comment="使用的模型")
    parameters = Column(Text, comment="处理参数")
    status = Column(String(50), default="active", comment="状态: active, archived, deleted")
    
    # 关系
    project = relationship("NovelProject", back_populates="audio_files")
    chapter = relationship("BookChapter")
    voice_profile = relationship("VoiceProfile")
    
    def to_dict(self):
        """转换为字典"""
        result = super().to_dict()
        return result