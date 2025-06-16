"""
语音合成任务管理服务
处理语音合成任务的创建、执行、监控等功能
"""

import os
import json
import asyncio
import aiofiles
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models import (
    SynthesisTask, NovelProject, BookChapter, 
    AnalysisResult, TextSegment, AudioFile, VoiceProfile
)
from ..exceptions import ServiceException, TTSException
from ..utils.websocket_manager import ProgressWebSocketManager
from ..utils.path_manager import get_path_manager, get_storage_path
from ..tts_client import get_tts_client
import logging

logger = logging.getLogger(__name__)


class SynthesisTaskManager:
    """合成任务管理器"""
    
    def __init__(self, db: Session, websocket_manager: ProgressWebSocketManager):
        self.db = db
        self.websocket_manager = websocket_manager
        self.tts_client = get_tts_client()
        self.path_manager = get_path_manager()
        
    async def create_task(
        self,
        project_id: int,
        analysis_result_id: int = None,
        chapter_id: int = None,
        synthesis_plan: Dict[str, Any] = None,
        batch_size: int = 10
    ) -> SynthesisTask:
        """创建新的合成任务"""
        
        # 验证项目存在
        project = self.db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise ServiceException("项目不存在")
        
        # 获取合成计划
        if analysis_result_id:
            result = self.db.query(AnalysisResult).filter(AnalysisResult.id == analysis_result_id).first()
            if not result:
                raise ServiceException("分析结果不存在")
            synthesis_plan = result.final_config or result.synthesis_plan
            chapter_id = result.chapter_id
        
        if not synthesis_plan:
            raise ServiceException("缺少合成计划配置")
        
        # 统计需要合成的段落数量
        total_segments = 0
        if chapter_id:
            # 单章节合成
            total_segments = self.db.query(TextSegment).filter(
                and_(
                    TextSegment.project_id == project_id,
                    TextSegment.id.in_(
                        self.db.query(TextSegment.id).join(BookChapter).filter(
                            BookChapter.id == chapter_id
                        )
                    )
                )
            ).count()
        else:
            # 全项目合成
            total_segments = self.db.query(TextSegment).filter(
                TextSegment.project_id == project_id
            ).count()
        
        # 创建任务
        task = SynthesisTask(
            project_id=project_id,
            analysis_result_id=analysis_result_id,
            chapter_id=chapter_id,
            synthesis_plan=synthesis_plan,
            batch_size=batch_size,
            total_segments=total_segments,
            status="pending"
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    async def start_task(self, task_id: int) -> bool:
        """启动合成任务"""
        task = self.db.query(SynthesisTask).filter(SynthesisTask.id == task_id).first()
        if not task:
            raise ServiceException("任务不存在")
        
        if task.status != "pending":
            raise ServiceException(f"任务状态不正确: {task.status}")
        
        # 更新任务状态
        task.status = "running"
        task.started_at = datetime.utcnow()
        self.db.commit()
        
        # 异步启动合成任务
        asyncio.create_task(self._run_synthesis_task(task))
        
        return True
    
    async def _run_synthesis_task(self, task: SynthesisTask):
        """执行合成任务主逻辑"""
        try:
            # 获取需要合成的文本段落
            segments_query = self.db.query(TextSegment).filter(
                TextSegment.project_id == task.project_id
            )
            
            if task.chapter_id:
                # 获取指定章节的段落
                segments_query = segments_query.join(BookChapter).filter(
                    BookChapter.id == task.chapter_id
                )
            
            segments = segments_query.order_by(TextSegment.segment_order).all()
            
            if not segments:
                raise ServiceException("没有找到需要合成的文本段落")
            
            # 解析声音映射配置
            voice_mapping = self._parse_voice_mapping(task.synthesis_plan)
            
            # 批量处理段落
            batch_size = task.batch_size
            completed = 0
            output_files = []
            
            for i in range(0, len(segments), batch_size):
                batch_segments = segments[i:i + batch_size]
                
                # 并发处理本批次段落
                batch_tasks = [
                    self._synthesize_segment(task, segment, voice_mapping)
                    for segment in batch_segments
                ]
                
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # 处理结果
                for j, result in enumerate(batch_results):
                    segment = batch_segments[j]
                    completed += 1
                    
                    if isinstance(result, Exception):
                        # 记录失败的段落
                        failed_segments = json.loads(task.failed_segments or "[]")
                        failed_segments.append({
                            "segment_id": segment.id,
                            "error": str(result),
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        task.failed_segments = json.dumps(failed_segments)
                        
                        await self._send_progress_update(
                            task, completed, f"段落 {segment.id} 合成失败: {str(result)}"
                        )
                    else:
                        # 成功完成
                        task.completed_segments += 1
                        output_files.append(result)
                        
                        await self._send_progress_update(
                            task, completed, f"段落 {segment.id} 合成完成"
                        )
                    
                    # 更新数据库
                    task.current_segment = segment.id
                    self.db.commit()
                
                # 批次间休息
                if i + batch_size < len(segments):
                    await asyncio.sleep(1)
            
            # 合并音频文件（如果需要）
            if task.synthesis_plan.get("merge_audio", True):
                final_audio_path = await self._merge_audio_files(task, output_files)
                task.final_audio_path = final_audio_path
            
            # 更新任务状态
            task.output_files = json.dumps(output_files)
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            task.processing_time = int((task.completed_at - task.started_at).total_seconds())
            
            await self._send_progress_update(task, completed, "合成任务完成")
            
        except Exception as e:
            # 处理全局错误
            task.status = "failed"
            task.error_message = str(e)
            task.retry_count += 1
            
            # 判断是否需要重试
            if task.retry_count <= task.max_retries:
                logger.warning(f"合成任务失败，准备重试 (第{task.retry_count}次): {str(e)}")
                await asyncio.sleep(5)  # 等待5秒后重试
                task.status = "pending"
                await self.start_task(task.id)
            else:
                logger.error(f"合成任务最终失败: {str(e)}")
                await self._send_progress_update(task, task.completed_segments, f"任务失败: {str(e)}")
        
        finally:
            self.db.commit()
    
    def _parse_voice_mapping(self, synthesis_plan: Dict[str, Any]) -> Dict[str, int]:
        """解析声音映射配置"""
        voice_mapping = {}
        
        # 从合成计划中提取角色声音映射
        characters = synthesis_plan.get("characters", [])
        for character in characters:
            character_name = character.get("name")
            voice_id = character.get("voice_id")
            if character_name and voice_id:
                voice_mapping[character_name] = voice_id
        
        # 添加默认声音
        default_voice_id = synthesis_plan.get("default_voice_id")
        if default_voice_id:
            voice_mapping["__default__"] = default_voice_id
        
        return voice_mapping
    
    async def _synthesize_segment(
        self, 
        task: SynthesisTask, 
        segment: TextSegment, 
        voice_mapping: Dict[str, int]
    ) -> Dict[str, Any]:
        """合成单个文本段落"""
        try:
            # 确定使用的声音
            voice_id = voice_mapping.get(segment.detected_speaker) or voice_mapping.get("__default__")
            if not voice_id:
                raise TTSException(f"无法为段落 {segment.id} 找到合适的声音")
            
            # 获取声音配置
            voice_profile = self.db.query(VoiceProfile).filter(VoiceProfile.id == voice_id).first()
            if not voice_profile:
                raise TTSException(f"声音配置 {voice_id} 不存在")
            
            # 验证声音文件是否存在
            file_validation = voice_profile.validate_files()
            if not file_validation['valid']:
                missing_files = ', '.join(file_validation['missing_files'])
                raise TTSException(f"声音文件不存在: {missing_files}")
            
            # 调用TTS服务
            audio_result = await self.tts_client.synthesize_text(
                text=segment.text_content,
                voice_profile=voice_profile,
                parameters=task.synthesis_plan.get("synthesis_params", {})
            )
            
            # 保存音频文件记录
            audio_file = AudioFile(
                filename=audio_result["filename"],
                original_name=f"segment_{segment.id}_{segment.detected_speaker or 'unknown'}.wav",
                file_path=audio_result["file_path"],
                file_size=audio_result["file_size"],
                duration=audio_result.get("duration", 0),
                project_id=task.project_id,
                segment_id=segment.id,
                voice_profile_id=voice_id,
                text_content=segment.text_content,
                audio_type="segment",
                processing_time=audio_result.get("processing_time"),
                model_used=audio_result.get("model_used"),
                parameters=json.dumps(task.synthesis_plan.get("synthesis_params", {}))
            )
            
            self.db.add(audio_file)
            
            # 更新段落状态
            segment.status = "completed"
            segment.audio_file_path = audio_result["file_path"]
            segment.processing_time = audio_result.get("processing_time")
            
            self.db.commit()
            
            return {
                "segment_id": segment.id,
                "audio_file_id": audio_file.id,
                "file_path": audio_result["file_path"],
                "duration": audio_result.get("duration", 0)
            }
            
        except Exception as e:
            # 更新段落错误状态
            segment.status = "failed"
            segment.error_message = str(e)
            self.db.commit()
            
            raise TTSException(f"段落 {segment.id} 合成失败: {str(e)}")
    
    async def _merge_audio_files(self, task: SynthesisTask, audio_files: List[Dict[str, Any]]) -> str:
        """合并音频文件"""
        try:
            # 使用路径管理器构建输出文件路径
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if task.chapter_id:
                output_filename = f"chapter_{task.chapter_id}_{timestamp}.wav"
            else:
                output_filename = f"project_{task.project_id}_{timestamp}.wav"
            
            # 创建项目专用目录
            project_subdir = f"projects/{task.project_id}"
            project_audio_dir = get_storage_path('audio', project_subdir)
            os.makedirs(project_audio_dir, exist_ok=True)
            
            output_path = os.path.join(project_audio_dir, output_filename)
            
            # 调用音频合并服务
            file_paths = [af["file_path"] for af in audio_files if af.get("file_path")]
            merged_path = await self.tts_client.merge_audio_files(file_paths, output_path)
            
            return merged_path
            
        except Exception as e:
            logger.error(f"音频合并失败: {str(e)}")
            return None
    
    async def _send_progress_update(self, task: SynthesisTask, completed: int, message: str):
        """发送进度更新"""
        progress = min(100, round((completed / task.total_segments) * 100)) if task.total_segments > 0 else 0
        
        # 通过WebSocket发送更新
        await self.websocket_manager.send_progress_update(
            session_id=f"synthesis_{task.id}",
            data={
                "task_id": task.id,
                "project_id": task.project_id,
                "status": task.status,
                "progress": progress,
                "completed_segments": completed,
                "total_segments": task.total_segments,
                "failed_segments": len(json.loads(task.failed_segments or "[]")),
                "current_processing": message,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


class SynthesisService:
    """TTS合成服务主类"""
    
    def __init__(self, db: Session, websocket_manager: ProgressWebSocketManager = None):
        self.db = db
        self.websocket_manager = websocket_manager or ProgressWebSocketManager()
        self.task_manager = SynthesisTaskManager(db, self.websocket_manager)
    
    async def create_synthesis_task(
        self,
        project_id: int,
        analysis_result_id: int = None,
        chapter_id: int = None,
        synthesis_config: Dict[str, Any] = None,
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """创建合成任务"""
        
        # 检查是否有正在运行的任务
        active_task = self.db.query(SynthesisTask).filter(
            and_(
                SynthesisTask.project_id == project_id,
                SynthesisTask.status.in_(["pending", "running"])
            )
        ).first()
        
        if active_task:
            raise ServiceException("该项目已有正在进行的合成任务")
        
        # 创建任务
        task = await self.task_manager.create_task(
            project_id=project_id,
            analysis_result_id=analysis_result_id,
            chapter_id=chapter_id,
            synthesis_plan=synthesis_config,
            batch_size=batch_size
        )
        
        return {
            "task_id": task.id,
            "status": task.status,
            "total_segments": task.total_segments,
            "message": "合成任务已创建"
        }
    
    async def start_synthesis(self, task_id: int) -> Dict[str, Any]:
        """启动合成任务"""
        await self.task_manager.start_task(task_id)
        
        return {
            "task_id": task_id,
            "status": "running",
            "message": "合成已启动"
        }
    
    async def get_task_status(self, task_id: int) -> Dict[str, Any]:
        """获取任务状态"""
        task = self.db.query(SynthesisTask).filter(SynthesisTask.id == task_id).first()
        if not task:
            raise ServiceException("任务不存在")
        
        # 计算进度
        progress = 0
        if task.total_segments > 0:
            progress = round((task.completed_segments / task.total_segments) * 100)
        
        return {
            "task_id": task.id,
            "project_id": task.project_id,
            "status": task.status,
            "progress": progress,
            "total_segments": task.total_segments,
            "completed_segments": task.completed_segments,
            "failed_segments": len(json.loads(task.failed_segments or "[]")),
            "current_segment": task.current_segment,
            "batch_size": task.batch_size,
            "retry_count": task.retry_count,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "processing_time": task.processing_time,
            "error_message": task.error_message,
            "final_audio_path": task.final_audio_path
        }
    
    async def pause_task(self, task_id: int) -> bool:
        """暂停合成任务"""
        task = self.db.query(SynthesisTask).filter(SynthesisTask.id == task_id).first()
        if not task:
            raise ServiceException("任务不存在")
        
        if task.status != "running":
            raise ServiceException(f"无法暂停状态为 {task.status} 的任务")
        
        task.status = "paused"
        self.db.commit()
        
        return True
    
    async def resume_task(self, task_id: int) -> bool:
        """恢复合成任务"""
        task = self.db.query(SynthesisTask).filter(SynthesisTask.id == task_id).first()
        if not task:
            raise ServiceException("任务不存在")
        
        if task.status != "paused":
            raise ServiceException(f"无法恢复状态为 {task.status} 的任务")
        
        # 重新启动任务
        await self.task_manager.start_task(task_id)
        
        return True
    
    async def cancel_task(self, task_id: int) -> bool:
        """取消合成任务"""
        task = self.db.query(SynthesisTask).filter(SynthesisTask.id == task_id).first()
        if not task:
            raise ServiceException("任务不存在")
        
        if task.status in ["completed", "failed"]:
            raise ServiceException(f"无法取消状态为 {task.status} 的任务")
        
        task.status = "failed"
        task.error_message = "用户取消"
        self.db.commit()
        
        return True
    
    async def get_project_tasks(self, project_id: int) -> List[Dict[str, Any]]:
        """获取项目的合成任务列表"""
        tasks = self.db.query(SynthesisTask).filter(
            SynthesisTask.project_id == project_id
        ).order_by(SynthesisTask.created_at.desc()).all()
        
        return [self._task_to_dict(task) for task in tasks]
    
    async def delete_task(self, task_id: int) -> bool:
        """删除合成任务"""
        task = self.db.query(SynthesisTask).filter(SynthesisTask.id == task_id).first()
        if not task:
            raise ServiceException("任务不存在")
        
        if task.status == "running":
            raise ServiceException("无法删除正在运行的任务")
        
        self.db.delete(task)
        self.db.commit()
        
        return True
    
    async def get_task_output_files(self, task_id: int) -> List[Dict[str, Any]]:
        """获取任务的输出文件列表"""
        task = self.db.query(SynthesisTask).filter(SynthesisTask.id == task_id).first()
        if not task:
            raise ServiceException("任务不存在")
        
        # 获取项目相关的音频文件
        audio_files = self.db.query(AudioFile).filter(
            AudioFile.project_id == task.project_id
        ).order_by(AudioFile.created_at.desc()).all()
        
        return [audio_file.to_dict() for audio_file in audio_files]
    
    def _task_to_dict(self, task: SynthesisTask) -> Dict[str, Any]:
        """转换任务对象为字典"""
        progress = 0
        if task.total_segments > 0:
            progress = round((task.completed_segments / task.total_segments) * 100)
        
        return {
            "id": task.id,
            "project_id": task.project_id,
            "chapter_id": task.chapter_id,
            "status": task.status,
            "progress": progress,
            "total_segments": task.total_segments,
            "completed_segments": task.completed_segments,
            "failed_segments": len(json.loads(task.failed_segments or "[]")),
            "batch_size": task.batch_size,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "processing_time": task.processing_time,
            "error_message": task.error_message,
            "final_audio_path": task.final_audio_path
        } 