"""
优化的Prompt工程服务
包含针对不同分析任务的专门化Prompt模板和多轮验证机制
"""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from app.config.analysis_config import analysis_config

logger = logging.getLogger(__name__)

@dataclass
class PromptTemplate:
    """Prompt模板数据类"""
    name: str
    description: str
    template: str
    variables: List[str]
    examples: List[Dict[str, Any]]
    confidence_threshold: float
    max_retries: int = 3

class PromptEngine:
    """Prompt工程引擎"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
        self.validation_prompts = self._initialize_validation_prompts()
    
    def _initialize_templates(self) -> Dict[str, PromptTemplate]:
        """初始化Prompt模板"""
        return {
            "story_analysis": PromptTemplate(
                name="故事分析",
                description="分析章节的故事结构、情节发展和主题",
                template="""你是一个专业的小说分析专家。请分析以下章节内容，提取关键信息：

章节标题：{chapter_title}
章节内容：{chapter_content}

请按照以下格式输出分析结果：

## 故事结构分析
- 主要情节：{story_plot}
- 情节发展：{plot_development}
- 冲突点：{conflicts}
- 高潮部分：{climax}

## 主题分析
- 核心主题：{core_theme}
- 次要主题：{sub_themes}
- 象征意义：{symbolism}

## 情感基调
- 整体氛围：{atmosphere}
- 情感变化：{emotion_changes}

请确保分析准确、深入，置信度不低于{confidence_threshold}。""",
                variables=["chapter_title", "chapter_content", "confidence_threshold"],
                examples=[
                    {
                        "input": "长安初遇章节",
                        "output": "故事结构清晰，情节发展自然..."
                    }
                ],
                confidence_threshold=0.95
            ),
            
            "character_analysis": PromptTemplate(
                name="角色分析",
                description="分析章节中出现的角色特征、关系和对话",
                template="""你是一个专业的角色分析专家。请分析以下章节中的角色信息：

章节内容：{chapter_content}

请按照以下格式输出分析结果：

## 角色识别
- 主要角色：{main_characters}
- 次要角色：{supporting_characters}
- 角色关系：{character_relationships}

## 角色特征
- 性格特点：{personality_traits}
- 行为模式：{behavior_patterns}
- 对话风格：{dialogue_style}

## 角色发展
- 角色弧线：{character_arc}
- 成长变化：{character_growth}

请确保角色分析准确、全面，置信度不低于{confidence_threshold}。""",
                variables=["chapter_content", "confidence_threshold"],
                examples=[
                    {
                        "input": "萧炎角色分析",
                        "output": "萧炎是一个勇敢、坚韧的主角..."
                    }
                ],
                confidence_threshold=0.92
            ),
            
            "scene_analysis": PromptTemplate(
                name="场景分析",
                description="分析章节中的场景设置、环境和氛围",
                template="""你是一个专业的场景分析专家。请分析以下章节的场景信息：

章节内容：{chapter_content}

请按照以下格式输出分析结果：

## 场景设置
- 地理位置：{location}
- 时间背景：{time_period}
- 环境描述：{environment}

## 氛围营造
- 视觉元素：{visual_elements}
- 听觉元素：{audio_elements}
- 情感氛围：{emotional_atmosphere}

## 场景转换
- 场景变化：{scene_transitions}
- 空间关系：{spatial_relationships}

请确保场景分析准确、详细，置信度不低于{confidence_threshold}。""",
                variables=["chapter_content", "confidence_threshold"],
                examples=[
                    {
                        "input": "客栈场景分析",
                        "output": "客栈位于长安城内，夜晚时分..."
                    }
                ],
                confidence_threshold=0.90
            ),
            
            "event_analysis": PromptTemplate(
                name="事件分析",
                description="分析章节中的关键事件、因果关系和影响",
                template="""你是一个专业的事件分析专家。请分析以下章节中的事件信息：

章节内容：{chapter_content}

请按照以下格式输出分析结果：

## 关键事件
- 主要事件：{main_events}
- 事件顺序：{event_sequence}
- 事件重要性：{event_significance}

## 因果关系
- 事件原因：{event_causes}
- 事件结果：{event_consequences}
- 连锁反应：{chain_reactions}

## 事件影响
- 对角色影响：{character_impact}
- 对情节影响：{plot_impact}
- 对主题影响：{theme_impact}

请确保事件分析准确、深入，置信度不低于{confidence_threshold}。""",
                variables=["chapter_content", "confidence_threshold"],
                examples=[
                    {
                        "input": "萧炎点酒事件",
                        "output": "萧炎点酒是章节的关键事件..."
                    }
                ],
                confidence_threshold=0.93
            ),
            
            "emotion_analysis": PromptTemplate(
                name="情感分析",
                description="分析章节中的情感表达、心理状态和情感变化",
                template="""你是一个专业的情感分析专家。请分析以下章节的情感信息：

章节内容：{chapter_content}

请按照以下格式输出分析结果：

## 情感识别
- 主要情感：{primary_emotions}
- 情感强度：{emotion_intensity}
- 情感变化：{emotion_changes}

