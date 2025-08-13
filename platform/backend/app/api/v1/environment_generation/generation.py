"""
环境音生成API端点
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.tangoflux_environment_generator import TangoFluxEnvironmentGenerator
from app.services.environment_project_service import EnvironmentProjectService
from app.utils.logger import get_logger
from app.database import get_db
from .schemas import BatchGenerationRequest

logger = get_logger(__name__)
router = APIRouter()


@router.post("/finalize/{project_id}")
async def finalize_generation(
    project_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    完成环境音生成流程
    """
    try:
        logger.info(f"[ENV_GEN_API] 完成环境音生成流程，项目ID: {project_id}")
        
        # 使用环境音项目服务完成项目
        env_service = EnvironmentProjectService(db)
        env_project = env_service.get_by_novel_project_id(project_id)
        
        if not env_project or not env_project.analysis_result:
            raise HTTPException(status_code=404, detail="未找到环境音分析结果")
        
        environment_tracks = env_project.analysis_result.get('environment_tracks', [])
        
        # 检查是否有轨道配置
        if not environment_tracks:
            raise HTTPException(status_code=400, detail="没有环境音轨道配置")
        
        # 完成项目
        success = env_service.finalize_project(project_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="完成项目失败")
        
        logger.info(f"[ENV_GEN_API] 环境音生成流程完成，项目ID: {project_id}，轨道数量: {len(environment_tracks)}")
        
        return {
            "success": True,
            "data": {
                "project_id": project_id,
                "config": {
                    "project_id": project_id,
                    "environment_tracks": environment_tracks,
                    "analysis_stats": env_project.matching_result.get('analysis_stats', {}) if env_project.matching_result else {},
                    "session_stage": "completed",
                    "total_tracks": len(environment_tracks)
                }
            },
            "message": f"环境音生成流程完成，共 {len(environment_tracks)} 个轨道"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 完成环境音生成流程失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"完成环境音生成流程失败: {str(e)}")


@router.post("/batch-generate")
async def batch_generate_environment_sounds(
    request: BatchGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    批量生成环境音
    """
    try:
        logger.info(f"[ENV_GEN_API] 开始批量生成环境音，轨道数量: {len(request.tracks)}")
        
        if not request.tracks:
            raise HTTPException(status_code=400, detail="没有需要生成的轨道")
        
        # 转换前端数据格式为后端期望的格式
        generation_requests = []
        for track in request.tracks:
            # 从environment_keywords中获取主要关键词
            keyword = track.get('environment_keywords', [''])[0] if track.get('environment_keywords') else ''
            if not keyword and track.get('scene_description'):
                keyword = track.get('scene_description')
            
            generation_request = {
                'keyword': keyword,
                'description': track.get('scene_description', ''),
                'duration': track.get('duration', 30.0),
                'intensity': track.get('intensity_level', 'medium')
            }
            generation_requests.append(generation_request)
        
        # 创建生成器实例
        generator = TangoFluxEnvironmentGenerator()
        
        # 生成任务ID
        task_id = f"batch_gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(generation_requests)}"
        
        # 记录生成任务
        generation_stats = {
            "task_id": task_id,
            "total_tracks": len(generation_requests),
            "generated_tracks": 0,
            "failed_tracks": 0,
            "status": "processing",
            "start_time": datetime.now().isoformat(),
            "tracks": []
        }
        
        # 在后台任务中执行生成
        background_tasks.add_task(
            generator.batch_generate_environment_sounds,
            generation_requests=generation_requests,
            max_concurrent=request.options.get('max_concurrent', 3)
        )
        
        logger.info(f"[ENV_GEN_API] 批量生成任务已启动: {task_id}")
        
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "total_tracks": len(request.tracks),
                "status": "processing",
                "message": f"批量生成任务已启动，共 {len(request.tracks)} 个环境音"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 批量生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量生成失败: {str(e)}")
