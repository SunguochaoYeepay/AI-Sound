#!/usr/bin/env python3
"""
场景分析器
使用AI分析小说中的场景信息
"""

import logging
from typing import Dict, Any, List, Optional

from .base_analyzer import BaseAnalyzer
from .prompts.scene_prompts import SCENE_ANALYSIS_PROMPT, SCENE_ANALYSIS_PROMPT_SIMPLE

logger = logging.getLogger(__name__)


class SceneAnalyzer(BaseAnalyzer):
    """场景分析器"""
    
    async def analyze(self, content: str, **kwargs) -> List[Dict[str, Any]]:
        """分析场景"""
        if not self._validate_content(content):
            return []
        
        try:
            # 检查AI服务是否可用
            if not self.llm_client.health_check():
                logger.warning("AI服务不可用，使用规则分析")
                return self._rule_based_analysis(content)
            
            # 分块处理长内容
            chunks = self._chunk_content(content)
            all_scenes = []
            
            for i, chunk in enumerate(chunks):
                logger.info(f"分析场景块 {i+1}/{len(chunks)}")
                
                # 构建提示词
                prompt = self._build_prompt(chunk, chunk_index=i, total_chunks=len(chunks))
                
                # 调用AI分析
                result = await self._call_llm_json(prompt, temperature=0.3)
                
                if result and "scenes" in result:
                    scenes = result["scenes"]
                    # 为每个场景添加块索引信息
                    for scene in scenes:
                        scene["chunk_index"] = i
                        scene["chunk_total"] = len(chunks)
                    all_scenes.extend(scenes)
                else:
                    logger.warning(f"场景块 {i+1} 分析失败，使用规则分析")
                    rule_scenes = self._rule_based_analysis(chunk)
                    for scene in rule_scenes:
                        scene["chunk_index"] = i
                        scene["chunk_total"] = len(chunks)
                    all_scenes.extend(rule_scenes)
            
            # 合并和去重场景
            merged_scenes = self._merge_scenes(all_scenes)
            
            logger.info(f"场景分析完成，识别到 {len(merged_scenes)} 个场景")
            return merged_scenes
            
        except Exception as e:
            logger.error(f"场景分析失败: {str(e)}")
            return self._rule_based_analysis(content)
    
    def _build_prompt(self, content: str, **kwargs) -> str:
        """构建提示词"""
        chunk_index = kwargs.get("chunk_index", 0)
        total_chunks = kwargs.get("total_chunks", 1)
        
        if total_chunks > 1:
            # 多块处理时的提示词
            prompt = f"""
这是第 {chunk_index + 1}/{total_chunks} 块内容，请分析其中的场景：

{content}

注意：这是章节的一部分，请专注于当前块中的场景，不要重复前面块的内容。
"""
            return prompt + SCENE_ANALYSIS_PROMPT_SIMPLE.format(content=content)
        else:
            # 单块处理
            return SCENE_ANALYSIS_PROMPT.format(content=content)
    
    def _rule_based_analysis(self, content: str) -> List[Dict[str, Any]]:
        """规则分析（AI不可用时的备选方案）"""
        scenes = []
        
        # 简单的关键词匹配
        if "实验室" in content or "穿越" in content:
            scenes.append({
                "scene_name": "实验室穿越场景",
                "scene_type": "特殊",
                "location": {"type": "实验室", "description": "现代实验室环境"},
                "atmosphere": {"mood": "紧张", "lighting": "明亮"},
                "time_period": "现代",
                "environmental_sounds": ["玻璃破碎声", "电流声"]
            })
        
        if "长安" in content or "古代" in content:
            scenes.append({
                "scene_name": "古代街道场景",
                "scene_type": "室外",
                "location": {"type": "街道", "description": "古代城市街道"},
                "atmosphere": {"mood": "热闹", "lighting": "自然光"},
                "time_period": "古代",
                "environmental_sounds": ["叫卖声", "马蹄声", "人声"]
            })
        
        if "救助" in content or "骨折" in content:
            scenes.append({
                "scene_name": "救助场景",
                "scene_type": "室外",
                "location": {"type": "街道", "description": "救助现场"},
                "atmosphere": {"mood": "紧张", "lighting": "自然光"},
                "time_period": "古代",
                "environmental_sounds": ["马蹄声", "人声", "布料摩擦声"]
            })
        
        return scenes
    
    def _merge_scenes(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并和去重场景"""
        if not scenes:
            return []
        
        # 简单的去重逻辑：基于场景名称
        seen_names = set()
        merged = []
        
        for scene in scenes:
            scene_name = scene.get("scene_name", "")
            if scene_name and scene_name not in seen_names:
                seen_names.add(scene_name)
                merged.append(scene)
        
        return merged
