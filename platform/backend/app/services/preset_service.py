"""
预设配置管理服务
处理用户配置模板的创建、管理、应用等功能
"""

import json
import copy
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ..models import UserPreset, Book, NovelProject
from ..exceptions import ServiceException


class PresetTemplates:
    """内置预设模板"""
    
    @staticmethod
    def get_default_voice_mapping() -> Dict[str, Any]:
        """默认声音映射模板"""
        return {
            "type": "voice_mapping",
            "version": "1.0",
            "mappings": {
                "主角": {"voice_id": None, "voice_name": "请选择声音"},
                "旁白": {"voice_id": None, "voice_name": "请选择声音"}
            }
        }
    
    @staticmethod
    def get_default_synthesis_params() -> Dict[str, Any]:
        """默认合成参数模板"""
        return {
            "type": "synthesis_params",
            "version": "1.0",
            "parameters": {
                "timeStep": 20,
                "pWeight": 1.0,
                "tWeight": 1.0,
                "speed": 1.0,
                "pitch": 0,
                "volume": 1.0
            },
            "quality_settings": {
                "sample_rate": 22050,
                "bit_depth": 16,
                "format": "wav"
            }
        }
    
    @staticmethod
    def get_default_analysis_params() -> Dict[str, Any]:
        """默认分析参数模板"""
        return {
            "type": "analysis_params",
            "version": "1.0",
            "llm_config": {
                "provider": "dify",
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 4000
            },
            "analysis_options": {
                "enable_character_detection": True,
                "enable_emotion_analysis": True,
                "enable_voice_recommendation": True,
                "enable_dialogue_detection": True,
                "batch_size": 5
            },
            "character_detection": {
                "min_character_mentions": 3,
                "dialogue_markers": ["\"", """, """, "『", "』"],
                "narrator_keywords": ["旁白", "叙述", "描述"]
            }
        }
    
    @staticmethod
    def get_complete_analysis_preset() -> Dict[str, Any]:
        """完整分析预设模板"""
        return {
            "type": "analysis_complete",
            "version": "1.0",
            "name": "标准分析配置",
            "description": "包含所有分析和合成参数的完整配置",
            "llm_config": PresetTemplates.get_default_analysis_params()["llm_config"],
            "analysis_params": PresetTemplates.get_default_analysis_params()["analysis_options"],
            "synthesis_params": PresetTemplates.get_default_synthesis_params()["parameters"],
            "voice_mapping": PresetTemplates.get_default_voice_mapping()["mappings"],
            "processing_options": {
                "max_retries": 3,
                "timeout_seconds": 60,
                "concurrent_limit": 3,
                "enable_caching": True
            }
        }


