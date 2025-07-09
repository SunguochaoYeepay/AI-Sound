from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
import json
import os
from app.models.base import BaseModel

class Character(BaseModel):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="角色名称")
    description = Column(Text, nullable=True, comment="角色描述")
    
    # 书籍关联
    book_id = Column(Integer, ForeignKey("books.id", ondelete="SET NULL"), nullable=True, comment="所属书籍ID")
    chapter_id = Column(Integer, ForeignKey("book_chapters.id", ondelete="SET NULL"), nullable=True, comment="首次出现章节ID")
    
    # 声音配置字段（合并VoiceProfile功能）
    voice_type = Column(String(50), default="custom", comment="声音类型: male, female, child, elder, custom")
    color = Column(String(20), default="#8b5cf6", comment="显示颜色")
    
    # 音频文件路径
    reference_audio_path = Column(String(500), comment="参考音频路径")
    latent_file_path = Column(String(500), comment="latent文件路径")
    
    # 参数配置
    voice_parameters = Column(JSON, comment="TTS参数配置")
    tags = Column(JSON, comment="标签")
    
    # 状态信息
    status = Column(String(50), default="unconfigured", comment="状态: configured, unconfigured, training")
    quality_score = Column(Float, comment="质量评分")
    usage_count = Column(Integer, default=0, comment="使用次数")
    
    # 关联关系
    book = relationship("Book", back_populates="characters")
    chapter = relationship("BookChapter", back_populates="characters")
    
    def get_voice_parameters(self):
        """获取声音参数配置"""
        try:
            return json.loads(self.voice_parameters) if self.voice_parameters else {
                "time_step": 20,
                "p_weight": 1.0,
                "t_weight": 1.0
            }
        except json.JSONDecodeError:
            return {
                "time_step": 20,
                "p_weight": 1.0,
                "t_weight": 1.0
            }
    
    def set_voice_parameters(self, params):
        """设置声音参数配置"""
        self.voice_parameters = json.dumps(params, ensure_ascii=False)
    
    def get_tags(self):
        """获取标签列表"""
        try:
            return json.loads(self.tags) if self.tags else []
        except json.JSONDecodeError:
            return []
    
    def set_tags(self, tags):
        """设置标签列表"""
        self.tags = json.dumps(tags, ensure_ascii=False)
    
    def validate_voice_files(self):
        """验证声音文件是否存在"""
        missing_files = []
        
        if self.reference_audio_path and not os.path.exists(self.reference_audio_path):
            missing_files.append(self.reference_audio_path)
        
        if self.latent_file_path and not os.path.exists(self.latent_file_path):
            missing_files.append(self.latent_file_path)
        
        return {
            'valid': len(missing_files) == 0,
            'missing_files': missing_files
        }
    
    @property
    def is_voice_configured(self):
        """检查是否已配置声音"""
        return bool(self.reference_audio_path and os.path.exists(self.reference_audio_path))
    
    def to_dict(self):
        """转换为字典"""
        result = super().to_dict()
        result['voice_parameters'] = self.get_voice_parameters()
        result['tags'] = self.get_tags()
        result['is_voice_configured'] = self.is_voice_configured
        
        # 生成音频文件URL
        if self.reference_audio_path:
            filename = os.path.basename(self.reference_audio_path)
            result['referenceAudioUrl'] = f"/voice_profiles/{filename}"
        else:
            result['referenceAudioUrl'] = None
            
        if self.latent_file_path:
            filename = os.path.basename(self.latent_file_path)
            result['latentFileUrl'] = f"/voice_profiles/{filename}"
        else:
            result['latentFileUrl'] = None
        
        return result 