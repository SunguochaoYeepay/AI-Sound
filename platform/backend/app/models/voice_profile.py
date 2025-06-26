"""
声音档案模型
基于Docker数据库中的正确表结构
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any
import json

from .base import Base
from ..utils.path_manager import normalize_path


class VoiceProfile(Base):
    """声音档案模型 - 匹配docker数据库表结构"""
    
    __tablename__ = 'voice_profiles'
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    type = Column(String(20), nullable=False)  # 'male', 'female', 'child'
    
    # 文件路径
    reference_audio_path = Column(String(500))
    latent_file_path = Column(String(500))
    sample_audio_path = Column(String(500))
    
    # 参数和配置
    parameters = Column(Text, default='{"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}')
    
    # 评分和使用统计
    quality_score = Column(Float, default=3.0)
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime)
    
    # 显示和组织
    color = Column(String(20), default='#06b6d4')
    tags = Column(Text, default='[]')
    status = Column(String(20), default='active')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<VoiceProfile(id={self.id}, name='{self.name}', type='{self.type}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        # 解析parameters JSON
        try:
            parameters = json.loads(self.parameters) if self.parameters else {}
        except (json.JSONDecodeError, TypeError):
            parameters = {"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}
        
        # 解析tags JSON
        try:
            tags = json.loads(self.tags) if self.tags else []
        except (json.JSONDecodeError, TypeError):
            tags = []
        
        # 标准化路径格式（使用正斜杠）
        def normalize_path(path):
            return path.replace('\\', '/') if path else None
        
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'reference_audio_path': normalize_path(self.reference_audio_path),
            'latent_file_path': normalize_path(self.latent_file_path),
            'sample_audio_path': normalize_path(self.sample_audio_path),
            'parameters': parameters,
            'quality_score': self.quality_score,
            'usage_count': self.usage_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'color': self.color,
            'tags': tags,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def set_tags(self, tags_list):
        """设置标签列表"""
        self.tags = json.dumps(tags_list) if tags_list else '[]'
        
    def get_tags(self):
        """获取标签列表"""
        try:
            return json.loads(self.tags) if self.tags else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_parameters(self, params_dict):
        """设置参数字典"""
        self.parameters = json.dumps(params_dict) if params_dict else '{"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}'
        
    def get_parameters(self):
        """获取参数字典"""
        try:
            return json.loads(self.parameters) if self.parameters else {}
        except (json.JSONDecodeError, TypeError):
            return {"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}
    
    def get_actual_reference_audio_path(self):
        """获取实际的参考音频路径（自动适配环境）"""
        return normalize_path(self.reference_audio_path)
    
    def get_actual_latent_file_path(self):
        """获取实际的Latent文件路径（自动适配环境）"""
        return normalize_path(self.latent_file_path)
    
    def get_actual_sample_audio_path(self):
        """获取实际的示例音频路径（自动适配环境）"""
        return normalize_path(self.sample_audio_path)
    
    def validate_files(self):
        """验证所有文件是否存在"""
        result = {
            'valid': True,
            'missing_files': []
        }
        
        # 检查参考音频
        if self.reference_audio_path:
            actual_path = self.get_actual_reference_audio_path()
            if not actual_path:
                result['valid'] = False
                result['missing_files'].append('reference_audio')
        
        # 检查Latent文件
        if self.latent_file_path:
            actual_path = self.get_actual_latent_file_path()
            if not actual_path:
                result['valid'] = False
                result['missing_files'].append('latent_file')
        
        # 检查示例音频
        if self.sample_audio_path:
            actual_path = self.get_actual_sample_audio_path()
            if not actual_path:
                result['valid'] = False
                result['missing_files'].append('sample_audio')
        
        return result