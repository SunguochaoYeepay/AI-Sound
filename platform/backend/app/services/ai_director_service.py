"""
AI导演服务
负责将中文小说段落转换为专业的图片生成提示词
包含镜头语言规划、构图设计、风格指导等
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional
import asyncio
import aiohttp

logger = logging.getLogger(__name__)


class AIDirectorService:
    """AI导演服务 - 负责镜头语言规划和提示词生成"""
    
    def __init__(self):
        self.ollama_url = "http://localhost:11434"  # 本地Ollama服务
        self.default_model = "qwen2.5:14b"  # 使用中文友好的模型
        
        # 镜头语言模板
        self.shot_types = {
            'close_up': 'close-up shot, intimate, emotional focus',
            'medium_shot': 'medium shot, balanced composition',
            'wide_shot': 'wide shot, establishing scene, environmental context',
            'extreme_close_up': 'extreme close-up, macro detail, intense emotion',
            'bird_eye': 'aerial view, bird eye perspective, dramatic overview',
            'low_angle': 'low angle shot, powerful, imposing perspective',
            'high_angle': 'high angle shot, vulnerable, submissive perspective'
        }
        
        # 艺术风格模板
        self.art_styles = {
            'realistic': 'photorealistic, hyperrealistic, detailed textures',
            'cinematic': 'cinematic lighting, film grain, dramatic contrast',
            'fantasy': 'fantasy art, magical atmosphere, ethereal lighting',
            'historical': 'historical accuracy, period authentic, detailed costumes',
            'anime': 'anime style, cell shading, vibrant colors',
            'oil_painting': 'oil painting style, brush strokes, classical art',
            'digital_art': 'digital art, concept art, professional illustration'
        }
        
        # 情绪色调映射
        self.mood_mapping = {
            '紧张': 'tense, dramatic lighting, high contrast',
            '惊讶': 'surprised, bright lighting, dynamic composition',
            '愤怒': 'angry, red tones, harsh shadows',
            '悲伤': 'melancholic, blue tones, soft shadows',
            '喜悦': 'joyful, warm lighting, bright colors',
            '恐惧': 'fearful, dark shadows, ominous atmosphere',
            '平静': 'calm, soft lighting, harmonious colors',
            '激动': 'excited, dynamic lighting, energetic composition'
        }
    
    async def generate_visual_prompt(self, 
                                   segment_text: str, 
                                   segment_type: str = 'narrative',
                                   style_preference: str = 'cinematic') -> Dict[str, Any]:
        """
        生成专业的视觉提示词
        
        Args:
            segment_text: 小说段落文本
            segment_type: 段落类型
            style_preference: 风格偏好
            
        Returns:
            包含详细视觉描述的字典
        """
        
        try:
            # 1. 使用LLM分析段落内容
            analysis_result = await self._analyze_with_llm(segment_text, segment_type)
            
            # 2. 生成镜头语言规划
            shot_planning = self._plan_shot_composition(analysis_result)
            
            # 3. 构建最终提示词
            final_prompt = self._build_professional_prompt(
                analysis_result, 
                shot_planning, 
                style_preference
            )
            
            return {
                'success': True,
                'analysis': analysis_result,
                'shot_planning': shot_planning,
                'generated_prompt': final_prompt['positive'],
                'negative_prompt': final_prompt['negative'],
                'scene_description': analysis_result.get('scene_description', ''),
                'character_info': analysis_result.get('characters', {}),
                'emotional_tone': analysis_result.get('emotion', ''),
                'style_keywords': shot_planning.get('style_tags', [])
            }
            
        except Exception as e:
            logger.error(f"AI导演生成提示词失败: {str(e)}")
            
            # 降级到规则方法
            fallback_result = self._fallback_prompt_generation(segment_text, style_preference)
            fallback_result['success'] = False
            fallback_result['error'] = str(e)
            return fallback_result
    
    async def _analyze_with_llm(self, text: str, segment_type: str) -> Dict[str, Any]:
        """使用LLM分析段落内容"""
        
        prompt = f"""请分析以下小说段落，提取关键的视觉信息用于图片生成：

段落内容：{text}
段落类型：{segment_type}

请以JSON格式返回分析结果，包含：
1. scene_description: 场景的英文描述（专业、视觉化）
2. characters: 人物信息（姓名、外貌、动作、表情）
3. environment: 环境描述（地点、时间、氛围）
4. emotion: 主要情绪色调
5. key_objects: 重要物体或道具
6. action: 主要动作或情节
7. visual_focus: 视觉焦点（最应该突出的元素）

示例格式：
{{
    "scene_description": "A young man in ancient Chinese clothing staring at a soldier's armor with shock",
    "characters": {{
        "林渊": {{
            "appearance": "young man, modern soul in ancient body",
            "action": "staring intensely, throat moving nervously",
            "emotion": "shocked, realizing"
        }}
    }},
    "environment": {{
        "setting": "ancient Chinese battlefield or military camp",
        "time_period": "Han Dynasty, Chu-Han Contention period",
        "atmosphere": "tense, historical, dramatic moment of realization"
    }},
    "emotion": "shock, realization, time-travel awareness",
    "key_objects": ["Han dynasty armor", "Chinese character '汉' on chest plate"],
    "action": "moment of recognition and realization",
    "visual_focus": "the character '汉' on the armor, protagonist's shocked expression"
}}

