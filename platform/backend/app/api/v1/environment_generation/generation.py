"""
环境音生成API端点
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Body
from fastapi.responses import FileResponse, StreamingResponse
from typing import Dict, Any, List
from datetime import datetime
import os
import json
from sqlalchemy.orm import Session

from app.services.tangoflux_environment_generator import TangoFluxEnvironmentGenerator
from app.services.environment_project_service import EnvironmentProjectService
from app.services.environment_mixing_service import EnvironmentMixingService
from app.utils.logger import get_logger
from app.database import get_db
from app.models.environment_generation import EnvironmentProject
from .schemas import BatchGenerationRequest

logger = get_logger(__name__)
router = APIRouter()


@router.post("/generate/{project_id}")
async def generate_environment_sounds(
    project_id: int,
    background_tasks: BackgroundTasks,
    request: Dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    生成环境音文件
    支持指定轨道索引或生成所有轨道
    """
    try:
        # 从请求体中获取轨道索引
        track_indices = request.get('track_indices') if request else None
        logger.info(f"[ENV_GEN_API] 开始生成环境音，项目ID: {project_id}，轨道索引: {track_indices}")
        
        # 获取环境音项目 - 支持通过环境音项目ID或合成项目ID查找
        env_service = EnvironmentProjectService(db)
        env_project = None
        
        # 首先尝试通过环境音项目ID直接查找
        env_project = db.query(EnvironmentProject).filter(EnvironmentProject.id == project_id).first()
        logger.info(f"[ENV_GEN_API] 通过环境音项目ID查找结果: {env_project.id if env_project else 'None'}")
        
        # 如果没找到，再尝试通过合成项目ID查找
        if not env_project:
            env_project = env_service.get_by_novel_project_id(project_id)
            logger.info(f"[ENV_GEN_API] 通过合成项目ID查找结果: {env_project.id if env_project else 'None'}")
        
        if not env_project:
            logger.error(f"[ENV_GEN_API] 未找到环境音项目，项目ID: {project_id}")
            raise HTTPException(status_code=404, detail="未找到环境音项目")
        
        if not env_project.analysis_result:
            logger.error(f"[ENV_GEN_API] 环境音项目没有分析结果，项目ID: {project_id}")
            raise HTTPException(status_code=404, detail="未找到环境音分析结果")
        
        # 处理多章节格式的分析结果
        analysis_result = env_project.analysis_result
        environment_tracks = []
        
        # 检查是否是多章节格式（键是章节ID）
        if isinstance(analysis_result, dict) and not analysis_result.get('environment_tracks'):
            # 多章节格式，收集所有章节的环境轨道
            for chapter_id, chapter_analysis in analysis_result.items():
                if isinstance(chapter_analysis, dict) and chapter_analysis.get('environment_tracks'):
                    environment_tracks.extend(chapter_analysis['environment_tracks'])
        else:
            # 单章节格式，直接获取environment_tracks
            environment_tracks = analysis_result.get('environment_tracks', [])
        
        if not environment_tracks:
            raise HTTPException(status_code=400, detail="没有环境音轨道配置")
        
        # 确定要生成的轨道
        tracks_to_generate = []
        if track_indices:
            # 生成指定轨道
            for index in track_indices:
                if 0 <= index < len(environment_tracks):
                    tracks_to_generate.append((index, environment_tracks[index]))
                else:
                    logger.warning(f"轨道索引 {index} 超出范围，跳过")
        else:
            # 生成所有轨道
            tracks_to_generate = [(i, track) for i, track in enumerate(environment_tracks)]
        
        if not tracks_to_generate:
            raise HTTPException(status_code=400, detail="没有有效的轨道需要生成")
        
        # 创建生成器实例
        generator = TangoFluxEnvironmentGenerator()
        
        # 生成任务ID
        task_id = f"env_gen_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 在后台任务中执行生成
        background_tasks.add_task(
            generator.generate_project_environment_sounds,
            project_id=project_id,
            tracks_to_generate=tracks_to_generate,
            task_id=task_id
        )
        
        logger.info(f"[ENV_GEN_API] 环境音生成任务已启动: {task_id}")
        
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "project_id": project_id,
                "total_tracks": len(tracks_to_generate),
                "status": "processing",
                "message": f"环境音生成任务已启动，共 {len(tracks_to_generate)} 个轨道"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 环境音生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"环境音生成失败: {str(e)}")


