"""
AI分析配置文件
包含优化的LLM配置、置信度阈值和监控指标
"""

from typing import Dict, Any

class AnalysisConfig:
    """分析配置类"""
    
    # 优化的LLM配置
    OPTIMIZED_LLM_CONFIG = {
        "provider": "ollama",  # 使用本地Ollama服务
        "model": "qwen3",  # 使用qwen3模型
        "temperature": 0.3,  # 降低随机性，提高一致性
        "top_p": 0.9,  # 控制输出质量
        "max_tokens": 4000,  # 增加输出长度
        "frequency_penalty": 0.1,  # 减少重复内容
        "presence_penalty": 0.1,  # 鼓励多样性
        "stop": None,  # 不设置停止词
        "timeout": 120  # 增加超时时间
    }
    
    # 优化的置信度阈值
    CONFIDENCE_THRESHOLDS = {
        "story": 0.95,           # 故事分析要求最高
        "character": 0.92,       # 角色分析要求高
        "scene": 0.90,           # 场景分析要求高
        "event": 0.93,           # 事件分析要求高
        "emotion": 0.88,         # 情感分析要求中等
        "audio_storyboard": 0.90, # 分镜分析要求高
        "audio_script": 0.92     # 剧本分析要求高
    }
    
    # 分析选项配置
    ANALYSIS_OPTIONS = {
        "enable_character_detection": True,
        "enable_emotion_analysis": True,
        "enable_voice_recommendation": True,
        "enable_dialogue_detection": True,
        "batch_size": 5,
        "confidence_threshold": 0.9,  # 提高置信度阈值
        "enable_cross_reference": True,  # 启用跨段落引用检查
        "enable_consistency_check": True,  # 启用一致性检查
        "enable_validation": True,  # 启用结果验证
        "max_retries": 3,  # 最大重试次数
        "timeout_seconds": 120  # 超时时间
    }
    
    # 监控指标配置
    MONITORING_METRICS = {
        "accuracy_score": {
            "description": "分析结果与原文的匹配度",
            "target": ">90%",
            "current": "75-80%",
            "weight": 0.4
        },
        "confidence_distribution": {
            "description": "置信度分数的分布情况",
            "target": ">85%达到阈值",
            "current": "60-70%达到阈值",
            "weight": 0.3
        },
        "processing_time": {
            "description": "分析处理时间",
            "target": "<30秒",
            "current": "未知",
            "weight": 0.2
        },
        "consistency_score": {
            "description": "分析结果内部一致性",
            "target": ">90%",
            "current": "80%",
            "weight": 0.1
        }
    }
    
    # 质量检查点配置
    QUALITY_CHECKPOINTS = {
        "pre_analysis": [
            "文本完整性检查",
            "编码格式验证",
            "长度限制检查",
            "内容质量评估"
        ],
        "post_analysis": [
            "置信度验证",
            "结果完整性检查",
            "格式一致性验证",
            "跨引用一致性检查"
        ]
    }
    
    # 处理选项配置
    PROCESSING_OPTIONS = {
        "max_retries": 3,
        "timeout_seconds": 120,
        "concurrent_limit": 3,
        "enable_caching": True,
        "enable_validation": True,
        "enable_consistency_check": True,
        "confidence_thresholds": CONFIDENCE_THRESHOLDS
    }
    
    @classmethod
    def get_optimized_config(cls) -> Dict[str, Any]:
        """获取优化的完整配置"""
        return {
            "llm_config": cls.OPTIMIZED_LLM_CONFIG,
            "analysis_options": cls.ANALYSIS_OPTIONS,
            "confidence_thresholds": cls.CONFIDENCE_THRESHOLDS,
            "monitoring_metrics": cls.MONITORING_METRICS,
            "quality_checkpoints": cls.QUALITY_CHECKPOINTS,
            "processing_options": cls.PROCESSING_OPTIONS
        }
    
    @classmethod
    def get_llm_config(cls) -> Dict[str, Any]:
        """获取LLM配置"""
        return cls.OPTIMIZED_LLM_CONFIG.copy()
    
    @classmethod
    def get_confidence_thresholds(cls) -> Dict[str, float]:
        """获取置信度阈值"""
        return cls.CONFIDENCE_THRESHOLDS.copy()
    
    @classmethod
    def get_monitoring_metrics(cls) -> Dict[str, Any]:
        """获取监控指标配置"""
        return cls.MONITORING_METRICS.copy()
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> bool:
        """验证配置的有效性"""
        required_keys = [
            "llm_config", "analysis_options", "confidence_thresholds"
        ]
        
        for key in required_keys:
            if key not in config:
                return False
        
        # 验证LLM配置
        llm_config = config["llm_config"]
        if "model" not in llm_config or "temperature" not in llm_config:
            return False
        
        # 验证置信度阈值
        confidence_thresholds = config["confidence_thresholds"]
        for threshold in confidence_thresholds.values():
            if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
                return False
        
        return True

# 创建全局配置实例
analysis_config = AnalysisConfig()