class PresetValidator:
    """预设配置验证器"""
    
    @staticmethod
    def validate_config_data(config_type: str, config_data: Dict[str, Any]) -> List[str]:
        """验证配置数据格式"""
        errors = []
        
        if config_type == "voice_mapping":
            errors.extend(PresetValidator._validate_voice_mapping(config_data))
        elif config_type == "synthesis_params":
            errors.extend(PresetValidator._validate_synthesis_params(config_data))
        elif config_type == "analysis_params":
            errors.extend(PresetValidator._validate_analysis_params(config_data))
        elif config_type == "analysis_complete":
            errors.extend(PresetValidator._validate_complete_preset(config_data))
        else:
            errors.append(f"不支持的配置类型: {config_type}")
        
        return errors
    
    @staticmethod
    def _validate_voice_mapping(config_data: Dict[str, Any]) -> List[str]:
        """验证声音映射配置"""
        errors = []
        
        if "mappings" not in config_data:
            errors.append("声音映射配置缺少 'mappings' 字段")
            return errors
        
        mappings = config_data["mappings"]
        if not isinstance(mappings, dict):
            errors.append("mappings 必须是字典类型")
            return errors
        
        for character, voice_config in mappings.items():
            if not isinstance(voice_config, dict):
                errors.append(f"角色 '{character}' 的声音配置必须是字典类型")
                continue
            
            if "voice_id" not in voice_config:
                errors.append(f"角色 '{character}' 缺少 voice_id 字段")
        
        return errors
    
    @staticmethod
    def _validate_synthesis_params(config_data: Dict[str, Any]) -> List[str]:
        """验证合成参数配置"""
        errors = []
        
        if "parameters" not in config_data:
            errors.append("合成参数配置缺少 'parameters' 字段")
            return errors
        
        params = config_data["parameters"]
        required_params = ["timeStep", "pWeight", "tWeight"]
        
        for param in required_params:
            if param not in params:
                errors.append(f"合成参数缺少必需字段: {param}")
                continue
            
            if not isinstance(params[param], (int, float)):
                errors.append(f"参数 {param} 必须是数字类型")
        
        # 验证参数范围
        if "timeStep" in params and (params["timeStep"] < 5 or params["timeStep"] > 100):
            errors.append("timeStep 必须在 5-100 范围内")
        
        if "pWeight" in params and (params["pWeight"] < 0 or params["pWeight"] > 2):
            errors.append("pWeight 必须在 0-2 范围内")
        
        if "tWeight" in params and (params["tWeight"] < 0 or params["tWeight"] > 2):
            errors.append("tWeight 必须在 0-2 范围内")
        
        return errors
    
    @staticmethod
    def _validate_analysis_params(config_data: Dict[str, Any]) -> List[str]:
        """验证分析参数配置"""
        errors = []
        
        if "llm_config" not in config_data:
            errors.append("分析参数配置缺少 'llm_config' 字段")
        else:
            llm_config = config_data["llm_config"]
            if "provider" not in llm_config:
                errors.append("LLM配置缺少 provider 字段")
        
        if "analysis_options" not in config_data:
            errors.append("分析参数配置缺少 'analysis_options' 字段")
        
        return errors
    
    @staticmethod
    def _validate_complete_preset(config_data: Dict[str, Any]) -> List[str]:
        """验证完整预设配置"""
        errors = []
        
        required_sections = ["llm_config", "analysis_params", "synthesis_params"]
        for section in required_sections:
            if section not in config_data:
                errors.append(f"完整预设配置缺少 '{section}' 字段")
        
        return errors