@router.get("/preview/{project_id}/{track_index}")
async def preview_environment_sound(
    project_id: int,
    track_index: int,
    db: Session = Depends(get_db)
):
    """
    预览环境音文件
    """
    try:
        logger.info(f"[ENV_GEN_API] 预览环境音，项目ID: {project_id}，轨道索引: {track_index}")
        
        # 获取环境音项目 - 支持通过环境音项目ID或合成项目ID查找
        env_service = EnvironmentProjectService(db)
        env_project = None
        
        # 首先尝试通过环境音项目ID直接查找
        env_project = db.query(EnvironmentProject).filter(EnvironmentProject.id == project_id).first()
        
        # 如果没找到，再尝试通过合成项目ID查找
        if not env_project:
            env_project = env_service.get_by_novel_project_id(project_id)
        
        if not env_project or not env_project.analysis_result:
            raise HTTPException(status_code=404, detail="未找到环境音分析结果")
        
        environment_tracks = env_project.analysis_result.get('environment_tracks', [])
        if track_index >= len(environment_tracks):
            raise HTTPException(status_code=404, detail="轨道索引超出范围")
        
        track = environment_tracks[track_index]
        
        # 检查是否有生成的文件
        if not track.get('generated_file_path'):
            raise HTTPException(status_code=404, detail="环境音文件尚未生成")
        
        file_path = track['generated_file_path']
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="环境音文件不存在")
        
        # 返回音频文件
        return FileResponse(
            path=file_path,
            media_type="audio/wav",
            filename=f"environment_sound_{project_id}_{track_index}.wav"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 预览环境音失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"预览环境音失败: {str(e)}")


