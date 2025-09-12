"""
简化的环境音生成API端点
流程：书籍分析 → 同步环境音 → 生成音频 → 混音/文件操作
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Body, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.tangoflux_environment_generator import TangoFluxEnvironmentGenerator
from app.services.environment_mixing_service import EnvironmentMixingService
from app.services.environment_data_service import EnvironmentDataService
from app.services.environment_project_data_service import EnvironmentProjectDataService
from app.services.environment_file_service import EnvironmentFileService
from app.utils.logger import get_logger
from app.database import get_db

logger = get_logger(__name__)
router = APIRouter()


@router.post("/generate/{project_id}")
async def generate_environment_sounds(
    project_id: int,
    background_tasks: BackgroundTasks,
    request: Dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """生成环境音文件"""
    try:
        track_indices = request.get('track_indices')
        logger.info(f"[ENV_GEN] 开始生成，项目: {project_id}，轨道: {track_indices}")
        
        # 获取项目和轨道数据
        data_service = EnvironmentProjectDataService(db)
        env_project = data_service.get_project_with_validation(project_id)
        environment_tracks = data_service.extract_environment_tracks(env_project)
        
        if not environment_tracks:
            raise HTTPException(status_code=400, detail="没有环境音轨道配置")
        
        # 筛选要生成的轨道
        tracks_to_generate = data_service.filter_tracks_for_generation(environment_tracks, track_indices)
        
        if not tracks_to_generate:
            raise HTTPException(status_code=400, detail="没有有效的轨道需要生成")
        
        # 启动生成任务
        generator = TangoFluxEnvironmentGenerator()
        task_id = f"env_gen_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        background_tasks.add_task(
            generator.generate_project_environment_sounds,
            project_id=project_id,
            tracks_to_generate=tracks_to_generate,
            task_id=task_id
        )
        
        logger.info(f"[ENV_GEN] 任务已启动: {task_id}")
        
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "project_id": project_id,
                "total_tracks": len(tracks_to_generate),
                "status": "processing"
            },
            "message": f"生成任务已启动，共 {len(tracks_to_generate)} 个轨道"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[ENV_GEN] 生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.post("/mix/{project_id}")
async def mix_environment_sounds(
    project_id: int,
    background_tasks: BackgroundTasks,
    request: Dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """混音环境音文件"""
    try:
        track_indices = request.get('track_indices')
        chapter_id = request.get('chapter_id')
        logger.info(f"[ENV_MIX] 开始混音，项目: {project_id}，章节: {chapter_id}，轨道: {track_indices}")
        
        # 获取项目和轨道数据
        data_service = EnvironmentProjectDataService(db)
        env_project = data_service.get_project_with_validation(project_id)
        environment_tracks = data_service.extract_environment_tracks(env_project, chapter_id)
        
        if not environment_tracks:
            raise HTTPException(status_code=400, detail="没有环境音轨道配置")
        
        # 筛选要混音的轨道
        tracks_to_mix = data_service.filter_tracks_for_mixing(environment_tracks, track_indices)
        
        if not tracks_to_mix:
            raise HTTPException(status_code=400, detail="没有可混音的环境音文件")
        
        # 启动混音任务
        task_id = f"env_mix_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        background_tasks.add_task(
            EnvironmentMixingService.mix_environment_sounds_task,
            task_id=task_id,
            project_id=project_id,
            tracks_to_mix=tracks_to_mix
        )
        
        logger.info(f"[ENV_MIX] 任务已启动: {task_id}")
        
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "project_id": project_id,
                "total_tracks": len(tracks_to_mix),
                "status": "processing"
            },
            "message": f"混音任务已启动，共 {len(tracks_to_mix)} 个轨道"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[ENV_MIX] 混音失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"混音失败: {str(e)}")


@router.get("/file/{project_id}/{track_index}")
async def handle_track_file(
    project_id: int,
    track_index: int,
    action: str = Query(..., description="文件操作类型: preview, download"),
    db: Session = Depends(get_db)
):
    """统一的轨道文件处理端点"""
    try:
        logger.info(f"[ENV_FILE] {action} 轨道文件，项目: {project_id}，轨道: {track_index}")
        
        # 获取轨道数据
        data_service = EnvironmentProjectDataService(db)
        env_project, track = data_service.get_track_by_index(project_id, track_index)
        
        # 检查文件
        file_path = track.get('generated_file_path')
        if not file_path:
            raise HTTPException(status_code=404, detail="环境音文件尚未生成")
        
        # 生成文件名并返回响应
        filename = EnvironmentFileService.generate_safe_filename(track, project_id, track_index)
        return EnvironmentFileService.create_file_response(file_path, filename, action)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[ENV_FILE] {action} 失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"{action} 失败: {str(e)}")


@router.get("/mixed-file/{project_id}")
async def handle_mixed_file(
    project_id: int,
    action: str = Query(..., description="文件操作类型: preview, download, play"),
    db: Session = Depends(get_db)
):
    """统一的混音文件处理端点"""
    try:
        logger.info(f"[ENV_MIXED_FILE] {action} 混音文件，项目: {project_id}")
        
        # 获取项目数据
        data_service = EnvironmentProjectDataService(db)
        env_project = data_service.get_project_with_validation(project_id)
        
        # 检查混音文件
        if not env_project.matching_result or not env_project.matching_result.get('mixed_file_path'):
            raise HTTPException(status_code=404, detail="混音文件尚未生成")
        
        file_path = env_project.matching_result['mixed_file_path']
        filename = f"mixed_environment_{project_id}.wav"
        
        return EnvironmentFileService.create_file_response(file_path, filename, action)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[ENV_MIXED_FILE] {action} 失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"{action} 失败: {str(e)}")


@router.get("/status/{project_id}")
async def get_generation_status(
    project_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取环境音生成状态"""
    try:
        import os
        logger.info(f"[ENV_STATUS] 获取状态，项目: {project_id}")
        
        # 获取项目和轨道数据
        data_service = EnvironmentProjectDataService(db)
        env_project = data_service.get_project_with_validation(project_id)
        environment_tracks = data_service.extract_environment_tracks(env_project)
        
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
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[ENV_STATUS] 获取状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.post("/projects/{env_project_id}/sync-chapter/{chapter_id}")
async def sync_chapter_environment_sounds(
    env_project_id: int,
    chapter_id: int,
    request: Dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """同步章节环境音数据到环境音项目"""
    try:
        import json
        from app.models.analysis_result import AnalysisResult
        
        mode = request.get('mode', 'overwrite')
        logger.info(f"[ENV_SYNC] 同步章节环境音，项目: {env_project_id}，章节: {chapter_id}，模式: {mode}")
        
        # 获取环境音项目
        data_service = EnvironmentProjectDataService(db)
        env_project = data_service.env_service.get_by_project_id(env_project_id)
        
        if not env_project:
            raise HTTPException(status_code=404, detail="未找到环境音项目")
        
        if not env_project.novel_project_id:
            raise HTTPException(status_code=400, detail="环境音项目未关联书籍分析项目")
        
        # 获取书籍分析结果
        analysis_result = db.query(AnalysisResult).filter(
            AnalysisResult.project_id == env_project.novel_project_id,
            AnalysisResult.chapter_id == chapter_id
        ).first()
        
        if not analysis_result or not analysis_result.original_analysis:
            raise HTTPException(status_code=404, detail=f"未找到章节 {chapter_id} 的书籍分析结果")
        
        # 提取和转换数据
        chapter_data = analysis_result.original_analysis
        if isinstance(chapter_data, str):
            chapter_data = json.loads(chapter_data)
        
        book_analysis = {str(chapter_id): chapter_data}
        environment_sounds = EnvironmentDataService.extract_environment_sounds_from_analysis(book_analysis, chapter_id)
        
        if not environment_sounds:
            raise HTTPException(status_code=404, detail=f"章节 {chapter_id} 中未找到可同步的环境音数据")
        
        environment_tracks = EnvironmentDataService.convert_to_environment_tracks_format(environment_sounds)
        
        # 🚀 新增：使用LLM批量翻译中文描述生成英文提示词
        from app.services.translation_service import TranslationService
        translation_service = TranslationService()
        
        # 收集需要翻译的描述
        tracks_to_translate = []
        descriptions_to_translate = []
        
        for i, track in enumerate(environment_tracks):
            chinese_description = track.get('chinese_description', '')
            if chinese_description and not track.get('english_prompt'):
                tracks_to_translate.append(i)
                descriptions_to_translate.append(f"环境音效描述: {chinese_description}")
        
        # 批量翻译
        if descriptions_to_translate:
            try:
                logger.info(f"[ENV_SYNC] 开始批量翻译 {len(descriptions_to_translate)} 个环境音描述")
                english_prompts = await translation_service.batch_translate_chinese_to_english(descriptions_to_translate)
                
                # 应用翻译结果
                for track_index, english_prompt in zip(tracks_to_translate, english_prompts):
                    track = environment_tracks[track_index]
                    # 清理翻译结果，移除可能的前缀
                    if english_prompt.lower().startswith('environmental sound'):
                        english_prompt = english_prompt[len('environmental sound'):].strip(':').strip()
                    track['english_prompt'] = f"Natural ambient sound: {english_prompt}"
                    
                logger.info(f"[ENV_SYNC] 批量翻译完成: {len(descriptions_to_translate)} 个描述")
                
            except Exception as e:
                logger.error(f"[ENV_SYNC] 批量翻译失败: {str(e)}")
                # 翻译失败时为每个轨道生成基础英文提示
                for track_index in tracks_to_translate:
                    track = environment_tracks[track_index]
                    keyword = track.get('keyword', '环境音')
                    track['english_prompt'] = f"Natural ambient sound of {keyword}, environmental audio, realistic and clear"
        
        # 更新环境音项目的分析结果
        current_analysis_result = env_project.analysis_result or {}
        
        if mode == 'overwrite':
            current_analysis_result[str(chapter_id)] = {
                'environment_tracks': environment_tracks,
                'chapter_id': chapter_id,
                'sync_timestamp': datetime.now().isoformat(),
                'source': 'book_analysis_sync'
            }
        elif mode == 'merge':
            if str(chapter_id) in current_analysis_result:
                existing_tracks = current_analysis_result[str(chapter_id)].get('environment_tracks', [])
                merged_tracks = existing_tracks + environment_tracks
                current_analysis_result[str(chapter_id)]['environment_tracks'] = merged_tracks
            else:
                current_analysis_result[str(chapter_id)] = {
                    'environment_tracks': environment_tracks,
                    'chapter_id': chapter_id,
                    'sync_timestamp': datetime.now().isoformat(),
                    'source': 'book_analysis_sync'
                }
        
        # 保存到数据库 - 🚀 修复：使用flag_modified告诉SQLAlchemy JSON字段已修改
        from sqlalchemy.orm.attributes import flag_modified
        env_project.analysis_result = current_analysis_result
        flag_modified(env_project, 'analysis_result')  # 标记字段已修改
        
        logger.info(f"[ENV_SYNC] 准备提交数据库更新，项目: {env_project_id}")
        db.commit()
        logger.info(f"[ENV_SYNC] 数据库更新完成")
        
        logger.info(f"[ENV_SYNC] 成功同步章节 {chapter_id}，共 {len(environment_tracks)} 个轨道")
        
        return {
            "success": True,
            "data": {
                "chapter_id": chapter_id,
                "tracks_count": len(environment_tracks),
                "environment_tracks": environment_tracks,
                "mode": mode,
                "sync_timestamp": datetime.now().isoformat()
            },
            "message": f"成功同步章节 {chapter_id} 的环境音数据，共 {len(environment_tracks)} 个轨道"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ENV_SYNC] 同步失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


@router.get("/book-analysis/{project_id}/environment-sounds")
async def get_book_analysis_environment_sounds(
    project_id: int,
    chapter_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """从书籍分析结果中获取环境音数据（用于预览）"""
    try:
        import json
        from app.models.novel_project import NovelProject
        from app.models.analysis_result import AnalysisResult
        
        logger.info(f"[ENV_BOOK_ANALYSIS] 获取环境音数据，项目: {project_id}，章节: {chapter_id}")
        
        # 获取项目和分析结果
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="未找到项目")
        
        analysis_results = db.query(AnalysisResult).filter(
            AnalysisResult.project_id == project_id
        ).all()
        
        if not analysis_results:
            raise HTTPException(status_code=404, detail="未找到书籍分析结果")
        
        # 构建分析结果字典
        analysis_result = {}
        for result in analysis_results:
            if result.original_analysis:
                chapter_data = result.original_analysis
                if isinstance(chapter_data, str):
                    chapter_data = json.loads(chapter_data)
                analysis_result[str(result.chapter_id)] = chapter_data
        
        # 提取和转换数据
        environment_sounds = EnvironmentDataService.extract_environment_sounds_from_analysis(analysis_result, chapter_id)
        formatted_data = EnvironmentDataService.convert_to_frontend_format(environment_sounds)
        
        logger.info(f"[ENV_BOOK_ANALYSIS] 成功提取 {len(formatted_data)} 个环境音数据")
        
        return {
            "success": True,
            "data": formatted_data,
            "message": f"成功提取{len(formatted_data)}个环境音数据"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ENV_BOOK_ANALYSIS] 获取失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "获取书籍分析环境音失败"
        }


