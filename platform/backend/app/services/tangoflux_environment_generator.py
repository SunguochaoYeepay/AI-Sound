"""
TangoFlux环境音生成服务
集成TangoFlux AI生成环境音频，支持批量生成和质量控制
为新的环境音优化流程提供AI生成能力
"""

import logging
import asyncio
import aiohttp
import json
import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from app.models.environment_sound import EnvironmentSound
from app.models.environment_generation import EnvironmentGenerationSession
from sqlalchemy.orm import Session
try:
    from app.config.environment import get_environment_config
except ImportError:
    def get_environment_config():
        return {}

logger = logging.getLogger(__name__)

class GenerationTask:
    """环境音生成任务"""
    def __init__(self, task_id: str, keyword: str, description: str, 
                 duration: float = 30.0, intensity: str = 'medium'):
        self.task_id = task_id
        self.keyword = keyword
        self.description = description
        self.duration = duration
        self.intensity = intensity
        self.status = 'pending'  # pending, generating, completed, failed
        self.progress = 0.0
        self.result_path = None
        self.error_message = None
        self.start_time = None
        self.end_time = None
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'keyword': self.keyword,
            'description': self.description,
            'duration': self.duration,
            'intensity': self.intensity,
            'status': self.status,
            'progress': self.progress,
            'result_path': self.result_path,
            'error_message': self.error_message,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }

