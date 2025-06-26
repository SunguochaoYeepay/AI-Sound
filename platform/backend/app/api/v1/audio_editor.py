"""
音频编辑器API接口
提供音频混合、章节创建、文件上传下载等功能
"""

import os
import asyncio
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...database import get_db
from ...services.moviepy_service import (
    moviepy_service,
    AudioMixConfig,
    AudioEffectConfig,
    ChapterAudioConfig
)
from ...services.audio_editor_service import AudioEditorService
from ...config.environment import get_environment_config

logger = logging.getLogger(__name__)
env_config = get_environment_config()

router = APIRouter()

# 请求/响应模型
class AudioMixRequest(BaseModel):
    """音频混合请求"""
    dialogue_path: str = Field(..., description="对话音频文件路径")
    environment_path: str = Field(..., description="环境音频文件路径")
    output_filename: str = Field(..., description="输出文件名")
    config: AudioMixConfig = Field(default_factory=AudioMixConfig, description="混合配置")

class AudioMixResult(BaseModel):
    """音频混合结果"""
    success: bool
    output_path: str
    duration: float
    file_size: int
    format: str
    bitrate: str
    download_url: str

class ChapterAudioRequest(BaseModel):
    """章节音频请求"""
    audio_files: List[str] = Field(..., description="音频文件路径列表")
    output_filename: str = Field(..., description="输出文件名")
    config: ChapterAudioConfig = Field(default_factory=ChapterAudioConfig, description="章节配置")

class ChapterAudioResult(BaseModel):
    """章节音频结果"""
    success: bool
    output_path: str
    duration: float
    segments_count: int
    file_size: int
    format: str
    bitrate: str
    download_url: str

class AudioEffectRequest(BaseModel):
    """音频效果请求"""
    input_path: str = Field(..., description="输入音频文件路径")
    output_filename: str = Field(..., description="输出文件名")
    effects: AudioEffectConfig = Field(..., description="音频效果配置")

class AudioEffectResult(BaseModel):
    """音频效果结果"""
    success: bool
    output_path: str
    duration: float
    file_size: int
    effects_applied: Dict[str, Any]
    download_url: str

class AudioInfoResult(BaseModel):
    """音频信息结果"""
    file_path: str
    duration: float
    fps: int
    channels: int
    file_size: int
    format: str

class UploadResult(BaseModel):
    """文件上传结果"""
    success: bool
    filename: str
    file_path: str
    file_size: int
    upload_time: str

# 工具函数
def get_output_path(filename: str) -> str:
    """获取输出文件路径"""
    storage_config = env_config.get_storage_config()
    base_path = storage_config["base_paths"].get("storage", "./storage")
    output_dir = Path(base_path) / "audio_editor" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    return str(output_dir / filename)

def get_upload_path(filename: str) -> str:
    """获取上传文件路径"""
    storage_config = env_config.get_storage_config()
    base_path = storage_config["base_paths"].get("storage", "./storage")
    upload_dir = Path(base_path) / "audio_editor" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return str(upload_dir / filename)

def get_download_url(filename: str) -> str:
    """获取下载URL"""
    return f"/api/v1/audio-editor/download/{filename}"

def validate_audio_file(file_path: str) -> bool:
    """验证音频文件是否存在且有效"""
    if not os.path.exists(file_path):
        return False
    
    # 检查文件扩展名
    valid_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']
    file_ext = os.path.splitext(file_path)[1].lower()
    return file_ext in valid_extensions

