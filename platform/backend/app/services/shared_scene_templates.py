#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共享场景模板库
提供统一的场景关键词映射和基础提示词模板
供智能场景分析、环境音导入、合成中心等多个服务复用
"""

from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class SceneTemplateConfig:
    """场景模板配置"""
    use_detailed_prompts: bool = False      # 是否使用详细提示词
    include_quality_suffix: bool = True     # 是否包含质量后缀
    enable_dynamic_elements: bool = False   # 是否启用动态元素
    target_application: str = "general"     # 目标应用: general/environment/synthesis/llm

class SharedSceneTemplates:
    """共享场景模板库"""
    
    def __init__(self):
        # 🎯 核心关键词映射 - 所有服务共享
        self.scene_keywords_map = {
            # 地点类别
            "房间": {"location": "indoor", "keywords": ["room", "indoor", "house"]},
            "室内": {"location": "indoor", "keywords": ["indoor", "room", "building"]},
            "户外": {"location": "outdoor", "keywords": ["outdoor", "nature", "open"]},
            "森林": {"location": "forest", "keywords": ["forest", "trees", "nature", "woods"]},
            "城市": {"location": "city", "keywords": ["city", "urban", "traffic", "street"]},
            "海边": {"location": "beach", "keywords": ["ocean", "waves", "beach", "seaside"]},
            "大海": {"location": "beach", "keywords": ["ocean", "waves", "sea", "water"]},
            "海": {"location": "beach", "keywords": ["ocean", "waves", "sea", "water"]},
            "山": {"location": "mountain", "keywords": ["mountain", "wind", "echo", "highland"]},
            "街道": {"location": "street", "keywords": ["street", "traffic", "footsteps", "road"]},
            "咖啡厅": {"location": "cafe", "keywords": ["cafe", "coffee", "chatter", "urban"]},
            "公园": {"location": "park", "keywords": ["park", "nature", "outdoor", "peaceful"]},
            "学校": {"location": "school", "keywords": ["school", "classroom", "indoor", "learning"]},
            "医院": {"location": "hospital", "keywords": ["hospital", "medical", "indoor", "quiet"]},
            "商场": {"location": "mall", "keywords": ["mall", "shopping", "indoor", "crowd"]},
            "地铁": {"location": "subway", "keywords": ["subway", "train", "underground", "transit"]},
            
            # 天气类别
            "雨": {"weather": "rainy", "keywords": ["rain", "water", "drops", "wet"]},
            "雷": {"weather": "stormy", "keywords": ["thunder", "storm", "lightning"]},
            "风": {"weather": "windy", "keywords": ["wind", "breeze", "air"]},
            "雪": {"weather": "snowy", "keywords": ["snow", "winter", "cold"]},
            "雾": {"weather": "foggy", "keywords": ["fog", "mist", "cloudy"]},
            
            # 时间类别
            "夜": {"time_of_day": "night", "keywords": ["night", "crickets", "quiet", "dark"]},
            "晚": {"time_of_day": "evening", "keywords": ["evening", "sunset", "dusk"]},
            "早": {"time_of_day": "morning", "keywords": ["morning", "birds", "dawn"]},
            "午": {"time_of_day": "noon", "keywords": ["noon", "midday", "bright"]},
            "黄昏": {"time_of_day": "dusk", "keywords": ["dusk", "twilight", "golden"]},
            "拂晓": {"time_of_day": "dawn", "keywords": ["dawn", "sunrise", "awakening"]},
            
            # 氛围类别
            "紧张": {"atmosphere": "tense", "keywords": ["tense", "suspense", "dramatic"]},
            "恐怖": {"atmosphere": "scary", "keywords": ["scary", "horror", "dark", "ominous"]},
            "浪漫": {"atmosphere": "romantic", "keywords": ["romantic", "soft", "gentle", "intimate"]},
            "战斗": {"atmosphere": "action", "keywords": ["action", "battle", "intense", "dynamic"]},
            "安静": {"atmosphere": "calm", "keywords": ["calm", "peaceful", "serene", "tranquil"]},
            "神秘": {"atmosphere": "mysterious", "keywords": ["mysterious", "enigmatic", "unknown"]},
            "欢乐": {"atmosphere": "joyful", "keywords": ["joyful", "happy", "cheerful", "uplifting"]},
            "悲伤": {"atmosphere": "sad", "keywords": ["sad", "melancholic", "somber", "mournful"]},
        }
        
        # 🎨 基础环境描述模板 - 所有服务共享
        self.base_location_templates = {
            "indoor": "indoor atmosphere",
            "outdoor": "outdoor ambience", 
            "forest": "forest environment",
            "city": "urban environment",
            "beach": "oceanic soundscape",
            "mountain": "mountain atmosphere",
            "desert": "arid desert ambience",
            "village": "peaceful village sounds",
            "castle": "medieval castle atmosphere",
            "cafe": "cozy cafe ambience",
            "park": "park atmosphere",
            "school": "classroom environment",
            "hospital": "medical facility ambience",
            "mall": "shopping center sounds",
            "subway": "underground transit ambience"
        }
        
        self.base_weather_templates = {
            "rainy": "with gentle rain",
            "stormy": "with dramatic storm",
            "windy": "with strong wind",
            "snowy": "with soft snow",
            "foggy": "with mysterious fog",
            "sunny": "with bright sunlight",
            "cloudy": "with overcast sky"
        }
        
        self.base_time_templates = {
            "morning": "morning ambience",
            "day": "daytime atmosphere",
            "evening": "evening sounds",
            "night": "nighttime ambience",
            "dawn": "dawn atmosphere",
            "dusk": "dusk ambience"
        }
        
        self.base_atmosphere_templates = {
            "calm": "peaceful mood",
            "tense": "suspenseful atmosphere",
            "romantic": "intimate feeling",
            "mysterious": "enigmatic mood",
            "scary": "ominous atmosphere",
            "joyful": "cheerful mood",
            "sad": "melancholic tone",
            "action": "intense atmosphere"
        }
        
        # 🚀 详细提示词模板 - 用于精确控制
        self.detailed_templates = {
            # 地点组合模板
            "indoor_calm": "soft indoor ambience, gentle air conditioning hum, peaceful room tone",
            "indoor_tense": "tense indoor atmosphere, subtle creaking sounds, dramatic silence",
            "outdoor_day": "outdoor daytime ambience, gentle breeze, distant nature sounds",
            "outdoor_night": "night outdoor ambience, cricket sounds, soft wind through trees",
            "forest_calm": "peaceful forest ambience, birds chirping, leaves rustling gently",
            "forest_tense": "dense forest with dramatic wind, ominous tree creaking",
            "city_day": "busy urban daytime, distant traffic, city life sounds",
            "city_night": "nighttime city ambience, distant traffic, urban quietness",
            "beach_calm": "gentle ocean waves, seabird calls, peaceful coastal atmosphere",
            "beach_stormy": "powerful ocean waves, storm winds, dramatic coastal weather",
            
            # 天气特效模板
            "rainy_gentle": "soft rain falling, water droplets, peaceful rain atmosphere",
            "rainy_heavy": "heavy rain pouring, storm intensity, dramatic weather",
            "stormy_dramatic": "thunderstorm with lightning, dramatic thunder rolls, intense rain",
            "windy_gentle": "gentle breeze blowing, soft air movement",
            "windy_strong": "strong wind gusts, dramatic air movement, atmospheric power",
            
            # 氛围特化模板
            "romantic_soft": "romantic soft ambience, gentle warm atmosphere, intimate setting",
            "action_intense": "intense action atmosphere, dramatic tension, suspenseful ambience",
            "scary_dark": "dark and ominous atmosphere, eerie sounds, horror ambience",
            "mysterious_enigmatic": "mysterious and enigmatic ambience, unknown elements"
        }
        
        # 📈 质量后缀模板
        self.quality_suffixes = {
            "general": "ambient sound, natural recording",
            "cinematic": "cinematic quality, high fidelity audio",
            "immersive": "immersive soundscape, 3D audio experience",
            "professional": "professional audio quality, studio recording",
            "atmospheric": "atmospheric design, environmental storytelling"
        }
        
        # 🎭 动态元素库
        self.dynamic_elements = {
            "rain": ["rain_intensity_changes", "water_droplets", "puddle_splash"],
            "storm": ["thunder_rolls", "lightning_cracks", "wind_gusts"],
            "forest": ["bird_calls", "rustling_leaves", "branch_creaks"],
            "city": ["car_horns", "footsteps", "door_slams"],
            "ocean": ["wave_crashes", "seagull_cries", "wind_over_water"],
            "tension": ["heartbeat", "breathing", "dramatic_pauses"],
            "action": ["impact_sounds", "motion_effects", "intensity_builds"]
        }
    
    def build_prompt(self, scene_info, config: SceneTemplateConfig = None) -> str:
        """
        构建场景提示词
        
        Args:
            scene_info: 场景信息对象
            config: 模板配置
            
        Returns:
            构建的提示词
        """
        if config is None:
            config = SceneTemplateConfig()
        
        prompt_parts = []
        
        # 1. 选择基础模板
        if config.use_detailed_prompts:
            # 尝试精确匹配组合模板
            template_key = f"{scene_info.location}_{scene_info.atmosphere}"
            if template_key in self.detailed_templates:
                prompt_parts.append(self.detailed_templates[template_key])
            else:
                # 组合基础模板
                location_desc = self.base_location_templates.get(scene_info.location, f"{scene_info.location} environment")
                atmosphere_desc = self.base_atmosphere_templates.get(scene_info.atmosphere, f"{scene_info.atmosphere} mood")
                prompt_parts.append(f"{location_desc}, {atmosphere_desc}")
        else:
            # 使用简单基础模板
            location_desc = self.base_location_templates.get(scene_info.location, f"{scene_info.location} environment")
            prompt_parts.append(location_desc)
        
        # 2. 添加天气效果
        if scene_info.weather != "clear":
            if config.use_detailed_prompts:
                weather_key = f"{scene_info.weather}_{scene_info.atmosphere}"
                if weather_key in self.detailed_templates:
                    weather_desc = self.detailed_templates[weather_key]
                else:
                    weather_desc = self.base_weather_templates.get(scene_info.weather, f"with {scene_info.weather}")
            else:
                weather_desc = self.base_weather_templates.get(scene_info.weather, f"with {scene_info.weather}")
            
            prompt_parts.append(weather_desc)
        
        # 3. 添加时间特征
        if scene_info.time_of_day != "day":
            time_desc = self.base_time_templates.get(scene_info.time_of_day, f"{scene_info.time_of_day} time")
            prompt_parts.append(time_desc)
        
        # 4. 添加动态元素（如果启用）
        if config.enable_dynamic_elements:
            elements = []
            for key in [scene_info.location, scene_info.weather, scene_info.atmosphere]:
                if key in self.dynamic_elements:
                    elements.extend(self.dynamic_elements[key][:2])  # 最多2个动态元素
            
            if elements:
                prompt_parts.append(f"with {', '.join(elements)}")
        
        # 5. 组合提示词
        base_prompt = ", ".join(prompt_parts)
        
        # 6. 添加质量后缀（如果启用）
        if config.include_quality_suffix:
            quality_level = "cinematic" if config.use_detailed_prompts else "general"
            if config.target_application == "llm":
                quality_level = "immersive"
            elif config.target_application == "synthesis":
                quality_level = "professional"
            
            quality_suffix = self.quality_suffixes.get(quality_level, "high quality audio")
            base_prompt = f"{base_prompt}, {quality_suffix}"
        
        return base_prompt
    
    def get_scene_keywords(self, text: str) -> List[str]:
        """
        从文本中提取场景关键词
        
        Args:
            text: 输入文本
            
        Returns:
            关键词列表
        """
        keywords = []
        for keyword, scene_data in self.scene_keywords_map.items():
            if keyword in text:
                keywords.extend(scene_data.get("keywords", []))
        return list(set(keywords))  # 去重
    
    def get_scene_attributes(self, text: str) -> Dict[str, str]:
        """
        从文本中提取场景属性
        
        Args:
            text: 输入文本
            
        Returns:
            场景属性字典
        """
        attributes = {
            "location": "indoor",
            "weather": "clear", 
            "time_of_day": "day",
            "atmosphere": "calm"
        }
        
        for keyword, scene_data in self.scene_keywords_map.items():
            if keyword in text:
                for attr_type in ["location", "weather", "time_of_day", "atmosphere"]:
                    if attr_type in scene_data:
                        attributes[attr_type] = scene_data[attr_type]
        
        return attributes
    
    def get_template_config_for_app(self, app_name: str) -> SceneTemplateConfig:
        """
        获取特定应用的模板配置
        
        Args:
            app_name: 应用名称 (environment/synthesis/llm)
            
        Returns:
            模板配置对象
        """
        configs = {
            "environment": SceneTemplateConfig(
                use_detailed_prompts=False,
                include_quality_suffix=True,
                enable_dynamic_elements=False,
                target_application="environment"
            ),
            "synthesis": SceneTemplateConfig(
                use_detailed_prompts=True,
                include_quality_suffix=True,
                enable_dynamic_elements=True,
                target_application="synthesis"
            ),
            "llm": SceneTemplateConfig(
                use_detailed_prompts=True,
                include_quality_suffix=True,
                enable_dynamic_elements=True,
                target_application="llm"
            )
        }
        
        return configs.get(app_name, SceneTemplateConfig())


# 全局共享实例
shared_scene_templates = SharedSceneTemplates() 