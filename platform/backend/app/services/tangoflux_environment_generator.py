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
from app.models.environment_generation import EnvironmentGenerationSession, EnvironmentProject
from sqlalchemy.orm import Session
try:
    from app.config.environment import get_environment_config
except ImportError:
    def get_environment_config():
        return {}

# WebSocket管理器导入
try:
    from app.websocket.manager import websocket_manager
except ImportError:
    websocket_manager = None

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
            'num_inference_steps': 150,  # 增加推理步数，提高质量
            'guidance_scale': 7.5,  # 增加引导强度，减少噪音
            'audio_length_in_s': 30.0,
            'num_waveforms_per_prompt': 1
        }
        
        # 强度级别配置
        self.INTENSITY_CONFIGS = {
            'low': {
                'guidance_scale': 6.0,
                'description_suffix': '，声音轻柔、安静、舒缓，低音量背景音'
            },
            'medium': {
                'guidance_scale': 7.5,
                'description_suffix': '，声音清晰、自然、平衡，中等音量环境音'
            },
            'high': {
                'guidance_scale': 9.0,
                'description_suffix': '，声音强烈、突出、有力，高音量环境音'
            }
        }
        
        # 输出目录配置
        env_sounds_dir = 'data/environment_sounds'
        if hasattr(self.config, 'get'):
            env_sounds_dir = self.config.get('ENVIRONMENT_SOUNDS_DIR', env_sounds_dir)
        elif isinstance(self.config, dict):
            env_sounds_dir = self.config.get('ENVIRONMENT_SOUNDS_DIR', env_sounds_dir)
        
        # 使用绝对路径
        if not os.path.isabs(env_sounds_dir):
            # 获取当前工作目录
            current_dir = os.getcwd()
            env_sounds_dir = os.path.join(current_dir, env_sounds_dir)
        
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
    
    def _build_generation_prompt(self, keyword: str, description: str, intensity: str, english_prompt: Optional[str] = None) -> str:
        """构建生成提示词"""
        intensity_config = self.INTENSITY_CONFIGS.get(intensity, self.INTENSITY_CONFIGS['medium'])
        
        # 如果提供了预生成的英文提示词，直接使用
        if english_prompt and english_prompt.strip():
            prompt = english_prompt.strip()
            logger.info(f"[TANGOFLUX_GEN] 使用预生成提示词: {prompt}")
        else:
            # 使用更详细的模板逻辑
            base_templates = {
                '雨声': f"Heavy rain falling on leaves and ground, natural rainfall sounds, environmental ambience, {keyword}",
                '雷声': f"Thunder rumbling in the distance, natural thunder sounds, storm atmosphere, {keyword}",
                '风声': f"Wind blowing through trees and leaves, natural wind sounds, outdoor ambience, {keyword}",
                '鸟鸣': f"Birds singing in a peaceful forest, natural bird sounds, wildlife ambience, {keyword}",
                '海浪声': f"Ocean waves gently crashing on shore, natural wave sounds, beach ambience, {keyword}",
                '流水声': f"Water flowing in a peaceful stream, natural water sounds, river ambience, {keyword}",
                '虫鸣': f"Insects chirping in a quiet night, natural insect sounds, night ambience, {keyword}",
                '脚步声': f"Footsteps walking on different surfaces, human footstep sounds, indoor ambience, {keyword}",
                '火焰声': f"Fire crackling in a fireplace, natural fire sounds, warm ambience, {keyword}",
                '嗡鸣': f"Gentle humming sound, mechanical background noise, quiet ambience, {keyword}",
                '叮': f"Light bell sound, gentle chime, peaceful ambience, {keyword}",
                '开门声': f"Door opening and closing, wooden door creak, indoor ambience, {keyword}",
                '娇喝声': f"Shout or call sound, human voice, outdoor ambience, {keyword}"
            }
            
            # 获取基础提示词或使用通用模板
            base_prompt = base_templates.get(keyword, f"Natural ambient sound of {keyword}, environmental audio, peaceful atmosphere")
            
            # 添加场景描述
            if description and description.strip():
                prompt = f"{base_prompt}, {description}"
            else:
                prompt = base_prompt
            
            logger.info(f"[TANGOFLUX_GEN] 使用模板提示词: {prompt}")
        
        # 添加强度描述
        prompt += intensity_config['description_suffix']
        
        logger.info(f"[TANGOFLUX_GEN] 最终提示词: {prompt}")
        return prompt
    
    async def generate_single_environment_sound(self, 
                                              keyword: str, 
                                              description: str = "",
                                              duration: float = 30.0,
                                              intensity: str = 'medium',
                                              english_prompt: Optional[str] = None) -> GenerationTask:
        """
        生成单个环境音
        
        Args:
            keyword: 环境音关键词
            description: 场景描述
            duration: 音频时长（秒）
            intensity: 强度级别 (low, medium, high)
            english_prompt: 预生成的英文提示词
            
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
            prompt = self._build_generation_prompt(keyword, description, intensity, english_prompt)
            
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
                        # 获取JSON响应
                        response_text = await response.text()
                        logger.info(f"[TANGOFLUX_GEN] 收到响应: {len(response_text)} 字符")
                        
                        try:
                            # 解析JSON响应
                            response_data = json.loads(response_text)
                            
                            # 检查是否包含音频数据
                            if 'audio_base64' not in response_data:
                                logger.error(f"[TANGOFLUX_GEN] 响应中没有audio_base64字段: {task_id}")
                                task.error_message = "响应中没有音频数据"
                                return None
                            
                            # 解码base64音频数据
                            import base64
                            audio_base64 = response_data['audio_base64']
                            audio_data = base64.b64decode(audio_base64)
                            
                            logger.info(f"[TANGOFLUX_GEN] 解码音频数据: {len(audio_data)} 字节")
                            
                            # 验证音频数据
                            if not audio_data or len(audio_data) == 0:
                                logger.error(f"[TANGOFLUX_GEN] 音频数据为空: {task_id}")
                                task.error_message = "音频数据为空"
                                return None
                            
                            # 保存文件
                            timestamp = int(time.time())
                            # 修复文件名编码问题：清理关键词中的特殊字符
                            safe_keyword = "".join(c for c in task.keyword if c.isalnum() or c in (' ', '-', '_')).strip()
                            if not safe_keyword:
                                safe_keyword = "environment_sound"
                            filename = f"{safe_keyword}_{timestamp}.wav"
                            output_path = self.output_dir / filename
                            
                            # 确保输出目录存在
                            self.output_dir.mkdir(parents=True, exist_ok=True)
                            
                            # 保存文件
                            with open(output_path, 'wb') as f:
                                f.write(audio_data)
                            
                            # 验证文件是否成功保存
                            if not output_path.exists():
                                logger.error(f"[TANGOFLUX_GEN] 文件保存失败: {output_path}")
                                task.error_message = "文件保存失败"
                                return None
                            
                            # 验证文件大小
                            actual_size = output_path.stat().st_size
                            if actual_size != len(audio_data):
                                logger.warning(f"[TANGOFLUX_GEN] 文件大小不匹配: 期望{len(audio_data)}, 实际{actual_size}")
                            
                            task.progress = 0.9
                            
                            logger.info(f"[TANGOFLUX_GEN] 音频文件已保存: {output_path} ({actual_size} 字节)")
                            return str(output_path)
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"[TANGOFLUX_GEN] JSON解析失败: {str(e)}")
                            task.error_message = f"JSON解析失败: {str(e)}"
                            return None
                        except Exception as e:
                            logger.error(f"[TANGOFLUX_GEN] 处理响应失败: {str(e)}")
                            task.error_message = f"处理响应失败: {str(e)}"
                            return None
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
                    intensity=request.get('intensity', 'medium'),
                    english_prompt=request.get('english_prompt', None)  # 添加英文提示词
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
                                              session_id: Optional[int] = None,
                                              project_id: Optional[int] = None,
                                              track_mapping: Optional[Dict[int, int]] = None,
                                              chapter_id: Optional[str] = None) -> List[EnvironmentSound]:
        """
        将生成的环境音保存到数据库
        
        Args:
            generation_tasks: 生成任务列表
            db: 数据库会话
            session_id: 生成会话ID
            project_id: 环境音项目ID
            track_mapping: 轨道映射 {track_index: task_index}
        """
        saved_sounds = []
        
        for task in generation_tasks:
            if task.status != 'completed' or not task.result_path:
                continue
                
            try:
                # 获取轨道索引
                track_index = None
                if track_mapping:
                    for track_idx, task_idx in track_mapping.items():
                        if task_idx == generation_tasks.index(task):
                            track_index = track_idx
                            break
                
                # 获取文件大小
                file_size = None
                if task.result_path and os.path.exists(task.result_path):
                    try:
                        file_size = os.path.getsize(task.result_path)
                        logger.info(f"[TANGOFLUX_GEN] 文件大小: {file_size} 字节")
                    except Exception as size_error:
                        logger.warning(f"[TANGOFLUX_GEN] 获取文件大小失败: {str(size_error)}")
                
                # 创建EnvironmentSound实体
                environment_sound = EnvironmentSound(
                    name=f"{task.keyword}_{int(time.time())}",
                    prompt=f"{task.keyword} - {task.description}",
                    description=task.description or f"AI生成的{task.keyword}环境音",
                    file_path=task.result_path,
                    file_size=file_size,  # 设置文件大小
                    duration=task.duration,
                    tags=[task.keyword, "AI生成", f"强度_{task.intensity}"],
                    generation_status='completed',
                    is_active=True,
                    # 新增项目关联字段
                    environment_project_id=project_id,
                    track_index=track_index,
                    novel_project_id=session_id,  # 使用session_id作为novel_project_id
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
            # 更新项目生成状态
            if project_id:
                await self._update_project_generation_status(db, project_id, saved_sounds, chapter_id)
            
            # 提交所有更改
            db.commit()
            logger.info(f"[TANGOFLUX_GEN] 成功保存{len(saved_sounds)}个环境音到数据库")
                
        except Exception as e:
            db.rollback()
            logger.error(f"[TANGOFLUX_GEN] 数据库提交失败: {str(e)}")
            saved_sounds = []
        
        return saved_sounds
    
    async def _update_project_generation_status(self, db: Session, project_id: int, saved_sounds: List[EnvironmentSound], chapter_id: str = None):
        """更新项目生成状态"""
        try:
            from app.models.environment_generation import EnvironmentProject
            
            env_project = db.query(EnvironmentProject).filter(EnvironmentProject.id == project_id).first()
            if not env_project:
                logger.warning(f"[TANGOFLUX_GEN] 未找到环境音项目: {project_id}")
                return
            
            # 更新项目状态
            env_project.generation_count = len(saved_sounds)
            env_project.updated_at = datetime.utcnow()
            
            # 更新轨道状态 - 支持多章节格式
            if env_project.analysis_result:
                analysis_result = env_project.analysis_result
                
                # 检查是否是多章节格式（键是章节ID）
                if isinstance(analysis_result, dict) and not analysis_result.get('environment_tracks'):
                    # 多章节格式，需要找到对应的轨道
                    logger.info(f"[TANGOFLUX_GEN] 处理多章节格式的分析结果")
                    
                    # 收集所有章节的轨道，按全局索引更新
                    all_tracks = []
                    chapter_track_mapping = {}  # 记录每个轨道属于哪个章节
                    
                    for current_chapter_id, chapter_data in analysis_result.items():
                        if isinstance(chapter_data, dict) and chapter_data.get('environment_tracks'):
                            chapter_tracks = chapter_data['environment_tracks']
                            start_index = len(all_tracks)
                            
                            for i, track in enumerate(chapter_tracks):
                                all_tracks.append(track)
                                chapter_track_mapping[start_index + i] = current_chapter_id
                    
                    # 更新轨道状态
                    if chapter_id:
                        # 多章节项目，只更新指定章节的轨道
                        if chapter_id in analysis_result:
                            chapter_tracks = analysis_result[chapter_id]['environment_tracks']
                            for sound in saved_sounds:
                                if sound.track_index is not None and sound.track_index < len(chapter_tracks):
                                    track = chapter_tracks[sound.track_index]
                                    track['generated_sound_id'] = sound.id
                                    track['generation_status'] = 'completed'
                                    track['generated_file_path'] = sound.file_path
                                    
                                    logger.info(f"[TANGOFLUX_GEN] 更新章节{chapter_id}轨道 {sound.track_index} 状态: {sound.file_path}")
                        else:
                            logger.warning(f"[TANGOFLUX_GEN] 未找到章节 {chapter_id}")
                    else:
                        # 单章节项目，使用全局索引更新
                        for sound in saved_sounds:
                            if sound.track_index is not None and sound.track_index < len(all_tracks):
                                track = all_tracks[sound.track_index]
                                track['generated_sound_id'] = sound.id
                                track['generation_status'] = 'completed'
                                track['generated_file_path'] = sound.file_path
                                
                                logger.info(f"[TANGOFLUX_GEN] 更新轨道 {sound.track_index} 状态: {sound.file_path}")
                else:
                    # 单章节格式，直接更新environment_tracks
                    tracks = analysis_result.get('environment_tracks', [])
                    for sound in saved_sounds:
                        if sound.track_index is not None and sound.track_index < len(tracks):
                            tracks[sound.track_index]['generated_sound_id'] = sound.id
                            tracks[sound.track_index]['generation_status'] = 'completed'
                            tracks[sound.track_index]['generated_file_path'] = sound.file_path
                    
                    analysis_result['environment_tracks'] = tracks
                
                # 更新项目的分析结果
                env_project.analysis_result = analysis_result
                
                # 强制标记JSON字段为已修改
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(env_project, "analysis_result")
                
                # 强制刷新数据库会话
                db.flush()
                
                # 添加调试日志
                logger.info(f"[TANGOFLUX_GEN] 更新后的analysis_result类型: {type(env_project.analysis_result)}")
                if isinstance(env_project.analysis_result, dict) and '830' in env_project.analysis_result:
                    chapter_830 = env_project.analysis_result['830']
                    if isinstance(chapter_830, dict) and 'environment_tracks' in chapter_830:
                        tracks = chapter_830['environment_tracks']
                        logger.info(f"[TANGOFLUX_GEN] 章节830轨道数量: {len(tracks)}")
                        for i, track in enumerate(tracks):
                            logger.info(f"[TANGOFLUX_GEN] 轨道{i} 生成路径: {track.get('generated_file_path')}")
            
            logger.info(f"[TANGOFLUX_GEN] 项目 {project_id} 生成状态已更新")
            
        except Exception as e:
            logger.error(f"[TANGOFLUX_GEN] 更新项目状态失败: {str(e)}")
            import traceback
            logger.error(f"[TANGOFLUX_GEN] 错误堆栈: {traceback.format_exc()}")
    
    async def check_existing_environment_sound(self, 
                                             keyword: str, 
                                             db: Session,
                                             duration_tolerance: float = 5.0) -> Optional[Any]:
        """
        检查音乐库中是否已存在相同的环境音
        
        Args:
            keyword: 环境音关键词
            db: 数据库会话
            duration_tolerance: 时长容差（秒）
            
        Returns:
            如果找到匹配的环境音则返回EnvironmentSound对象，否则返回None
        """
        try:
            from app.models.environment_sound import EnvironmentSound
            
            # 查找包含该关键词的环境音
            existing_sounds = db.query(EnvironmentSound).filter(
                EnvironmentSound.is_active == True,
                EnvironmentSound.generation_status == 'completed'
            ).all()
            
            for sound in existing_sounds:
                # 检查标签中是否包含该关键词
                if sound.tags and keyword in sound.tags:
                    logger.info(f"[REUSE_CHECK] 找到已存在的环境音: {sound.name} (ID: {sound.id})")
                    return sound
                
                # 检查名称中是否包含关键词
                if keyword in sound.name:
                    logger.info(f"[REUSE_CHECK] 通过名称匹配找到环境音: {sound.name} (ID: {sound.id})")
                    return sound
                    
                # 检查提示词中是否包含关键词
                if sound.prompt and keyword in sound.prompt:
                    logger.info(f"[REUSE_CHECK] 通过提示词匹配找到环境音: {sound.name} (ID: {sound.id})")
                    return sound
            
            logger.info(f"[REUSE_CHECK] 未找到匹配的环境音: {keyword}")
            return None
            
        except Exception as e:
            logger.error(f"[REUSE_CHECK] 检查已存在环境音失败: {str(e)}")
            return None
    
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
    
    def _detect_track_format(self, track: Dict[str, Any]) -> str:
        """检测轨道数据格式类型"""
        if 'environment_keywords' in track:
            return 'environment_analysis'  # 环境音分析结果格式
        elif 'type' in track and track.get('type') == '环境音效':
            return 'audio_storyboard'      # 音频制作卡格式
        else:
            return 'unknown'               # 未知格式
    
    async def _generate_english_prompt(self, chinese_description: str, scene_context: Dict[str, Any] = None) -> str:
        """使用AI生成英文提示词 - 带场景上下文"""
        try:
            if scene_context:
                location = scene_context.get('location', '')
                time = scene_context.get('time', '')
                atmosphere = scene_context.get('atmosphere', '')
                
                prompt = f"""
                将以下中文环境音描述翻译为英文提示词，用于AI音频生成：
                
                环境音：{chinese_description}
                场景：{location}
                时间：{time}
                氛围：{atmosphere}
                
                请生成详细的英文提示词，包含场景、时间、氛围等上下文信息。
                """
            else:
                prompt = f"将以下中文环境音描述翻译为英文提示词，用于AI音频生成：{chinese_description}"
            
            # 调用LLM API（使用现有的LLM客户端）
            from app.services.storyboard_analysis.llm_client import LLMClient
            llm_client = LLMClient()
            response = await llm_client.call(prompt)
            
            # 提取生成的英文提示词
            english_prompt = response.strip()
            
            logger.info(f"[TANGOFLUX_GEN] 生成英文提示词: {chinese_description} -> {english_prompt}")
            return english_prompt
            
        except Exception as e:
            logger.error(f"[TANGOFLUX_GEN] 生成英文提示词失败: {e}")
            # 返回默认英文提示词
            return f"Ambient sound: {chinese_description}"
    
    def _volume_to_intensity(self, volume: int) -> str:
        """从音量推导强度级别"""
        if volume <= 30:
            return 'low'
        elif volume <= 50:
            return 'medium'
        else:
            return 'high'
    
    async def _convert_track_to_generation_request(self, track: Dict[str, Any], scene_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """转换轨道数据为生成请求 - 支持两种格式"""
        
        format_type = self._detect_track_format(track)
        
        if format_type == 'environment_analysis':
            # 环境音分析结果格式
            keyword = track.get('environment_keywords', [''])[0] if track.get('environment_keywords') else ''
            description = track.get('chinese_description', '')
            english_prompt = track.get('english_prompt', '')
            duration = track.get('duration', 30.0)
            intensity = track.get('intensity_level', 'medium')
            
        elif format_type == 'audio_storyboard':
            # 音频制作卡格式
            keyword = track.get('description', '')
            description = track.get('description', '')
            english_prompt = await self._generate_english_prompt(keyword, scene_context)
            duration = track.get('end_time', 30) - track.get('start_time', 0)
            intensity = self._volume_to_intensity(track.get('volume', 40))
            
        else:
            # 默认处理
            keyword = track.get('description', '')
            description = track.get('description', '')
            english_prompt = await self._generate_english_prompt(keyword)
            duration = track.get('duration', 30.0)
            intensity = 'medium'
        
        return {
            'keyword': keyword,
            'description': description,
            'duration': duration,
            'intensity': intensity,
            'english_prompt': english_prompt
        }
    
    async def generate_project_environment_sounds(self, 
                                                project_id: int,
                                                tracks_to_generate: List[tuple],
                                                task_id: str,
                                                chapter_id: str = None,
                                                scene_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        为项目生成环境音文件
        
        Args:
            project_id: 项目ID
            tracks_to_generate: 要生成的轨道列表，每个元素为(index, track_data)
            task_id: 任务ID
            chapter_id: 章节ID（可选，用于多章节项目）
            
        Returns:
            生成结果字典
        """
        logger.info(f"[TANGOFLUX_GEN] 开始为项目{project_id}生成环境音，轨道数量: {len(tracks_to_generate)}")
        
        try:
            # 检查服务健康状态
            if not await self.check_service_health():
                logger.error("[TANGOFLUX_GEN] TangoFlux服务不可用，生成取消")
                return {
                    "success": False,
                    "error": "TangoFlux服务不可用"
                }
            
            # 转换轨道数据为生成请求
            generation_requests = []
            for index, track in tracks_to_generate:
                try:
                    request = await self._convert_track_to_generation_request(track, scene_context)
                    generation_requests.append(request)
                    logger.info(f"[TANGOFLUX_GEN] 转换轨道数据: {track.get('description', 'unknown')} -> {request['keyword']}")
                except Exception as e:
                    logger.error(f"[TANGOFLUX_GEN] 转换轨道数据失败: {e}")
                    continue
            
            if not generation_requests:
                raise ValueError("没有有效的轨道数据可生成")
            
            # 批量生成环境音
            generation_tasks = await self.batch_generate_environment_sounds(
                generation_requests=generation_requests,
                max_concurrent=3
            )
            
            # 保存生成的环境音到数据库，包含项目关联信息
            from app.services.environment_project_service import EnvironmentProjectService
            from app.database import SessionLocal
            
            db = SessionLocal()
            try:
                logger.info(f"[TANGOFLUX_GEN] 开始保存生成结果到数据库，项目ID: {project_id}")
                
                # 构建轨道映射 - 如果指定了章节ID，使用章节内索引
                if chapter_id:
                    # 多章节项目，使用章节内索引
                    track_mapping = {index: i for i, (index, _) in enumerate(tracks_to_generate)}
                    logger.info(f"[TANGOFLUX_GEN] 多章节项目，章节ID: {chapter_id}，轨道映射: {track_mapping}")
                else:
                    # 单章节项目，使用全局索引
                    track_mapping = {index: i for i, (index, _) in enumerate(tracks_to_generate)}
                    logger.info(f"[TANGOFLUX_GEN] 单章节项目，轨道映射: {track_mapping}")
                
                # 保存到数据库，包含项目关联
                saved_sounds = await self.save_generated_sounds_to_database(
                    generation_tasks=generation_tasks,
                    db=db,
                    session_id=project_id,  # 使用项目ID作为session_id
                    project_id=project_id,
                    track_mapping=track_mapping,
                    chapter_id=chapter_id  # 传递章节ID
                )
                
                logger.info(f"[TANGOFLUX_GEN] 成功保存{len(saved_sounds)}个环境音到数据库")
                
                # 更新项目中的轨道文件路径
                env_service = EnvironmentProjectService(db)
                
                # 使用新的统一查找方法
                env_project = env_service.get_by_project_id(project_id)
                logger.info(f"[TANGOFLUX_GEN] 项目查找结果: {env_project.id if env_project else 'None'}")
                
                logger.info(f"[TANGOFLUX_GEN] 最终获取到环境音项目: {env_project.id if env_project else 'None'}")
                
                if env_project and env_project.analysis_result:
                    # 处理多章节格式的分析结果
                    analysis_result = env_project.analysis_result
                    environment_tracks = []
                    
                    # 检查是否是多章节格式（键是章节ID）
                    if isinstance(analysis_result, dict) and not analysis_result.get('environment_tracks'):
                        # 多章节格式，收集所有章节的环境轨道
                        # 按章节ID数字顺序排序，确保轨道顺序一致
                        sorted_chapter_ids = sorted(analysis_result.keys(), key=lambda x: int(x))
                        for chapter_id in sorted_chapter_ids:
                            chapter_analysis = analysis_result[chapter_id]
                            if isinstance(chapter_analysis, dict) and chapter_analysis.get('environment_tracks'):
                                environment_tracks.extend(chapter_analysis['environment_tracks'])
                    else:
                        # 单章节格式，直接获取environment_tracks
                        environment_tracks = analysis_result.get('environment_tracks', [])
                    
                    logger.info(f"[TANGOFLUX_GEN] 找到环境轨道数量: {len(environment_tracks)}")
                    
                    # 更新轨道文件路径和关联信息
                    # 多章节格式已经在_update_project_generation_status中处理了
                    # 这里只需要处理单章节格式
                    if not isinstance(analysis_result, dict) or analysis_result.get('environment_tracks'):
                        for i, (index, track) in enumerate(tracks_to_generate):
                            if i < len(generation_tasks) and generation_tasks[i].status == 'completed':
                                if index < len(environment_tracks):
                                    environment_tracks[index]['generated_file_path'] = generation_tasks[i].result_path
                                    environment_tracks[index]['generation_status'] = 'completed'
                                    environment_tracks[index]['generation_task_id'] = task_id
                                    
                                    # 添加数据库记录关联
                                    if i < len(saved_sounds):
                                        environment_tracks[index]['generated_sound_id'] = saved_sounds[i].id
                                
                                # 通过WebSocket推送单个轨道完成消息
                                logger.info(f"[TANGOFLUX_GEN] 准备推送轨道完成消息: 轨道{index}, websocket_manager={websocket_manager is not None}")
                                if websocket_manager:
                                    try:
                                        message_data = {
                                            "type": "environment_generation_progress",
                                            "data": {
                                                "task_id": task_id,
                                                "project_id": project_id,
                                                "track_index": index,  # 使用真实的轨道索引
                                                "status": "completed",
                                                "file_path": generation_tasks[i].result_path,
                                                "sound_id": saved_sounds[i].id if i < len(saved_sounds) else None,
                                                "message": f"轨道 {index} 生成完成"
                                            }
                                        }
                                        logger.info(f"[TANGOFLUX_GEN] 推送WebSocket消息: {message_data}")
                                        await websocket_manager.broadcast_message(message_data)
                                        logger.info(f"[TANGOFLUX_GEN] WebSocket推送轨道完成消息成功: 轨道{index}")
                                    except Exception as ws_error:
                                        logger.warning(f"[TANGOFLUX_GEN] WebSocket推送失败: {str(ws_error)}")
                                else:
                                    logger.warning(f"[TANGOFLUX_GEN] websocket_manager为None，跳过WebSocket推送")
                    
                    # 保存更新后的分析结果
                    # 多章节格式已经在_update_project_generation_status中处理了
                    # 这里只需要处理单章节格式
                    if not isinstance(analysis_result, dict) or analysis_result.get('environment_tracks'):
                        # 单章节格式，直接更新
                        logger.info(f"[TANGOFLUX_GEN] 单章节格式，直接更新轨道数据")
                        analysis_result['environment_tracks'] = environment_tracks
                    
                    # 保存前检查数据
                    logger.info(f"[TANGOFLUX_GEN] 保存前检查分析结果:")
                    if isinstance(analysis_result, dict):
                        for key, value in analysis_result.items():
                            if isinstance(value, dict) and 'environment_tracks' in value:
                                tracks_with_path = [t for t in value['environment_tracks'] if t.get('generated_file_path')]
                                logger.info(f"[TANGOFLUX_GEN] 章节{key}: 总轨道数{len(value['environment_tracks'])}, 有生成路径的轨道数{len(tracks_with_path)}")
                    
                    env_project.analysis_result = analysis_result
                    db.commit()
                    
                    logger.info(f"[TANGOFLUX_GEN] 项目{project_id}环境音生成完成，更新了{len(tracks_to_generate)}个轨道")
                    
                    # 通过WebSocket推送整体完成消息
                    logger.info(f"[TANGOFLUX_GEN] 准备推送整体完成消息: 任务{task_id}, websocket_manager={websocket_manager is not None}")
                    if websocket_manager:
                        try:
                            message_data = {
                                "type": "environment_generation_progress",
                                "data": {
                                    "task_id": task_id,
                                    "project_id": project_id,
                                    "status": "completed",
                                    "total_tracks": len(tracks_to_generate),
                                    "completed_tracks": len([t for t in generation_tasks if t.status == 'completed']),
                                    "saved_sounds_count": len(saved_sounds),
                                    "message": f"环境音生成完成，共 {len(tracks_to_generate)} 个轨道，已保存 {len(saved_sounds)} 个音频记录"
                                }
                            }
                            logger.info(f"[TANGOFLUX_GEN] 推送整体完成WebSocket消息: {message_data}")
                            await websocket_manager.broadcast_message(message_data)
                            logger.info(f"[TANGOFLUX_GEN] WebSocket推送整体完成消息成功: 任务{task_id}")
                        except Exception as ws_error:
                            logger.warning(f"[TANGOFLUX_GEN] WebSocket推送失败: {str(ws_error)}")
                    else:
                        logger.warning(f"[TANGOFLUX_GEN] websocket_manager为None，跳过整体完成WebSocket推送")
                
            except Exception as e:
                logger.error(f"[TANGOFLUX_GEN] 更新项目轨道失败: {str(e)}")
                db.rollback()
                
                # 推送错误消息
                if websocket_manager:
                    try:
                        await websocket_manager.broadcast_message({
                            "type": "environment_generation_progress",
                            "data": {
                                "task_id": task_id,
                                "project_id": project_id,
                                "status": "failed",
                                "error": str(e),
                                "message": "环境音生成失败"
                            }
                        })
                    except Exception as ws_error:
                        logger.warning(f"[TANGOFLUX_GEN] WebSocket推送失败: {str(ws_error)}")
            finally:
                db.close()
            
            # 统计结果
            successful = len([task for task in generation_tasks if task.status == 'completed'])
            failed = len([task for task in generation_tasks if task.status == 'failed'])
            
            return {
                "success": True,
                "task_id": task_id,
                "project_id": project_id,
                "total_tracks": len(tracks_to_generate),
                "successful_tracks": successful,
                "failed_tracks": failed,
                "message": f"环境音生成完成: {successful}个成功, {failed}个失败"
            }
            
        except Exception as e:
            logger.error(f"[TANGOFLUX_GEN] 项目环境音生成失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            } 