@router.get("/download/{project_id}/{track_index}")
async def download_environment_sound(
    project_id: int,
    track_index: int,
    db: Session = Depends(get_db)
):
    """
    下载环境音文件
    """
    try:
        logger.info(f"[ENV_GEN_API] 下载环境音，项目ID: {project_id}，轨道索引: {track_index}")
        
        # 获取环境音项目
        env_service = EnvironmentProjectService(db)
        env_project = env_service.get_by_novel_project_id(project_id)
        
        if not env_project or not env_project.analysis_result:
            raise HTTPException(status_code=404, detail="未找到环境音分析结果")
        
        environment_tracks = env_project.analysis_result.get('environment_tracks', [])
        if track_index >= len(environment_tracks):
            raise HTTPException(status_code=404, detail="轨道索引超出范围")
        
        track = environment_tracks[track_index]
        
        # 检查是否有生成的文件
        if not track.get('generated_file_path'):
            raise HTTPException(status_code=404, detail="环境音文件尚未生成")
        
        file_path = track['generated_file_path']
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="环境音文件不存在")
        
        # 生成文件名
        keywords = track.get('environment_keywords', ['环境音'])
        filename = f"{keywords[0]}_{project_id}_{track_index}.wav"
        
        # 返回音频文件
        return FileResponse(
            path=file_path,
            media_type="audio/wav",
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 下载环境音失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载环境音失败: {str(e)}")


@router.post("/mix/{project_id}")
async def mix_environment_sounds(
    project_id: int,
    background_tasks: BackgroundTasks,
    request: Dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    混音环境音文件
    """
    try:
        # 从请求体中获取轨道索引
        track_indices = request.get('track_indices') if request else None
        logger.info(f"[ENV_GEN_API] 开始混音环境音，项目ID: {project_id}，轨道索引: {track_indices}")
        
        # 获取环境音项目
        env_service = EnvironmentProjectService(db)
        env_project = env_service.get_by_novel_project_id(project_id)
        
        if not env_project or not env_project.analysis_result:
            raise HTTPException(status_code=404, detail="未找到环境音分析结果")
        
        environment_tracks = env_project.analysis_result.get('environment_tracks', [])
        if not environment_tracks:
            raise HTTPException(status_code=400, detail="没有环境音轨道配置")
        
        # 确定要混音的轨道
        tracks_to_mix = []
        if track_indices:
            # 混音指定轨道
            for index in track_indices:
                if 0 <= index < len(environment_tracks):
                    track = environment_tracks[index]
                    if track.get('generated_file_path') and os.path.exists(track['generated_file_path']):
                        tracks_to_mix.append((index, track))
                    else:
                        logger.warning(f"轨道 {index} 文件不存在，跳过")
                else:
                    logger.warning(f"轨道索引 {index} 超出范围，跳过")
        else:
            # 混音所有已生成的轨道
            for i, track in enumerate(environment_tracks):
                if track.get('generated_file_path') and os.path.exists(track['generated_file_path']):
                    tracks_to_mix.append((i, track))
        
        if not tracks_to_mix:
            raise HTTPException(status_code=400, detail="没有可混音的环境音文件")
        
        # 创建混音服务实例
        mixing_service = EnvironmentMixingService()
        
        # 生成混音任务ID
        task_id = f"env_mix_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 在后台任务中执行混音
        background_tasks.add_task(
            mixing_service.mix_project_environment_sounds,
            project_id=project_id,
            tracks_to_mix=tracks_to_mix,
            task_id=task_id
        )
        
        logger.info(f"[ENV_GEN_API] 环境音混音任务已启动: {task_id}")
        
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "project_id": project_id,
                "total_tracks": len(tracks_to_mix),
                "status": "processing",
                "message": f"环境音混音任务已启动，共 {len(tracks_to_mix)} 个轨道"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 环境音混音失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"环境音混音失败: {str(e)}")


@router.get("/mix-preview/{project_id}")
async def preview_mixed_environment_sounds(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    预览混音后的环境音文件
    """
    try:
        logger.info(f"[ENV_GEN_API] 预览混音环境音，项目ID: {project_id}")
        
        # 获取环境音项目
        env_service = EnvironmentProjectService(db)
        env_project = env_service.get_by_novel_project_id(project_id)
        
        if not env_project:
            raise HTTPException(status_code=404, detail="未找到环境音项目")
        
        # 检查是否有混音文件
        mixed_file_path = env_project.matching_result.get('mixed_file_path')
        if not mixed_file_path or not os.path.exists(mixed_file_path):
            raise HTTPException(status_code=404, detail="混音文件尚未生成")
        
        # 返回混音文件
        return FileResponse(
            path=mixed_file_path,
            media_type="audio/wav",
            filename=f"mixed_environment_{project_id}.wav"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 预览混音环境音失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"预览混音环境音失败: {str(e)}")


@router.get("/mix-download/{project_id}")
async def download_mixed_environment_sounds(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    下载混音后的环境音文件
    """
    try:
        logger.info(f"[ENV_GEN_API] 下载混音环境音，项目ID: {project_id}")
        
        # 获取环境音项目
        env_service = EnvironmentProjectService(db)
        env_project = env_service.get_by_novel_project_id(project_id)
        
        if not env_project:
            raise HTTPException(status_code=404, detail="未找到环境音项目")
        
        # 检查是否有混音文件
        mixed_file_path = env_project.matching_result.get('mixed_file_path')
        if not mixed_file_path or not os.path.exists(mixed_file_path):
            raise HTTPException(status_code=404, detail="混音文件尚未生成")
        
        # 生成文件名
        filename = f"mixed_environment_{project_id}.wav"
        
        # 返回混音文件
        return FileResponse(
            path=mixed_file_path,
            media_type="audio/wav",
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 下载混音环境音失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载混音环境音失败: {str(e)}")


@router.get("/status/{project_id}")
async def get_generation_status(
    project_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取环境音生成状态
    """
    try:
        logger.info(f"[ENV_GEN_API] 获取生成状态，项目ID: {project_id}")
        
        # 获取环境音项目
        env_service = EnvironmentProjectService(db)
        env_project = env_service.get_by_novel_project_id(project_id)
        
        if not env_project:
            raise HTTPException(status_code=404, detail="未找到环境音项目")
        
        environment_tracks = env_project.analysis_result.get('environment_tracks', []) if env_project.analysis_result else []
        
        # 统计生成状态
        total_tracks = len(environment_tracks)
        generated_tracks = 0
        failed_tracks = 0
        track_statuses = []
        
        for i, track in enumerate(environment_tracks):
            status = "pending"
            if track.get('generated_file_path') and os.path.exists(track['generated_file_path']):
                status = "completed"
                generated_tracks += 1
            elif track.get('generation_error'):
                status = "failed"
                failed_tracks += 1
            
            track_statuses.append({
                "index": i,
                "status": status,
                "keywords": track.get('environment_keywords', []),
                "duration": track.get('duration', 30.0),
                "error": track.get('generation_error')
            })
        
        # 检查混音状态
        mixing_status = "pending"
        if env_project.matching_result and env_project.matching_result.get('mixed_file_path'):
            if os.path.exists(env_project.matching_result['mixed_file_path']):
                mixing_status = "completed"
            else:
                mixing_status = "failed"
        
        return {
            "success": True,
            "data": {
                "project_id": project_id,
                "total_tracks": total_tracks,
                "generated_tracks": generated_tracks,
                "failed_tracks": failed_tracks,
                "track_statuses": track_statuses,
                "mixing_status": mixing_status,
                "project_status": env_project.status
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 获取生成状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取生成状态失败: {str(e)}")


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
