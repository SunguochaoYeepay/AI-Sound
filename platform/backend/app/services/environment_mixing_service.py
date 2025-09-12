"""
环境音混音服务
从 generation.py 中提取的混音任务逻辑
"""

import os
import logging
from typing import List, Tuple, Dict
from datetime import datetime
from pydub import AudioSegment

from app.services.environment_project_service import EnvironmentProjectService
from app.database import get_db

logger = logging.getLogger(__name__)


class EnvironmentMixingService:
    """环境音混音服务"""
    
    @staticmethod
    async def mix_environment_sounds_task(
        task_id: str,
        project_id: int,
        tracks_to_mix: List[Tuple[int, Dict]]
    ):
        """
        后台混音任务
        """
        try:
            logger.info(f"[ENV_MIX_TASK] 开始混音任务: {task_id}")
            logger.info(f"[ENV_MIX_TASK] 项目ID: {project_id}")
            logger.info(f"[ENV_MIX_TASK] 要混音的轨道数量: {len(tracks_to_mix)}")
            
            for i, (track_index, track) in enumerate(tracks_to_mix):
                keywords = track.get('environment_keywords', [])
                keyword_name = keywords[0] if keywords and len(keywords) > 0 else "无环境音"
                logger.info(f"[ENV_MIX_TASK] 轨道{i}: 索引={track_index}, 关键词={keyword_name}")
                logger.info(f"[ENV_MIX_TASK] 轨道{i}: 文件路径={track.get('generated_file_path')}")
                logger.info(f"[ENV_MIX_TASK] 轨道{i}: 开始时间={track.get('start_time', 0)}, 时长={track.get('duration', 30)}")
            
            # 获取环境音项目
            db = next(get_db())
            try:
                env_service = EnvironmentProjectService(db)
                env_project = env_service.get_by_project_id(project_id)
                
                if not env_project:
                    logger.error(f"[ENV_MIX_TASK] 未找到环境音项目: {project_id}")
                    return
                
                logger.info(f"[ENV_MIX_TASK] 成功获取环境音项目: {env_project.id}")
                logger.info(f"[ENV_MIX_TASK] 项目状态: {env_project.status}")
                logger.info(f"[ENV_MIX_TASK] 项目分析结果: {type(env_project.analysis_result)}")
                
            except Exception as e:
                logger.error(f"[ENV_MIX_TASK] 获取环境音项目失败: {str(e)}")
                db.close()
                return
            
            # 创建混音输出目录
            output_dir = os.path.join("data", "environment_sounds", "mixed")
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"[ENV_MIX_TASK] 混音输出目录: {output_dir}")
            
            # 生成输出文件路径
            output_filename = f"mixed_environment_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            output_path = os.path.join(output_dir, output_filename)
            logger.info(f"[ENV_MIX_TASK] 混音输出文件路径: {output_path}")
            
            # 加载所有音频文件
            audio_segments = []
            max_duration = 0
            
            for track_index, track in tracks_to_mix:
                try:
                    file_path = track['generated_file_path']
                    logger.info(f"[ENV_MIX_TASK] 处理轨道 {track_index}: {file_path}")
                    logger.info(f"[ENV_MIX_TASK] 文件是否存在: {os.path.exists(file_path)}")
                    
                    if os.path.exists(file_path):
                        # 加载音频文件
                        logger.info(f"[ENV_MIX_TASK] 开始加载音频文件: {file_path}")
                        audio = AudioSegment.from_wav(file_path)
                        logger.info(f"[ENV_MIX_TASK] 音频加载成功，原始长度: {len(audio)}ms")
                        
                        # 获取轨道的时间信息
                        start_time = track.get('start_time', 0.0)
                        duration = track.get('duration', 30.0)
                        logger.info(f"[ENV_MIX_TASK] 轨道时间信息: 开始={start_time}s, 时长={duration}s")
                        
                        # 调整音频长度以匹配轨道时长
                        target_length = int(duration * 1000)  # 转换为毫秒
                        logger.info(f"[ENV_MIX_TASK] 目标长度: {target_length}ms")
                        
                        if len(audio) < target_length:
                            # 如果音频太短，循环播放
                            repeat_count = target_length // len(audio) + 1
                            logger.info(f"[ENV_MIX_TASK] 音频太短，需要循环 {repeat_count} 次")
                            audio = audio * repeat_count
                        
                        audio = audio[:target_length]
                        logger.info(f"[ENV_MIX_TASK] 调整后音频长度: {len(audio)}ms")
                        
                        # 设置音量（默认-15dB，避免过于突出）
                        volume = track.get('volume', -15)
                        logger.info(f"[ENV_MIX_TASK] 设置音量: {volume}dB")
                        audio = audio + volume
                        
                        # 添加淡入淡出效果
                        fade_in = int(track.get('fade_in', 1.0) * 1000)  # 转换为毫秒并转为整数
                        fade_out = int(track.get('fade_out', 1.0) * 1000)
                        logger.info(f"[ENV_MIX_TASK] 淡入淡出: {fade_in}ms / {fade_out}ms")
                        audio = audio.fade_in(fade_in).fade_out(fade_out)
                        
                        # 计算在混音中的位置
                        position = int(start_time * 1000)
                        logger.info(f"[ENV_MIX_TASK] 混音位置: {position}ms")
                        
                        audio_segments.append({
                            'audio': audio,
                            'position': position,
                            'track_index': track_index
                        })
                        
                        # 更新最大时长
                        track_end = position + len(audio)
                        max_duration = max(max_duration, track_end)
                        
                        logger.info(f"[ENV_MIX_TASK] 轨道 {track_index} 处理完成")
                        logger.info(f"[ENV_MIX_TASK] 轨道结束位置: {track_end}ms")
                        logger.info(f"[ENV_MIX_TASK] 当前最大时长: {max_duration}ms")
                    else:
                        logger.warning(f"[ENV_MIX_TASK] 文件不存在: {file_path}")
                        
                except Exception as e:
                    logger.error(f"[ENV_MIX_TASK] 加载轨道 {track_index} 失败: {str(e)}")
                    continue
            
            if not audio_segments:
                logger.error(f"[ENV_MIX_TASK] 没有可混音的音频文件")
                return
            
            logger.info(f"[ENV_MIX_TASK] 成功加载 {len(audio_segments)} 个音频段")
            logger.info(f"[ENV_MIX_TASK] 最终混音时长: {max_duration}ms")
            
            # 创建混音轨道
            mixed_audio = AudioSegment.silent(duration=max_duration)
            logger.info(f"[ENV_MIX_TASK] 创建静音轨道，长度: {len(mixed_audio)}ms")
            
            # 叠加所有音频
            for segment_info in audio_segments:
                try:
                    mixed_audio = mixed_audio.overlay(
                        segment_info['audio'],
                        position=segment_info['position']
                    )
                    logger.info(f"[ENV_MIX_TASK] 叠加轨道 {segment_info['track_index']}")
                except Exception as e:
                    logger.error(f"[ENV_MIX_TASK] 叠加轨道 {segment_info['track_index']} 失败: {str(e)}")
                    continue
            
            # 导出混音文件
            mixed_audio.export(output_path, format="wav")
            
            # 更新项目状态 - 重新获取数据库会话确保数据一致性
            try:
                # 重新获取数据库会话
                db.close()
                db = next(get_db())
                env_service = EnvironmentProjectService(db)
                env_project = env_service.get_by_project_id(project_id)
                
                if env_project:
                    # 获取现有的matching_result
                    current_matching_result = env_project.matching_result or {}
                    
                    # 创建新的matching_result，保留现有数据
                    new_matching_result = {
                        **current_matching_result,
                        'mixed_file_path': output_path,
                        'mixed_file_size': os.path.getsize(output_path),
                        'mixed_duration': len(mixed_audio) / 1000.0,  # 转换为秒
                        'mixed_tracks_count': len(tracks_to_mix),
                        'mixed_at': datetime.now().isoformat()
                    }
                    
                    # 更新整个matching_result字段
                    env_project.matching_result = new_matching_result
                    
                    db.commit()
                    logger.info(f"[ENV_MIX_TASK] 数据库更新成功，混音文件路径已保存: {output_path}")
                    logger.info(f"[ENV_MIX_TASK] 更新后的matching_result: {new_matching_result}")
                else:
                    logger.error(f"[ENV_MIX_TASK] 重新查询项目失败，项目ID: {project_id}")
            except Exception as db_error:
                logger.error(f"[ENV_MIX_TASK] 数据库更新失败: {str(db_error)}")
            finally:
                db.close()
            
            logger.info(f"[ENV_MIX_TASK] 混音完成: {output_path}")
             
             # 发送WebSocket通知
            try:
                 from app.websocket.manager import websocket_manager
                 await websocket_manager.broadcast_message({
                     "type": "environment_mixing_progress",
                     "data": {
                         "task_id": task_id,
                         "project_id": project_id,
                         "status": "completed",
                         "mixed_file_path": output_path,
                         "total_tracks": len(tracks_to_mix),
                         "message": f"环境音混音完成，共 {len(tracks_to_mix)} 个轨道"
                     }
                 })
            except Exception as e:
                 logger.warning(f"[ENV_MIX_TASK] WebSocket通知失败: {str(e)}")
            
        except Exception as e:
            logger.error(f"[ENV_MIX_TASK] 混音任务失败: {str(e)}")
            
            # 发送错误通知
            try:
                from app.websocket.manager import websocket_manager
                await websocket_manager.broadcast_message({
                    "type": "environment_mixing_progress",
                    "data": {
                        "task_id": task_id,
                        "project_id": project_id,
                        "status": "failed",
                        "error_message": str(e),
                        "message": f"环境音混音失败: {str(e)}"
                    }
                })
            except Exception as ws_error:
                logger.warning(f"[ENV_MIX_TASK] WebSocket错误通知失败: {str(ws_error)}")