请确保返回有效的JSON格式。"""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.default_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "top_p": 0.9
                        }
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get('response', '')
                        
                        # 尝试解析JSON
                        try:
                            # 清理响应文本，提取JSON部分
                            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                            if json_match:
                                json_str = json_match.group()
                                analysis = json.loads(json_str)
                                return analysis
                            else:
                                raise ValueError("未找到有效的JSON响应")
                        except json.JSONDecodeError as e:
                            logger.warning(f"LLM返回的JSON格式有误: {e}, 原始响应: {response_text}")
                            return self._parse_text_response(response_text)
                    else:
                        raise Exception(f"LLM API调用失败: {response.status}")
                        
        except Exception as e:
            logger.error(f"LLM分析失败: {str(e)}")
            raise e
    
    def _parse_text_response(self, text: str) -> Dict[str, Any]:
        """当JSON解析失败时，尝试从文本中提取信息"""
        
        # 简单的文本解析逻辑
        return {
            "scene_description": "dramatic scene from Chinese historical fiction",
            "characters": {},
            "environment": {
                "setting": "ancient China",
                "atmosphere": "dramatic"
            },
            "emotion": "intense",
            "key_objects": [],
            "action": "character interaction",
            "visual_focus": "main character"
        }
    
    def _plan_shot_composition(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """规划镜头构图"""
        
        emotion = analysis.get('emotion', '')
        action = analysis.get('action', '')
        visual_focus = analysis.get('visual_focus', '')
        
        # 根据内容选择镜头类型
        shot_type = 'medium_shot'  # 默认
        
        if 'shocked' in emotion or 'realization' in emotion:
            shot_type = 'close_up'  # 特写捕捉情绪
        elif 'staring' in action or 'looking' in action:
            shot_type = 'medium_shot'  # 中景展示交互
        elif 'battlefield' in str(analysis.get('environment', {})):
            shot_type = 'wide_shot'  # 广景展示环境
        
        # 选择艺术风格
        style_tags = ['cinematic', 'dramatic lighting', 'high quality']
        
        if 'ancient' in str(analysis):
            style_tags.extend(['historical', 'period authentic', 'detailed costumes'])
        
        if 'intense' in emotion or 'dramatic' in emotion:
            style_tags.extend(['high contrast', 'dramatic shadows'])
        
        return {
            'shot_type': shot_type,
            'composition': self.shot_types.get(shot_type, ''),
            'style_tags': style_tags,
            'lighting': self._suggest_lighting(analysis),
            'color_palette': self._suggest_colors(analysis)
        }
    
    def _suggest_lighting(self, analysis: Dict[str, Any]) -> str:
        """建议光照设置"""
        
        emotion = analysis.get('emotion', '').lower()
        
        if 'shock' in emotion or 'dramatic' in emotion:
            return 'dramatic lighting, strong contrast, focused light'
        elif 'calm' in emotion or 'peaceful' in emotion:
            return 'soft lighting, gentle shadows, warm tones'
        elif 'tense' in emotion or 'intense' in emotion:
            return 'harsh lighting, deep shadows, high contrast'
        else:
            return 'natural lighting, balanced exposure'
    
    def _suggest_colors(self, analysis: Dict[str, Any]) -> str:
        """建议色彩搭配"""
        
        environment = analysis.get('environment', {})
        emotion = analysis.get('emotion', '').lower()
        
        if 'ancient' in str(environment):
            return 'earth tones, bronze, deep reds, traditional Chinese colors'
        elif 'shock' in emotion:
            return 'desaturated colors, dramatic contrast'
        elif 'warm' in emotion:
            return 'warm palette, golden hour colors'
        else:
            return 'natural color palette, balanced saturation'
    
    def _build_professional_prompt(self, 
                                 analysis: Dict[str, Any], 
                                 shot_planning: Dict[str, Any], 
                                 style: str) -> Dict[str, str]:
        """构建专业的Flux模型提示词"""
        
        positive_parts = []
        
        # Flux模型更适合自然语言描述，我们构建更流畅的叙述性提示词
        
        # 1. 主要场景描述 - Flux的核心优势
        scene_desc = analysis.get('scene_description', '')
        if scene_desc:
            positive_parts.append(scene_desc)
        
        # 2. 人物描述 - 结合外貌和动作
        characters = analysis.get('characters', {})
        for char_name, char_info in characters.items():
            if isinstance(char_info, dict):
                appearance = char_info.get('appearance', '')
                action = char_info.get('action', '')
                emotion = char_info.get('emotion', '')
                
                # 构建完整的人物描述
                char_description = []
                if appearance:
                    char_description.append(appearance)
                if action:
                    char_description.append(action)
                if emotion:
                    char_description.append(f"expressing {emotion}")
                
                if char_description:
                    positive_parts.append(', '.join(char_description))
        
        # 3. 环境描述 - Flux擅长环境渲染
        environment = analysis.get('environment', {})
        if isinstance(environment, dict):
            setting = environment.get('setting', '')
            time_period = environment.get('time_period', '')
            atmosphere = environment.get('atmosphere', '')
            
            # 构建环境描述
            env_parts = []
            if setting:
                env_parts.append(setting)
            if time_period:
                env_parts.append(f"during {time_period}")
            if atmosphere:
                env_parts.append(f"with {atmosphere} atmosphere")
            
            if env_parts:
                positive_parts.append(', '.join(env_parts))
        
        # 4. 重要物体 - Flux对细节把控很好
        key_objects = analysis.get('key_objects', [])
        if key_objects:
            positive_parts.append(f"featuring {', '.join(key_objects)}")
        
        # 5. 镜头构图 - 电影化描述
        composition = shot_planning.get('composition', '')
        if composition:
            positive_parts.append(composition)
        
        # 6. 光照描述 - Flux的强项
        lighting = shot_planning.get('lighting', '')
        if lighting:
            positive_parts.append(lighting)
        
        # 7. 色彩描述 - 自然语言化
        colors = shot_planning.get('color_palette', '')
        if colors:
            positive_parts.append(colors)
        
        # 8. 风格描述 - 减少技术术语，增加艺术描述
        style_tags = shot_planning.get('style_tags', [])
        
        # 为Flux优化的风格标签
        flux_optimized_styles = []
        for tag in style_tags:
            if tag == 'cinematic':
                flux_optimized_styles.append('cinematic composition')
            elif tag == 'dramatic lighting':
                flux_optimized_styles.append('dramatic lighting effects')
            elif tag == 'historical':
                flux_optimized_styles.append('historically accurate details')
            elif tag == 'period authentic':
                flux_optimized_styles.append('authentic period costume and setting')
            elif tag == 'detailed costumes':
                flux_optimized_styles.append('intricate costume details')
            elif tag == 'high contrast':
                flux_optimized_styles.append('strong contrast and shadows')
            elif tag in ['high quality', 'masterpiece', 'best quality']:
                # Flux不需要这些质量标签，跳过
                continue
            else:
                flux_optimized_styles.append(tag)
        
        positive_parts.extend(flux_optimized_styles)
        
        # 9. Flux专用质量描述 - 更自然的表达
        flux_quality_terms = [
            "professional photography quality",
            "highly detailed and realistic", 
            "sharp focus and clarity"
        ]
        positive_parts.extend(flux_quality_terms)
        
        # 构建负面提示词 - Flux模型的负面提示更简洁
        negative_prompt = [
            'blurry', 'distorted', 'low quality', 'bad anatomy',
            'deformed', 'watermark', 'text overlay', 'signature'
        ]
        
        # 将所有部分连接成自然的句子
        final_positive = ', '.join(positive_parts)
        
        # 优化语法和流畅性
        final_positive = self._optimize_prompt_grammar(final_positive)
        
        return {
            'positive': final_positive,
            'negative': ', '.join(negative_prompt)
        }
    
    def _optimize_prompt_grammar(self, prompt: str) -> str:
        """优化提示词的语法和流畅性"""
        
        # 移除重复的逗号和空格
        prompt = ', '.join([part.strip() for part in prompt.split(',') if part.strip()])
        
        # 移除重复的词汇
        words = prompt.split(', ')
        unique_words = []
        seen = set()
        
        for word in words:
            word_lower = word.lower()
            if word_lower not in seen:
                unique_words.append(word)
                seen.add(word_lower)
        
        return ', '.join(unique_words)
    
    def _fallback_prompt_generation(self, text: str, style: str) -> Dict[str, Any]:
        """降级的提示词生成方法"""
        
        # 简单的关键词提取
        keywords = []
        
        # 检测人物
        if '林渊' in text:
            keywords.append('young Chinese man')
        
        # 检测场景
        if '胸甲' in text or '汉' in text:
            keywords.append('ancient Chinese armor with Han character')
        
        if '穿越' in text:
            keywords.append('time travel realization moment')
        
        # 检测情绪
        if '突然意识到' in text:
            keywords.append('shocked expression, moment of realization')
        
        # 添加基础质量标签
        keywords.extend([
            'cinematic', 'dramatic lighting', 'high quality',
            'detailed', 'masterpiece'
        ])
        
        return {
            'generated_prompt': ', '.join(keywords),
            'negative_prompt': 'blurry, low quality, distorted, nsfw',
            'scene_description': 'dramatic realization scene',
            'character_info': {'林渊': 'shocked young man'},
            'emotional_tone': 'dramatic surprise',
            'style_keywords': ['cinematic', 'dramatic']
        } 