# API端点
@router.post("/mix-audio", response_model=AudioMixResult)
async def mix_audio(
    request: AudioMixRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    混合对话音频与环境音
    """
    try:
        logger.info(f"接收音频混合请求: {request.dialogue_path} + {request.environment_path}")
        
        # 验证输入文件
        if not validate_audio_file(request.dialogue_path):
            raise HTTPException(
                status_code=400,
                detail=f"对话音频文件不存在或格式不支持: {request.dialogue_path}"
            )
        
        if not validate_audio_file(request.environment_path):
            raise HTTPException(
                status_code=400,
                detail=f"环境音频文件不存在或格式不支持: {request.environment_path}"
            )
        
        # 生成输出路径
        output_path = get_output_path(request.output_filename)
        
        # 执行音频混合
        result = await moviepy_service.mix_dialogue_with_environment(
            dialogue_path=request.dialogue_path,
            environment_path=request.environment_path,
            output_path=output_path,
            config=request.config
        )
        
        # 构造响应
        response = AudioMixResult(
            success=result["success"],
            output_path=result["output_path"],
            duration=result["duration"],
            file_size=result["file_size"],
            format=result["format"],
            bitrate=result["bitrate"],
            download_url=get_download_url(request.output_filename)
        )
        
        logger.info(f"音频混合完成: {output_path}")
        return response
        
    except Exception as e:
        logger.error(f"音频混合失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"音频混合失败: {str(e)}")

@router.post("/create-chapter", response_model=ChapterAudioResult)
async def create_chapter_audio(
    request: ChapterAudioRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    创建章节音频（拼接多个音频文件）
    """
    try:
        logger.info(f"接收章节音频创建请求，共{len(request.audio_files)}个片段")
        
        # 验证输入文件
        invalid_files = []
        for audio_file in request.audio_files:
            if not validate_audio_file(audio_file):
                invalid_files.append(audio_file)
        
        if invalid_files:
            raise HTTPException(
                status_code=400,
                detail=f"以下音频文件不存在或格式不支持: {', '.join(invalid_files)}"
            )
        
        # 生成输出路径
        output_path = get_output_path(request.output_filename)
        
        # 执行章节音频创建
        result = await moviepy_service.create_chapter_audio(
            audio_files=request.audio_files,
            output_path=output_path,
            config=request.config
        )
        
        # 构造响应
        response = ChapterAudioResult(
            success=result["success"],
            output_path=result["output_path"],
            duration=result["duration"],
            segments_count=result["segments_count"],
            file_size=result["file_size"],
            format=result["format"],
            bitrate=result["bitrate"],
            download_url=get_download_url(request.output_filename)
        )
        
        logger.info(f"章节音频创建完成: {output_path}")
        return response
        
    except Exception as e:
        logger.error(f"章节音频创建失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"章节音频创建失败: {str(e)}")

@router.post("/apply-effects", response_model=AudioEffectResult)
async def apply_audio_effects(
    request: AudioEffectRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    应用音频效果
    """
    try:
        logger.info(f"接收音频效果应用请求: {request.input_path}")
        
        # 验证输入文件
        if not validate_audio_file(request.input_path):
            raise HTTPException(
                status_code=400,
                detail=f"输入音频文件不存在或格式不支持: {request.input_path}"
            )
        
        # 生成输出路径
        output_path = get_output_path(request.output_filename)
        
        # 应用音频效果
        result = await moviepy_service.apply_audio_effects(
            input_path=request.input_path,
            output_path=output_path,
            effects=request.effects
        )
        
        # 构造响应
        response = AudioEffectResult(
            success=result["success"],
            output_path=result["output_path"],
            duration=result["duration"],
            file_size=result["file_size"],
            effects_applied=result["effects_applied"],
            download_url=get_download_url(request.output_filename)
        )
        
        logger.info(f"音频效果应用完成: {output_path}")
        return response
        
    except Exception as e:
        logger.error(f"音频效果应用失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"音频效果应用失败: {str(e)}")

@router.get("/audio-info", response_model=AudioInfoResult)
async def get_audio_info(
    audio_path: str,
    db: Session = Depends(get_db)
):
    """
    获取音频文件信息
    """
    try:
        logger.info(f"获取音频信息: {audio_path}")
        
        # 验证输入文件
        if not validate_audio_file(audio_path):
            raise HTTPException(
                status_code=400,
                detail=f"音频文件不存在或格式不支持: {audio_path}"
            )
        
        # 获取音频信息
        info = await moviepy_service.get_audio_info(audio_path)
        
        response = AudioInfoResult(**info)
        
        logger.info(f"音频信息获取完成: {audio_path}")
        return response
        
    except Exception as e:
        logger.error(f"获取音频信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取音频信息失败: {str(e)}")

@router.post("/upload", response_model=UploadResult)
async def upload_audio_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    上传音频文件
    """
    try:
        logger.info(f"接收文件上传请求: {file.filename}")
        
        # 验证文件类型
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        file_ext = os.path.splitext(file.filename)[1].lower()
        valid_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']
        
        if file_ext not in valid_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式: {file_ext}. 支持的格式: {', '.join(valid_extensions)}"
            )
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = get_upload_path(filename)
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        
        response = UploadResult(
            success=True,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            upload_time=datetime.now().isoformat()
        )
        
        logger.info(f"文件上传完成: {file_path}")
        return response
        
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.get("/download/{filename}")
async def download_file(
    filename: str,
    db: Session = Depends(get_db)
):
    """
    下载音频文件
    """
    try:
        logger.info(f"接收文件下载请求: {filename}")
        
        # 查找文件（先在outputs目录，再在uploads目录）
        file_path = None
        
        # 获取存储配置
        storage_config = env_config.get_storage_config()
        base_path = storage_config["base_paths"].get("storage", "./storage")
        
        # 检查outputs目录
        outputs_path = Path(base_path) / "audio_editor" / "outputs" / filename
        if outputs_path.exists():
            file_path = str(outputs_path)
        else:
            # 检查uploads目录
            uploads_path = Path(base_path) / "audio_editor" / "uploads" / filename
            if uploads_path.exists():
                file_path = str(uploads_path)
        
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"文件不存在: {filename}"
            )
        
        # 确定媒体类型
        file_ext = os.path.splitext(filename)[1].lower()
        media_type_map = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.flac': 'audio/flac',
            '.aac': 'audio/aac',
            '.ogg': 'audio/ogg',
            '.m4a': 'audio/mp4'
        }
        
        media_type = media_type_map.get(file_ext, 'application/octet-stream')
        
        logger.info(f"文件下载开始: {file_path}")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type
        )
        
    except Exception as e:
        logger.error(f"文件下载失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件下载失败: {str(e)}")

