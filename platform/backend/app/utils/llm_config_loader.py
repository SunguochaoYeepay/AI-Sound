"""
LLM配置加载工具
统一管理所有LLM相关的配置读取
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class LLMConfigLoader:
    """LLM配置加载器"""
    
    _instance = None
    _config_cache = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_config(self) -> Dict[str, Any]:
        """获取LLM配置（单例模式，缓存配置）"""
        if self._config_cache is None:
            self._config_cache = self._load_config()
        return self._config_cache.copy()
    
    def _load_config(self) -> Dict[str, Any]:
        """从配置文件加载LLM配置"""
        config_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "app", "config", "data", "system_settings.json"
        )
        
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"配置文件不存在: {config_file}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                ai_config = settings.get("ai", {})
                
                # 验证必需的配置项
                required_keys = ["defaultLlmModel", "ollamaServiceUrl", "analysisTimeout"]
                missing_keys = [key for key in required_keys if key not in ai_config]
                if missing_keys:
                    raise ValueError(f"配置文件缺少必需的配置项: {missing_keys}")
                
                return {
                    "model": ai_config["defaultLlmModel"],
                    "base_url": ai_config["ollamaServiceUrl"],
                    "timeout": ai_config["analysisTimeout"],
                    "fast_mode": ai_config.get("fastModeEnabled", True),
                    "analysis_mode": ai_config.get("analysisMode", "balanced")
                }
        except Exception as e:
            logger.error(f"无法加载LLM配置: {e}")
            raise
    
    def get_model_config(self, model_type: str = "default") -> Dict[str, Any]:
        """获取特定类型的模型配置"""
        config = self.get_config()
        
        # 根据模型类型返回不同配置
        if model_type == "fast":
            # 快速模型配置 - 从配置文件读取或使用默认值
            fast_model = self._get_fast_model_from_config()
            return {
                "model": fast_model,
                "base_url": config["base_url"],
                "timeout": config["timeout"] // 2,  # 快速模式超时时间减半
                "temperature": 0.3,
                "max_tokens": 2000
            }
        elif model_type == "advanced":
            # 高级模型配置 - 从配置文件读取或使用默认值
            advanced_model = self._get_advanced_model_from_config()
            return {
                "model": advanced_model,
                "base_url": config["base_url"],
                "timeout": config["timeout"] * 2,  # 高级模式超时时间加倍
                "temperature": 0.1,
                "max_tokens": 4000
            }
        else:
            # 默认配置
            return {
                "model": config["model"],
                "base_url": config["base_url"],
                "timeout": config["timeout"],
                "temperature": 0.7,
                "max_tokens": 4000
            }
    
    def _get_fast_model_from_config(self) -> str:
        """从配置文件获取快速模型名称"""
        config_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "app", "config", "data", "system_settings.json"
        )
        
        with open(config_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            ai_config = settings.get("ai", {})
            return ai_config["fastLlmModel"]
    
    def _get_advanced_model_from_config(self) -> str:
        """从配置文件获取高级模型名称"""
        config_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "app", "config", "data", "system_settings.json"
        )
        
        with open(config_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            ai_config = settings.get("ai", {})
            return ai_config["advancedLlmModel"]
    
    def refresh_config(self):
        """刷新配置缓存"""
        self._config_cache = None
        logger.info("LLM配置缓存已刷新")


# 全局配置加载器实例
llm_config_loader = LLMConfigLoader()