## 心理状态
- 角色心理：{character_psychology}
- 心理冲突：{psychological_conflicts}
- 心理成长：{psychological_growth}

## 情感表达
- 表达方式：{expression_methods}
- 情感层次：{emotion_layers}
- 情感共鸣：{emotional_resonance}

请确保情感分析准确、细腻，置信度不低于{confidence_threshold}。""",
                variables=["chapter_content", "confidence_threshold"],
                examples=[
                    {
                        "input": "萧炎情感分析",
                        "output": "萧炎表现出坚定和期待的情感..."
                    }
                ],
                confidence_threshold=0.88
            ),
            
            "audio_storyboard": PromptTemplate(
                name="音频分镜",
                description="生成音频分镜脚本，包含语音、音效和音乐建议",
                template="""你是一个专业的音频分镜专家。请为以下章节生成音频分镜脚本：

章节内容：{chapter_content}

请按照以下格式输出音频分镜：

## 语音分镜
- 角色配音：{voice_acting}
- 旁白处理：{narration}
- 语音节奏：{voice_rhythm}

## 音效设计
- 环境音效：{ambient_sounds}
- 动作音效：{action_sounds}
- 情感音效：{emotional_sounds}

## 音乐建议
- 背景音乐：{background_music}
- 情感音乐：{emotional_music}
- 音乐节奏：{music_rhythm}

## 音频节奏
- 整体节奏：{overall_pacing}
- 高潮处理：{climax_handling}
- 过渡处理：{transition_handling}

请确保音频分镜专业、实用，置信度不低于{confidence_threshold}。""",
                variables=["chapter_content", "confidence_threshold"],
                examples=[
                    {
                        "input": "长安初遇音频分镜",
                        "output": "建议使用古风背景音乐..."
                    }
                ],
                confidence_threshold=0.90
            )
        }
    
    def _initialize_validation_prompts(self) -> Dict[str, str]:
        """初始化验证Prompt"""
        return {
            "consistency_check": """请检查以下分析结果的一致性：

原始分析：{original_analysis}
验证要点：{validation_points}

请评估：
1. 内容一致性：{content_consistency}
2. 逻辑一致性：{logic_consistency}
3. 格式一致性：{format_consistency}

如果发现不一致，请提供修正建议。""",
            
            "accuracy_verification": """请验证以下分析结果的准确性：

分析结果：{analysis_result}
原文内容：{original_text}

请评估：
1. 事实准确性：{fact_accuracy}
2. 理解准确性：{comprehension_accuracy}
3. 推理准确性：{reasoning_accuracy}

如果发现不准确，请提供修正建议。""",
            
            "quality_assessment": """请评估以下分析结果的质量：

分析结果：{analysis_result}

请从以下维度评估：
1. 完整性：{completeness}
2. 深度：{depth}
3. 清晰度：{clarity}
4. 实用性：{usability}

请给出总体质量评分（0-100）和改进建议。"""
        }
    
    def get_template(self, template_name: str) -> Optional[PromptTemplate]:
        """获取指定的Prompt模板"""
        return self.templates.get(template_name)
    
    def render_prompt(self, template_name: str, variables: Dict[str, Any]) -> str:
        """渲染Prompt模板"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"模板 '{template_name}' 不存在")
        
        # 检查必需变量
        missing_vars = [var for var in template.variables if var not in variables]
        if missing_vars:
            raise ValueError(f"缺少必需变量: {missing_vars}")
        
        # 渲染模板
        prompt = template.template
        for var, value in variables.items():
            prompt = prompt.replace(f"{{{var}}}", str(value))
        
        return prompt
    
    def get_validation_prompt(self, validation_type: str, variables: Dict[str, Any]) -> str:
        """获取验证Prompt"""
        if validation_type not in self.validation_prompts:
            raise ValueError(f"验证类型 '{validation_type}' 不存在")
        
        prompt = self.validation_prompts[validation_type]
        for var, value in variables.items():
            prompt = prompt.replace(f"{{{var}}}", str(value))
        
        return prompt
    
    def get_all_templates(self) -> Dict[str, PromptTemplate]:
        """获取所有Prompt模板"""
        return self.templates.copy()
    
    def add_custom_template(self, name: str, template: PromptTemplate):
        """添加自定义Prompt模板"""
        if name in self.templates:
            logger.warning(f"模板 '{name}' 已存在，将被覆盖")
        
        self.templates[name] = template
        logger.info(f"添加自定义模板: {name}")
    
    def validate_template(self, template: PromptTemplate) -> List[str]:
        """验证Prompt模板"""
        errors = []
        
        if not template.name:
            errors.append("模板名称不能为空")
        
        if not template.template:
            errors.append("模板内容不能为空")
        
        if not template.variables:
            errors.append("模板变量列表不能为空")
        
        if template.confidence_threshold < 0 or template.confidence_threshold > 1:
            errors.append("置信度阈值必须在0-1之间")
        
        if template.max_retries < 0:
            errors.append("最大重试次数不能为负数")
        
        return errors

# 创建全局Prompt引擎实例
prompt_engine = PromptEngine()