@router.get("/files/{filename}")
async def get_file(
    filename: str,
    db: Session = Depends(get_db)
):
    """
    获取音频文件（用于前端直接访问）
    """
    try:
        logger.info(f"接收文件访问请求: {filename}")
        
        # 查找文件（先在uploads目录，再在outputs目录）
        file_path = None
        
        # 获取存储配置
        storage_config = env_config.get_storage_config()
        base_path = storage_config["base_paths"].get("storage", "./storage")
        
        # 检查uploads目录（上传的文件优先）
        uploads_path = Path(base_path) / "audio_editor" / "uploads" / filename
        if uploads_path.exists():
            file_path = str(uploads_path)
        else:
            # 检查outputs目录
            outputs_path = Path(base_path) / "audio_editor" / "outputs" / filename
            if outputs_path.exists():
                file_path = str(outputs_path)
        
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"文件不存在: {filename}"
            )
        
        # 确定媒体类型
        file_ext = os.path.splitext(filename)[1].lower()
        media_type_map = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.flac': 'audio/flac',
            '.aac': 'audio/aac',
            '.ogg': 'audio/ogg',
            '.m4a': 'audio/mp4'
        }
        
        media_type = media_type_map.get(file_ext, 'application/octet-stream')
        
        logger.info(f"文件访问成功: {file_path}")
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            headers={"Accept-Ranges": "bytes"}  # 支持音频播放器的范围请求
        )
        
    except Exception as e:
        logger.error(f"文件访问失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件访问失败: {str(e)}")

