"""
简化的TangoFlux环境音生成服务
只保留核心功能，移除冗余代码
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.tangoflux_core_generator import TangoFluxCoreGenerator
from app.services.environment_sound_database_service import EnvironmentSoundDatabaseService
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class TangoFluxEnvironmentGenerator:
    """简化的TangoFlux环境音生成器"""
    
    def __init__(self):
        self.core_generator = TangoFluxCoreGenerator()
        
        logger.info("[TANGOFLUX_GEN] 简化版环境音生成器初始化完成")
    
    def convert_track_to_request(self, track: Dict[str, Any]) -> Dict[str, Any]:
        """转换轨道数据为生成请求"""
        # 优先从environment_keywords获取关键词
        keywords = track.get('environment_keywords', [])
        keyword = keywords[0] if keywords else ''
        
        # 如果没有关键词，尝试其他字段
        if not keyword:
            keyword = track.get('keyword', '') or track.get('description', '')
        
        # 获取描述
        description = track.get('chinese_description', '') or track.get('description', '')
        
        # 获取其他参数
        duration = track.get('duration', 30.0)
        intensity = track.get('intensity', 'medium')
        english_prompt = track.get('english_prompt', '')
        
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
                                                chapter_id: str = None) -> Dict[str, Any]:
        """
        为项目生成环境音文件
        
        Args:
            project_id: 项目ID
            tracks_to_generate: 要生成的轨道列表，每个元素为(index, track_data)
            task_id: 任务ID
            chapter_id: 章节ID（可选）
            
        Returns:
            生成结果字典
        """
        logger.info(f"[TANGOFLUX_GEN] 开始为项目{project_id}生成环境音，轨道数量: {len(tracks_to_generate)}")
        
        try:
            # 检查服务健康状态
            if not await self.core_generator.check_service_health():
                logger.error("[TANGOFLUX_GEN] TangoFlux服务不可用，生成取消")
                return {"success": False, "error": "TangoFlux服务不可用"}
            
            # 转换轨道数据为生成请求
            generation_requests = []
            for index, track in tracks_to_generate:
                try:
                    request = self.convert_track_to_request(track)
                    # 添加原始信息用于数据库保存
                    request['track_index'] = index
                    request['track_data'] = track
                    generation_requests.append(request)
                    
                    logger.info(f"[TANGOFLUX_GEN] 转换轨道数据: {track.get('description', 'unknown')} -> {request['keyword']}")
                except Exception as e:
                    logger.error(f"[TANGOFLUX_GEN] 转换轨道数据失败: {e}")
                    continue
            
            if not generation_requests:
                raise ValueError("没有有效的轨道数据可生成")
            
            # 批量生成环境音
            generation_results = await self.core_generator.batch_generate_audio(
                requests=generation_requests,
                max_concurrent=3
            )
            
            # 添加原始信息到结果中
            for i, result in enumerate(generation_results):
                if i < len(generation_requests):
                    result.update({
                        'keyword': generation_requests[i]['keyword'],
                        'description': generation_requests[i]['description'],
                        'duration': generation_requests[i]['duration'],
                        'intensity': generation_requests[i]['intensity'],
                        'track_index': generation_requests[i]['track_index']
                    })
            
            # 保存到数据库
            db = SessionLocal()
            try:
                db_service = EnvironmentSoundDatabaseService(db)
                
                # 构建轨道映射
                track_mapping = {}
                for i, (track_index, _) in enumerate(tracks_to_generate):
                    track_mapping[track_index] = i
                
                # 保存生成的音频
                saved_sounds = db_service.save_generated_sounds(
                    generation_results=generation_results,
                    project_id=project_id,
                    track_mapping=track_mapping
                )
                
                # 更新项目轨道状态
                update_success = db_service.update_project_tracks(
                    project_id=project_id,
                    saved_sounds=saved_sounds,
                    tracks_to_generate=tracks_to_generate
                )
                
                if update_success:
                    logger.info(f"[TANGOFLUX_GEN] 项目{project_id}环境音生成完成，保存了{len(saved_sounds)}个音频")
                else:
                    logger.warning(f"[TANGOFLUX_GEN] 项目{project_id}轨道状态更新失败")
                
                # 发送WebSocket通知
                await self._send_completion_notification(task_id, project_id, generation_results, saved_sounds)
                
            except Exception as e:
                logger.error(f"[TANGOFLUX_GEN] 数据库操作失败: {str(e)}")
                db.rollback()
            finally:
                db.close()
            
            # 统计结果
            successful = len([r for r in generation_results if r['success']])
            failed = len([r for r in generation_results if not r['success']])
            
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
            
            # 发送错误通知
            await self._send_error_notification(task_id, project_id, str(e))
            
            return {"success": False, "error": str(e)}
    
    async def _send_completion_notification(self, task_id: str, project_id: int, generation_results: list, saved_sounds: list):
        """发送完成通知"""
        try:
            from app.websocket.manager import websocket_manager
            if websocket_manager:
                successful = len([r for r in generation_results if r['success']])
                message_data = {
                    "type": "environment_generation_progress",
                    "data": {
                        "task_id": task_id,
                        "project_id": project_id,
                        "status": "completed",
                        "total_tracks": len(generation_results),
                        "completed_tracks": successful,
                        "saved_sounds_count": len(saved_sounds),
                        "message": f"环境音生成完成，共 {len(generation_results)} 个轨道，已保存 {len(saved_sounds)} 个音频记录"
                    }
                }
                await websocket_manager.broadcast_message(message_data)
                logger.info(f"[TANGOFLUX_GEN] WebSocket完成通知发送成功: {task_id}")
        except Exception as e:
            logger.warning(f"[TANGOFLUX_GEN] WebSocket通知发送失败: {str(e)}")
    
    async def _send_error_notification(self, task_id: str, project_id: int, error_message: str):
        """发送错误通知"""
        try:
            from app.websocket.manager import websocket_manager
            if websocket_manager:
                await websocket_manager.broadcast_message({
                    "type": "environment_generation_progress",
                    "data": {
                        "task_id": task_id,
                        "project_id": project_id,
                        "status": "failed",
                        "error": error_message,
                        "message": "环境音生成失败"
                    }
                })
        except Exception as e:
            logger.warning(f"[TANGOFLUX_GEN] WebSocket错误通知发送失败: {str(e)}")
    
    async def check_service_health(self) -> bool:
        """检查TangoFlux服务健康状态"""
        return await self.core_generator.check_service_health()
