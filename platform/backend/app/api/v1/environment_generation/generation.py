"""
环境音生成API端点
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Body
from fastapi.responses import FileResponse, StreamingResponse
from typing import Dict, Any, List, Tuple
from datetime import datetime
import os
import json
from sqlalchemy.orm import Session

from app.services.tangoflux_environment_generator import TangoFluxEnvironmentGenerator
from app.services.environment_project_service import EnvironmentProjectService

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
        env_project = env_service.get_by_project_id(project_id)
        logger.info(f"[ENV_GEN_API] 项目查找结果: {env_project.id if env_project else 'None'}")
        
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
            # 按章节ID数字顺序排序，确保轨道顺序一致
            sorted_chapter_ids = sorted(analysis_result.keys(), key=lambda x: int(x))
            for chapter_id in sorted_chapter_ids:
                chapter_analysis = analysis_result[chapter_id]
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
                    track = environment_tracks[index]
                    keywords = track.get('environment_keywords') or []
                    if keywords:
                        tracks_to_generate.append((index, track))
                    else:
                        logger.warning(f"轨道 {index} 无环境关键词，跳过生成")
                else:
                    logger.warning(f"轨道索引 {index} 超出范围，跳过")
        else:
            # 仅生成有关键词的轨道（跳过无环境音占位段）
            for i, track in enumerate(environment_tracks):
                keywords = track.get('environment_keywords') or []
                if keywords:
                    tracks_to_generate.append((i, track))
        
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
        env_project = env_service.get_by_project_id(project_id)
        
        if not env_project or not env_project.analysis_result:
            raise HTTPException(status_code=404, detail="未找到环境音分析结果")
        
        # 处理多章节格式的分析结果
        analysis_result = env_project.analysis_result
        
        # 如果是多章节格式，需要找到对应的轨道
        if isinstance(analysis_result, dict) and not analysis_result.get('environment_tracks'):
            # 多章节格式，遍历所有章节找到对应的轨道
            all_tracks = []
            for chapter_id, chapter_data in analysis_result.items():
                if isinstance(chapter_data, dict) and 'environment_tracks' in chapter_data:
                    all_tracks.extend(chapter_data['environment_tracks'])
            
            if track_index >= len(all_tracks):
                raise HTTPException(status_code=404, detail="轨道索引超出范围")
            
            track = all_tracks[track_index]
        else:
            # 单章节格式，直接获取environment_tracks
            environment_tracks = analysis_result.get('environment_tracks', [])
            if track_index >= len(environment_tracks):
                raise HTTPException(status_code=404, detail="轨道索引超出范围")
            
            track = environment_tracks[track_index]
        
        # 检查是否有生成的文件
        if not track.get('generated_file_path'):
            raise HTTPException(status_code=404, detail="环境音文件尚未生成")
        
        file_path = track['generated_file_path']
        logger.info(f"[ENV_GEN_API] 检查文件路径: {file_path}")
        logger.info(f"[ENV_GEN_API] 文件是否存在: {os.path.exists(file_path)}")
        
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
        env_project = env_service.get_by_project_id(project_id)
        
        if not env_project or not env_project.analysis_result:
            raise HTTPException(status_code=404, detail="未找到环境音分析结果")
        
        # 处理多章节格式的分析结果
        analysis_result = env_project.analysis_result
        
        # 如果是多章节格式，需要找到对应的轨道
        if isinstance(analysis_result, dict) and not analysis_result.get('environment_tracks'):
            # 多章节格式，遍历所有章节找到对应的轨道
            all_tracks = []
            for chapter_id, chapter_data in analysis_result.items():
                if isinstance(chapter_data, dict) and 'environment_tracks' in chapter_data:
                    all_tracks.extend(chapter_data['environment_tracks'])
            
            if track_index >= len(all_tracks):
                raise HTTPException(status_code=404, detail="轨道索引超出范围")
            
            track = all_tracks[track_index]
        else:
            # 单章节格式，直接获取environment_tracks
            environment_tracks = analysis_result.get('environment_tracks', [])
            if track_index >= len(environment_tracks):
                raise HTTPException(status_code=404, detail="轨道索引超出范围")
            
            track = environment_tracks[track_index]
        
        # 检查是否有生成的文件
        if not track.get('generated_file_path'):
            raise HTTPException(status_code=404, detail="环境音文件尚未生成")
        
        file_path = track['generated_file_path']
        logger.info(f"[ENV_GEN_API] 文件路径: {file_path}")
        logger.info(f"[ENV_GEN_API] 文件路径长度: {len(file_path) if file_path else 0}")
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="环境音文件不存在")
        
        # 生成文件名 - 使用英文文件名避免编码问题
        keywords = track.get('environment_keywords', [])
        keyword_name = keywords[0] if keywords and len(keywords) > 0 else 'environment'
        # 将中文关键词转换为英文或使用默认名称
        if keyword_name == '娇喝声':
            safe_filename = f"shout_{project_id}_{track_index}.wav"
        elif keyword_name == '脚步声':
            safe_filename = f"footsteps_{project_id}_{track_index}.wav"
        elif keyword_name == '开门声':
            safe_filename = f"door_open_{project_id}_{track_index}.wav"
        else:
            # 对于其他中文关键词，使用拼音或英文
            safe_filename = f"environment_{project_id}_{track_index}.wav"
        
        # 返回音频文件 - 使用简单的英文文件名
        return FileResponse(
            path=file_path,
            media_type="audio/wav",
            filename=safe_filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 下载环境音失败: {str(e)}")
        import traceback
        logger.error(f"[ENV_GEN_API] 错误堆栈: {traceback.format_exc()}")
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
        # 从请求体中获取参数
        track_indices = request.get('track_indices') if request else None
        chapter_id = request.get('chapter_id') if request else None
        logger.info(f"[ENV_GEN_API] 开始混音环境音，项目ID: {project_id}，章节ID: {chapter_id}，轨道索引: {track_indices}")
        
        # 获取环境音项目
        env_service = EnvironmentProjectService(db)
        env_project = env_service.get_by_project_id(project_id)
        
        if not env_project or not env_project.analysis_result:
            raise HTTPException(status_code=404, detail="未找到环境音分析结果")
        
        # 重新查询数据库，确保读取到最新数据
        db.refresh(env_project)
        # 强制重新查询项目数据
        from app.models.environment_generation import EnvironmentProject
        env_project = db.query(EnvironmentProject).filter(EnvironmentProject.id == project_id).first()
        if not env_project:
            raise HTTPException(status_code=404, detail="未找到环境音项目")
        
        logger.info(f"[ENV_GEN_API] 重新查询数据库，确保读取最新数据")
        
        # 处理多章节格式的分析结果
        analysis_result = env_project.analysis_result
        environment_tracks = []
        
        logger.info(f"[ENV_GEN_API] 分析结果类型: {type(analysis_result)}")
        logger.info(f"[ENV_GEN_API] 分析结果键: {list(analysis_result.keys()) if isinstance(analysis_result, dict) else 'N/A'}")
        
        # 检查是否是多章节格式（键是章节ID）
        if isinstance(analysis_result, dict) and not analysis_result.get('environment_tracks'):
            # 多章节格式
            if chapter_id:
                # 只处理指定章节的轨道
                if str(chapter_id) in analysis_result:
                    chapter_analysis = analysis_result[str(chapter_id)]
                    logger.info(f"[ENV_GEN_API] 处理指定章节 {chapter_id} 的分析结果")
                    
                    if isinstance(chapter_analysis, dict) and chapter_analysis.get('environment_tracks'):
                        environment_tracks = chapter_analysis['environment_tracks']
                        logger.info(f"[ENV_GEN_API] 章节 {chapter_id} 轨道数量: {len(environment_tracks)}")
                    else:
                        logger.warning(f"[ENV_GEN_API] 章节 {chapter_id} 没有环境轨道")
                        environment_tracks = []
                else:
                    logger.warning(f"[ENV_GEN_API] 未找到章节 {chapter_id}")
                    environment_tracks = []
            else:
                # 如果没有指定章节ID，收集所有章节的环境轨道（保持向后兼容）
                sorted_chapter_ids = sorted(analysis_result.keys(), key=lambda x: int(x))
                logger.info(f"[ENV_GEN_API] 多章节格式，未指定章节ID，收集所有章节: {sorted_chapter_ids}")
                
                for chapter_id in sorted_chapter_ids:
                    chapter_analysis = analysis_result[chapter_id]
                    logger.info(f"[ENV_GEN_API] 章节 {chapter_id} 分析结果: {type(chapter_analysis)}")
                    
                    if isinstance(chapter_analysis, dict) and chapter_analysis.get('environment_tracks'):
                        chapter_tracks = chapter_analysis['environment_tracks']
                        logger.info(f"[ENV_GEN_API] 章节 {chapter_id} 轨道数量: {len(chapter_tracks)}")
                        environment_tracks.extend(chapter_tracks)
                    else:
                        logger.warning(f"[ENV_GEN_API] 章节 {chapter_id} 没有环境轨道")
        else:
            # 单章节格式，直接获取environment_tracks
            environment_tracks = analysis_result.get('environment_tracks', [])
            logger.info(f"[ENV_GEN_API] 单章节格式，轨道数量: {len(environment_tracks)}")
        
        logger.info(f"[ENV_GEN_API] 总轨道数量: {len(environment_tracks)}")
        
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
                keywords = track.get('environment_keywords', [])
                keyword_name = keywords[0] if keywords and len(keywords) > 0 else "无环境音"
                logger.info(f"[ENV_GEN_API] 检查轨道 {i}: {keyword_name}")
                logger.info(f"[ENV_GEN_API] 轨道 {i} 生成路径: {track.get('generated_file_path')}")
                if track.get('generated_file_path'):
                    logger.info(f"[ENV_GEN_API] 轨道 {i} 文件是否存在: {os.path.exists(track['generated_file_path'])}")
                    if os.path.exists(track['generated_file_path']):
                        tracks_to_mix.append((i, track))
                        logger.info(f"[ENV_GEN_API] 轨道 {i} 添加到混音列表")
                    else:
                        logger.warning(f"[ENV_GEN_API] 轨道 {i} 文件不存在: {track['generated_file_path']}")
                else:
                    logger.warning(f"[ENV_GEN_API] 轨道 {i} 没有生成路径")
        
        if not tracks_to_mix:
            raise HTTPException(status_code=400, detail="没有可混音的环境音文件")
        
        # 生成混音任务ID
        task_id = f"env_mix_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 启动混音任务
        logger.info(f"[ENV_GEN_API] 准备启动混音任务: {task_id}")
        logger.info(f"[ENV_GEN_API] 混音轨道数量: {len(tracks_to_mix)}")
        for i, (track_index, track) in enumerate(tracks_to_mix):
            logger.info(f"[ENV_GEN_API] 轨道{i}: 索引={track_index}, 文件={track.get('generated_file_path')}")
        
        background_tasks.add_task(
            mix_environment_sounds_task,
            task_id=task_id,
            project_id=project_id,
            tracks_to_mix=tracks_to_mix
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
        env_project = env_service.get_by_project_id(project_id)
        
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


@router.get("/mix-play/{project_id}")
async def play_mixed_environment_sounds(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    播放混音后的环境音文件
    """
    try:
        logger.info(f"[ENV_GEN_API] 播放混音环境音，项目ID: {project_id}")
        
        # 获取环境音项目
        env_service = EnvironmentProjectService(db)
        env_project = env_service.get_by_project_id(project_id)
        
        if not env_project:
            raise HTTPException(status_code=404, detail="未找到环境音项目")
        
        # 检查是否有混音文件
        mixed_file_path = env_project.matching_result.get('mixed_file_path')
        if not mixed_file_path or not os.path.exists(mixed_file_path):
            raise HTTPException(status_code=404, detail="混音文件尚未生成")
        
        # 返回混音文件用于播放
        return FileResponse(
            path=mixed_file_path,
            media_type="audio/wav",
            headers={"Content-Disposition": "inline"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ENV_GEN_API] 播放混音环境音失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"播放混音环境音失败: {str(e)}")


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
        env_project = env_service.get_by_project_id(project_id)
        
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
        env_project = env_service.get_by_project_id(project_id)
        
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
                "project_status": env_project.status,
                "matching_result": env_project.matching_result
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
        env_project = env_service.get_by_project_id(project_id)
        
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
            keywords = track.get('environment_keywords', [])
            keyword = keywords[0] if keywords and len(keywords) > 0 else ''
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
        
        # 导入必要的模块
        from pydub import AudioSegment
        import os
        from datetime import datetime
        
        # 获取环境音项目
        from app.database import get_db
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