@router.delete("/cleanup-temp")
async def cleanup_temp_files(
    db: Session = Depends(get_db)
):
    """
    清理临时文件
    """
    try:
        logger.info("开始清理临时文件")
        
        # 清理MoviePy临时文件
        await asyncio.get_event_loop().run_in_executor(
            None,
            moviepy_service.cleanup_temp_files
        )
        
        logger.info("临时文件清理完成")
        return {"success": True, "message": "临时文件清理完成"}
        
    except Exception as e:
        logger.error(f"临时文件清理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"临时文件清理失败: {str(e)}")

@router.get("/health")
async def health_check():
    """
    健康检查
    """
    try:
        # 检查MoviePy是否可用
        import moviepy
        
        return {
            "status": "healthy",
            "moviepy_version": moviepy.__version__,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")

# =================== 项目管理API端点 ===================

class AudioVideoProjectResponse(BaseModel):
    """音视频项目响应模型"""
    id: int
    name: str
    description: Optional[str]
    source_project_id: Optional[int]
    project_type: str
    status: str
    total_duration: float
    track_count: int
    clip_count: int
    created_at: str
    updated_at: str

class ProjectListResponse(BaseModel):
    """项目列表响应模型"""
    projects: List[AudioVideoProjectResponse]
    total_count: int
    page: int
    limit: int

class ProjectImportRequest(BaseModel):
    """项目导入请求"""
    source_project_id: int = Field(..., description="源项目ID")
    project_name: Optional[str] = Field(None, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")

class AudioVideoProjectCreate(BaseModel):
    """创建音视频项目请求"""
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    project_type: str = Field(default="audio_editing", description="项目类型")

@router.get("/projects")
async def get_projects(
    page: int = 1,
    page_size: int = 10,
    search: Optional[str] = None,
    status: Optional[str] = None,
    type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取项目列表"""
    try:
        service = AudioEditorService(db)
        skip = (page - 1) * page_size
        projects, total_count = await service.get_projects(
            skip=skip, 
            limit=page_size, 
            search=search, 
            status=status, 
            project_type=type
        )
        
        # 转换为前端期望的格式
        project_items = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "source_project_id": p.source_project_id,
                "project_type": p.project_type,
                "status": p.status,
                "total_duration": p.total_duration or 0.0,
                "track_count": p.track_count,
                "clip_count": p.clip_count,
                "created_at": p.created_at.isoformat() if p.created_at else "",
                "updated_at": p.updated_at.isoformat() if p.updated_at else "",
                "duration": f"{int((p.total_duration or 0) // 60)}:{int((p.total_duration or 0) % 60):02d}"
            }
            for p in projects
        ]
        
        return {
            "success": True,
            "data": {
                "items": project_items,
                "total": total_count,
                "page": page,
                "page_size": page_size
            }
        }
        
    except Exception as e:
        logger.error(f"获取项目列表失败: {str(e)}")
        return {
            "success": False,
            "message": f"获取项目列表失败: {str(e)}"
        }

@router.post("/projects", response_model=AudioVideoProjectResponse)
async def create_project(
    project_data: AudioVideoProjectCreate,
    db: Session = Depends(get_db)
):
    """创建新项目"""
    try:
        service = AudioEditorService(db)
        project = await service.create_project(project_data)
        
        return AudioVideoProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            source_project_id=project.source_project_id,
            project_type=project.project_type,
            status=project.status,
            total_duration=project.total_duration or 0.0,
            track_count=project.track_count,
            clip_count=project.clip_count,
            created_at=project.created_at.isoformat() if project.created_at else "",
            updated_at=project.updated_at.isoformat() if project.updated_at else ""
        )
        
    except Exception as e:
        logger.error(f"创建项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建项目失败: {str(e)}")

@router.post("/projects/import", response_model=AudioVideoProjectResponse)
async def import_project_from_synthesis(
    import_request: ProjectImportRequest,
    db: Session = Depends(get_db)
):
    """从合成中心导入项目"""
    try:
        service = AudioEditorService(db)
        project = await service.import_from_synthesis(import_request)
        
        return AudioVideoProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            source_project_id=project.source_project_id,
            project_type=project.project_type,
            status=project.status,
            total_duration=project.total_duration or 0.0,
            track_count=project.track_count,
            clip_count=project.clip_count,
            created_at=project.created_at.isoformat() if project.created_at else "",
            updated_at=project.updated_at.isoformat() if project.updated_at else ""
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"导入项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导入项目失败: {str(e)}")

@router.get("/projects/{project_id}", response_model=AudioVideoProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目详情"""
    try:
        service = AudioEditorService(db)
        project = await service.get_project_with_details(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")
        
        return AudioVideoProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            source_project_id=project.source_project_id,
            project_type=project.project_type,
            status=project.status,
            total_duration=project.total_duration or 0.0,
            track_count=project.track_count,
            clip_count=project.clip_count,
            created_at=project.created_at.isoformat() if project.created_at else "",
            updated_at=project.updated_at.isoformat() if project.updated_at else ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目详情失败: {str(e)}")

@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """删除项目"""
    try:
        service = AudioEditorService(db)
        success = await service.delete_project(project_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")
        
        return {"success": True, "message": f"项目 {project_id} 已删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")

@router.post("/projects/{project_id}/export")
async def export_project(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """导出项目音频"""
    try:
        service = AudioEditorService(db)
        result_path = await service.mix_project_audio(project_id)
        
        # 获取文件名
        filename = os.path.basename(result_path)
        
        return {
            "success": True,
            "output_path": result_path,
            "download_url": get_download_url(filename),
            "message": "项目导出成功"
        }
        
    except Exception as e:
        logger.error(f"导出项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出项目失败: {str(e)}")

# 导出路由
__all__ = ["router"] 