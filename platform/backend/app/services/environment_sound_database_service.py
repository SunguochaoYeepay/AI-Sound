"""
环境音数据库服务
专门处理环境音的数据库操作和项目状态更新
"""

import logging
import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.environment_sound import EnvironmentSound
from app.models.environment_generation import EnvironmentProject

logger = logging.getLogger(__name__)


class EnvironmentSoundDatabaseService:
    """环境音数据库服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save_generated_sounds(self, generation_results: List[Dict[str, Any]], project_id: int, track_mapping: Optional[Dict[int, int]] = None) -> List[EnvironmentSound]:
        """
        保存生成的环境音到数据库
        
        Args:
            generation_results: 生成结果列表，每个包含 success, file_path, keyword, description等
            project_id: 环境音项目ID
            track_mapping: 轨道映射 {track_index: result_index}
        
        Returns:
            保存的EnvironmentSound对象列表
        """
        saved_sounds = []
        
        for i, result in enumerate(generation_results):
            if not result['success'] or not result['file_path']:
                continue
                
            try:
                # 获取轨道索引
                track_index = None
                if track_mapping:
                    for track_idx, result_idx in track_mapping.items():
                        if result_idx == i:
                            track_index = track_idx
                            break
                
                # 获取文件大小
                file_size = None
                if result['file_path'] and os.path.exists(result['file_path']):
                    try:
                        file_size = os.path.getsize(result['file_path'])
                    except Exception as e:
                        logger.warning(f"[ENV_DB] 获取文件大小失败: {str(e)}")
                
                # 从结果中提取信息 - 减少硬编码默认值
                keyword = result.get('keyword', f"环境音_{i}")
                description = result.get('description') or result.get('chinese_description', f"AI生成的{keyword}环境音")
                duration = result.get('duration', 30.0)  # 保留作为最后的安全默认值
                intensity = result.get('intensity', 'medium')  # 保留作为最后的安全默认值
                
                # 创建EnvironmentSound实体
                environment_sound = EnvironmentSound(
                    name=f"{keyword}_{int(time.time())}",
                    prompt=f"{keyword} - {description}",
                    description=description,
                    file_path=result['file_path'],
                    file_size=file_size,
                    duration=duration,
                    tags=[keyword, "AI生成", f"强度_{intensity}"],
                    generation_status='completed',
                    is_active=True,
                    environment_project_id=project_id,
                    track_index=track_index,
                    novel_project_id=project_id,
                )
                
                self.db.add(environment_sound)
                self.db.flush()  # 获取ID但不提交
                
                saved_sounds.append(environment_sound)
                
                logger.info(f"[ENV_DB] 环境音已保存: {environment_sound.name} (ID: {environment_sound.id})")
                
            except Exception as e:
                logger.error(f"[ENV_DB] 保存环境音失败: {result.get('keyword', 'unknown')} - {str(e)}")
                continue
        
        return saved_sounds
    
    def update_project_tracks(self, project_id: int, saved_sounds: List[EnvironmentSound], tracks_to_generate: List[tuple]) -> bool:
        """
        更新项目轨道状态
        
        Args:
            project_id: 项目ID
            saved_sounds: 保存的环境音列表
            tracks_to_generate: 生成的轨道列表 [(index, track_data), ...]
        
        Returns:
            更新是否成功
        """
        try:
            # 获取环境音项目
            env_project = self.db.query(EnvironmentProject).filter(EnvironmentProject.id == project_id).first()
            if not env_project or not env_project.analysis_result:
                logger.warning(f"[ENV_DB] 未找到环境音项目或分析结果: {project_id}")
                return False
            
            analysis_result = env_project.analysis_result
            
            # 检查是否是多章节格式
            if isinstance(analysis_result, dict) and not analysis_result.get('environment_tracks'):
                # 多章节格式 - 收集所有轨道
                all_tracks = []
                for chapter_id, chapter_data in analysis_result.items():
                    if isinstance(chapter_data, dict) and chapter_data.get('environment_tracks'):
                        all_tracks.extend(chapter_data['environment_tracks'])
                
                # 更新轨道状态
                for i, (track_index, track_data) in enumerate(tracks_to_generate):
                    if i < len(saved_sounds) and track_index < len(all_tracks):
                        all_tracks[track_index]['generated_file_path'] = saved_sounds[i].file_path
                        all_tracks[track_index]['generation_status'] = 'completed'
                        all_tracks[track_index]['generated_sound_id'] = saved_sounds[i].id
                        
                        logger.info(f"[ENV_DB] 更新轨道 {track_index} 状态: {saved_sounds[i].file_path}")
            else:
                # 单章节格式
                tracks = analysis_result.get('environment_tracks', [])
                for i, (track_index, track_data) in enumerate(tracks_to_generate):
                    if i < len(saved_sounds) and track_index < len(tracks):
                        tracks[track_index]['generated_file_path'] = saved_sounds[i].file_path
                        tracks[track_index]['generation_status'] = 'completed'
                        tracks[track_index]['generated_sound_id'] = saved_sounds[i].id
                
                analysis_result['environment_tracks'] = tracks
            
            # 更新项目状态
            env_project.analysis_result = analysis_result
            env_project.generation_count = len(saved_sounds)
            env_project.updated_at = datetime.utcnow()
            
            # 强制标记JSON字段为已修改
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(env_project, "analysis_result")
            
            self.db.commit()
            
            logger.info(f"[ENV_DB] 项目 {project_id} 轨道状态更新完成")
            return True
            
        except Exception as e:
            logger.error(f"[ENV_DB] 更新项目轨道状态失败: {str(e)}")
            self.db.rollback()
            return False
