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
        import os
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")  # 从环境变量获取Ollama服务地址
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
                                   style_preference: str = 'cinematic',
                                   character_context: Optional[Dict] = None) -> Dict[str, Any]:
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
            
            # 2. 如果有角色上下文，融入分析结果
            if character_context:
                analysis_result = self._integrate_character_context(analysis_result, character_context)
            
            # 3. 生成镜头语言规划
            shot_planning = self._plan_shot_composition(analysis_result)
            
            # 4. 构建最终提示词
            final_prompt = self._build_professional_prompt(
                analysis_result, 
                shot_planning, 
                style_preference,
                character_context
            )
            
            return {
                'success': True,
                'analysis': analysis_result,
                'shot_planning': shot_planning,
                'generated_prompt': final_prompt['positive'],
                'generated_prompt_chinese': final_prompt['positive_chinese'],
                'negative_prompt': final_prompt['negative'],
                'negative_prompt_chinese': final_prompt['negative_chinese'],
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
    
    def _integrate_character_context(self, analysis: Dict[str, Any], character_context: Dict) -> Dict[str, Any]:
        """
        将角色上下文信息融入分析结果
        
        Args:
            analysis: LLM分析结果
            character_context: 角色上下文信息
        
        Returns:
            融入角色信息后的分析结果
        """
        try:
            enhanced_analysis = analysis.copy()
            
            # 获取角色信息
            character_name = character_context.get('character_name', '')
            character_features = character_context.get('character_features', {})
            consistency_weight = character_context.get('consistency_weight', 0.5)
            
            # 增强角色描述
            if 'characters' not in enhanced_analysis:
                enhanced_analysis['characters'] = {}
            
            # 如果分析结果中已有该角色，增强其描述
            if character_name in enhanced_analysis['characters']:
                existing_char = enhanced_analysis['characters'][character_name]
                # 融合角色特征
                if character_features.get('age_range'):
                    existing_char['age'] = character_features['age_range']
                if character_features.get('build_type'):
                    existing_char['build'] = character_features['build_type']
                if character_features.get('clothing_style'):
                    existing_char['clothing'] = character_features['clothing_style']
                if character_features.get('distinctive_features'):
                    existing_char['features'] = character_features['distinctive_features']
            else:
                # 添加新的角色信息
                enhanced_analysis['characters'][character_name] = {
                    'name': character_name,
                    'age': character_features.get('age_range', ''),
                    'build': character_features.get('build_type', ''),
                    'clothing': character_features.get('clothing_style', ''),
                    'features': character_features.get('distinctive_features', ''),
                    'consistency_weight': consistency_weight
                }
            
            # 添加角色一致性标记
            enhanced_analysis['character_consistency'] = {
                'enabled': True,
                'target_character': character_name,
                'weight': consistency_weight
            }
            
            logger.debug(f"成功融入角色上下文: {character_name}")
            return enhanced_analysis
            
        except Exception as e:
            logger.error(f"融入角色上下文失败: {str(e)}")
            return analysis
    
    def _build_professional_prompt(self, 
                                 analysis: Dict[str, Any], 
                                 shot_planning: Dict[str, Any], 
                                 style: str,
                                 character_context: Optional[Dict] = None) -> Dict[str, str]:
        """构建专业的Flux模型提示词（中英文双语）"""
        
        # 构建英文提示词
        english_parts = []
        chinese_parts = []
        
        # Flux模型更适合自然语言描述，我们构建更流畅的叙述性提示词
        
        # 1. 主要场景描述 - Flux的核心优势
        scene_desc = analysis.get('scene_description', '')
        if scene_desc:
            english_parts.append(scene_desc)
            # 生成中文场景描述
            chinese_scene = self._translate_scene_to_chinese(scene_desc, analysis)
            chinese_parts.append(chinese_scene)
        
        # 2. 人物描述 - 结合外貌和动作，优先使用角色一致性信息
        characters = analysis.get('characters', {})
        character_consistency = analysis.get('character_consistency', {})
        
        for char_name, char_info in characters.items():
            if isinstance(char_info, dict):
                appearance = char_info.get('appearance', '')
                action = char_info.get('action', '')
                emotion = char_info.get('emotion', '')
                
                # 构建完整的人物描述（英文）
                char_description_en = []
                char_description_cn = []
                
                # 如果启用了角色一致性且是目标角色，使用一致性信息增强描述
                if (character_consistency.get('enabled') and 
                    char_name == character_consistency.get('target_character') and 
                    character_context):
                    
                    # 获取角色特征
                    char_features = character_context.get('character_features', {})
                    consistency_weight = character_context.get('consistency_weight', 0.5)
                    
                    # 构建角色一致性描述
                    consistency_desc_en = self._build_character_consistency_prompt(char_features, consistency_weight)
                    consistency_desc_cn = self._build_character_consistency_prompt_chinese(char_features, consistency_weight)
                    
                    if consistency_desc_en:
                        char_description_en.append(consistency_desc_en)
                    if consistency_desc_cn:
                        char_description_cn.append(consistency_desc_cn)
                    
                    logger.debug(f"为角色 {char_name} 添加一致性描述: {consistency_desc_en}")
                
                # 添加原有的描述信息
                if appearance:
                    char_description_en.append(appearance)
                    char_description_cn.append(self._translate_appearance_to_chinese(appearance))
                if action:
                    char_description_en.append(action)
                    char_description_cn.append(self._translate_action_to_chinese(action))
                if emotion:
                    char_description_en.append(f"expressing {emotion}")
                    char_description_cn.append(f"表现出{self._translate_emotion_to_chinese(emotion)}")
                
                if char_description_en:
                    english_parts.append(', '.join(char_description_en))
                if char_description_cn:
                    chinese_parts.append('，'.join(char_description_cn))
        
        # 3. 环境描述 - Flux擅长环境渲染
        environment = analysis.get('environment', {})
        if isinstance(environment, dict):
            setting = environment.get('setting', '')
            time_period = environment.get('time_period', '')
            atmosphere = environment.get('atmosphere', '')
            
            # 构建环境描述（英文）
            env_parts_en = []
            env_parts_cn = []
            
            if setting:
                env_parts_en.append(setting)
                env_parts_cn.append(self._translate_setting_to_chinese(setting))
            if time_period:
                env_parts_en.append(f"during {time_period}")
                env_parts_cn.append(f"在{self._translate_time_period_to_chinese(time_period)}")
            if atmosphere:
                env_parts_en.append(f"with {atmosphere} atmosphere")
                env_parts_cn.append(f"营造{self._translate_atmosphere_to_chinese(atmosphere)}氛围")
            
            if env_parts_en:
                english_parts.append(', '.join(env_parts_en))
            if env_parts_cn:
                chinese_parts.append('，'.join(env_parts_cn))
        
        # 4. 重要物体 - Flux对细节把控很好
        key_objects = analysis.get('key_objects', [])
        if key_objects:
            english_parts.append(f"featuring {', '.join(key_objects)}")
            chinese_objects = [self._translate_object_to_chinese(obj) for obj in key_objects]
            chinese_parts.append(f"包含{', '.join(chinese_objects)}")
        
        # 5. 镜头构图 - 电影化描述
        composition = shot_planning.get('composition', '')
        if composition:
            english_parts.append(composition)
            chinese_parts.append(self._translate_composition_to_chinese(composition))
        
        # 6. 光照描述 - Flux的强项
        lighting = shot_planning.get('lighting', '')
        if lighting:
            english_parts.append(lighting)
            chinese_parts.append(self._translate_lighting_to_chinese(lighting))
        
        # 7. 色彩描述 - 自然语言化
        colors = shot_planning.get('color_palette', '')
        if colors:
            english_parts.append(colors)
            chinese_parts.append(self._translate_colors_to_chinese(colors))
        
        # 8. 风格描述 - 减少技术术语，增加艺术描述
        style_tags = shot_planning.get('style_tags', [])
        
        # 为Flux优化的风格标签（英文和中文）
        flux_optimized_styles_en = []
        flux_optimized_styles_cn = []
        
        for tag in style_tags:
            if tag == 'cinematic':
                flux_optimized_styles_en.append('cinematic composition')
                flux_optimized_styles_cn.append('电影级构图')
            elif tag == 'dramatic lighting':
                flux_optimized_styles_en.append('dramatic lighting effects')
                flux_optimized_styles_cn.append('戏剧性光影效果')
            elif tag == 'historical':
                flux_optimized_styles_en.append('historically accurate details')
                flux_optimized_styles_cn.append('历史细节准确')
            elif tag == 'period authentic':
                flux_optimized_styles_en.append('authentic period costume and setting')
                flux_optimized_styles_cn.append('时代服饰和场景真实')
            elif tag == 'detailed costumes':
                flux_optimized_styles_en.append('intricate costume details')
                flux_optimized_styles_cn.append('精致服装细节')
            elif tag == 'high contrast':
                flux_optimized_styles_en.append('strong contrast and shadows')
                flux_optimized_styles_cn.append('强烈对比和阴影')
            elif tag in ['high quality', 'masterpiece', 'best quality']:
                # Flux不需要这些质量标签，跳过
                continue
            else:
                flux_optimized_styles_en.append(tag)
                flux_optimized_styles_cn.append(self._translate_style_to_chinese(tag))
        
        english_parts.extend(flux_optimized_styles_en)
        chinese_parts.extend(flux_optimized_styles_cn)
        
        # 9. Flux专用质量描述 - 更自然的表达
        flux_quality_terms_en = [
            "professional photography quality",
            "highly detailed and realistic", 
            "sharp focus and clarity"
        ]
        flux_quality_terms_cn = [
            "专业摄影品质",
            "高度细致逼真",
            "清晰锐利焦点"
        ]
        
        english_parts.extend(flux_quality_terms_en)
        chinese_parts.extend(flux_quality_terms_cn)
        
        # 构建负面提示词 - Flux模型的负面提示更简洁
        negative_prompt_en = [
            'blurry', 'distorted', 'low quality', 'bad anatomy',
            'deformed', 'watermark', 'text overlay', 'signature'
        ]
        negative_prompt_cn = [
            '模糊', '扭曲', '低质量', '解剖错误',
            '变形', '水印', '文字覆盖', '签名'
        ]
        
        # 将所有部分连接成自然的句子
        final_positive_en = ', '.join(english_parts)
        final_positive_cn = '，'.join(chinese_parts)
        
        # 优化语法和流畅性
        final_positive_en = self._optimize_prompt_grammar(final_positive_en)
        
        return {
            'positive': final_positive_en,
            'positive_chinese': final_positive_cn,
            'negative': ', '.join(negative_prompt_en),
            'negative_chinese': '，'.join(negative_prompt_cn)
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
    
    def _translate_scene_to_chinese(self, scene_desc: str, analysis: Dict[str, Any]) -> str:
        """将场景描述翻译为中文"""
        # 基于分析结果生成中文场景描述
        chinese_desc = []
        
        # 从原始文本中提取关键信息
        if 'museum' in scene_desc.lower() or 'display' in scene_desc.lower():
            chinese_desc.append('博物馆展示场景')
        elif 'ancient' in scene_desc.lower():
            chinese_desc.append('古代场景')
        elif 'modern' in scene_desc.lower():
            chinese_desc.append('现代场景')
        
        if 'man' in scene_desc.lower() and 'staring' in scene_desc.lower():
            chinese_desc.append('男子凝视')
        
        if 'sword' in scene_desc.lower():
            chinese_desc.append('剑类文物')
        
        if 'pendant' in scene_desc.lower():
            chinese_desc.append('玉佩饰品')
        
        return '，'.join(chinese_desc) if chinese_desc else '戏剧性场景'
    
    def _translate_appearance_to_chinese(self, appearance: str) -> str:
        """将外貌描述翻译为中文"""
        translations = {
            'young man': '年轻男子',
            'modern attire': '现代服装',
            'casual clothing': '休闲装',
            'traditional costume': '传统服饰',
            'ancient armor': '古代盔甲'
        }
        
        for en, cn in translations.items():
            if en in appearance.lower():
                return cn
        
        return '人物外貌'
    
    def _translate_action_to_chinese(self, action: str) -> str:
        """将动作描述翻译为中文"""
        translations = {
            'staring': '凝视',
            'looking': '观看',
            'touching': '触摸',
            'holding': '握持',
            'examining': '检视',
            'gazing': '注视'
        }
        
        for en, cn in translations.items():
            if en in action.lower():
                return cn
        
        return '动作'
    
    def _translate_emotion_to_chinese(self, emotion: str) -> str:
        """将情感描述翻译为中文"""
        translations = {
            'nostalgic': '怀旧',
            'contemplative': '沉思',
            'shocked': '震惊',
            'surprised': '惊讶',
            'thoughtful': '深思',
            'intense': '强烈',
            'dramatic': '戏剧性'
        }
        
        for en, cn in translations.items():
            if en in emotion.lower():
                return cn
        
        return '情感'
    
    def _translate_setting_to_chinese(self, setting: str) -> str:
        """将场景设置翻译为中文"""
        translations = {
            'museum': '博物馆',
            'exhibition hall': '展览厅',
            'display room': '展示室',
            'ancient palace': '古代宫殿',
            'battlefield': '战场',
            'courtyard': '庭院'
        }
        
        for en, cn in translations.items():
            if en in setting.lower():
                return cn
        
        return '场景设置'
    
    def _translate_time_period_to_chinese(self, time_period: str) -> str:
        """将时间段翻译为中文"""
        translations = {
            'han dynasty': '汉朝',
            'ancient times': '古代',
            'modern era': '现代',
            'night': '夜晚',
            'day': '白天',
            'evening': '傍晚'
        }
        
        for en, cn in translations.items():
            if en in time_period.lower():
                return cn
        
        return '时间段'
    
    def _translate_atmosphere_to_chinese(self, atmosphere: str) -> str:
        """将氛围翻译为中文"""
        translations = {
            'mysterious': '神秘',
            'dramatic': '戏剧性',
            'peaceful': '宁静',
            'tense': '紧张',
            'nostalgic': '怀旧',
            'solemn': '庄严'
        }
        
        for en, cn in translations.items():
            if en in atmosphere.lower():
                return cn
        
        return '氛围'
    
    def _translate_object_to_chinese(self, obj: str) -> str:
        """将物体翻译为中文"""
        translations = {
            'bronze sword': '青铜剑',
            'jade pendant': '玉佩',
            'armor': '盔甲',
            'display case': '展示柜',
            'glass case': '玻璃柜',
            'ancient artifact': '古代文物'
        }
        
        for en, cn in translations.items():
            if en in obj.lower():
                return cn
        
        return obj
    
    def _translate_composition_to_chinese(self, composition: str) -> str:
        """将构图描述翻译为中文"""
        translations = {
            'close-up shot': '特写镜头',
            'medium shot': '中景镜头',
            'wide shot': '远景镜头',
            'dramatic angle': '戏剧性角度',
            'low angle': '低角度',
            'high angle': '高角度'
        }
        
        for en, cn in translations.items():
            if en in composition.lower():
                return cn
        
        return '构图'
    
    def _translate_lighting_to_chinese(self, lighting: str) -> str:
        """将光照描述翻译为中文"""
        translations = {
            'dramatic lighting': '戏剧性光照',
            'soft lighting': '柔和光照',
            'natural lighting': '自然光照',
            'harsh lighting': '强烈光照',
            'focused light': '聚焦光线',
            'warm tones': '暖色调'
        }
        
        for en, cn in translations.items():
            if en in lighting.lower():
                return cn
        
        return '光照效果'
    
    def _translate_colors_to_chinese(self, colors: str) -> str:
        """将色彩描述翻译为中文"""
        translations = {
            'earth tones': '大地色调',
            'bronze': '青铜色',
            'deep reds': '深红色',
            'traditional chinese colors': '传统中国色彩',
            'warm palette': '暖色调',
            'natural color palette': '自然色彩',
            'golden hour colors': '黄金时段色彩'
        }
        
        for en, cn in translations.items():
            if en in colors.lower():
                return cn
        
        return '色彩搭配'
    
    def _translate_style_to_chinese(self, style: str) -> str:
        """将风格标签翻译为中文"""
        translations = {
            'cinematic': '电影级',
            'dramatic': '戏剧性',
            'realistic': '写实',
            'artistic': '艺术性',
            'professional': '专业',
            'detailed': '细致',
            'high quality': '高质量'
        }
        
        for en, cn in translations.items():
            if en in style.lower():
                return cn
        
        return style
    
    def _build_character_consistency_prompt(self, char_features: Dict, consistency_weight: float) -> str:
        """构建角色一致性英文提示词"""
        if not char_features:
            return ""
        
        prompt_parts = []
        
        # 年龄描述
        age = char_features.get('age')
        if age:
            prompt_parts.append(f"{age} years old")
        
        # 体型描述
        build = char_features.get('build')
        if build:
            build_mapping = {
                '瘦弱': 'slim and delicate',
                '苗条': 'slender',
                '匀称': 'well-proportioned',
                '健壮': 'athletic and strong',
                '丰满': 'full-figured',
                '魁梧': 'robust and sturdy'
            }
            prompt_parts.append(build_mapping.get(build, build))
        
        # 服装描述
        clothing = char_features.get('clothing')
        if clothing:
            clothing_mapping = {
                '休闲装': 'casual wear',
                '正装': 'formal attire',
                '运动装': 'sportswear',
                '传统服装': 'traditional clothing',
                '时尚装': 'fashionable outfit',
                '工作服': 'work uniform'
            }
            prompt_parts.append(f"wearing {clothing_mapping.get(clothing, clothing)}")
        
        # 特征描述
        distinctive_features = char_features.get('distinctive_features')
        if distinctive_features:
            # 如果是中文特征，需要翻译
            if any('\u4e00' <= char <= '\u9fff' for char in distinctive_features):
                # 简单的特征翻译映射
                feature_mapping = {
                    '长发': 'long hair',
                    '短发': 'short hair',
                    '卷发': 'curly hair',
                    '直发': 'straight hair',
                    '眼镜': 'glasses',
                    '胡须': 'beard',
                    '微笑': 'smiling',
                    '严肃': 'serious expression'
                }
                translated_features = feature_mapping.get(distinctive_features, distinctive_features)
                prompt_parts.append(translated_features)
            else:
                prompt_parts.append(distinctive_features)
        
        if not prompt_parts:
            return ""
        
        # 根据一致性权重调整描述强度
        if consistency_weight >= 0.8:
            intensity = "highly detailed"
        elif consistency_weight >= 0.6:
            intensity = "detailed"
        else:
            intensity = "subtle"
        
        return f"{intensity} character with {', '.join(prompt_parts)}"
    
    def _build_character_consistency_prompt_chinese(self, char_features: Dict, consistency_weight: float) -> str:
        """构建角色一致性中文提示词"""
        if not char_features:
            return ""
        
        prompt_parts = []
        
        # 年龄描述
        age = char_features.get('age')
        if age:
            prompt_parts.append(f"{age}岁")
        
        # 体型描述
        build = char_features.get('build')
        if build:
            prompt_parts.append(f"{build}体型")
        
        # 服装描述
        clothing = char_features.get('clothing')
        if clothing:
            prompt_parts.append(f"穿着{clothing}")
        
        # 特征描述
        distinctive_features = char_features.get('distinctive_features')
        if distinctive_features:
            prompt_parts.append(distinctive_features)
        
        if not prompt_parts:
            return ""
        
        # 根据一致性权重调整描述强度
        if consistency_weight >= 0.8:
            intensity = "高度细致的"
        elif consistency_weight >= 0.6:
            intensity = "细致的"
        else:
            intensity = "微妙的"
        
        return f"{intensity}角色，{', '.join(prompt_parts)}"
    
    def _fallback_prompt_generation(self, text: str, style: str) -> Dict[str, Any]:
        """降级的提示词生成方法（中英文双语）"""
        
        # 简单的关键词提取（英文）
        keywords_en = []
        keywords_cn = []
        
        # 检测人物
        if '林渊' in text:
            keywords_en.append('young Chinese man')
            keywords_cn.append('年轻中国男子')
        
        # 检测场景
        if '胸甲' in text or '汉' in text:
            keywords_en.append('ancient Chinese armor with Han character')
            keywords_cn.append('刻有汉字的古代中国盔甲')
        
        if '穿越' in text:
            keywords_en.append('time travel realization moment')
            keywords_cn.append('穿越时空的觉醒时刻')
        
        if '青铜剑' in text:
            keywords_en.append('ancient bronze sword')
            keywords_cn.append('古代青铜剑')
        
        if '玉佩' in text:
            keywords_en.append('jade pendant')
            keywords_cn.append('玉佩')
        
        if '展柜' in text:
            keywords_en.append('display case, museum setting')
            keywords_cn.append('展示柜，博物馆环境')
        
        # 检测情绪
        if '突然意识到' in text:
            keywords_en.append('shocked expression, moment of realization')
            keywords_cn.append('震惊表情，觉醒时刻')
        
        if '盯着' in text:
            keywords_en.append('intense gaze, focused attention')
            keywords_cn.append('专注凝视，集中注意力')
        
        # 添加基础质量标签
        keywords_en.extend([
            'cinematic', 'dramatic lighting', 'high quality',
            'detailed', 'masterpiece'
        ])
        keywords_cn.extend([
            '电影级', '戏剧性光照', '高质量',
            '细致入微', '杰作'
        ])
        
        return {
            'generated_prompt': ', '.join(keywords_en),
            'generated_prompt_chinese': '，'.join(keywords_cn),
            'negative_prompt': 'blurry, low quality, distorted, nsfw',
            'negative_prompt_chinese': '模糊，低质量，扭曲，不当内容',
            'scene_description': 'dramatic realization scene',
            'character_info': {'林渊': 'shocked young man'},
            'emotional_tone': 'dramatic surprise',
            'style_keywords': ['cinematic', 'dramatic']
        }