class TangoFluxEnvironmentGenerator:
    """TangoFlux环境音生成器"""
    
    def __init__(self):
        try:
            self.config = get_environment_config()
        except:
            # 如果配置失败，使用默认配置
            self.config = {}
        
        # TangoFlux服务配置
        self.tangoflux_url = 'http://localhost:7930'
        self.tangoflux_timeout = 300  # 5分钟超时
        
        if hasattr(self.config, 'get'):
            self.tangoflux_url = self.config.get('TANGOFLUX_API_URL', self.tangoflux_url)
            self.tangoflux_timeout = self.config.get('TANGOFLUX_TIMEOUT', self.tangoflux_timeout)
        elif isinstance(self.config, dict):
            self.tangoflux_url = self.config.get('TANGOFLUX_API_URL', self.tangoflux_url)
            self.tangoflux_timeout = self.config.get('TANGOFLUX_TIMEOUT', self.tangoflux_timeout)
        
        # 生成参数配置
        self.DEFAULT_GENERATION_PARAMS = {
            'num_inference_steps': 100,
            'guidance_scale': 4.5,
            'audio_length_in_s': 30.0,
            'num_waveforms_per_prompt': 1
        }
        
        # 强度级别配置
        self.INTENSITY_CONFIGS = {
            'low': {
                'guidance_scale': 3.0,
                'description_suffix': '，声音轻柔、安静、舒缓'
            },
            'medium': {
                'guidance_scale': 4.5,
                'description_suffix': '，声音清晰、自然、平衡'
            },
            'high': {
                'guidance_scale': 6.0,
                'description_suffix': '，声音强烈、突出、有力'
            }
        }
        
        # 输出目录配置
        env_sounds_dir = 'data/environment_sounds'
        if hasattr(self.config, 'get'):
            env_sounds_dir = self.config.get('ENVIRONMENT_SOUNDS_DIR', env_sounds_dir)
        elif isinstance(self.config, dict):
            env_sounds_dir = self.config.get('ENVIRONMENT_SOUNDS_DIR', env_sounds_dir)
        
        self.output_dir = Path(env_sounds_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 任务跟踪
        self.active_tasks: Dict[str, GenerationTask] = {}
        
        logger.info("[TANGOFLUX_GEN] TangoFlux环境音生成器初始化完成")
        logger.info(f"[TANGOFLUX_GEN] TangoFlux服务地址: {self.tangoflux_url}")
        logger.info(f"[TANGOFLUX_GEN] 输出目录: {self.output_dir}")
    
    async def check_service_health(self) -> bool:
        """检查TangoFlux服务健康状态"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.tangoflux_url}/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("[TANGOFLUX_GEN] TangoFlux服务健康检查通过")
                        return True
                    else:
                        logger.warning(f"[TANGOFLUX_GEN] TangoFlux服务状态异常: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"[TANGOFLUX_GEN] TangoFlux服务健康检查失败: {str(e)}")
            return False
    
    def _generate_task_id(self) -> str:
        """生成任务ID"""
        return f"env_gen_{int(time.time() * 1000)}"
    
    def _build_generation_prompt(self, keyword: str, description: str, intensity: str) -> str:
        """构建生成提示词"""
        intensity_config = self.INTENSITY_CONFIGS.get(intensity, self.INTENSITY_CONFIGS['medium'])
        
        # 基础提示词模板
        base_templates = {
            '雨声': f"Heavy rain falling on leaves and ground, natural rainfall sounds, {keyword}",
            '雷声': f"Thunder rumbling in the distance, natural thunder sounds, {keyword}",
            '风声': f"Wind blowing through trees and leaves, natural wind sounds, {keyword}",
            '鸟鸣': f"Birds singing in a peaceful forest, natural bird sounds, {keyword}",
            '海浪声': f"Ocean waves gently crashing on shore, natural wave sounds, {keyword}",
            '流水声': f"Water flowing in a peaceful stream, natural water sounds, {keyword}",
            '虫鸣': f"Insects chirping in a quiet night, natural insect sounds, {keyword}",
            '脚步声': f"Footsteps walking on different surfaces, human footstep sounds, {keyword}",
            '火焰声': f"Fire crackling in a fireplace, natural fire sounds, {keyword}"
        }
        
        # 获取基础提示词或使用通用模板
        base_prompt = base_templates.get(keyword, f"Natural ambient sound of {keyword}, environmental audio")
        
        # 添加场景描述
        if description and description.strip():
            prompt = f"{base_prompt}, {description}"
        else:
            prompt = base_prompt
        
        # 添加强度描述
        prompt += intensity_config['description_suffix']
        
        logger.info(f"[TANGOFLUX_GEN] 生成提示词: {prompt}")
        return prompt
    
    async def generate_single_environment_sound(self, 
                                              keyword: str, 
                                              description: str = "",
                                              duration: float = 30.0,
                                              intensity: str = 'medium') -> GenerationTask:
        """
        生成单个环境音
        
        Args:
            keyword: 环境音关键词
            description: 场景描述
            duration: 音频时长（秒）
            intensity: 强度级别 (low, medium, high)
            
        Returns:
            生成任务对象
        """
        task_id = self._generate_task_id()
        task = GenerationTask(task_id, keyword, description, duration, intensity)
        self.active_tasks[task_id] = task
        
        logger.info(f"[TANGOFLUX_GEN] 开始生成环境音: {keyword} (任务ID: {task_id})")
        
        try:
            task.status = 'generating'
            task.start_time = datetime.now()
            task.progress = 0.1
            
            # 构建生成参数
            intensity_config = self.INTENSITY_CONFIGS.get(intensity, self.INTENSITY_CONFIGS['medium'])
            prompt = self._build_generation_prompt(keyword, description, intensity)
            
            generation_params = self.DEFAULT_GENERATION_PARAMS.copy()
            generation_params.update({
                'prompt': prompt,
                'audio_length_in_s': duration,
                'guidance_scale': intensity_config['guidance_scale']
            })
            
            task.progress = 0.2
            
            # 调用TangoFlux API
            result_path = await self._call_tangoflux_api(task_id, generation_params, task)
            
            if result_path:
                task.status = 'completed'
                task.result_path = result_path
                task.progress = 1.0
                task.end_time = datetime.now()
                
                logger.info(f"[TANGOFLUX_GEN] 环境音生成完成: {keyword} -> {result_path}")
            else:
                task.status = 'failed'
                task.error_message = "生成失败，未返回结果文件"
                
        except Exception as e:
            task.status = 'failed'
            task.error_message = str(e)
            task.end_time = datetime.now()
            logger.error(f"[TANGOFLUX_GEN] 环境音生成失败: {keyword} - {str(e)}")
        
        return task
    
    async def _call_tangoflux_api(self, task_id: str, params: Dict[str, Any], task: GenerationTask) -> Optional[str]:
        """调用TangoFlux API生成音频"""
        try:
            async with aiohttp.ClientSession() as session:
                # 构建请求数据
                request_data = {
                    'prompt': params['prompt'],
                    'num_inference_steps': params['num_inference_steps'],
                    'guidance_scale': params['guidance_scale'],
                    'audio_length_in_s': params['audio_length_in_s'],
                    'num_waveforms_per_prompt': params['num_waveforms_per_prompt']
                }
                
                task.progress = 0.3
                
                # 发送生成请求
                async with session.post(
                    f"{self.tangoflux_url}/api/v1/audio/generate",
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=self.tangoflux_timeout)
                ) as response:
                    
                    task.progress = 0.7
                    
                    if response.status == 200:
                        # 获取音频数据
                        audio_data = await response.read()
                        
                        # 保存文件
                        timestamp = int(time.time())
                        filename = f"{task.keyword}_{timestamp}.wav"
                        output_path = self.output_dir / filename
                        
                        with open(output_path, 'wb') as f:
                            f.write(audio_data)
                        
                        task.progress = 0.9
                        
                        logger.info(f"[TANGOFLUX_GEN] 音频文件已保存: {output_path}")
                        return str(output_path)
                    else:
                        error_text = await response.text()
                        logger.error(f"[TANGOFLUX_GEN] TangoFlux API错误: {response.status} - {error_text}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error(f"[TANGOFLUX_GEN] 生成超时: {task_id}")
            task.error_message = "生成超时"
            return None
        except Exception as e:
            logger.error(f"[TANGOFLUX_GEN] API调用失败: {str(e)}")
            task.error_message = f"API调用失败: {str(e)}"
            return None
    
    async def batch_generate_environment_sounds(self, 
                                              generation_requests: List[Dict[str, Any]],
                                              max_concurrent: int = 3) -> List[GenerationTask]:
        """
        批量生成环境音
        
        Args:
            generation_requests: 生成请求列表，每个包含keyword, description, duration, intensity
            max_concurrent: 最大并发数
            
        Returns:
            生成任务列表
        """
        logger.info(f"[TANGOFLUX_GEN] 开始批量生成{len(generation_requests)}个环境音")
        
        # 检查服务健康状态
        if not await self.check_service_health():
            logger.error("[TANGOFLUX_GEN] TangoFlux服务不可用，批量生成取消")
            return []
        
        # 创建任务队列
        tasks = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_with_semaphore(request):
            async with semaphore:
                return await self.generate_single_environment_sound(
                    keyword=request.get('keyword', ''),
                    description=request.get('description', ''),
                    duration=request.get('duration', 30.0),
                    intensity=request.get('intensity', 'medium')
                )
        
        # 并发执行生成任务
        generation_tasks = [generate_with_semaphore(req) for req in generation_requests]
        results = await asyncio.gather(*generation_tasks, return_exceptions=True)
        
        # 处理结果
        completed_tasks = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"[TANGOFLUX_GEN] 任务{i}执行异常: {str(result)}")
                # 创建失败任务
                failed_task = GenerationTask(
                    self._generate_task_id(),
                    generation_requests[i].get('keyword', ''),
                    generation_requests[i].get('description', ''),
                    generation_requests[i].get('duration', 30.0),
                    generation_requests[i].get('intensity', 'medium')
                )
                failed_task.status = 'failed'
                failed_task.error_message = str(result)
                completed_tasks.append(failed_task)
            else:
                completed_tasks.append(result)
        
        # 统计结果
        successful = len([task for task in completed_tasks if task.status == 'completed'])
        failed = len([task for task in completed_tasks if task.status == 'failed'])
        
        logger.info(f"[TANGOFLUX_GEN] 批量生成完成: {successful}个成功, {failed}个失败")
        
        return completed_tasks
    
    async def save_generated_sounds_to_database(self, 
                                              generation_tasks: List[GenerationTask],
                                              db: Session,
                                              session_id: Optional[int] = None) -> List[EnvironmentSound]:
        """
        将生成的环境音保存到数据库
        
        Args:
            generation_tasks: 生成任务列表
            db: 数据库会话
            session_id: 关联的生成会话ID
            
        Returns:
            保存的环境音实体列表
        """
        logger.info(f"[TANGOFLUX_GEN] 开始保存{len(generation_tasks)}个生成结果到数据库")
        
        saved_sounds = []
        
        for task in generation_tasks:
            if task.status != 'completed' or not task.result_path:
                continue
                
            try:
                # 创建EnvironmentSound实体
                environment_sound = EnvironmentSound(
                    name=f"{task.keyword}_{int(time.time())}",
                    description=task.description or f"AI生成的{task.keyword}环境音",
                    file_path=task.result_path,
                    duration=task.duration,
                    category="AI生成",
                    tags=[task.keyword, "AI生成", f"强度_{task.intensity}"],
                    volume_level=0.8,
                    fade_in_duration=1.0,
                    fade_out_duration=1.0,
                    loop_enabled=True,
                    is_active=True,
                    status='completed',
                    metadata={
                        'generation_task_id': task.task_id,
                        'generation_prompt': f"{task.keyword} - {task.description}",
                        'generation_intensity': task.intensity,
                        'generation_timestamp': task.start_time.isoformat() if task.start_time else None,
                        'tangoflux_version': '1.0'
                    }
                )
                
                # 关联生成会话
                if session_id:
                    environment_sound.generation_session_id = session_id
                
                db.add(environment_sound)
                db.flush()  # 获取ID但不提交
                
                saved_sounds.append(environment_sound)
                
                logger.info(f"[TANGOFLUX_GEN] 环境音已保存到数据库: {environment_sound.name} (ID: {environment_sound.id})")
                
            except Exception as e:
                logger.error(f"[TANGOFLUX_GEN] 保存环境音失败: {task.keyword} - {str(e)}")
                continue
        
        # 提交所有更改
        try:
            db.commit()
            logger.info(f"[TANGOFLUX_GEN] 成功保存{len(saved_sounds)}个环境音到数据库")
        except Exception as e:
            db.rollback()
            logger.error(f"[TANGOFLUX_GEN] 数据库提交失败: {str(e)}")
            saved_sounds = []
        
        return saved_sounds
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self.active_tasks.get(task_id)
        return task.to_dict() if task else None
    
    def get_all_active_tasks(self) -> List[Dict[str, Any]]:
        """获取所有活动任务状态"""
        return [task.to_dict() for task in self.active_tasks.values()]
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """清理已完成的任务（超过指定小时数）"""
        current_time = datetime.now()
        to_remove = []
        
        for task_id, task in self.active_tasks.items():
            if task.end_time and (current_time - task.end_time).total_seconds() > max_age_hours * 3600:
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.active_tasks[task_id]
        
        if to_remove:
            logger.info(f"[TANGOFLUX_GEN] 清理了{len(to_remove)}个过期任务") 