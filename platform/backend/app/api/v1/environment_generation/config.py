"""
环境音配置管理API端点
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.services.environment_project_service import EnvironmentProjectService
from app.utils.logger import get_logger
from app.database import get_db
from .schemas import ValidationEditRequest

logger = get_logger(__name__)
router = APIRouter()


@router.get("/config/{project_id}")
async def get_environment_config(
    project_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取项目的环境音配置
    """
    try:
        logger.info(f"[ENV_GEN_API] 获取环境音配置，项目ID: {project_id}")
        
        # 使用环境音项目服务获取配置
        env_service = EnvironmentProjectService(db)
        env_project = env_service.get_by_id(project_id)
        
        if not env_project or not env_project.analysis_result:
            return {
                "success": False,
                "message": "未找到环境音配置，请先进行环境音分析"
            }
        
        # 构建返回的配置数据
        analysis_result = env_project.analysis_result
        analysis_stats = env_project.matching_result.get('analysis_stats', {}) if env_project.matching_result else {}
        session_stage = env_project.matching_result.get('session_stage', 'analyzed') if env_project.matching_result else 'analyzed'
        
        # 构建环境音轨道配置
        environment_tracks = []
        if 'environment_tracks' in analysis_result:
            for i, track in enumerate(analysis_result['environment_tracks']):
                environment_tracks.append({
                    'id': f"track_{i}",
                    'segment_id': track.get('segment_id', i + 1),
                    'environment_keywords': track.get('environment_keywords', []),
                    'scene_description': track.get('scene_description', ''),
                    'duration': track.get('duration', 30.0),
                    'intensity_level': track.get('intensity_level', 'medium'),
                    'tangoflux_config': {
                        'prompt': track.get('tangoflux_prompt', ''),
                        'volume': track.get('volume', 0.6),
                        'duration': track.get('duration', 30.0),
                        'fade_in': track.get('fade_in', 3.0),
                        'fade_out': track.get('fade_out', 2.0),
                        'loop': track.get('loop', True)
                    },
                    'environment_sound_id': track.get('environment_sound_id'),
                    'user_confirmed': track.get('user_confirmed', False),
                    'confidence': track.get('confidence', 0.8)
                })
        
        return {
            "success": True,
            "config": {
                "project_id": project_id,
                "environment_tracks": environment_tracks,
                "analysis_stats": analysis_stats,
                "session_stage": session_stage,
                "total_tracks": len(environment_tracks)
            },
            "message": f"找到 {len(environment_tracks)} 个环境音轨道配置"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 获取环境音配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取环境音配置失败: {str(e)}")


@router.put("/track/{project_id}/{track_index}")
async def update_track_config(
    project_id: int,
    track_index: int,
    request: ValidationEditRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    更新环境音轨道配置
    """
    try:
        logger.info(f"[ENV_GEN_API] 更新轨道配置，项目ID: {project_id}，轨道索引: {track_index}")
        
        # 使用环境音项目服务更新轨道配置
        env_service = EnvironmentProjectService(db)
        
        # 构建轨道配置更新数据
        track_config = {}
        manual_edits = request.manual_edits
        
        if 'environment_keywords' in manual_edits:
            track_config['environment_keywords'] = manual_edits['environment_keywords']
        if 'scene_description' in manual_edits:
            track_config['scene_description'] = manual_edits['scene_description']
        if 'environment_sound_id' in manual_edits:
            track_config['environment_sound_id'] = manual_edits['environment_sound_id']
        if 'tangoflux_config' in manual_edits:
            track_config['tangoflux_config'] = manual_edits['tangoflux_config']
            # 同步更新相关字段
            tangoflux_config = manual_edits['tangoflux_config']
            if 'prompt' in tangoflux_config:
                track_config['tangoflux_prompt'] = tangoflux_config['prompt']
            if 'volume' in tangoflux_config:
                track_config['volume'] = tangoflux_config['volume']
            if 'duration' in tangoflux_config:
                track_config['duration'] = tangoflux_config['duration']
        
        # 更新轨道配置
        success = env_service.update_track_config(project_id, track_index, track_config)
        
        if not success:
            raise HTTPException(status_code=404, detail="未找到环境音分析结果或轨道索引超出范围")
        
        logger.info(f"[ENV_GEN_API] 轨道配置更新成功，项目ID: {project_id}，轨道索引: {track_index}")
        
        return {
            "success": True,
            "data": {
                "project_id": project_id,
                "track_index": track_index
            },
            "message": "轨道配置更新成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 更新轨道配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新轨道配置失败: {str(e)}")


@router.delete("/track/{project_id}/{track_index}")
async def delete_track(
    project_id: int,
    track_index: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    删除环境音轨道
    """
    try:
        logger.info(f"[ENV_GEN_API] 删除轨道，项目ID: {project_id}，轨道索引: {track_index}")
        
        # 使用环境音项目服务删除轨道
        env_service = EnvironmentProjectService(db)
        
        # 删除轨道
        success = env_service.delete_track(project_id, track_index)
        
        if not success:
            raise HTTPException(status_code=404, detail="未找到环境音分析结果或轨道索引超出范围")
        
        logger.info(f"[ENV_GEN_API] 轨道删除成功，项目ID: {project_id}，轨道索引: {track_index}")
        
        return {
            "success": True,
            "data": {
                "project_id": project_id,
                "track_index": track_index
            },
            "message": "轨道删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 删除轨道失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除轨道失败: {str(e)}")
