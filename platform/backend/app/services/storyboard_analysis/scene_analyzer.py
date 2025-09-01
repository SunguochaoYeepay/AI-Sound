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
            logger.info("开始场景分析...")
            
            # 强制使用AI分析，不进行健康检查
            chunks = self._chunk_content(content)
            logger.info(f"内容分块数量: {len(chunks)}")
            all_scenes = []
            
            for i, chunk in enumerate(chunks):
                logger.info(f"分析场景块 {i+1}/{len(chunks)}")
                logger.info(f"块内容长度: {len(chunk)}")
                
                # 构建提示词
                prompt = self._build_prompt(chunk, chunk_index=i, total_chunks=len(chunks))
                
                # 强制调用AI分析
                logger.info("调用AI分析...")
                result = await self._call_llm_json(prompt, temperature=0.3)
                
                if result and "scenes" in result:
                    scenes = result["scenes"]
                    logger.info(f"AI识别到 {len(scenes)} 个场景")
                    # 为每个场景添加块索引信息
                    for scene in scenes:
                        scene["chunk_index"] = i
                        scene["chunk_total"] = len(chunks)
                    all_scenes.extend(scenes)
                else:
                    logger.error(f"AI分析失败，返回结果: {result}")
                    raise Exception(f"AI分析失败，无法获取场景数据")
            
            # 合并和去重场景
            merged_scenes = self._merge_scenes(all_scenes)
            
            logger.info(f"场景分析完成，识别到 {len(merged_scenes)} 个场景")
            for i, scene in enumerate(merged_scenes):
                logger.info(f"场景 {i+1}: {scene.get('scene_name', 'Unknown')}")
            
            return merged_scenes
            
        except Exception as e:
            logger.error(f"场景分析失败: {str(e)}")
            raise Exception(f"场景分析失败: {str(e)}")
    
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
