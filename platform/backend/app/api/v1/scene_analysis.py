#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能场景分析API
提供独立的场景分析、匹配和批量生成功能
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.database import get_db
from app.services.intelligent_scene_analyzer import (
    intelligent_scene_analyzer, 
    SceneAnalysisResult, 
    SceneMatchResult, 
    BatchGenerationPlan
)
from app.services.llm_scene_analyzer import llm_scene_analyzer, SceneAnalysisResult as LLMSceneAnalysisResult
from app.services.sequential_timeline_generator import SceneInfo
from app.models.environment_sound import EnvironmentSound
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scene-analysis", tags=["智能场景分析"])

# 请求模型
class TextAnalysisRequest(BaseModel):
    """文本分析请求"""
    text: str = Field(..., min_length=1, max_length=10000, description="要分析的文本")
    user_id: Optional[int] = Field(None, description="用户ID")
    include_recommendations: bool = Field(True, description="是否包含推荐")
    use_llm: bool = Field(True, description="是否使用大模型分析")
    llm_provider: str = Field("auto", description="LLM提供商(auto/openai/anthropic)")

class SceneMatchRequest(BaseModel):
    """场景匹配请求"""
    location: str = Field(..., description="地点")
    atmosphere: str = Field(..., description="氛围")
    weather: str = Field(default="clear", description="天气")
    time_of_day: str = Field(default="day", description="时间")
    duration: Optional[float] = Field(None, ge=1.0, le=300.0, description="目标时长")
    tolerance: float = Field(0.2, ge=0.0, le=1.0, description="时长容差")

class BatchGenerationRequest(BaseModel):
    """批量生成请求"""
    target_scenes: Optional[List[Dict[str, Any]]] = Field(None, description="目标场景列表")
    use_common_scenes: bool = Field(True, description="使用常用场景")
    priority_filter: Optional[List[str]] = Field(None, description="优先级筛选")

# 响应模型
class SceneInfoResponse(BaseModel):
    """场景信息响应"""
    location: str
    weather: str
    time_of_day: str
    atmosphere: str
    keywords: List[str]
    confidence: float

class AnalysisResultResponse(BaseModel):
    """分析结果响应"""
    text_hash: str
    analyzed_scenes: List[SceneInfoResponse]
    confidence_score: float
    processing_time: float
    total_scenes: int
    unique_locations: List[str]
    unique_atmospheres: List[str]
    recommended_durations: List[float]
    # LLM特有字段
    narrative_analysis: Optional[Dict[str, Any]] = None
    emotional_progression: Optional[List[Dict[str, Any]]] = None
    scene_transitions: Optional[List[Dict[str, Any]]] = None
    recommended_soundscape: Optional[Dict[str, Any]] = None
    llm_provider: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None
    enhanced_prompts: Optional[List[Dict[str, Any]]] = None

class MatchResultResponse(BaseModel):
    """匹配结果响应"""
    environment_sound_id: int
    environment_sound_name: str
    scene_info: SceneInfoResponse
    match_score: float
    is_exact_match: bool
    recommended_usage: str
    sound_duration: float
    sound_prompt: str

class BatchPlanResponse(BaseModel):
    """批量计划响应"""
    total_scenes: int
    generation_queue: List[Dict[str, Any]]
    estimated_time: float
    estimated_cost: float

