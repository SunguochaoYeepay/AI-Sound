"""
声音档案模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float
from datetime import datetime
import json
import os

from .base import BaseModel


class VoiceProfile(BaseModel):
    """声音档案模型"""
    __tablename__ = "voice_profiles"
    
    name = Column(String(255), nullable=False, comment="声音名称")
    description = Column(Text, default="", comment="描述")
    type = Column(String(50), default="custom", comment="类型: male, female, child, elder, custom")
    color = Column(String(20), default="#1890ff", comment="显示颜色")
    
    # 音频文件路径
    reference_audio_path = Column(String(500), comment="参考音频路径")
    latent_file_path = Column(String(500), comment="latent文件路径")
    
    # 参数配置
    parameters = Column(JSON, comment="TTS参数配置")
    tags = Column(JSON, comment="标签")
    
    # 状态信息
    status = Column(String(50), default="active", comment="状态: active, inactive, training")
    quality_score = Column(Float, comment="质量评分")
    usage_count = Column(Integer, default=0, comment="使用次数")
    
    def get_parameters(self):
        """获取参数配置"""
        try:
            return json.loads(self.parameters) if self.parameters else {}
        except json.JSONDecodeError:
            return {}
    
    def set_parameters(self, params):
        """设置参数配置"""
        self.parameters = json.dumps(params, ensure_ascii=False)
    
    def get_tags(self):
        """获取标签列表"""
        try:
            return json.loads(self.tags) if self.tags else []
        except json.JSONDecodeError:
            return []
    
    def set_tags(self, tags):
        """设置标签列表"""
        self.tags = json.dumps(tags, ensure_ascii=False)
    
    def validate_files(self):
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
    
    def to_dict(self):
        """转换为字典"""
        result = super().to_dict()
        result['parameters'] = self.get_parameters()
        result['tags'] = self.get_tags()
        return result