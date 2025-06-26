"""
用户预设模型
管理用户配置模板和预设
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Index, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any

from .base import Base


class UserPreset(Base):
    """用户预设模型"""
    
    __tablename__ = 'user_presets'
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # 配置内容
    config_type = Column(String(50), nullable=False)  # voice_mapping, synthesis_params, analysis_params, analysis_complete
    config_data = Column(JSON, nullable=False)  # 配置数据
    
    # 作用域
    scope = Column(String(20), default='global')  # global, project, book
    scope_id = Column(Integer)  # 作用域ID（项目ID或书籍ID）
    
    # 使用统计
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 索引
    __table_args__ = (
        Index('idx_user_presets_config_type', 'config_type'),
        Index('idx_user_presets_scope', 'scope'),
        Index('idx_user_presets_scope_id', 'scope_id'),
        Index('idx_user_presets_usage_count', 'usage_count'),
        Index('idx_user_presets_name_scope', 'name', 'scope', 'scope_id'),
    )
    
    def __repr__(self):
        return f"<UserPreset(id={self.id}, name='{self.name}', type='{self.config_type}', scope='{self.scope}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'config_type': self.config_type,
            'config_data': self.config_data,
            'scope': self.scope,
            'scope_id': self.scope_id,
            'usage_count': self.usage_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_scope_display(self) -> str:
        """获取作用域显示名称"""
        if self.scope == 'global':
            return '全局'
        elif self.scope == 'project':
            return f'项目 #{self.scope_id}'
        elif self.scope == 'book':
            return f'书籍 #{self.scope_id}'
        else:
            return '未知'
    
    def is_global(self) -> bool:
        """检查是否为全局预设"""
        return self.scope == 'global'
    
    def is_project_scoped(self) -> bool:
        """检查是否为项目范围预设"""
        return self.scope == 'project'
    
    def is_book_scoped(self) -> bool:
        """检查是否为书籍范围预设"""
        return self.scope == 'book'
    
    def can_be_used_in_scope(self, scope: str, scope_id: int = None) -> bool:
        """检查预设是否可以在指定作用域使用"""
        # 全局预设可以在任何地方使用
        if self.is_global():
            return True
        
        # 项目或书籍预设只能在对应的作用域使用
        return self.scope == scope and self.scope_id == scope_id
    
    def increment_usage(self):
        """增加使用次数"""
        self.usage_count += 1
        self.last_used = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要信息"""
        summary = {
            'type': self.config_type,
            'has_data': bool(self.config_data),
            'data_keys': list(self.config_data.keys()) if self.config_data else []
        }
        
        # 根据配置类型提供更详细的摘要
        if self.config_type == 'voice_mapping' and self.config_data:
            mappings = self.config_data.get('mappings', {})
            summary['character_count'] = len(mappings)
            summary['characters'] = list(mappings.keys())
        
        elif self.config_type == 'synthesis_params' and self.config_data:
            params = self.config_data.get('parameters', {})
            summary['parameter_count'] = len(params)
            summary['parameters'] = list(params.keys())
        
        elif self.config_type == 'analysis_params' and self.config_data:
            llm_config = self.config_data.get('llm_config', {})
            summary['llm_provider'] = llm_config.get('provider')
            summary['llm_model'] = llm_config.get('model')
        
        elif self.config_type == 'analysis_complete' and self.config_data:
            summary['has_llm_config'] = 'llm_config' in self.config_data
            summary['has_synthesis_params'] = 'synthesis_params' in self.config_data
            summary['has_voice_mapping'] = 'voice_mapping' in self.config_data
        
        return summary
    
    def validate_config_data(self) -> Dict[str, Any]:
        """验证配置数据的有效性"""
        errors = []
        warnings = []
        
        if not self.config_data:
            errors.append("配置数据不能为空")
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        # 根据配置类型进行特定验证
        if self.config_type == 'voice_mapping':
            if 'mappings' not in self.config_data:
                errors.append("声音映射配置缺少 'mappings' 字段")
            else:
                mappings = self.config_data['mappings']
                if not isinstance(mappings, dict):
                    errors.append("mappings 必须是字典类型")
                elif len(mappings) == 0:
                    warnings.append("声音映射为空")
        
        elif self.config_type == 'synthesis_params':
            if 'parameters' not in self.config_data:
                errors.append("合成参数配置缺少 'parameters' 字段")
            else:
                params = self.config_data['parameters']
                required_params = ['timeStep', 'pWeight', 'tWeight']
                for param in required_params:
                    if param not in params:
                        errors.append(f"缺少必需参数: {param}")
        
        elif self.config_type == 'analysis_params':
            if 'llm_config' not in self.config_data:
                errors.append("分析参数配置缺少 'llm_config' 字段")
            else:
                llm_config = self.config_data['llm_config']
                if 'provider' not in llm_config:
                    errors.append("LLM配置缺少 provider 字段")
        
        elif self.config_type == 'analysis_complete':
            required_sections = ['llm_config', 'analysis_params', 'synthesis_params']
            for section in required_sections:
                if section not in self.config_data:
                    warnings.append(f"完整分析配置建议包含 '{section}' 字段")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        } 