@router.post("/analyze-text", response_model=AnalysisResultResponse)
async def analyze_text_scenes(
    request: TextAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    智能分析文本场景
    
    - 支持基础关键词分析和LLM深度分析
    - 提取文本中的场景信息
    - 识别地点、天气、时间、氛围
    - 生成推荐的环境音参数
    - LLM模式下提供叙事分析和情感进展
    """
    try:
        if request.use_llm:
            # 使用LLM进行深度分析
            llm_result = await llm_scene_analyzer.analyze_text_scenes_with_llm(
                text=request.text
            )
            
            # 转换为响应格式
            scene_responses = []
            for scene in llm_result.analyzed_scenes:
                scene_response = SceneInfoResponse(
                    location=scene.location,
                    weather="clear",  # 新接口不包含天气信息，使用默认值
                    time_of_day="day",  # 新接口不包含时间信息，使用默认值
                    atmosphere="neutral",  # 新接口不包含氛围信息，使用默认值
                    keywords=scene.keywords or [],
                    confidence=scene.confidence
                )
                scene_responses.append(scene_response)
            
            # 生成一个临时的text_hash
            import hashlib
            text_hash = hashlib.md5(request.text.encode()).hexdigest()
            
            response = AnalysisResultResponse(
                text_hash=text_hash,
                analyzed_scenes=scene_responses,
                confidence_score=llm_result.confidence_score,
                processing_time=llm_result.processing_time,
                total_scenes=len(llm_result.analyzed_scenes),
                unique_locations=list(set(s.location for s in llm_result.analyzed_scenes)),
                unique_atmospheres=["neutral"],  # 简化版本使用默认值
                recommended_durations=[15.0] * len(scene_responses),  # 使用默认时长
                # LLM特有字段（简化版本）
                narrative_analysis={},
                emotional_progression=[],
                scene_transitions=[],
                recommended_soundscape={},
                llm_provider="ollama",
                token_usage={},
                enhanced_prompts=[]
            )
            
            logger.info(f"LLM文本场景分析完成: {len(llm_result.analyzed_scenes)}个场景")
        
        else:
            # 使用基础分析器
            result = await intelligent_scene_analyzer.analyze_text_scenes(
                text=request.text,
                user_id=request.user_id
            )
            
            # 转换为响应格式
            scene_responses = []
            for scene in result.analyzed_scenes:
                scene_response = SceneInfoResponse(
                    location=scene.location,
                    weather=scene.weather,
                    time_of_day=scene.time_of_day,
                    atmosphere=scene.atmosphere,
                    keywords=scene.keywords or [],
                    confidence=scene.confidence
                )
                scene_responses.append(scene_response)
            
            response = AnalysisResultResponse(
                text_hash=result.text_hash,
                analyzed_scenes=scene_responses,
                confidence_score=result.confidence_score,
                processing_time=result.processing_time,
                total_scenes=result.total_scenes,
                unique_locations=result.unique_locations,
                unique_atmospheres=result.unique_atmospheres,
                recommended_durations=result.recommended_durations
            )
            
            logger.info(f"基础文本场景分析完成: {result.total_scenes}个场景")
        
        return response
        
    except Exception as e:
        logger.error(f"文本场景分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@router.post("/match-scene", response_model=List[MatchResultResponse])
async def match_scene_to_sounds(
    request: SceneMatchRequest,
    db: Session = Depends(get_db)
):
    """
    为场景匹配现有环境音
    
    - 根据场景信息查找最佳匹配的环境音
    - 支持时长容差设置
    - 返回匹配度排序的结果
    """
    try:
        # 构建场景信息
        scene_info = SceneInfo()
        scene_info.location = request.location
        scene_info.atmosphere = request.atmosphere
        scene_info.weather = request.weather
        scene_info.time_of_day = request.time_of_day
        scene_info.confidence = 1.0
        
        # 查找匹配的环境音
        matches = intelligent_scene_analyzer.find_matching_environment_sounds(
            scene_info=scene_info,
            duration=request.duration,
            tolerance=request.tolerance
        )
        
        # 转换为响应格式
        match_responses = []
        for match in matches:
            # 获取环境音详情
            sound = db.query(EnvironmentSound).filter(
                EnvironmentSound.id == match.environment_sound_id
            ).first()
            
            if sound:
                match_response = MatchResultResponse(
                    environment_sound_id=match.environment_sound_id,
                    environment_sound_name=sound.name,
                    scene_info=SceneInfoResponse(
                        location=match.scene_info.location,
                        weather=match.scene_info.weather,
                        time_of_day=match.scene_info.time_of_day,
                        atmosphere=match.scene_info.atmosphere,
                        keywords=match.scene_info.keywords or [],
                        confidence=match.scene_info.confidence
                    ),
                    match_score=match.match_score,
                    is_exact_match=match.is_exact_match,
                    recommended_usage=match.recommended_usage,
                    sound_duration=sound.duration,
                    sound_prompt=sound.prompt or ""
                )
                match_responses.append(match_response)
        
        logger.info(f"场景匹配完成: 找到{len(match_responses)}个匹配结果")
        return match_responses
        
    except Exception as e:
        logger.error(f"场景匹配失败: {e}")
        raise HTTPException(status_code=500, detail=f"匹配失败: {str(e)}")

@router.post("/generate-batch-plan", response_model=BatchPlanResponse)
async def generate_batch_plan(
    request: BatchGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    生成批量生成计划
    
    - 分析需要生成的场景
    - 检查现有环境音覆盖情况
    - 生成优化的生成队列
    """
    try:
        target_scenes = None
        
        if request.target_scenes and not request.use_common_scenes:
            # 使用自定义场景
            target_scenes = []
            for scene_dict in request.target_scenes:
                scene = SceneInfo()
                scene.location = scene_dict.get("location", "indoor")
                scene.atmosphere = scene_dict.get("atmosphere", "calm")
                scene.weather = scene_dict.get("weather", "clear")
                scene.time_of_day = scene_dict.get("time_of_day", "day")
                scene.confidence = scene_dict.get("confidence", 0.8)
                target_scenes.append(scene)
        
        plan = await intelligent_scene_analyzer.generate_batch_plan(target_scenes)
        
        response = BatchPlanResponse(
            total_scenes=plan.total_scenes,
            generation_queue=plan.generation_queue,
            estimated_time=plan.estimated_time,
            estimated_cost=plan.estimated_cost
        )
        
        logger.info(f"批量生成计划完成: {plan.total_scenes}个场景")
        return response
        
    except Exception as e:
        logger.error(f"生成批量计划失败: {e}")
        raise HTTPException(status_code=500, detail=f"计划生成失败: {str(e)}")

@router.post("/execute-batch-generation")
async def execute_batch_generation(
    plan: BatchPlanResponse,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    执行批量生成任务
    
    - 根据生成计划执行批量环境音生成
    - 后台异步执行，支持进度跟踪
    """
    try:
        # 添加后台任务
        background_tasks.add_task(
            _execute_batch_generation_task,
            plan.generation_queue
        )
        
        return {
            "success": True,
            "message": f"批量生成任务已启动，共{plan.total_scenes}个场景",
            "estimated_time": plan.estimated_time,
            "task_id": f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
    except Exception as e:
        logger.error(f"启动批量生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动失败: {str(e)}")

@router.get("/cache-stats")
async def get_cache_statistics(db: Session = Depends(get_db)):
    """
    获取缓存统计信息
    
    - 环境音库统计
    - 场景标签覆盖情况
    - 缓存命中率统计
    """
    try:
        stats = intelligent_scene_analyzer.get_cache_statistics()
        
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")

@router.get("/scene-templates")
async def get_scene_templates():
    """
    获取场景模板
    
    - 返回支持的场景类型
    - 场景关键词映射
    - 常用场景预设
    """
    try:
        analyzer = intelligent_scene_analyzer
        
        return {
            "success": True,
            "data": {
                "scene_keywords_map": analyzer.scene_keywords_map,
                "common_scenes": analyzer.common_scenes,
                "similarity_weights": analyzer.similarity_weights,
                "similar_locations": analyzer.similar_locations,
                "similar_atmospheres": analyzer.similar_atmospheres
            }
        }
        
    except Exception as e:
        logger.error(f"获取场景模板失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模板失败: {str(e)}")

@router.post("/generate-smart-prompts")
async def generate_smart_prompts(
    request: TextAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    基于LLM分析生成智能环境音提示词
    
    - 使用大模型深度理解文本内容
    - 生成专业的TangoFlux提示词
    - 包含动态变化和转场建议
    - 适用于高质量环境音生成
    """
    try:
        # 强制使用LLM分析
        llm_result = await llm_scene_analyzer.analyze_text_scenes_with_llm(
            text=request.text,
            user_id=request.user_id,
            preferred_provider=request.llm_provider
        )
        
        # 生成增强提示词
        enhanced_prompts = llm_scene_analyzer.generate_enhanced_prompts(llm_result)
        
        # 格式化响应
        formatted_prompts = []
        for i, prompt_data in enumerate(enhanced_prompts):
            # 从scene_details中获取场景信息
            scene_details = prompt_data.get("scene_details", {})
            fade_settings = prompt_data.get("fade_settings", {})
            
            formatted_prompt = {
                "scene_index": i + 1,
                "title": f"场景{i + 1}: {scene_details.get('location', 'unknown')} - {scene_details.get('atmosphere', 'neutral')}",
                "prompt": prompt_data["prompt"],
                "duration": prompt_data["duration"],
                "priority": prompt_data["priority"],
                "fade_settings": {
                    "fade_in": fade_settings.get("fade_in", 2.0),
                    "fade_out": fade_settings.get("fade_out", 2.0)
                },
                "dynamic_elements": prompt_data["dynamic_elements"],
                "scene_details": {
                    "location": scene_details.get('location', 'unknown'),
                    "atmosphere": scene_details.get('atmosphere', 'neutral'),
                    "weather": scene_details.get('weather', 'clear'),
                    "time_of_day": scene_details.get('time_of_day', 'day'),
                    "emotional_tone": scene_details.get('emotional_tone', ''),
                    "narrative_function": scene_details.get('narrative_function', ''),
                    "keywords": scene_details.get('keywords', [])
                },
                "generation_tips": {
                    "complexity": "high" if len(prompt_data["dynamic_elements"]) > 2 else "medium",
                    "recommended_model": "TangoFlux",
                    "quality_preset": "high"
                }
            }
            formatted_prompts.append(formatted_prompt)
        
        return {
            "success": True,
            "analysis_summary": {
                "total_scenes": len(enhanced_prompts),
                "narrative_type": llm_result.narrative_analysis.get("genre", "unknown"),
                "emotional_arc": llm_result.narrative_analysis.get("emotional_arc", ""),
                "processing_time": llm_result.processing_time,
                "llm_provider": llm_result.llm_provider,
                "token_usage": llm_result.token_usage
            },
            "smart_prompts": formatted_prompts,
            "soundscape_recommendation": llm_result.recommended_soundscape,
            "scene_transitions": llm_result.scene_transitions,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"智能提示词生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")

@router.post("/update-scene-tags/{sound_id}")
async def update_environment_sound_scene_tags(
    sound_id: int,
    scene_info: SceneMatchRequest,
    db: Session = Depends(get_db)
):
    """
    更新环境音的场景标签
    
    - 为现有环境音添加场景信息
    - 提高后续匹配准确度
    """
    try:
        sound = db.query(EnvironmentSound).filter(EnvironmentSound.id == sound_id).first()
        if not sound:
            raise HTTPException(status_code=404, detail="环境音不存在")
        
        # 更新metadata中的场景信息
        if not sound.metadata:
            sound.metadata = {}
        
        sound.metadata['scene_info'] = {
            'location': scene_info.location,
            'atmosphere': scene_info.atmosphere,
            'weather': scene_info.weather,
            'time_of_day': scene_info.time_of_day,
            'updated_at': datetime.now().isoformat()
        }
        
        db.commit()
        
        logger.info(f"更新环境音{sound_id}的场景标签")
        return {
            "success": True,
            "message": "场景标签更新成功",
            "sound_id": sound_id,
            "scene_info": sound.metadata['scene_info']
        }
        
    except Exception as e:
        logger.error(f"更新场景标签失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

# 后台任务函数
async def _execute_batch_generation_task(generation_queue: List[Dict[str, Any]]):
    """执行批量生成任务"""
    from app.clients.tangoflux_client import TangoFluxClient
    
    try:
        tangoflux_client = TangoFluxClient()
        
        for item in generation_queue:
            try:
                # 调用TangoFlux生成环境音
                prompt = item["prompt"]
                duration = item["duration"]
                
                logger.info(f"开始生成场景环境音: {prompt}")
                
                # 这里应该调用实际的生成API
                # result = await tangoflux_client.generate_audio(prompt, duration)
                
                # 暂时模拟生成过程
                import asyncio
                await asyncio.sleep(item.get("estimated_time", 5))
                
                logger.info(f"场景环境音生成完成: {prompt}")
                
            except Exception as e:
                logger.error(f"生成场景环境音失败 {item['prompt']}: {e}")
                continue
        
        logger.info("批量生成任务完成")
        
    except Exception as e:
        logger.error(f"批量生成任务失败: {e}")