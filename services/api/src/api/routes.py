"""
API路由定义
"""

import os
import time
import uuid
import base64
import json
import logging
import tempfile
import glob
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import FileResponse

from src.utils.audio import save_audio
from .server import app, get_tts_engine, get_config, get_task_store
from .models.requests import TTSRequest, NovelProcessRequest
from .models.responses import (
    TTSResponse, NovelProcessResponse, TaskStatusResponse,
    SystemInfoResponse, StatsResponse, VoiceFeatureExtractResponse,
    VoiceFeatureListResponse, VoiceFeatureDetailResponse, VoiceTagsResponse,
    CharacterListResponse, CharacterDetailResponse, CharacterAnalysisResponse
)

logger = logging.getLogger("api.routes")

# 创建路由
router = APIRouter()

@router.get("/")
async def root():
    """API根路径"""
    return {"message": "MegaTTS API服务已启动", "version": "1.0.0"}

@router.get("/health")
async def health_check():
    """健康检查"""
    # 简化健康检查，仅返回基本信息，避免潜在的导入错误
    import time
    import platform
    from . import server
    start_time = server.start_time
    
    # 服务运行时间（秒）
    uptime = time.time() - start_time
    
    # 基本健康信息
    health_info = {
        "status": "ok",
        "version": "1.0.0",
        "uptime": uptime,
        "uptime_formatted": f"{int(uptime//86400)}天 {int((uptime%86400)//3600)}时 {int((uptime%3600)//60)}分 {int(uptime%60)}秒",
        "system": {
            "platform": platform.platform(),
            "python": platform.python_version(),
        }
    }
    
    # 尝试获取引擎状态
    try:
        # 获取服务监控器
        monitor = server.get_service_monitor()
        if monitor:
            # 获取引擎健康状态
            health_info["engines"] = monitor.get_health_status()
    except Exception as e:
        logger.warning(f"获取引擎健康状态失败: {str(e)}")
    
    return health_info

@router.get("/health/engines")
async def engine_health_check():
    """引擎健康检查"""
    try:
        # 获取TTS路由器
        from . import server
        router = server.get_tts_router()
        if not router:
            return {
                "status": "error",
                "message": "TTS引擎路由器未初始化"
            }
        
        # 执行健康检查
        results = await router.check_all_engines_health()
        
        # 所有引擎都健康时返回正常状态
        all_healthy = all(results.values())
        
        return {
            "status": "ok" if all_healthy else "warning",
            "message": "所有引擎健康" if all_healthy else "部分引擎不健康",
            "engines": router.get_health_status()
        }
    except Exception as e:
        logger.error(f"引擎健康检查失败: {str(e)}")
        return {
            "status": "error",
            "message": f"引擎健康检查失败: {str(e)}"
        }

@router.get("/api/engines/health")
async def get_engines_health():
    """获取所有引擎健康状态"""
    try:
        # 获取服务监控器
        from . import server
        monitor = server.get_service_monitor()
        if not monitor:
            raise HTTPException(
                status_code=500,
                detail="服务监控器未初始化"
            )
        
        # 获取健康状态
        health_status = monitor.get_health_status()
        
        # 如果没有健康状态数据，立即执行一次检查
        if not health_status:
            await monitor._check_services()
            health_status = monitor.get_health_status()
            
        return health_status
    except Exception as e:
        logger.error(f"获取引擎健康状态失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取引擎健康状态失败: {str(e)}"
        )