class PresetService:
    """预设配置管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_preset(
        self,
        name: str,
        config_type: str,
        config_data: Dict[str, Any],
        description: str = None,
        scope: str = "global",
        scope_id: int = None
    ) -> Dict[str, Any]:
        """创建新的预设配置"""
        
        # 验证配置数据
        validation_errors = PresetValidator.validate_config_data(config_type, config_data)
        if validation_errors:
            raise ServiceException(f"配置验证失败: {'; '.join(validation_errors)}")
        
        # 检查名称是否已存在
        existing = self.db.query(UserPreset).filter(
            and_(
                UserPreset.name == name,
                UserPreset.scope == scope,
                UserPreset.scope_id == scope_id
            )
        ).first()
        
        if existing:
            raise ServiceException(f"预设名称 '{name}' 已存在")
        
        # 验证scope_id的有效性
        if scope == "project" and scope_id:
            project = self.db.query(NovelProject).filter(NovelProject.id == scope_id).first()
            if not project:
                raise ServiceException("指定的项目不存在")
        elif scope == "book" and scope_id:
            book = self.db.query(Book).filter(Book.id == scope_id).first()
            if not book:
                raise ServiceException("指定的书籍不存在")
        
        # 创建预设
        preset = UserPreset(
            name=name,
            description=description,
            config_type=config_type,
            config_data=config_data,
            scope=scope,
            scope_id=scope_id
        )
        
        self.db.add(preset)
        self.db.commit()
        self.db.refresh(preset)
        
        return preset.to_dict()
    
    async def get_presets(
        self,
        config_type: str = None,
        scope: str = None,
        scope_id: int = None,
        search: str = None
    ) -> List[Dict[str, Any]]:
        """获取预设列表"""
        
        query = self.db.query(UserPreset)
        
        # 过滤条件
        if config_type:
            query = query.filter(UserPreset.config_type == config_type)
        
        if scope:
            query = query.filter(UserPreset.scope == scope)
        
        if scope_id is not None:
            query = query.filter(UserPreset.scope_id == scope_id)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    UserPreset.name.ilike(search_pattern),
                    UserPreset.description.ilike(search_pattern)
                )
            )
        
        # 排序：使用频率高的在前
        presets = query.order_by(
            UserPreset.usage_count.desc(),
            UserPreset.last_used.desc().nullslast(),
            UserPreset.created_at.desc()
        ).all()
        
        return [preset.to_dict() for preset in presets]
    
    async def get_preset(self, preset_id: int) -> Dict[str, Any]:
        """获取单个预设配置"""
        preset = self.db.query(UserPreset).filter(UserPreset.id == preset_id).first()
        if not preset:
            raise ServiceException("预设不存在")
        
        return preset.to_dict()
    
    async def update_preset(
        self,
        preset_id: int,
        name: str = None,
        config_data: Dict[str, Any] = None,
        description: str = None
    ) -> Dict[str, Any]:
        """更新预设配置"""
        preset = self.db.query(UserPreset).filter(UserPreset.id == preset_id).first()
        if not preset:
            raise ServiceException("预设不存在")
        
        # 更新字段
        if name is not None:
            # 检查新名称是否冲突
            existing = self.db.query(UserPreset).filter(
                and_(
                    UserPreset.name == name,
                    UserPreset.scope == preset.scope,
                    UserPreset.scope_id == preset.scope_id,
                    UserPreset.id != preset_id
                )
            ).first()
            
            if existing:
                raise ServiceException(f"预设名称 '{name}' 已存在")
            
            preset.name = name
        
        if config_data is not None:
            # 验证新的配置数据
            validation_errors = PresetValidator.validate_config_data(preset.config_type, config_data)
            if validation_errors:
                raise ServiceException(f"配置验证失败: {'; '.join(validation_errors)}")
            
            preset.config_data = config_data
        
        if description is not None:
            preset.description = description
        
        preset.updated_at = datetime.utcnow()
        
        self.db.commit()
        return preset.to_dict()
    
    async def delete_preset(self, preset_id: int) -> bool:
        """删除预设配置"""
        preset = self.db.query(UserPreset).filter(UserPreset.id == preset_id).first()
        if not preset:
            raise ServiceException("预设不存在")
        
        self.db.delete(preset)
        self.db.commit()
        
        return True
    
    async def apply_preset(self, preset_id: int) -> Dict[str, Any]:
        """应用预设配置（记录使用统计）"""
        preset = self.db.query(UserPreset).filter(UserPreset.id == preset_id).first()
        if not preset:
            raise ServiceException("预设不存在")
        
        # 更新使用统计
        preset.usage_count += 1
        preset.last_used = datetime.utcnow()
        
        self.db.commit()
        
        return preset.to_dict()
    
    async def duplicate_preset(
        self,
        preset_id: int,
        new_name: str,
        new_scope: str = None,
        new_scope_id: int = None
    ) -> Dict[str, Any]:
        """复制预设配置"""
        original = self.db.query(UserPreset).filter(UserPreset.id == preset_id).first()
        if not original:
            raise ServiceException("原预设不存在")
        
        # 设置新的作用域
        target_scope = new_scope or original.scope
        target_scope_id = new_scope_id if new_scope else original.scope_id
        
        # 检查新名称是否冲突
        existing = self.db.query(UserPreset).filter(
            and_(
                UserPreset.name == new_name,
                UserPreset.scope == target_scope,
                UserPreset.scope_id == target_scope_id
            )
        ).first()
        
        if existing:
            raise ServiceException(f"预设名称 '{new_name}' 已存在")
        
        # 创建副本
        new_preset = UserPreset(
            name=new_name,
            description=f"复制自: {original.name}",
            config_type=original.config_type,
            config_data=copy.deepcopy(original.config_data),
            scope=target_scope,
            scope_id=target_scope_id
        )
        
        self.db.add(new_preset)
        self.db.commit()
        self.db.refresh(new_preset)
        
        return new_preset.to_dict()
    
    async def export_preset(self, preset_id: int) -> Dict[str, Any]:
        """导出预设配置"""
        preset = self.db.query(UserPreset).filter(UserPreset.id == preset_id).first()
        if not preset:
            raise ServiceException("预设不存在")
        
        export_data = {
            "name": preset.name,
            "description": preset.description,
            "config_type": preset.config_type,
            "config_data": preset.config_data,
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "source": "AI-Sound"
        }
        
        return export_data
    
    async def import_preset(
        self,
        import_data: Dict[str, Any],
        name_override: str = None,
        scope: str = "global",
        scope_id: int = None
    ) -> Dict[str, Any]:
        """导入预设配置"""
        
        # 验证导入数据格式
        required_fields = ["name", "config_type", "config_data"]
        for field in required_fields:
            if field not in import_data:
                raise ServiceException(f"导入数据缺少必需字段: {field}")
        
        name = name_override or import_data["name"]
        config_type = import_data["config_type"]
        config_data = import_data["config_data"]
        description = import_data.get("description", "导入的预设配置")
        
        # 验证配置数据
        validation_errors = PresetValidator.validate_config_data(config_type, config_data)
        if validation_errors:
            raise ServiceException(f"导入配置验证失败: {'; '.join(validation_errors)}")
        
        # 创建预设
        return await self.create_preset(
            name=name,
            config_type=config_type,
            config_data=config_data,
            description=description,
            scope=scope,
            scope_id=scope_id
        )
    
    async def get_preset_templates(self) -> Dict[str, Dict[str, Any]]:
        """获取内置预设模板"""
        return {
            "voice_mapping": PresetTemplates.get_default_voice_mapping(),
            "synthesis_params": PresetTemplates.get_default_synthesis_params(),
            "analysis_params": PresetTemplates.get_default_analysis_params(),
            "analysis_complete": PresetTemplates.get_complete_analysis_preset()
        }
    
    async def create_from_template(
        self,
        template_name: str,
        preset_name: str,
        scope: str = "global",
        scope_id: int = None
    ) -> Dict[str, Any]:
        """基于模板创建预设"""
        templates = await self.get_preset_templates()
        
        if template_name not in templates:
            raise ServiceException(f"模板 '{template_name}' 不存在")
        
        template_data = templates[template_name]
        config_type = template_data.get("type", template_name)
        
        return await self.create_preset(
            name=preset_name,
            config_type=config_type,
            config_data=template_data,
            description=f"基于 {template_name} 模板创建",
            scope=scope,
            scope_id=scope_id
        )
    
    def get_preset_statistics(self) -> Dict[str, Any]:
        """获取预设使用统计"""
        stats = self.db.query(
            func.count(UserPreset.id).label('total_presets'),
            func.count(func.distinct(UserPreset.config_type)).label('unique_types'),
            func.sum(UserPreset.usage_count).label('total_usage'),
            func.avg(UserPreset.usage_count).label('avg_usage')
        ).first()
        
        # 按类型统计
        type_stats = self.db.query(
            UserPreset.config_type,
            func.count(UserPreset.id).label('count'),
            func.sum(UserPreset.usage_count).label('usage')
        ).group_by(UserPreset.config_type).all()
        
        # 最常用的预设
        popular_presets = self.db.query(UserPreset).order_by(
            UserPreset.usage_count.desc()
        ).limit(5).all()
        
        return {
            "total_presets": stats.total_presets or 0,
            "unique_types": stats.unique_types or 0,
            "total_usage": stats.total_usage or 0,
            "average_usage": round(stats.avg_usage or 0, 2),
            "by_type": [
                {
                    "type": item.config_type,
                    "count": item.count,
                    "usage": item.usage
                }
                for item in type_stats
            ],
            "most_popular": [
                {
                    "id": preset.id,
                    "name": preset.name,
                    "type": preset.config_type,
                    "usage_count": preset.usage_count
                }
                for preset in popular_presets
            ]
        } 