@router.post("/api/tts", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    """
    文本转语音API
    
    将文本转换为语音，支持不同音色和情感
    """
    try:
        # 获取TTS引擎路由器和选择器
        tts_router = server.get_tts_router()
        engine_selector = server.get_engine_selector()
        
        if not tts_router or not engine_selector:
            raise HTTPException(
                status_code=500,
                detail="TTS引擎路由器未初始化"
            )
        
        # 确定要使用的引擎
        engine_type = None
        
        # 如果用户指定了引擎
        if request.engine and request.engine != "auto":
            try:
                from src.tts.engine import TTSEngineType
                engine_type = TTSEngineType(request.engine)
                logger.info(f"用户指定引擎: {engine_type.value}")
            except ValueError:
                logger.warning(f"无效的引擎类型: {request.engine}，使用自动选择")
        
        # 如果未指定或指定了auto，使用选择器
        if not engine_type:
            # 准备选择器需要的额外参数
            requirements = {
                "emotion_type": request.emotion_type,
                "emotion_intensity": request.emotion_intensity,
                "formal": request.formal
            }
            
            # 使用选择器选择引擎
            engine_type = engine_selector.select_engine(request.text, requirements)
            logger.info(f"选择器选择的引擎: {engine_type.value}")
        
        # 合成语音
        process_start_time = time.time()
        audio = await tts_router.synthesize(
            engine_type=engine_type,
            text=request.text,
            voice_id=request.voice_id,
            emotion_type=request.emotion_type,
            emotion_intensity=request.emotion_intensity,
            speed_scale=request.speed_scale,
            pitch_scale=request.pitch_scale
        )
        process_time = time.time() - process_start_time
        
        # 返回Base64或临时文件
        if request.return_base64:
            # 使用唯一文件名避免冲突
            unique_filename = f"megatts_tmp_{uuid.uuid4().hex}.{request.output_format}"
            
            # 创建项目目录下的临时文件夹
            temp_dir = os.path.join("D:/AI-Sound/output/temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            # 在项目目录下创建临时文件
            tmp_name = os.path.join(temp_dir, unique_filename)
            
            try:
                # 保存音频
                save_audio(tmp_name, audio, format=request.output_format)
                
                # 添加小延迟确保文件写入完成
                time.sleep(0.1)
                
                # 读取为二进制数据
                with open(tmp_name, "rb") as f:
                    audio_bytes = f.read()
                
                # 关闭文件后再次延迟
                time.sleep(0.1)
                
                audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
                return TTSResponse(
                    success=True,
                    message="语音合成成功",
                    engine=engine_type.value,
                    audio_base64=audio_base64,
                    duration=len(audio) / 22050  # 假设采样率为22050
                )
            finally:
                # 确保无论如何都会尝试删除临时文件
                try:
                    if os.path.exists(tmp_name):
                        # 最多尝试3次删除
                        for i in range(3):
                            try:
                                os.unlink(tmp_name)
                                break
                            except Exception as e:
                                if i < 2:  # 如果不是最后一次尝试
                                    time.sleep(0.2)  # 等待一段时间再试
                                else:
                                    logger.warning(f"清理临时文件失败（第{i+1}次尝试）: {str(e)}")
                except Exception as cleanup_error:
                    logger.warning(f"清理临时文件失败: {str(cleanup_error)}")
        else:
            # 保存到临时文件并返回下载链接
            audio_id = f"audio_{uuid.uuid4().hex[:8]}"
            output_dir = os.path.join(get_config()["output_dir"], "single")
            os.makedirs(output_dir, exist_ok=True)
            
            output_path = os.path.join(output_dir, f"{audio_id}.{request.output_format}")
            save_audio(output_path, audio, format=request.output_format)
            
            return TTSResponse(
                success=True,
                message="语音合成成功",
                engine=engine_type.value,
                audio_url=f"/api/download/{audio_id}.{request.output_format}",
                duration=len(audio) / 22050  # 假设采样率为22050
            )
            
    except Exception as e:
        logger.error(f"语音合成失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"语音合成失败: {str(e)}"
        )

# 增加/api/tts/text路由作为/api/tts的别名
@router.post("/api/tts/text", response_model=TTSResponse)
async def text_to_speech_alias(request: TTSRequest):
    """
    文本转语音API (别名)
    
    与/api/tts完全相同的功能，作为兼容接口提供
    """
    # 直接调用原有API实现
    return await text_to_speech(request)

@router.post("/api/tts/text_multipart", response_model=TTSResponse)
async def text_to_speech_multipart(
    text: str = Form(...),
    voice_id: str = Form("female_young"),
    emotion_type: str = Form("neutral"),
    emotion_intensity: float = Form(0.5),
    speed_scale: float = Form(None),
    pitch_scale: float = Form(None),
    p_w: float = Form(None),
    t_w: float = Form(None),
    return_base64: bool = Form(False),
    output_format: str = Form("wav"),
    voice_file: UploadFile = File(None),
    voice_npy: UploadFile = File(None),
    voice_ref_id: str = Form(None)
):
    """
    文本转语音API（multipart版，支持声纹文件上传与参数灵活配置）
    """
    try:
        engine = get_tts_engine()
        # 声纹特征处理
        voice_feature = None
        if voice_npy is not None:
            # 直接上传npy特征
            npy_bytes = await voice_npy.read()
            import numpy as np
            import io
            voice_feature = np.load(io.BytesIO(npy_bytes))
        elif voice_file is not None:
            # 上传wav，需预处理
            wav_bytes = await voice_file.read()
            # 这里假设engine支持动态声纹特征注入
            voice_feature = engine.preprocess_voice(wav_bytes)
        elif voice_ref_id:
            # TODO: 支持通过ID引用已存储声纹
            voice_feature = engine.get_voice_feature_by_id(voice_ref_id)
        else:
            voice_feature = None  # 用默认参考音色

        # 合成语音
        audio = engine.synthesize(
            text=text,
            voice_id=voice_id,
            emotion_type=emotion_type,
            emotion_intensity=emotion_intensity,
            speed_scale=speed_scale,
            pitch_scale=pitch_scale,
            p_w=p_w,
            t_w=t_w,
            voice_feature=voice_feature
        )
        # 返回Base64或文件
        if return_base64:
            # 修改：使用上下文管理器确保文件被正确关闭，并使用try-finally保证文件被删除
            # 使用唯一文件名避免冲突
            unique_filename = f"megatts_tmp_{uuid.uuid4().hex}.{output_format}"
            
            # 创建项目目录下的临时文件夹
            temp_dir = os.path.join("D:/AI-Sound/output/temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            # 在项目目录下创建临时文件
            tmp_name = os.path.join(temp_dir, unique_filename)
            
            try:
                # 保存音频
                save_audio(tmp_name, audio, format=output_format)
                
                # 添加小延迟确保文件写入完成
                time.sleep(0.1)
                
                # 读取为二进制数据
                with open(tmp_name, "rb") as f:
                    audio_bytes = f.read()
                
                # 关闭文件后再次延迟
                time.sleep(0.1)
                
                audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
                return TTSResponse(
                    success=True,
                    message="语音合成成功",
                    audio_base64=audio_base64,
                    duration=len(audio) / 22050
                )
            finally:
                # 确保无论如何都会尝试删除临时文件
                try:
                    if os.path.exists(tmp_name):
                        # 最多尝试3次删除
                        for i in range(3):
                            try:
                                os.unlink(tmp_name)
                                break
                            except Exception as e:
                                if i < 2:  # 如果不是最后一次尝试
                                    time.sleep(0.2)  # 等待一段时间再试
                                else:
                                    logger.warning(f"清理临时文件失败（第{i+1}次尝试）: {str(e)}")
                except Exception as cleanup_error:
                    logger.warning(f"清理临时文件失败: {str(cleanup_error)}")
        else:
            audio_id = f"audio_{uuid.uuid4().hex[:8]}"
            output_dir = os.path.join(get_config()["output_dir"], "single")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{audio_id}.{output_format}")
            save_audio(output_path, audio, format=output_format)
            return TTSResponse(
                success=True,
                message="语音合成成功",
                audio_url=f"/api/download/{audio_id}.{output_format}",
                duration=len(audio) / 22050
            )
    except Exception as e:
        logger.error(f"语音合成失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"语音合成失败: {str(e)}"
        )

# 文件下载接口
@router.get("/api/download/{filename}")
async def download_file(filename: str):
    """
    下载文件
    
    通过文件名下载生成的音频文件
    """
    # 安全检查，避免路径遍历攻击
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=400,
            detail="无效的文件名"
        )
    
    # 确定文件类型
    if filename.startswith("audio_"):
        file_path = os.path.join(get_config()["output_dir"], "single", filename)
    else:
        file_path = os.path.join(get_config()["output_dir"], filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"文件不存在: {filename}"
        )
    
    return FileResponse(file_path)

# 小说处理接口
@router.post("/api/tts/novel", response_model=NovelProcessResponse)
async def process_novel(
    request: NovelProcessRequest, 
    background_tasks: BackgroundTasks
):
    """
    小说处理API
    
    将整本小说处理为章节有声书，异步执行
    """
    try:
        # 验证路径
        if not os.path.exists(request.novel_path):
            raise HTTPException(
                status_code=404,
                detail=f"小说文件不存在: {request.novel_path}"
            )
        
        # 确定输出目录
        output_dir = request.output_dir
        if not output_dir:
            novel_name = os.path.basename(request.novel_path)
            novel_name = os.path.splitext(novel_name)[0]
            output_dir = os.path.join(get_config()["output_dir"], "novels", novel_name)
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 创建任务ID
        task_id = f"novel_{uuid.uuid4().hex[:8]}"
        
        # 获取任务存储
        task_store = get_task_store()
        
        # 存储任务初始状态
        task_store[task_id] = {
            "status": "pending",
            "progress": 0.0,
            "message": "任务已创建，等待处理",
            "novel_path": request.novel_path,
            "output_dir": output_dir,
            "created_at": time.time(),
            "updated_at": time.time()
        }
        
        # 定义后台处理函数
        async def process_novel_background(task_id: str):
            try:
                # 对小说进行分段和处理
                from src.processor.novel_processor import NovelSegmenter, NovelAudioGenerator
                from src.tts.character_voice import CharacterVoiceMapper
                
                # 更新任务状态为处理中
                task_store[task_id] = {
                    **task_store[task_id],
                    "status": "processing",
                    "message": "正在处理小说...",
                    "updated_at": time.time()
                }
                
                # 获取TTS引擎
                engine = get_tts_engine()
                if not engine:
                    raise Exception("初始TTS引擎失败")
                
                # 定义进度回调
                def progress_callback(progress, current_chapter, total_chapters):
                    task_store[task_id] = {
                        **task_store[task_id],
                        "progress": progress,
                        "message": f"正在处理 {current_chapter}/{total_chapters} 章",
                        "current_chapter": current_chapter,
                        "total_chapters": total_chapters,
                        "updated_at": time.time()
                    }
                
                # 处理配置
                config = get_config()
                processor_config = config.get("processing", {})
                
                # 语音映射
                voice_mapping = request.voice_mapping or config.get("voice_mapping", {})
                
                # 获取角色声音映射器
                character_mapper = CharacterVoiceMapper()
                
                # 创建小说处理器
                segmenter = NovelSegmenter()
                audio_generator = NovelAudioGenerator(
                    tts_engine=engine,
                    config=processor_config,
                    voice_mapping=voice_mapping,
                    character_mapper=character_mapper
                )
                
                # 是否恢复处理
                if request.resume_if_exists and os.path.exists(os.path.join(output_dir, "progress.json")):
                    # 恢复处理
                    result = audio_generator.resume_processing(
                        output_dir=output_dir,
                        progress_callback=progress_callback
                    )
                else:
                    # 新处理
                    segments = segmenter.segment_novel(request.novel_path)
                    
                    result = audio_generator.process_novel(
                        novel_path=request.novel_path,
                        output_dir=output_dir,
                        progress_callback=progress_callback,
                        auto_character_mapping=request.auto_character_mapping
                    )
                
                # 更新任务状态为完成
                task_store[task_id] = {
                    **task_store[task_id],
                    "status": "completed",
                    "progress": 1.0,
                    "message": "小说处理完成",
                    "result": result,
                    "updated_at": time.time()
                }
                
            except Exception as e:
                logger.error(f"小说处理失败: {str(e)}")
                
                # 更新任务状态为失败
                task_store[task_id] = {
                    **task_store[task_id],
                    "status": "failed",
                    "message": "处理失败",
                    "error": str(e),
                    "updated_at": time.time()
                }
        
        # 添加到后台任务
        background_tasks.add_task(process_novel_background, task_id)
        
        return NovelProcessResponse(
            success=True,
            message="小说处理任务已创建",
            task_id=task_id,
            status_url=f"/api/tasks/{task_id}"
        )
            
    except Exception as e:
        logger.error(f"创建小说处理任务失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"创建小说处理任务失败: {str(e)}"
        )

@router.get("/api/novels")
async def get_novels():
    """
    获取小说列表
    
    返回所有已处理和待处理的小说信息
    """
    try:
        # 获取配置
        config = get_config()
        novels_dir = os.path.join(config["output_dir"], "novels")
        
        # 确保小说目录存在
        os.makedirs(novels_dir, exist_ok=True)
        
        # 获取所有小说目录
        novel_dirs = [d for d in os.listdir(novels_dir) if os.path.isdir(os.path.join(novels_dir, d))]
        
        novels = []
        for novel_dir in novel_dirs:
            novel_path = os.path.join(novels_dir, novel_dir)
            info_path = os.path.join(novel_path, "info.json")
            
            # 默认小说信息
            novel_info = {
                "id": novel_dir,
                "title": novel_dir,
                "chapters": 0,
                "status": "unknown",
                "created_at": os.path.getctime(novel_path),
                "updated_at": os.path.getmtime(novel_path),
                "audio_size_mb": 0,
                "duration_seconds": 0
            }
            
            # 读取info.json获取详细信息
            if os.path.exists(info_path):
                try:
                    with open(info_path, "r", encoding="utf-8") as f:
                        info = json.load(f)
                    
                    # 更新小说信息
                    novel_info.update(info)
                except Exception as e:
                    logger.warning(f"读取小说信息失败: {novel_dir} - {str(e)}")
            
            # 获取章节信息
            chapters_dir = os.path.join(novel_path, "chapters")
            if os.path.exists(chapters_dir):
                chapter_count = len([c for c in os.listdir(chapters_dir) if os.path.isdir(os.path.join(chapters_dir, c))])
                novel_info["chapters"] = chapter_count
            
            # 计算音频文件总大小
            audio_size = 0
            audio_files = []
            for root, _, files in os.walk(novel_path):
                for file in files:
                    if file.endswith((".wav", ".mp3", ".ogg")):
                        file_path = os.path.join(root, file)
                        audio_size += os.path.getsize(file_path)
                        audio_files.append(file_path)
            
            novel_info["audio_size_mb"] = round(audio_size / (1024 * 1024), 2)
            
            # 添加到小说列表
            novels.append(novel_info)
        
        # 按更新时间排序，最新的在前
        novels.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
        
        return {
            "success": True,
            "count": len(novels),
            "novels": novels
        }
    except Exception as e:
        logger.error(f"获取小说列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取小说列表失败: {str(e)}"
        )

@router.get("/api/novels/{novel_id}")
async def get_novel_details(novel_id: str):
    """
    获取小说详情
    
    返回指定小说的详细信息，包括章节列表等
    """
    try:
        # 获取配置
        config = get_config()
        novel_path = os.path.join(config["output_dir"], "novels", novel_id)
        
        # 检查小说是否存在
        if not os.path.exists(novel_path) or not os.path.isdir(novel_path):
            raise HTTPException(
                status_code=404,
                detail=f"小说不存在: {novel_id}"
            )
        
        # 读取小说信息
        info_path = os.path.join(novel_path, "info.json")
        
        # 默认小说信息
        novel_info = {
            "id": novel_id,
            "title": novel_id,
            "chapters": [],
            "status": "unknown",
            "created_at": os.path.getctime(novel_path),
            "updated_at": os.path.getmtime(novel_path),
            "audio_size_mb": 0,
            "duration_seconds": 0
        }
        
        # 读取info.json获取详细信息
        if os.path.exists(info_path):
            try:
                with open(info_path, "r", encoding="utf-8") as f:
                    info = json.load(f)
                
                # 更新小说信息
                novel_info.update(info)
            except Exception as e:
                logger.warning(f"读取小说信息失败: {novel_id} - {str(e)}")
        
        # 获取章节信息
        chapters_dir = os.path.join(novel_path, "chapters")
        chapters = []
        
        if os.path.exists(chapters_dir):
            # 获取所有章节目录
            chapter_dirs = [d for d in os.listdir(chapters_dir) if os.path.isdir(os.path.join(chapters_dir, d))]
            
            for chapter_dir in sorted(chapter_dirs):
                chapter_path = os.path.join(chapters_dir, chapter_dir)
                chapter_info_path = os.path.join(chapter_path, "info.json")
                
                # 默认章节信息
                chapter_info = {
                    "id": chapter_dir,
                    "title": chapter_dir,
                    "duration_seconds": 0,
                    "audio_size_mb": 0,
                    "has_audio": False
                }
                
                # 读取章节信息
                if os.path.exists(chapter_info_path):
                    try:
                        with open(chapter_info_path, "r", encoding="utf-8") as f:
                            info = json.load(f)
                        
                        # 更新章节信息
                        chapter_info.update(info)
                    except Exception as e:
                        logger.warning(f"读取章节信息失败: {chapter_dir} - {str(e)}")
                
                # 检查音频文件
                audio_files = []
                for ext in [".wav", ".mp3", ".ogg"]:
                    audio_file = os.path.join(chapter_path, f"audio{ext}")
                    if os.path.exists(audio_file):
                        audio_files.append(audio_file)
                        chapter_info["has_audio"] = True
                        chapter_info["audio_size_mb"] = round(os.path.getsize(audio_file) / (1024 * 1024), 2)
                        chapter_info["audio_url"] = f"/api/novels/{novel_id}/chapters/{chapter_dir}/audio"
                
                # 获取章节内容文件
                content_file = os.path.join(chapter_path, "content.txt")
                if os.path.exists(content_file):
                    try:
                        with open(content_file, "r", encoding="utf-8") as f:
                            chapter_info["content_preview"] = f.read(500) + "..."  # 只取前500字符作为预览
                    except Exception as e:
                        logger.warning(f"读取章节内容失败: {chapter_dir} - {str(e)}")
                
                chapters.append(chapter_info)
        
        novel_info["chapters"] = chapters
        
        # 计算总音频大小
        audio_size = 0
        for root, _, files in os.walk(novel_path):
            for file in files:
                if file.endswith((".wav", ".mp3", ".ogg")):
                    file_path = os.path.join(root, file)
                    audio_size += os.path.getsize(file_path)
        
        novel_info["audio_size_mb"] = round(audio_size / (1024 * 1024), 2)
        
        return {
            "success": True,
            "novel": novel_info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取小说详情失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取小说详情失败: {str(e)}"
        )

@router.get("/api/novels/{novel_id}/chapters")
async def get_novel_chapters(novel_id: str):
    """
    获取小说章节列表
    
    返回指定小说的所有章节信息
    """
    try:
        # 获取配置
        config = get_config()
        novel_path = os.path.join(config["output_dir"], "novels", novel_id)
        
        # 检查小说是否存在
        if not os.path.exists(novel_path) or not os.path.isdir(novel_path):
            raise HTTPException(
                status_code=404,
                detail=f"小说不存在: {novel_id}"
            )
        
        # 获取章节信息
        chapters_dir = os.path.join(novel_path, "chapters")
        chapters = []
        
        if os.path.exists(chapters_dir):
            # 获取所有章节目录
            chapter_dirs = [d for d in os.listdir(chapters_dir) if os.path.isdir(os.path.join(chapters_dir, d))]
            
            for chapter_dir in sorted(chapter_dirs):
                chapter_path = os.path.join(chapters_dir, chapter_dir)
                chapter_info_path = os.path.join(chapter_path, "info.json")
                
                # 默认章节信息
                chapter_info = {
                    "id": chapter_dir,
                    "title": chapter_dir,
                    "duration_seconds": 0,
                    "has_audio": False
                }
                
                # 读取章节信息
                if os.path.exists(chapter_info_path):
                    try:
                        with open(chapter_info_path, "r", encoding="utf-8") as f:
                            info = json.load(f)
                        
                        # 更新章节信息
                        chapter_info.update(info)
                    except Exception as e:
                        logger.warning(f"读取章节信息失败: {chapter_dir} - {str(e)}")
                
                # 检查音频文件
                for ext in [".wav", ".mp3", ".ogg"]:
                    audio_file = os.path.join(chapter_path, f"audio{ext}")
                    if os.path.exists(audio_file):
                        chapter_info["has_audio"] = True
                        chapter_info["audio_url"] = f"/api/novels/{novel_id}/chapters/{chapter_dir}/audio"
                        break
                
                chapters.append(chapter_info)
        
        return {
            "success": True,
            "chapters": chapters
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取小说章节列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取小说章节列表失败: {str(e)}"
        )

@router.get("/api/novels/{novel_id}/chapters/{chapter_id}")
async def get_chapter_content(novel_id: str, chapter_id: str):
    """
    获取章节内容
    
    返回指定章节的文本内容和音频信息
    """
    try:
        # 获取配置
        config = get_config()
        chapter_path = os.path.join(config["output_dir"], "novels", novel_id, "chapters", chapter_id)
        
        # 检查章节是否存在
        if not os.path.exists(chapter_path) or not os.path.isdir(chapter_path):
            raise HTTPException(
                status_code=404,
                detail=f"章节不存在: {novel_id}/{chapter_id}"
            )
        
        # 读取章节信息
        chapter_info_path = os.path.join(chapter_path, "info.json")
        
        # 默认章节信息
        chapter_info = {
            "id": chapter_id,
            "title": chapter_id,
            "duration_seconds": 0,
            "has_audio": False,
            "text": ""
        }
        
        # 读取章节信息
        if os.path.exists(chapter_info_path):
            try:
                with open(chapter_info_path, "r", encoding="utf-8") as f:
                    info = json.load(f)
                
                # 更新章节信息
                chapter_info.update(info)
            except Exception as e:
                logger.warning(f"读取章节信息失败: {chapter_id} - {str(e)}")
        
        # 获取章节内容
        content_file = os.path.join(chapter_path, "content.txt")
        if os.path.exists(content_file):
            try:
                with open(content_file, "r", encoding="utf-8") as f:
                    chapter_info["text"] = f.read()
            except Exception as e:
                logger.warning(f"读取章节内容失败: {chapter_id} - {str(e)}")
                chapter_info["text"] = "无法读取章节内容"
        else:
            chapter_info["text"] = "章节内容不存在"
        
        # 检查音频文件
        for ext in [".wav", ".mp3", ".ogg"]:
            audio_file = os.path.join(chapter_path, f"audio{ext}")
            if os.path.exists(audio_file):
                chapter_info["has_audio"] = True
                chapter_info["audio_url"] = f"/api/novels/{novel_id}/chapters/{chapter_id}/audio"
                chapter_info["audio_size_mb"] = round(os.path.getsize(audio_file) / (1024 * 1024), 2)
                chapter_info["audio_format"] = ext[1:]  # 移除.
                break
        
        return chapter_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取章节内容失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取章节内容失败: {str(e)}"
        )

@router.get("/api/novels/{novel_id}/chapters/{chapter_id}/audio")
async def get_chapter_audio(novel_id: str, chapter_id: str):
    """
    获取章节音频
    
    返回指定章节的音频文件
    """
    try:
        # 获取配置
        config = get_config()
        chapter_path = os.path.join(config["output_dir"], "novels", novel_id, "chapters", chapter_id)
        
        # 检查章节是否存在
        if not os.path.exists(chapter_path) or not os.path.isdir(chapter_path):
            raise HTTPException(
                status_code=404,
                detail=f"章节不存在: {novel_id}/{chapter_id}"
            )
        
        # 查找音频文件
        audio_file = None
        audio_format = None
        
        for ext in [".wav", ".mp3", ".ogg"]:
            file_path = os.path.join(chapter_path, f"audio{ext}")
            if os.path.exists(file_path):
                audio_file = file_path
                audio_format = f"audio/{ext[1:]}"  # 例如 audio/wav
                break
        
        if not audio_file:
            raise HTTPException(
                status_code=404,
                detail=f"章节音频不存在: {novel_id}/{chapter_id}"
            )
        
        return FileResponse(
            path=audio_file,
            media_type=audio_format,
            filename=f"{chapter_id}{os.path.splitext(audio_file)[1]}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取章节音频失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取章节音频失败: {str(e)}"
        )

# 任务状态查询接口
@router.get("/api/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    获取任务状态
    
    通过任务ID查询处理状态和进度
    """
    task_store = get_task_store()
    task = task_store.get(task_id)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"未找到任务: {task_id}"
        )
    
    return TaskStatusResponse(
        success=True,
        task_id=task_id,
        status=task.get("status", "unknown"),
        progress=task.get("progress", 0.0),
        message=task.get("message", ""),
        result=task.get("result"),
        error=task.get("error"),
        created_at=task.get("created_at"),
        updated_at=task.get("updated_at")
    )

# 系统信息接口
@router.get("/api/system/info", response_model=SystemInfoResponse)
async def get_system_info():
    """
    获取系统信息
    
    返回服务器环境、硬件资源和MegaTTS配置信息
    """
    try:
        import platform
        import psutil
        import torch
        import numpy as np
        
        # 获取配置
        config = get_config()
        
        # 获取GPU信息
        gpu_info = []
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                gpu_info.append({
                    "index": i,
                    "name": torch.cuda.get_device_name(i),
                    "memory_total": torch.cuda.get_device_properties(i).total_memory,
                    "memory_used": torch.cuda.memory_allocated(i),
                    "memory_free": torch.cuda.get_device_properties(i).total_memory - torch.cuda.memory_allocated(i)
                })
        
        # 获取CPU信息
        cpu_info = {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "frequency": psutil.cpu_freq().current if psutil.cpu_freq() else None,
            "usage_percent": psutil.cpu_percent(interval=0.1)
        }
        
        # 获取内存信息
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percent": memory.percent
        }
        
        # 获取磁盘信息
        disk = psutil.disk_usage(os.path.abspath(os.getcwd()))
        disk_info = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }
        
        # 构建响应
        return SystemInfoResponse(
            success=True,
            system={
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "hostname": platform.node(),
                "cpu": cpu_info,
                "memory": memory_info,
                "disk": disk_info,
                "gpu": gpu_info
            },
            services={
                "tts_engine": "MegaTTS3" if hasattr(get_tts_engine(), "name") else "MockAudioGenerator",
                "using_mock": isinstance(get_tts_engine(), type) and "Mock" in get_tts_engine().__class__.__name__
            },
            dependencies={
                "torch": torch.__version__,
                "numpy": np.__version__,
                "fastapi": "0.95.0"  # 这里应当动态获取，但简化处理
            },
            config={
                "output_dir": config.get("output_dir", ""),
                "model_dir": config.get("model_dir", ""),
                "processing": config.get("processing", {})
            }
        )
    except Exception as e:
        logger.error(f"获取系统信息失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取系统信息失败: {str(e)}"
        )

# 统计信息接口
@router.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """
    获取API使用统计信息
    
    返回服务器运行状态、API调用统计和资源使用情况
    """
    try:
        from . import server
        import psutil
        
        # 获取进程信息
        process = psutil.Process(os.getpid())
        process_info = {
            "cpu_percent": process.cpu_percent(interval=0.1),
            "memory_info": {
                "rss": process.memory_info().rss,  # 物理内存
                "vms": process.memory_info().vms   # 虚拟内存
            },
            "threads": len(process.threads()),
            "connections": len(process.connections())
        }
        
        # 获取文件统计
        output_dir = get_config().get("output_dir", "")
        single_audio_count = 0
        novel_count = 0
        
        if os.path.exists(os.path.join(output_dir, "single")):
            single_audio_count = len(glob.glob(os.path.join(output_dir, "single", "*.*")))
        
        if os.path.exists(os.path.join(output_dir, "novels")):
            novel_count = len(os.listdir(os.path.join(output_dir, "novels")))
        
        # 获取任务统计
        task_store = get_task_store()
        task_stats = {
            "total": len(task_store),
            "pending": len([t for t in task_store.values() if t.get("status") == "pending"]),
            "processing": len([t for t in task_store.values() if t.get("status") == "processing"]),
            "completed": len([t for t in task_store.values() if t.get("status") == "completed"]),
            "failed": len([t for t in task_store.values() if t.get("status") == "failed"])
        }
        
        # 计算启动时间
        uptime = time.time() - server.start_time
        
        # 构建响应
        return StatsResponse(
            success=True,
            server={
                "uptime": uptime,
                "uptime_formatted": f"{int(uptime//86400)}天 {int((uptime%86400)//3600)}时 {int((uptime%3600)//60)}分 {int(uptime%60)}秒",
                "process": process_info
            },
            api={
                "routes_count": len([r for r in server.app.routes]),
                "task_stats": task_stats
            },
            files={
                "single_audio_count": single_audio_count,
                "novel_count": novel_count,
                "total_files": single_audio_count + novel_count
            }
        )
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取统计信息失败: {str(e)}"
        )

# 其他API路由待迁移
# 语音模型管理接口
@router.get("/api/engines")
async def list_engines():
    """
    获取可用的TTS引擎列表
    
    返回所有可用的TTS引擎及其状态
    """
    try:
        # 获取TTS引擎路由器
        from . import server
        tts_router = server.get_tts_router()
        if not tts_router:
            raise HTTPException(
                status_code=500,
                detail="TTS引擎路由器未初始化"
            )
        
        # 获取健康状态
        health_status = tts_router.get_health_status()
        
        # 获取所有已注册的引擎
        engines = {}
        for engine_type, engine in tts_router.get_registered_engines().items():
            engines[engine_type.value] = {
                "name": engine_type.value,
                "healthy": health_status.get(engine_type.value, {}).get("healthy", False),
                "last_check": health_status.get(engine_type.value, {}).get("last_check", 0),
                "message": health_status.get(engine_type.value, {}).get("message", "")
            }
        
        return {
            "success": True,
            "engines": engines
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取TTS引擎列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取TTS引擎列表失败: {str(e)}"
        )

@router.get("/api/engines/{engine_name}")
async def get_engine_details(engine_name: str):
    """
    获取特定引擎的详细信息
    
    返回特定引擎的详细信息和功能
    """
    try:
        # 验证引擎名称
        try:
            from src.tts.engine import TTSEngineType
            engine_type = TTSEngineType(engine_name)
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail=f"无效的引擎名称: {engine_name}"
            )
        
        # 获取TTS引擎路由器
        from . import server
        tts_router = server.get_tts_router()
        if not tts_router:
            raise HTTPException(
                status_code=500,
                detail="TTS引擎路由器未初始化"
            )
        
        # 获取引擎
        engine = tts_router.get_engine(engine_type)
        if not engine:
            raise HTTPException(
                status_code=404,
                detail=f"引擎 {engine_name} 未注册"
            )
        
        # 获取健康状态
        health_status = tts_router.get_health_status().get(engine_name, {})
        
        # 获取引擎音色
        voices = {}
        try:
            voices = await tts_router.get_available_voices(engine_type)
        except Exception as e:
            logger.warning(f"获取引擎 {engine_name} 音色失败: {str(e)}")
        
        # 创建引擎详情
        engine_details = {
            "name": engine_name,
            "healthy": health_status.get("healthy", False),
            "last_check": health_status.get("last_check", 0),
            "message": health_status.get("message", ""),
            "voices_count": len(voices),
            "voices": voices
        }
        
        return {
            "success": True,
            "engine": engine_details
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取引擎详情失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取引擎详情失败: {str(e)}"
        )

@router.post("/api/engines/{engine_name}/health")
async def check_engine_health(engine_name: str):
    """
    检查特定引擎的健康状态
    
    强制执行引擎健康检查
    """
    try:
        # 验证引擎名称
        try:
            from src.tts.engine import TTSEngineType
            engine_type = TTSEngineType(engine_name)
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail=f"无效的引擎名称: {engine_name}"
            )
        
        # 获取TTS引擎路由器
        from . import server
        tts_router = server.get_tts_router()
        if not tts_router:
            raise HTTPException(
                status_code=500,
                detail="TTS引擎路由器未初始化"
            )
        
        # 检查引擎是否存在
        if not tts_router.get_engine(engine_type):
            raise HTTPException(
                status_code=404,
                detail=f"引擎 {engine_name} 未注册"
            )
        
        # 执行健康检查
        is_healthy = await tts_router.check_engine_health(engine_type)
        health_status = tts_router.get_health_status().get(engine_name, {})
        
        return {
            "success": True,
            "engine": engine_name,
            "healthy": is_healthy,
            "status": health_status
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检查引擎健康状态失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"检查引擎健康状态失败: {str(e)}"
        )

@router.get("/api/voices")
async def list_voices():
    """
    获取可用的语音模型列表
    
    返回所有可用的语音模型及其参数
    """
    try:
        # 获取TTS引擎路由器
        from . import server
        tts_router = server.get_tts_router()
        if not tts_router:
            raise HTTPException(
                status_code=500,
                detail="TTS引擎路由器未初始化"
            )
        
        # 获取所有引擎的音色列表
        voices = await tts_router.get_available_voices()
        
        return {
            "success": True,
            "voices": voices
        }
    except Exception as e:
        logger.error(f"获取语音模型列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取语音模型列表失败: {str(e)}"
        )

@router.get("/api/emotions")
async def list_emotions():
    """
    获取可用的情感类型列表
    
    返回所有可用的情感类型及描述
    """
    try:
        engine = get_tts_engine()
        emotions = engine.get_available_emotions()
        
        return {
            "success": True,
            "emotions": emotions
        }
    except Exception as e:
        logger.error(f"获取情感类型列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取情感类型列表失败: {str(e)}"
        )

@router.post("/api/voices/preview")
async def generate_voice_preview(request: dict):
    """
    生成语音预览
    
    使用指定语音模型和参数生成预览音频
    """
    try:
        engine = get_tts_engine()
        
        # 预览文本，使用用户提供的文本，如果没有则使用默认文本
        preview_text = request.get("text")
        if not preview_text or preview_text.strip() == "":
            preview_text = "欢迎使用MegaTTS语音合成系统，这是一段预览音频。"
        
        # 合成参数
        voice_id = request.get("voice_id", "female_young")
        emotion_type = request.get("emotion_type", "neutral")
        emotion_intensity = request.get("emotion_intensity", 0.5)
        speed_scale = request.get("speed_scale", 1.0)
        pitch_scale = request.get("pitch_scale", 1.0)
        
        # 记录日志，用于调试
        logger.info(f"生成预览音频 - 文本: '{preview_text}', 声音ID: {voice_id}, 情感: {emotion_type}")
        
        # 合成音频
        audio = engine.synthesize(
            text=preview_text,
            voice_id=voice_id,
            emotion_type=emotion_type,
            emotion_intensity=emotion_intensity,
            speed_scale=speed_scale,
            pitch_scale=pitch_scale
        )
        
        # 保存到临时文件并返回下载链接
        audio_id = f"preview_{uuid.uuid4().hex[:8]}"
        output_format = request.get("output_format", "wav")
        output_dir = os.path.join(get_config()["output_dir"], "previews")
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, f"{audio_id}.{output_format}")
        save_audio(output_path, audio, format=output_format)
        
        return {
            "success": True,
            "message": "预览音频生成成功",
            "preview_url": f"/api/download/previews/{audio_id}.{output_format}",
            "duration": len(audio) / 22050,  # 假设采样率为22050
            "text": preview_text  # 返回实际使用的文本
        }
            
    except Exception as e:
        logger.error(f"生成预览音频失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"生成预览音频失败: {str(e)}"
        )

# 下载预览语音接口
@router.get("/api/download/previews/{filename}")
async def download_preview(filename: str):
    """
    下载预览语音文件
    
    通过文件名下载生成的预览音频文件
    """
    # 安全检查，避免路径遍历攻击
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=400,
            detail="无效的文件名"
        )
    
    # 确定文件路径
    file_path = os.path.join(get_config()["output_dir"], "previews", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"预览文件不存在: {filename}"
        )
    
    return FileResponse(file_path)

# 声纹特征管理API
@router.post("/api/voices/extract", response_model=VoiceFeatureExtractResponse)
async def extract_voice_feature(
    voice_file: UploadFile = File(...),
    name: str = Form(None),
    description: str = Form(None),
    tags: str = Form(None),
    gender: str = Form(None),
    age_group: str = Form(None)
):
    """
    从音频文件提取声纹特征
    
    上传音频文件并提取声纹特征，返回声音ID和特征信息
    """
    try:
        # 检查文件类型
        file_extension = os.path.splitext(voice_file.filename)[1].lower()
        if file_extension not in ['.wav', '.mp3', '.flac', '.ogg', '.m4a']:
            raise HTTPException(
                status_code=400,
                detail="不支持的音频格式，请上传WAV、MP3、FLAC格式文件"
            )
        
        # 读取文件内容
        content = await voice_file.read()
        
        # 保存到临时文件
        temp_dir = "temp_audio"
        os.makedirs(temp_dir, exist_ok=True)
        
        # 使用安全的文件名
        temp_filename = f"upload_{uuid.uuid4().hex}{file_extension}"
        temp_path = os.path.join(temp_dir, temp_filename)
        
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # 准备元数据
        metadata = {
            "name": name or os.path.splitext(voice_file.filename)[0],
            "description": description or "",
            "tags": tags.split(",") if tags else [],
            "attributes": {}
        }
        
        # 添加属性
        if gender:
            metadata["attributes"]["gender"] = gender
        if age_group:
            metadata["attributes"]["age_group"] = age_group
        
        # 获取声纹特征提取器
        from src.tts.voice_feature import VoiceFeatureExtractor
        extractor = VoiceFeatureExtractor()
        
        # 提取特征
        voice_info = extractor.extract_feature(temp_path, metadata=metadata)
        
        # 清理临时文件
        try:
            os.remove(temp_path)
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")
        
        # 准备音频预览
        preview_url = f"/api/voices/{voice_info['id']}/preview"
        
        # 返回结果
        return {
            "success": True,
            "message": "声纹特征提取成功",
            "voice_id": voice_info["id"],
            "name": voice_info["name"],
            "preview_url": preview_url,
            "feature_url": f"/api/voices/{voice_info['id']}/feature",
            "metadata": {
                "description": voice_info["description"],
                "tags": voice_info["tags"],
                "attributes": voice_info["attributes"],
                "feature_shape": voice_info["feature_shape"],
                "created_at": voice_info["created_at"]
            }
        }
        
    except Exception as e:
        logger.error(f"提取声纹特征失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"提取声纹特征失败: {str(e)}"
        )


@router.get("/api/voices/list", response_model=VoiceFeatureListResponse)
async def list_voice_features():
    """
    获取所有声纹特征列表
    
    返回所有可用的自定义声纹特征及其元数据
    """
    try:
        # 获取声纹特征提取器
        from src.tts.voice_feature import VoiceFeatureExtractor
        extractor = VoiceFeatureExtractor()
        
        # 获取所有声音
        voices = extractor.get_all_voices()
        
        # 处理为API响应格式
        result = []
        for voice in voices:
            result.append({
                "id": voice["id"],
                "name": voice["name"],
                "description": voice["description"],
                "tags": voice["tags"],
                "attributes": voice["attributes"],
                "preview_url": f"/api/voices/{voice['id']}/preview",
                "feature_url": f"/api/voices/{voice['id']}/feature",
                "created_at": voice["created_at"]
            })
        
        return {
            "success": True,
            "count": len(result),
            "voices": result
        }
        
    except Exception as e:
        logger.error(f"获取声纹特征列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取声纹特征列表失败: {str(e)}"
        )


@router.get("/api/voices/{voice_id}", response_model=VoiceFeatureDetailResponse)
async def get_voice_feature(voice_id: str):
    """
    获取特定声纹特征的详细信息
    
    根据声音ID返回详细的元数据和特征信息
    """
    try:
        # 获取声纹特征提取器
        from src.tts.voice_feature import VoiceFeatureExtractor
        extractor = VoiceFeatureExtractor()
        
        # 获取声音信息
        voice_info = extractor.get_voice(voice_id)
        
        # 检查是否存在
        if not voice_info:
            raise HTTPException(
                status_code=404,
                detail=f"声纹特征不存在: {voice_id}"
            )
        
        # 返回结果
        return {
            "success": True,
            "voice": {
                "id": voice_info["id"],
                "name": voice_info["name"],
                "description": voice_info["description"],
                "tags": voice_info["tags"],
                "attributes": voice_info["attributes"],
                "preview_url": f"/api/voices/{voice_info['id']}/preview",
                "feature_url": f"/api/voices/{voice_info['id']}/feature",
                "created_at": voice_info["created_at"],
                "feature_shape": voice_info["feature_shape"],
                "file_size": voice_info["file_size"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取声纹特征信息失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取声纹特征信息失败: {str(e)}"
        )


@router.put("/api/voices/{voice_id}")
async def update_voice_feature(
    voice_id: str,
    request: dict
):
    """
    更新声纹特征元数据
    
    根据声音ID更新名称、描述、标签等元数据
    """
    try:
        # 获取声纹特征提取器
        from src.tts.voice_feature import VoiceFeatureExtractor
        extractor = VoiceFeatureExtractor()
        
        # 检查声音是否存在
        if not extractor.get_voice(voice_id):
            raise HTTPException(
                status_code=404,
                detail=f"声纹特征不存在: {voice_id}"
            )
        
        # 更新元数据
        updated = extractor.update_voice_metadata(voice_id, request)
        
        # 返回结果
        return {
            "success": True,
            "message": "声纹特征元数据已更新",
            "voice": {
                "id": updated["id"],
                "name": updated["name"],
                "description": updated["description"],
                "tags": updated["tags"],
                "attributes": updated["attributes"],
                "created_at": updated["created_at"],
                "updated_at": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新声纹特征失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"更新声纹特征失败: {str(e)}"
        )


@router.delete("/api/voices/{voice_id}")
async def delete_voice_feature(voice_id: str):
    """
    删除声纹特征
    
    根据声音ID删除声纹特征和元数据
    """
    try:
        # 获取声纹特征提取器
        from src.tts.voice_feature import VoiceFeatureExtractor
        extractor = VoiceFeatureExtractor()
        
        # 检查声音是否存在
        if not extractor.get_voice(voice_id):
            raise HTTPException(
                status_code=404,
                detail=f"声纹特征不存在: {voice_id}"
            )
        
        # 删除声纹特征
        result = extractor.delete_voice(voice_id)
        
        # 返回结果
        if result:
            return {
                "success": True,
                "message": f"声纹特征已成功删除: {voice_id}"
            }
        else:
            return {
                "success": False,
                "message": f"删除声纹特征失败: {voice_id}"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除声纹特征失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"删除声纹特征失败: {str(e)}"
        )


@router.get("/api/voices/{voice_id}/feature")
async def download_voice_feature(voice_id: str):
    """
    下载声纹特征NPY文件
    
    根据声音ID下载对应的NPY文件
    """
    try:
        # 获取声纹特征提取器
        from src.tts.voice_feature import VoiceFeatureExtractor
        extractor = VoiceFeatureExtractor()
        
        # 获取声音信息
        voice_info = extractor.get_voice(voice_id)
        
        # 检查是否存在
        if not voice_info:
            raise HTTPException(
                status_code=404,
                detail=f"声纹特征不存在: {voice_id}"
            )
        
        # 检查文件是否存在
        if not os.path.exists(voice_info["feature_path"]):
            raise HTTPException(
                status_code=404,
                detail=f"声纹特征文件不存在: {voice_id}"
            )
        
        # 返回文件
        return FileResponse(
            voice_info["feature_path"],
            filename=f"{voice_info['name']}.npy",
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载声纹特征失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"下载声纹特征失败: {str(e)}"
        )


@router.get("/api/voices/{voice_id}/preview")
async def preview_voice_feature(voice_id: str, text: str = None):
    """
    预览声纹特征音频
    
    根据声音ID返回原始音频文件，或使用指定文本生成预览
    """
    try:
        # 获取声纹特征提取器
        from src.tts.voice_feature import VoiceFeatureExtractor
        extractor = VoiceFeatureExtractor()
        
        # 获取声音信息
        voice_info = extractor.get_voice(voice_id)
        
        # 检查是否存在
        if not voice_info:
            raise HTTPException(
                status_code=404,
                detail=f"声纹特征不存在: {voice_id}"
            )
        
        # 如果提供了自定义文本或没有原始音频，则生成预览
        if text or not voice_info.get("audio_path") or not os.path.exists(voice_info["audio_path"]):
            # 生成预览音频
            engine = get_tts_engine()
            
            # 使用传入的文本或默认文本
            sample_text = text if text else "这是一段使用该声音生成的示例音频。"
            logger.info(f"为声音 {voice_id} 生成预览音频 - 文本: '{sample_text}'")
            
            # 获取声纹特征
            voice_feature = extractor.get_voice_feature(voice_id)
            
            # 合成音频
            audio = engine.synthesize_with_feature(
                text=sample_text,
                voice_feature=voice_feature
            )
            
            # 保存到临时文件
            temp_dir = os.path.join(get_config()["output_dir"], "previews")
            os.makedirs(temp_dir, exist_ok=True)
            
            # 使用唯一ID避免缓存问题
            unique_id = uuid.uuid4().hex[:8]
            temp_path = os.path.join(temp_dir, f"{voice_id}_preview_{unique_id}.wav")
            import soundfile as sf
            sf.write(temp_path, audio, 24000)
            
            # 返回临时文件
            return FileResponse(
                temp_path,
                filename=f"{voice_info['name']}_preview.wav",
                media_type="audio/wav"
            )
        
        # 返回原始音频
        return FileResponse(
            voice_info["audio_path"],
            filename=f"{voice_info['name']}{os.path.splitext(voice_info['audio_path'])[1]}",
            media_type="audio/wav"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预览声纹特征失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"预览声纹特征失败: {str(e)}"
        )


@router.get("/api/voices/tags", response_model=VoiceTagsResponse)
async def get_voice_tags():
    """
    获取所有声音标签列表
    
    返回系统中所有声音标签及其统计
    """
    try:
        # 获取声纹特征提取器
        from src.tts.voice_feature import VoiceFeatureExtractor
        extractor = VoiceFeatureExtractor()
        
        # 获取所有声音
        voices = extractor.get_all_voices()
        
        # 统计标签
        tag_count = {}
        for voice in voices:
            for tag in voice.get("tags", []):
                tag_count[tag] = tag_count.get(tag, 0) + 1
        
        # 统计属性
        attribute_stats = {}
        for voice in voices:
            for attr_key, attr_value in voice.get("attributes", {}).items():
                if attr_key not in attribute_stats:
                    attribute_stats[attr_key] = {}
                
                if isinstance(attr_value, list):
                    for value in attr_value:
                        attribute_stats[attr_key][value] = attribute_stats[attr_key].get(value, 0) + 1
                else:
                    attribute_stats[attr_key][attr_value] = attribute_stats[attr_key].get(attr_value, 0) + 1
        
        # 返回结果
        return {
            "success": True,
            "tags": [{"name": tag, "count": count} for tag, count in tag_count.items()],
            "attributes": {
                attr: [{"name": value, "count": count} for value, count in values.items()]
                for attr, values in attribute_stats.items()
            }
        }
        
    except Exception as e:
        logger.error(f"获取声音标签失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取声音标签失败: {str(e)}"
        )


@router.post("/api/voices/import")
async def import_voice_feature(
    npy_file: UploadFile = File(...),
    name: str = Form(None),
    description: str = Form(None),
    tags: str = Form(None),
    gender: str = Form(None),
    age_group: str = Form(None),
    audio_file: UploadFile = File(None)
):
    """
    导入已有的声纹特征NPY文件
    
    上传NPY文件和可选的原始音频文件，导入声纹特征
    """
    try:
        # 检查文件类型
        if not npy_file.filename.lower().endswith('.npy'):
            raise HTTPException(
                status_code=400,
                detail="不支持的文件格式，请上传NPY格式文件"
            )
        
        # 读取NPY文件内容
        npy_content = await npy_file.read()
        
        # 保存到临时文件
        temp_dir = "temp_features"
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_npy_path = os.path.join(temp_dir, f"import_{uuid.uuid4().hex}.npy")
        with open(temp_npy_path, "wb") as f:
            f.write(npy_content)
        
        # 处理音频文件
        temp_audio_path = None
        if audio_file:
            audio_content = await audio_file.read()
            audio_ext = os.path.splitext(audio_file.filename)[1].lower()
            temp_audio_path = os.path.join(temp_dir, f"import_{uuid.uuid4().hex}{audio_ext}")
            with open(temp_audio_path, "wb") as f:
                f.write(audio_content)
        
        # 准备元数据
        metadata = {
            "name": name or os.path.splitext(npy_file.filename)[0],
            "description": description or "导入的声纹特征",
            "tags": tags.split(",") if tags else [],
            "attributes": {},
            "audio_path": temp_audio_path
        }
        
        # 添加属性
        if gender:
            metadata["attributes"]["gender"] = gender
        if age_group:
            metadata["attributes"]["age_group"] = age_group
        
        # 获取声纹特征提取器
        from src.tts.voice_feature import VoiceFeatureExtractor
        extractor = VoiceFeatureExtractor()
        
        # 导入特征
        voice_info = extractor.import_voice_feature(temp_npy_path, metadata=metadata)
        
        # 清理临时文件
        try:
            os.remove(temp_npy_path)
        except Exception as e:
            logger.warning(f"清理临时NPY文件失败: {e}")
        
        # 返回结果
        if voice_info:
            return {
                "success": True,
                "message": "声纹特征导入成功",
                "voice_id": voice_info["id"],
                "name": voice_info["name"],
                "preview_url": f"/api/voices/{voice_info['id']}/preview",
                "feature_url": f"/api/voices/{voice_info['id']}/feature",
                "metadata": {
                    "description": voice_info["description"],
                    "tags": voice_info["tags"],
                    "attributes": voice_info["attributes"],
                    "feature_shape": voice_info["feature_shape"],
                    "created_at": voice_info["created_at"]
                }
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="导入声纹特征失败，请检查NPY文件格式"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入声纹特征失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"导入声纹特征失败: {str(e)}"
        )

# 角色声音映射API
@router.get("/api/characters", response_model=CharacterListResponse)
async def list_characters():
    """
    获取所有角色及其声音映射
    
    返回当前定义的所有角色和关联声音的列表
    """
    try:
        # 获取声音映射管理器
        from src.tts.character_voice import CharacterVoiceMapper
        mapper = CharacterVoiceMapper()
        
        # 获取所有角色
        characters = mapper.get_all_characters()
        
        return {
            "success": True,
            "count": len(characters),
            "characters": characters
        }
        
    except Exception as e:
        logger.error(f"获取角色列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取角色列表失败: {str(e)}"
        )

@router.post("/api/characters/map")
async def map_character(request: dict):
    """
    创建或更新角色和声音的映射
    
    将角色映射到特定声音
    """
    try:
        # 验证请求参数
        character_name = request.get("character")
        voice_id = request.get("voice_id")
        
        if not character_name:
            raise HTTPException(
                status_code=400,
                detail="必须提供角色名称"
            )
            
        if not voice_id:
            raise HTTPException(
                status_code=400,
                detail="必须提供声音ID"
            )
            
        # 获取声音映射管理器
        from src.tts.character_voice import CharacterVoiceMapper
        mapper = CharacterVoiceMapper()
        
        # 创建映射
        attributes = request.get("attributes", {})
        character_info = mapper.map_character(character_name, voice_id, attributes)
        
        return {
            "success": True,
            "message": f"角色 '{character_name}' 已映射到声音 '{voice_id}'",
            "character": character_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"映射角色失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"映射角色失败: {str(e)}"
        )

@router.get("/api/characters/{character_name}", response_model=CharacterDetailResponse)
async def get_character(character_name: str):
    """
    获取特定角色的声音映射
    
    根据角色名称获取关联的声音
    """
    try:
        # 获取声音映射管理器
        from src.tts.character_voice import CharacterVoiceMapper
        mapper = CharacterVoiceMapper()
        
        # 获取角色信息
        character_voice = mapper.get_character_voice(character_name)
        
        if not character_voice:
            raise HTTPException(
                status_code=404,
                detail=f"角色 '{character_name}' 不存在或没有关联声音"
            )
            
        return {
            "success": True,
            "character": character_voice.get("character"),
            "voice": character_voice.get("voice")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取角色失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取角色失败: {str(e)}"
        )

@router.delete("/api/characters/{character_name}")
async def delete_character_mapping(character_name: str):
    """
    删除角色声音映射
    
    根据角色名称删除声音映射
    """
    try:
        # 获取声音映射管理器
        from src.tts.character_voice import CharacterVoiceMapper
        mapper = CharacterVoiceMapper()
        
        # 删除映射
        result = mapper.delete_character(character_name)
        
        if result:
            return {
                "success": True,
                "message": f"角色 '{character_name}' 的声音映射已删除"
            }
        else:
            return {
                "success": False,
                "message": f"角色 '{character_name}' 不存在"
            }
        
    except Exception as e:
        logger.error(f"删除角色映射失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"删除角色映射失败: {str(e)}"
        )

@router.post("/api/characters/analyze", response_model=CharacterAnalysisResponse)
async def analyze_novel_characters(request: dict):
    """
    分析小说中的角色
    
    分析文本中的角色，并提供音色映射建议
    """
    try:
        # 获取小说文本
        novel_text = request.get("text")
        novel_path = request.get("path")
        
        if not novel_text and not novel_path:
            raise HTTPException(
                status_code=400,
                detail="必须提供小说文本或文件路径"
            )
            
        # 获取声音映射管理器
        from src.tts.character_voice import CharacterVoiceMapper
        mapper = CharacterVoiceMapper()
        
        # 如果提供的是路径，读取文件内容
        if novel_path and not novel_text:
            try:
                from src.processor.novel_processor import NovelSegmenter
                segmenter = NovelSegmenter()
                novel_text = segmenter.load_novel(novel_path)
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"读取小说文件失败: {str(e)}"
                )
                
        # 分析角色
        characters = mapper.analyze_novel_characters(novel_text)
        
        # 生成建议映射
        suggestions = mapper.suggest_character_mapping(novel_text)
        
        # 构建角色列表，按出现频率排序
        character_list = [
            {"name": name, "count": count, "suggested_voices": suggestions.get(name, [])}
            for name, count in sorted(characters.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return {
            "success": True,
            "total_characters": len(character_list),
            "characters": character_list
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析小说角色失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"分析小说角色失败: {str(e)}"
        )

@router.get("/api/tasks")
async def get_tasks(limit: int = 5):
    """
    获取任务列表
    
    返回所有任务或限定数量的最近任务
    """
    try:
        task_store = get_task_store()
        tasks = task_store  # 直接使用task_store字典，而不是调用get_tasks()方法
        
        # 按创建时间排序，最新的在前
        sorted_tasks = sorted(tasks.values(), key=lambda x: x.get('created_at', 0), reverse=True)
        
        # 限制返回数量
        limited_tasks = sorted_tasks[:limit] if limit > 0 else sorted_tasks
        
        return {
            "success": True,
            "count": len(limited_tasks),
            "tasks": limited_tasks
        }
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取任务列表失败: {str(e)}"
        )