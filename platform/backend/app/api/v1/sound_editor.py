"""
音频编辑器API接口 - 多轨音频编辑器
为朋友的Sound-Edit组件提供后端支持
"""

import os
import asyncio
import logging
import time
import subprocess
import json
from typing import List, Dict, Optional, Any, Union
from pathlib import Path
import tempfile
import shutil
import json
from datetime import datetime

# 音频处理相关导入
try:
    import mutagen
except ImportError:
    mutagen = None

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel, Field

from ...database import get_db
from ...config.environment import get_environment_config
from ...models import AudioFile

logger = logging.getLogger(__name__)
env_config = get_environment_config()

router = APIRouter(prefix="/sound-editor")

# ========== 数据模型 ==========

class AudioFileInfo(BaseModel):
    """音频文件信息"""
    id: str
    filename: str
    category: str  # 'dialogue', 'environment', 'background'
    duration: float
    file_size: int
    format: str
    sample_rate: int
    channels: int
    url: str
    created_at: str

class AudioFileUploadResponse(BaseModel):
    """音频文件上传响应"""
    success: bool
    message: str
    file: Optional[AudioFileInfo] = None

class AudioFilesListResponse(BaseModel):
    """音频文件列表响应"""
    success: bool
    files: List[AudioFileInfo]
    total_count: int

# 多轨项目相关模型
class ProjectInfo(BaseModel):
    """项目基本信息"""
    id: Optional[str] = None
    title: str
    description: str
    author: str
    bookId: Optional[int] = None  # 新增：书籍ID
    chapterId: Optional[int] = None  # 新增：章节ID
    totalDuration: float
    sampleRate: int
    channels: int
    bitDepth: int
    exportFormat: str
    createdAt: Optional[str] = None
    version: str = "1.0"

class ClipInfo(BaseModel):
    """音频片段信息"""
    id: str
    fileId: str
    filename: str
    startTime: float
    duration: float
    volume: float = 1.0
    offset: float = 0.0
    fadeIn: float = 0.0
    fadeOut: float = 0.0

class TrackInfo(BaseModel):
    """音轨信息"""
    id: str
    name: str
    type: str  # 'dialogue', 'environment', 'background'
    volume: float = 1.0
    muted: bool = False
    solo: bool = False
    color: str
    order: int
    clips: List[ClipInfo] = []

class ProjectData(BaseModel):
    """完整项目数据"""
    project: ProjectInfo
    tracks: List[TrackInfo] = []
    markers: List[Dict] = []
    # 新增：素材区配置
    audioFiles: List[Dict] = []
    # 新增：章节选择信息
    selectedChapterId: Optional[int] = None
    # 新增：搜索配置
    searchKeyword: str = ""
    activeAudioTab: str = "dialogue"

class ProjectCreateRequest(BaseModel):
    """创建项目请求"""
    project: ProjectInfo

class ProjectSaveRequest(BaseModel):
    """保存项目请求"""
    project: ProjectData

class ProjectResponse(BaseModel):
    """项目响应"""
    success: bool
    message: str
    data: Optional[ProjectData] = None

class ProjectListResponse(BaseModel):
    """项目列表响应"""
    success: bool
    projects: List[ProjectInfo]

# ========== 工具函数 ==========

def get_audio_storage_path() -> Path:
    """获取音频存储路径"""
    # 统一存储在项目根目录的storage中
    # 确保使用绝对路径，避免工作目录问题
    current_dir = Path(__file__).parent.parent.parent.parent.parent  # 回到项目根目录
    audio_path = current_dir / "storage" / "audio_editor" / "uploads"
    audio_path.mkdir(parents=True, exist_ok=True)
    return audio_path

def get_project_storage_path() -> Path:
    """获取项目存储路径"""
    # 统一存储在项目根目录的storage中
    # 确保使用绝对路径，避免工作目录问题
    current_dir = Path(__file__).parent.parent.parent.parent.parent  # 回到项目根目录
    project_path = current_dir / "storage" / "audio_editor" / "projects"
    project_path.mkdir(parents=True, exist_ok=True)
    return project_path

def generate_file_id() -> str:
    """生成文件ID"""
    import uuid
    return f"file_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"

def generate_project_id() -> str:
    """生成项目ID"""
    import uuid
    return f"project_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"

# 添加FFmpeg音频处理服务
class FFmpegService:
    """
    FFmpeg音频处理服务
    """
    
    def __init__(self):
        # 临时注释FFmpeg检查以测试其他功能
        try:
            self.ffmpeg_path = self._find_ffmpeg()
            self.ffprobe_path = self._find_ffprobe()
        except RuntimeError:
            logger.warning("FFmpeg未找到，音频编辑功能将不可用")
            self.ffmpeg_path = None
            self.ffprobe_path = None
        
    def _find_ffmpeg(self) -> str:
        """查找FFmpeg可执行文件路径"""
        # Windows环境
        common_paths = [
            'ffmpeg.exe',
            'ffmpeg',
            r'C:\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files\ffmpeg\bin\ffmpeg.exe'
        ]
        
        for path in common_paths:
            try:
                subprocess.run([path, '-version'], capture_output=True, check=True, timeout=5)
                return path
            except:
                continue
                
        raise RuntimeError(
            "FFmpeg未安装或不在PATH中！\n"
            "请安装FFmpeg：\n"
            "1. Windows: winget install ffmpeg\n"
            "2. 或下载: https://ffmpeg.org/download.html\n"
            "3. 确保ffmpeg.exe在系统PATH中"
        )
    
    def _find_ffprobe(self) -> str:
        """查找FFprobe可执行文件路径"""
        # 通常与ffmpeg在同一目录
        ffmpeg_dir = os.path.dirname(self.ffmpeg_path) if '\\' in self.ffmpeg_path or '/' in self.ffmpeg_path else ''
        
        common_paths = [
            'ffprobe.exe',
            'ffprobe',
            os.path.join(ffmpeg_dir, 'ffprobe.exe') if ffmpeg_dir else 'ffprobe.exe',
            r'C:\ffmpeg\bin\ffprobe.exe',
            r'C:\Program Files\ffmpeg\bin\ffprobe.exe'
        ]
        
        for path in common_paths:
            try:
                subprocess.run([path, '-version'], capture_output=True, check=True, timeout=5)
                return path
            except:
                continue
                
        # 如果找不到，使用ffmpeg同目录的ffprobe
        return self.ffmpeg_path.replace('ffmpeg', 'ffprobe')

    async def get_audio_info(self, file_path: str) -> Dict:
        """获取音频文件信息"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"音频文件不存在: {file_path}")
        
        cmd = [
            self.ffprobe_path,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        try:
            # Windows兼容性：使用同步subprocess
            import subprocess
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10  # 10秒超时
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"FFprobe执行失败: {result.stderr}")
            
            info = json.loads(result.stdout)
            
            # 提取音频流信息
            audio_stream = None
            for stream in info.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break
            
            if not audio_stream:
                raise ValueError("文件中未找到音频流")
            
            return {
                'duration': float(info['format'].get('duration', 0)),
                'bitrate': int(info['format'].get('bit_rate', 0)),
                'size': int(info['format'].get('size', 0)),
                'format': info['format'].get('format_name', ''),
                'sample_rate': int(audio_stream.get('sample_rate', 44100)),
                'channels': int(audio_stream.get('channels', 2)),
                'codec': audio_stream.get('codec_name', ''),
                'file_path': file_path
            }
            
        except json.JSONDecodeError:
            raise RuntimeError("解析FFprobe输出失败")
        except Exception as e:
            raise RuntimeError(f"获取音频信息失败: {str(e)}")

    async def mix_audio_tracks(self, tracks: List[Dict], output_path: str, 
                             total_duration: float, sample_rate: int = 44100) -> str:
        """混合多个音轨"""
        if not tracks:
            raise ValueError("没有音轨数据")
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 构建FFmpeg命令
        cmd = [self.ffmpeg_path]
        
        # 添加所有输入文件
        input_files = []
        for i, track in enumerate(tracks):
            if os.path.exists(track['file_path']):
                cmd.extend(['-i', track['file_path']])
                input_files.append(i)
        
        if not input_files:
            raise ValueError("没有有效的音频文件")
        
        # 构建滤镜图
        filter_complex = []
        
        for i, track in enumerate(tracks):
            if not os.path.exists(track['file_path']):
                continue
                
            input_idx = input_files.index(i) if i in input_files else None
            if input_idx is None:
                continue
            
            # 音量调节
            volume_filter = f"[{input_idx}:a]volume={track['volume']}"
            
            # 淡入淡出
            if track.get('fade_in', 0) > 0:
                volume_filter += f",afade=t=in:st=0:d={track['fade_in']}"
            if track.get('fade_out', 0) > 0:
                duration = track.get('duration', 0)
                fade_start = max(0, duration - track['fade_out'])
                volume_filter += f",afade=t=out:st={fade_start}:d={track['fade_out']}"
            
            # 时间偏移
            if track.get('start_time', 0) > 0:
                delay_ms = int(track['start_time'] * 1000)
                volume_filter += f",adelay={delay_ms}|{delay_ms}"
            
            volume_filter += f"[a{i}]"
            filter_complex.append(volume_filter)
        
        # 混合所有音轨
        valid_tracks = [i for i, track in enumerate(tracks) if os.path.exists(track['file_path'])]
        mix_inputs = ''.join([f"[a{i}]" for i in valid_tracks])
        mix_filter = f"{mix_inputs}amix=inputs={len(valid_tracks)}:duration=longest[out]"
        filter_complex.append(mix_filter)
        
        # 添加滤镜复合参数
        cmd.extend([
            '-filter_complex', ';'.join(filter_complex),
            '-map', '[out]',
            '-ar', str(sample_rate),
            '-ac', '2',  # 立体声输出
            '-t', str(total_duration),  # 限制输出时长
            '-y',  # 覆盖输出文件
            output_path
        ])
        
        try:
            # Windows兼容性：使用同步subprocess
            import subprocess
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30秒超时
            )
            
            if result.returncode != 0:
                stderr_text = result.stderr if result.stderr else "未知错误"
                stdout_text = result.stdout if result.stdout else ""
                logger.error(f"FFmpeg stderr: {stderr_text}")
                logger.error(f"FFmpeg stdout: {stdout_text}")
                raise RuntimeError(f"FFmpeg音频混合失败: {stderr_text}")
            
            logger.info(f"FFmpeg音频混合成功: {output_path}")
            return output_path
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("音频混合超时（超过30秒）")
        except Exception as e:
            raise RuntimeError(f"音频混合失败: {str(e)}")

# 全局FFmpeg服务实例
ffmpeg_service = FFmpegService()

def get_uploaded_audio_file_path(file_id: str) -> Optional[str]:
    """获取上传音频文件的完整路径"""
    if not file_id:
        return None
    
        # 音频文件存储在 storage/audio_editor/uploads/ 目录下（按category分类）
    audio_uploads_dir = get_audio_storage_path()
    
    # 先检查目录是否存在
    if not audio_uploads_dir.exists():
        logger.warning(f"音频存储目录不存在: {audio_uploads_dir}")
        return None

    logger.debug(f"音频存储目录: {audio_uploads_dir.absolute()}")
    logger.debug(f"查找音频文件: {file_id}")
    
    # 在所有可能的子目录中查找文件
    search_dirs = [
        audio_uploads_dir,  # 主目录（兼容旧文件）
        audio_uploads_dir / "dialogue",
        audio_uploads_dir / "environment", 
        audio_uploads_dir / "theme",
        audio_uploads_dir / "background"
    ]
    
    # 如果是环境音混合文件（以env_开头），添加环境音混合目录
    if file_id.startswith("env_"):
        current_dir = Path(__file__).parent.parent.parent.parent.parent  # 回到项目根目录
        mixed_dir = current_dir / "backend" / "data" / "environment_sounds" / "mixed"
        search_dirs.append(mixed_dir)
    
    # 尝试不同的文件扩展名
    possible_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.ogg']
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
            
        # 尝试带扩展名的文件
        for ext in possible_extensions:
            file_path = search_dir / f"{file_id}{ext}"
            logger.debug(f"尝试查找文件: {file_path}")
            if file_path.exists():
                logger.info(f"找到音频文件: {file_path}")
                return str(file_path)
        
        # 直接尝试原文件名
        direct_path = search_dir / file_id
        logger.debug(f"尝试查找文件: {direct_path}")
        if direct_path.exists():
            logger.info(f"找到音频文件: {direct_path}")
            return str(direct_path)
    
    # 列出目录内容以便调试
    try:
        all_files = []
        for search_dir in search_dirs:
            if search_dir.exists():
                all_files.extend([f"{search_dir.name}/{f.name}" for f in search_dir.iterdir() if f.is_file()])
        logger.warning(f"音频文件未找到: {file_id}, 所有文件: {all_files}")
    except Exception as e:
        logger.error(f"无法列出目录内容: {e}")
    
    return None

def get_audio_info(file_path: str) -> Dict[str, Any]:
    """获取音频文件信息"""
    try:
        # 检查mutagen是否可用
        if mutagen is None:
            raise ImportError("mutagen库未安装")
            
        # 使用mutagen获取音频信息
        audio_file = mutagen.File(file_path)
        if audio_file is None:
            raise ValueError("无法读取音频文件")
        
        # 获取时长
        duration = getattr(audio_file, 'length', 0.0) or 0.0
        
        # 获取音频信息
        info = audio_file.info
        sample_rate = getattr(info, 'sample_rate', 44100) or 44100
        channels = getattr(info, 'channels', 2) or 2
        bitrate = getattr(info, 'bitrate', 128000) or 128000
        
        # 确保duration不为0（使用文件大小估算）
        if duration <= 0:
            file_size = os.path.getsize(file_path)
            # 粗略估算：假设128kbps，1MB约67秒
            estimated_duration = max(1.0, (file_size / 1024 / 1024) * 67)
            duration = min(estimated_duration, 300)  # 最长5分钟
        
        return {
            'duration': duration,
            'sample_rate': sample_rate,
            'channels': channels,
            'bitrate': bitrate // 1000  # 转换为kbps
        }
    except Exception as e:
        logger.warning(f"无法获取音频文件信息: {e}")
        # 使用文件大小估算兜底
        try:
            file_size = os.path.getsize(file_path)
            estimated_duration = max(30.0, (file_size / 1024 / 1024) * 67)  # 至少30秒
            return {
                'duration': min(estimated_duration, 300),  # 最长5分钟
                'sample_rate': 44100,
                'channels': 2,
                'bitrate': 128
            }
        except:
            return {
                'duration': 30.0,  # 兜底30秒而非0秒
                'sample_rate': 44100,
                'channels': 2,
                'bitrate': 128
            }

# ========== 音频文件管理 API ==========

@router.post("/audio-files/upload", response_model=AudioFileUploadResponse)
async def upload_audio_file(
    file: UploadFile = File(...),
    category: str = Query(default="dialogue"),
    project_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """上传单个音频文件"""
    try:
        # 验证文件类型
        if not file.filename.lower().endswith(('.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a')):
            raise HTTPException(
                status_code=400,
                detail="不支持的音频格式。请上传 MP3, WAV, FLAC, AAC, OGG 或 M4A 格式的文件。"
            )
        
        # 生成文件ID和保存路径（按category分类存储）
        file_id = generate_file_id()
        storage_path = get_audio_storage_path()
        
        # 按category创建子目录
        category_path = storage_path / category
        category_path.mkdir(exist_ok=True)
        
        file_extension = Path(file.filename).suffix
        saved_filename = f"{file_id}{file_extension}"
        file_path = category_path / saved_filename
        
        # 保存文件
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 获取音频信息
        audio_info = get_audio_info(str(file_path))
        
        # 构建文件信息
        file_info = AudioFileInfo(
            id=file_id,
            filename=file.filename,
            category=category,
            duration=audio_info['duration'],
            file_size=len(content),
            format=file_extension.lstrip('.').upper(),
            sample_rate=audio_info['sample_rate'],
            channels=audio_info['channels'],
            url=f"/api/v1/sound-editor/audio-files/download/{file_id}",
            created_at=datetime.now().isoformat()
        )
        
        logger.info(f"音频文件上传成功: {file.filename} -> {file_id}")
        
        return AudioFileUploadResponse(
            success=True,
            message="文件上传成功",
            file=file_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"音频文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.get("/audio-files/list", response_model=AudioFilesListResponse)
async def list_audio_files(
    category: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """获取音频文件列表"""
    try:
        storage_path = get_audio_storage_path()
        files = []
        
        if storage_path.exists():
            # 扫描主目录和子目录（兼容旧文件）
            def scan_directory(dir_path, file_category="dialogue"):
                """扫描目录并添加文件到列表"""
                if not dir_path.exists():
                    return
                    
                for file_path in dir_path.iterdir():
                    if file_path.is_file() and file_path.suffix.lower() in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']:
                        try:
                            # 从文件名提取ID
                            file_id = file_path.stem
                            if '_' in file_id:
                                file_id = file_id.split('_', 2)[-1] if len(file_id.split('_')) > 2 else file_id
                            
                            # 获取音频信息
                            audio_info = get_audio_info(str(file_path))
                            file_stats = file_path.stat()
                            
                            file_info = AudioFileInfo(
                                id=file_path.stem,
                                filename=file_path.name,
                                category=file_category,  # 从目录推断类别
                                duration=audio_info['duration'],
                                file_size=file_stats.st_size,
                                format=file_path.suffix.lstrip('.').upper(),
                                sample_rate=audio_info['sample_rate'],
                                channels=audio_info['channels'],
                                url=f"/api/v1/sound-editor/audio-files/download/{file_path.stem}",
                                created_at=datetime.fromtimestamp(file_stats.st_ctime).isoformat()
                            )
                            
                            # 按类别过滤
                            if category is None or file_info.category == category:
                                files.append(file_info)
                                
                        except Exception as e:
                            logger.warning(f"跳过文件 {file_path.name}: {str(e)}")
                            continue
            
            # 扫描各个category子目录
            scan_directory(storage_path / "dialogue", "dialogue")
            scan_directory(storage_path / "environment", "environment") 
            scan_directory(storage_path / "theme", "theme")
            scan_directory(storage_path / "background", "background")
            
            # 扫描主目录中的旧文件（兼容性）
            scan_directory(storage_path, "dialogue")
        
        # 按创建时间排序
        files.sort(key=lambda x: x.created_at, reverse=True)
        
        return AudioFilesListResponse(
            success=True,
            files=files,
            total_count=len(files)
        )
        
    except Exception as e:
        logger.error(f"获取音频文件列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")

@router.get("/audio-files/download/{file_id}")
async def download_audio_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    """下载音频文件"""
    try:
        # 处理audio_前缀的文件ID（从章节导入的音频文件）
        if file_id.startswith('audio_'):
            # 从数据库查找对应的音频文件
            audio_id = int(file_id.replace('audio_', ''))
            audio_file = db.query(AudioFile).filter(AudioFile.id == audio_id).first()
            if audio_file and audio_file.file_path:
                # 构建绝对路径
                current_dir = Path(__file__).parent.parent.parent.parent.parent  # 回到项目根目录
                file_path = current_dir / "backend" / audio_file.file_path
                if file_path.exists():
                    return FileResponse(
                        path=str(file_path),
                        filename=Path(audio_file.file_path).name,
                        media_type="audio/mpeg"
                    )
                else:
                    logger.warning(f"章节音频文件不存在: {file_path}")
                    raise HTTPException(status_code=404, detail="章节音频文件不存在")
            else:
                raise HTTPException(status_code=404, detail="音频文件记录不存在")
        
        # 处理env_前缀的文件ID（从环境音项目导入的音频文件）
        if file_id.startswith('env_'):
            # 从环境音混合目录查找文件
            mixed_dir = Path("data/environment_sounds/mixed")
            file_stem = file_id.replace('env_', '')
            
            for file_path in mixed_dir.glob(f"{file_stem}*.wav"):
                if file_path.exists():
                    return FileResponse(
                        path=str(file_path),
                        filename=file_path.name,
                        media_type="audio/mpeg"
                    )
            
            raise HTTPException(status_code=404, detail="环境音文件不存在")
        
        # 处理普通上传的音频文件
        storage_path = get_audio_storage_path()
        
        # 在所有可能的位置查找文件
        possible_paths = [
            storage_path / file_id,  # 直接文件名
            storage_path / "dialogue" / file_id,
            storage_path / "environment" / file_id, 
            storage_path / "theme" / file_id,
            storage_path / "background" / file_id
        ]
        
        # 为每个可能路径尝试不同扩展名
        extensions = ['.wav', '.mp3', '.flac', '.aac', '.ogg', '.m4a']
        
        for base_path in possible_paths:
            # 尝试直接匹配（文件名可能已包含扩展名）
            for file_path in storage_path.rglob("*"):
                if file_path.is_file() and file_path.stem == file_id:
                    return FileResponse(
                        path=str(file_path),
                        filename=file_path.name,
                        media_type="audio/mpeg"
                    )
            
            # 尝试添加扩展名
            for ext in extensions:
                full_path = base_path.parent / f"{base_path.name}{ext}"
                if full_path.exists() and full_path.is_file():
                    return FileResponse(
                        path=str(full_path),
                        filename=full_path.name,
                        media_type="audio/mpeg"
                    )
        
        raise HTTPException(status_code=404, detail="文件不存在")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载音频文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件下载失败: {str(e)}")

@router.get("/audio-files/waveform/{file_id}")
async def get_audio_waveform(
    file_id: str,
    width: int = Query(800, description="波形图宽度"),
    height: int = Query(100, description="波形图高度"),
    db: Session = Depends(get_db)
):
    """获取音频文件波形数据"""
    try:
        # 处理audio_前缀的文件ID
        if file_id.startswith('audio_'):
            # 从数据库查找对应的音频文件
            audio_id = int(file_id.replace('audio_', ''))
            audio_file = db.query(AudioFile).filter(AudioFile.id == audio_id).first()
            if audio_file and audio_file.file_path:
                file_path = Path(audio_file.file_path)
            else:
                raise HTTPException(status_code=404, detail="音频文件不存在")
        else:
            # 直接从存储路径查找
            storage_path = get_audio_storage_path()
            file_path = None
            
            # 在所有子目录中查找文件
            for ext in ['.wav', '.mp3', '.flac', '.aac', '.ogg', '.m4a']:
                for subdir in ['dialogue', 'environment', 'theme', 'background']:
                    test_path = storage_path / subdir / f"{file_id}{ext}"
                    if test_path.exists():
                        file_path = test_path
                        break
                if file_path:
                    break
            
            if not file_path:
                raise HTTPException(status_code=404, detail="音频文件不存在")
        
        # 获取音频文件基本信息
        try:
            audio_info = get_audio_info(str(file_path))
            duration = audio_info['duration']
        except Exception as e:
            logger.warning(f"无法获取音频信息: {e}")
            duration = 5.0  # 默认时长
        
        # 返回基本信息，不需要波形数据
        return {
            "success": True,
            "data": {
                "fileId": file_id,
                "duration": duration,
                "exists": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取音频波形失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取波形失败: {str(e)}")

@router.delete("/audio-files/{file_id}")
async def delete_audio_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    """删除音频文件"""
    try:
        # 首先尝试在上传目录中查找文件
        storage_path = get_audio_storage_path()
        found = False
        
        # 在所有子目录中查找并删除文件
        for file_path in storage_path.rglob("*"):
            if file_path.is_file() and file_path.stem == file_id:
                file_path.unlink()
                logger.info(f"上传音频文件删除成功: {file_id}")
                found = True
                break
        
        # 如果没有在上传目录找到，说明可能是导入的文件
        # 对于导入的文件，我们只从项目中移除引用，不删除实际文件
        if not found:
            logger.info(f"文件 {file_id} 不在上传目录中，可能是导入的文件，仅从项目中移除引用")
            # 这里可以添加从项目中移除文件引用的逻辑
            # 但由于删除API是独立的，我们返回成功，让前端处理项目数据的更新
            return {"success": True, "message": "导入文件引用已移除"}
        
        return {"success": True, "message": "文件删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除音频文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件删除失败: {str(e)}")

@router.delete("/multitrack/project/{project_id}/audio-files/{file_id}")
async def remove_audio_file_from_project(
    project_id: str,
    file_id: str,
    db: Session = Depends(get_db)
):
    """从多轨项目中移除音频文件引用"""
    try:
        # 加载项目数据
        project_storage_path = get_project_storage_path()
        project_file = project_storage_path / f"{project_id}.json"
        
        if not os.path.exists(project_file):
            raise HTTPException(status_code=404, detail="项目不存在")
            
        try:
            with open(project_file, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
        except Exception as e:
            logger.error(f"加载项目文件失败: {e}")
            raise HTTPException(status_code=500, detail="项目文件损坏")
        
        # 从audioFiles中移除指定文件
        original_count = len(project_data.get('audioFiles', []))
        project_data['audioFiles'] = [
            audio_file for audio_file in project_data.get('audioFiles', [])
            if audio_file.get('id') != file_id
        ]
        new_count = len(project_data.get('audioFiles', []))
        
        # 从所有轨道的clips中移除对该文件的引用
        for track in project_data.get('tracks', []):
            track['clips'] = [
                clip for clip in track.get('clips', [])
                if clip.get('fileId') != file_id
            ]
        
        # 保存更新后的项目数据
        try:
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存项目文件失败: {e}")
            raise HTTPException(status_code=500, detail="保存项目失败")
        
        logger.info(f"从项目 {project_id} 中移除音频文件 {file_id}，audioFiles数量: {original_count} -> {new_count}")
        return {"success": True, "message": "音频文件已从项目中移除"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"从项目中移除音频文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"移除音频文件失败: {str(e)}")

# ========== 多轨项目管理 API ==========

@router.post("/multitrack/create", response_model=ProjectResponse)
async def create_multitrack_project(
    request: ProjectCreateRequest,
    db: Session = Depends(get_db)
):
    """创建新的多轨项目"""
    try:
        # 生成项目ID
        if not request.project.id:
            request.project.id = generate_project_id()
        
        # 设置创建时间
        if not request.project.createdAt:
            request.project.createdAt = datetime.now().isoformat()
        
        # 构建默认轨道
        default_tracks = [
            TrackInfo(
                id='track_dialogue',
                name='角色对话',
                type='dialogue',
                volume=1.0,
                muted=False,
                solo=False,
                color='#3498db',
                order=1,
                clips=[]
            ),
            TrackInfo(
                id='track_environment',
                name='环境音效',
                type='environment',
                volume=0.8,
                muted=False,
                solo=False,
                color='#27ae60',
                order=2,
                clips=[]
            ),
            TrackInfo(
                id='track_background',
                name='背景音乐',
                type='background',
                volume=0.5,
                muted=False,
                solo=False,
                color='#e74c3c',
                order=3,
                clips=[]
            )
        ]
        
        # 构建完整项目数据，包含所有必要字段
        project_data = ProjectData(
            project=request.project,
            tracks=default_tracks,
            markers=[],
            # 初始化素材区配置
            audioFiles=[],
            # 初始化章节选择信息
            selectedChapterId=request.project.chapterId if hasattr(request.project, 'chapterId') else None,
            # 初始化搜索配置
            searchKeyword="",
            activeAudioTab="dialogue"
        )
        
        # 保存项目文件
        storage_path = get_project_storage_path()
        project_file = storage_path / f"{request.project.id}.json"
        
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(project_data.model_dump(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"多轨项目创建成功: {request.project.title} -> {request.project.id}")
        
        return ProjectResponse(
            success=True,
            message="项目创建成功",
            data=project_data
        )
        
    except Exception as e:
        logger.error(f"创建多轨项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"项目创建失败: {str(e)}")

@router.put("/multitrack/save/{project_id}", response_model=ProjectResponse)
async def save_multitrack_project(
    project_id: str,
    request: ProjectSaveRequest,
    db: Session = Depends(get_db)
):
    """保存多轨项目"""
    try:
        # 更新项目ID（如果需要）
        request.project.project.id = project_id
        
        # 添加调试日志
        logger.info(f"保存项目数据 - audioFiles: {len(request.project.audioFiles)}")
        logger.info(f"保存项目数据 - selectedChapterId: {request.project.selectedChapterId}")
        logger.info(f"保存项目数据 - searchKeyword: {request.project.searchKeyword}")
        logger.info(f"保存项目数据 - activeAudioTab: {request.project.activeAudioTab}")
        
        # 保存项目文件
        storage_path = get_project_storage_path()
        project_file = storage_path / f"{project_id}.json"
        
        # 序列化数据
        serialized_data = request.project.model_dump()
        logger.info(f"序列化后的数据包含字段: {list(serialized_data.keys())}")
        
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(serialized_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"多轨项目保存成功: {project_id}")
        
        return ProjectResponse(
            success=True,
            message="项目保存成功",
            data=request.project
        )
        
    except Exception as e:
        logger.error(f"保存多轨项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"项目保存失败: {str(e)}")

@router.get("/multitrack/load/{project_id}", response_model=ProjectResponse)
async def load_multitrack_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """加载多轨项目"""
    try:
        storage_path = get_project_storage_path()
        project_file = storage_path / f"{project_id}.json"
        
        if not project_file.exists():
            raise HTTPException(status_code=404, detail="项目不存在")
        
        with open(project_file, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        # 验证并构建项目数据
        project = ProjectData(**project_data)
        
        logger.info(f"多轨项目加载成功: {project_id}")
        
        return ProjectResponse(
            success=True,
            message="项目加载成功",
            data=project
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"加载多轨项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"项目加载失败: {str(e)}")

@router.get("/multitrack/list", response_model=ProjectListResponse)
async def list_multitrack_projects(
    db: Session = Depends(get_db)
):
    """获取多轨项目列表"""
    try:
        storage_path = get_project_storage_path()
        projects = []
        
        if storage_path.exists():
            for project_file in storage_path.glob("*.json"):
                try:
                    with open(project_file, 'r', encoding='utf-8') as f:
                        project_data = json.load(f)
                    
                    # 只返回项目基本信息
                    project_info = ProjectInfo(**project_data.get('project', {}))
                    projects.append(project_info)
                    
                except Exception as e:
                    logger.warning(f"跳过项目文件 {project_file.name}: {str(e)}")
                    continue
        
        # 按创建时间排序
        projects.sort(key=lambda x: x.createdAt or "", reverse=True)
        
        return ProjectListResponse(
            success=True,
            projects=projects
        )
        
    except Exception as e:
        logger.error(f"获取多轨项目列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")

@router.delete("/multitrack/{project_id}")
async def delete_multitrack_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """删除多轨项目"""
    try:
        storage_path = get_project_storage_path()
        project_file = storage_path / f"{project_id}.json"
        
        if not project_file.exists():
            raise HTTPException(status_code=404, detail="项目不存在")
        
        project_file.unlink()
        logger.info(f"多轨项目删除成功: {project_id}")
        
        return {"success": True, "message": "项目删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除多轨项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"项目删除失败: {str(e)}")

# ========== 书籍集成 API ==========

@router.get("/book/{book_id}/chapter/{chapter_id}/resources")
async def get_chapter_audio_resources(
    book_id: int,
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """获取章节相关的音频资源"""
    try:
        from ...models import Book, BookChapter, NovelProject, AudioFile, EnvironmentSound, BackgroundMusic
        from ...services.audio_editor_book_integration_service import AudioEditorBookIntegrationService
        
        # 验证书籍和章节
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
            
        chapter = db.query(BookChapter).filter(
            BookChapter.id == chapter_id,
            BookChapter.book_id == book_id
        ).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        
        # 创建集成服务实例
        integration_service = AudioEditorBookIntegrationService(db)
        
        # 获取章节的对话音频文件（包括章节级别和项目级别的完整合成结果）
        dialogue_files = db.query(AudioFile).join(NovelProject).filter(
            NovelProject.book_id == book_id,
            # 查询条件：章节ID匹配 或者 是项目级别的完整音频
            (AudioFile.chapter_id == chapter_id) | (AudioFile.audio_type == "final"),
            AudioFile.audio_type.in_(["chapter_final", "final"]),  # 只返回完整音频
            AudioFile.status == "active"
        ).order_by(AudioFile.created_at.desc()).all()  # 按创建时间倒序，最新的在前
        
        dialogues = []
        latest_final_audio = None  # 记录最新的项目级别完整音频
        
        for audio_file in dialogue_files:
            if audio_file.file_path and Path(audio_file.file_path).exists():
                # 根据音频类型生成文件名
                if audio_file.audio_type == "chapter_final":
                    # 章节完整音频
                    filename = f"📖 {chapter.chapter_title or f'第{chapter.chapter_number}章'} - 对话音"
                    dialogues.append({
                        "fileId": f"audio_{audio_file.id}",
                        "filename": filename,
                        "duration": audio_file.duration or 5.0,
                        "character": audio_file.character_name,
                        "content": audio_file.text_content,
                        "voiceId": audio_file.voice_profile_id,
                        "filePath": audio_file.file_path,
                        "audioType": audio_file.audio_type
                    })
                elif audio_file.audio_type == "final":
                    # 项目完整音频 - 只保留最新的一个
                    if latest_final_audio is None:
                        latest_final_audio = audio_file
                        filename = f"🎵 {book.title} - 完整音频"
                        dialogues.append({
                            "fileId": f"audio_{audio_file.id}",
                            "filename": filename,
                            "duration": audio_file.duration or 5.0,
                            "character": audio_file.character_name,
                            "content": audio_file.text_content,
                            "voiceId": audio_file.voice_profile_id,
                            "filePath": audio_file.file_path,
                            "audioType": audio_file.audio_type
                        })
                else:
                    filename = audio_file.original_name or f"音频_{audio_file.id}"
                    dialogues.append({
                        "fileId": f"audio_{audio_file.id}",
                        "filename": filename,
                        "duration": audio_file.duration or 5.0,
                        "character": audio_file.character_name,
                        "content": audio_file.text_content,
                        "voiceId": audio_file.voice_profile_id,
                        "filePath": audio_file.file_path,
                        "audioType": audio_file.audio_type
                    })
        
        # 获取章节的环境音文件（包括环境音和章节级别完整音频）
        environment_files = db.query(AudioFile).join(NovelProject).filter(
            NovelProject.book_id == book_id,
            AudioFile.chapter_id == chapter_id,
            AudioFile.audio_type.in_(["environment", "environment_final", "chapter"]),  # 包括章节级别音频
            AudioFile.status == "active"
        ).all()
        
        environments = []
        for audio_file in environment_files:
            if audio_file.file_path and Path(audio_file.file_path).exists():
                # 根据音频类型生成不同的文件名
                if audio_file.audio_type == "environment":
                    # 单个环境音
                    filename = f"🌲 {audio_file.original_name or '环境音'}"
                elif audio_file.audio_type == "environment_final":
                    # 章节环境音完整音频
                    filename = f"🌲 {chapter.chapter_title or f'第{chapter.chapter_number}章'} - 环境音"
                elif audio_file.audio_type == "chapter":
                    # 章节级别完整音频
                    filename = f"🌲 {chapter.chapter_title or f'第{chapter.chapter_number}章'} - 完整音频"
                elif audio_file.audio_type == "final":
                    # 项目完整音频（包含环境音）
                    filename = f"🌲 {book.title} - 完整环境音"
                else:
                    filename = audio_file.original_name or f"环境音_{audio_file.id}"
                
                environments.append({
                    "fileId": f"audio_{audio_file.id}",
                    "filename": filename,
                    "duration": audio_file.duration or 60.0,  # 环境音通常较长
                    "filePath": audio_file.file_path,
                    "audioType": audio_file.audio_type
                })
        
        # 暂时返回空的背景音乐（后续可以扩展）
        background_music = []
        
        # 获取章节配图（如果有）
        images = []
        # BookChapter模型暂时没有image_path字段，后续可以扩展
        
        return {
            "success": True,
            "data": {
                "dialogues": dialogues,
                "environments": environments,
                "backgroundMusic": background_music,
                "images": images,
                "chapterInfo": {
                    "title": chapter.chapter_title,
                    "number": chapter.chapter_number,
                    "bookTitle": book.title
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取章节音频资源失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取资源失败: {str(e)}")

@router.get("/environment-projects/{book_id}/audio-files")
async def get_environment_project_audio_files(
    book_id: int,
    db: Session = Depends(get_db)
):
    """获取环境音项目的音频文件"""
    try:
        from ...models import EnvironmentProject
        
        # 查找该书籍的环境音项目
        env_project = db.query(EnvironmentProject).filter(
            EnvironmentProject.book_id == book_id
        ).first()
        
        if not env_project:
            return {
                "success": True,
                "data": {
                    "audioFiles": []
                }
            }
        
        # 获取环境音混合文件
        mixed_files = []
        # 使用绝对路径，从当前文件位置计算
        current_dir = Path(__file__).parent.parent.parent.parent.parent  # 回到项目根目录
        mixed_dir = current_dir / "backend" / "data" / "environment_sounds" / "mixed"
        
        if mixed_dir.exists():
            # 查找该项目的混合环境音文件
            for file_path in mixed_dir.glob(f"mixed_environment_{env_project.id}*.wav"):
                if file_path.exists():
                    mixed_files.append({
                        "fileId": f"env_{file_path.stem}",
                        "filename": file_path.name,
                        "duration": 300.0,  # 默认5分钟
                        "filePath": str(file_path),
                        "audioType": "mixed_environment"
                    })
        
        return {
            "success": True,
            "data": {
                "audioFiles": mixed_files
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取环境音项目音频文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取环境音文件失败: {str(e)}")

# ========== 预览播放 API ==========

class PreviewResponse(BaseModel):
    """预览响应"""
    success: bool
    message: str
    preview_file_id: Optional[str] = None
    preview_url: Optional[str] = None

@router.post("/multitrack/preview/{project_id}", response_model=PreviewResponse)
async def generate_preview(
    project_id: str,
    start_time: float = Query(0, description="预览开始时间（秒）"),
    duration: float = Query(3, description="预览时长（秒）"),
    db: Session = Depends(get_db)
):
    """生成多轨项目预览音频"""
    try:
        logger.info(f"开始生成预览音频: project_id={project_id}, start_time={start_time}, duration={duration}")
        
        # 加载项目数据
        project_storage_path = get_project_storage_path()
        project_file = project_storage_path / f"{project_id}.json"
        
        if not os.path.exists(project_file):
            raise HTTPException(status_code=404, detail="项目不存在")
            
        try:
            with open(project_file, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
        except Exception as e:
            logger.error(f"加载项目文件失败: {e}")
            raise HTTPException(status_code=500, detail="项目文件损坏")
            
        # 生成预览文件ID
        preview_id = f"preview_{project_id}_{int(start_time)}_{int(duration)}"
        
        # 准备音频轨道数据
        audio_tracks = []
        for track in project_data.get('tracks', []):
            if track.get('muted', False):
                continue
                
            for clip in track.get('clips', []):
                # 检查片段是否在预览时间范围内
                clip_start = clip.get('startTime', 0)
                clip_duration = clip.get('duration', 0)
                clip_end = clip_start + clip_duration
                preview_end = start_time + duration
                
                if clip_end <= start_time or clip_start >= preview_end:
                    continue  # 片段不在预览范围内
                
                # 获取音频文件路径
                file_id = clip.get('fileId', '')
                filename = clip.get('filename', '')
                audio_file_path = clip.get('audioFilePath', '')  # 从章节导入的音频文件路径
                
                # 如果audioFilePath为空，尝试从audioFiles中查找
                if not audio_file_path and filename:
                    for audio_file in project_data.get('audioFiles', []):
                        audio_filename = audio_file.get('filename', '')
                        audio_original_name = audio_file.get('original_name', '')
                        
                        # 精确匹配
                        if audio_filename == filename or audio_original_name == filename:
                            audio_file_path = audio_file.get('metadata', {}).get('filePath', '')
                            logger.info(f"从audioFiles中找到文件路径: {filename} -> {audio_file_path}")
                            break
                        
                        # 处理.wav后缀不匹配的情况
                        if filename.endswith('.wav'):
                            filename_without_ext = filename[:-4]
                            if (audio_filename.endswith('.wav') and audio_filename[:-4] == filename_without_ext) or \
                               (audio_original_name.endswith('.wav') and audio_original_name[:-4] == filename_without_ext):
                                audio_file_path = audio_file.get('metadata', {}).get('filePath', '')
                                logger.info(f"从audioFiles中找到文件路径(处理后缀): {filename} -> {audio_file_path}")
                                break
                        else:
                            # filename没有后缀，但audio_file有后缀
                            if audio_filename == filename + '.wav' or audio_original_name == filename + '.wav':
                                audio_file_path = audio_file.get('metadata', {}).get('filePath', '')
                                logger.info(f"从audioFiles中找到文件路径(添加后缀): {filename} -> {audio_file_path}")
                                break
                
                # 如果fileId不为空，也尝试从audioFiles中查找
                if not audio_file_path and file_id:
                    for audio_file in project_data.get('audioFiles', []):
                        if audio_file.get('id') == file_id:
                            audio_file_path = audio_file.get('metadata', {}).get('filePath', '')
                            logger.info(f"从audioFiles中找到文件路径: {file_id} -> {audio_file_path}")
                            break
                # 优先使用audioFilePath（从章节导入的路径）
                if audio_file_path:
                    # 检查是否是相对路径，如果是则转换为绝对路径
                    if not os.path.isabs(audio_file_path):
                        current_dir = Path(__file__).parent.parent.parent.parent.parent  # 回到项目根目录
                        # 统一路径分隔符
                        normalized_path = audio_file_path.replace('\\', '/')
                        
                        # 根据路径类型选择不同的处理方式
                        if normalized_path.startswith('data/environment_sounds/'):
                            # 环境音文件路径
                            absolute_path = current_dir / "backend" / normalized_path
                        elif normalized_path.startswith('outputs/'):
                            # 章节音频文件路径
                            absolute_path = current_dir / "backend" / normalized_path
                        else:
                            # 其他路径
                            absolute_path = current_dir / "backend" / normalized_path
                        
                        audio_file_path = str(absolute_path)
                        logger.info(f"转换音频文件路径: {audio_file_path}")
                    
                    if os.path.exists(audio_file_path):
                        logger.info(f"使用音频文件路径: {audio_file_path}")
                    else:
                        logger.warning(f"音频文件不存在: {audio_file_path}")
                        audio_file_path = None
                else:
                    # 如果fileId为空，尝试使用filename
                    if not file_id and filename:
                        file_id = filename
                    
                    # 使用fileId查找上传的音频文件
                    audio_file_path = get_uploaded_audio_file_path(file_id)
                
                if not audio_file_path or not os.path.exists(audio_file_path):
                    logger.warning(f"音频文件不存在: {audio_file_path}")
                    continue
                
                # 计算相对于预览开始时间的偏移
                relative_start = max(0, clip_start - start_time)
                
                # 添加到音频轨道列表
                audio_tracks.append({
                    "file_path": audio_file_path,
                    "start_time": relative_start,
                    "duration": clip_duration,
                    "volume": clip.get('volume', 1.0) * track.get('volume', 1.0),
                    "fade_in": clip.get('fadeIn', 0),
                    "fade_out": clip.get('fadeOut', 0)
                })
        
        # 确保预览目录存在
        # 确保使用绝对路径
        current_dir = Path(__file__).parent.parent.parent.parent.parent  # 回到项目根目录
        preview_dir = current_dir / "storage" / "audio_editor" / "previews"
        preview_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成预览音频文件
        output_path = str(preview_dir / f"{preview_id}.wav")
        preview_url = f"/api/v1/sound-editor/preview/download/{preview_id}"
        
        if audio_tracks:
            logger.info(f"开始音频混合，轨道数量: {len(audio_tracks)}")
            for i, track in enumerate(audio_tracks):
                logger.info(f"轨道 {i}: 文件={track['file_path']}, 存在={os.path.exists(track['file_path'])}, 时长={track['duration']}, 音量={track['volume']}")
            
            # 使用FFmpeg进行真正的音频混合
            try:
                result_path = await ffmpeg_service.mix_audio_tracks(
                    audio_tracks,
                    output_path,
                    duration,
                    44100
                )
                logger.info(f"真实音频混合完成: {result_path}")
            except Exception as e:
                logger.error(f"FFmpeg音频混合失败: {e}")
                logger.error(f"详细错误信息: {str(e)}")
                # 降级到静音文件
                logger.info("降级到生成静音文件")
                await generate_silence_file(output_path, duration)
        else:
            # 没有音频轨道，生成静音文件
            logger.warning(f"项目 {project_id} 没有可用的音频轨道，生成静音文件")
            await generate_silence_file(output_path, duration)
        
        # 验证预览文件是否生成成功且不为空
        if not os.path.exists(output_path):
            logger.error(f"预览音频文件生成失败，文件不存在: {output_path}")
            raise HTTPException(status_code=500, detail="预览音频文件生成失败")
        
        file_size = os.path.getsize(output_path)
        if file_size == 0:
            logger.error(f"预览音频文件为空: {output_path}")
            raise HTTPException(
                status_code=500, 
                detail="预览音频生成失败：生成的文件为空\n请确保FFmpeg正常工作: winget install ffmpeg"
            )
        
        logger.info(f"预览音频生成成功: {output_path}, 文件大小: {file_size} bytes")
        
        return {
            "success": True,
            "message": "预览音频生成成功",
            "preview_file_id": preview_id,
            "preview_url": preview_url
        }
        
    except Exception as e:
        logger.error(f"生成预览音频失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成预览失败: {str(e)}")

async def generate_silence_file(output_path: str, duration: float):
    """生成静音文件 - 需要FFmpeg"""
    try:
        ffmpeg_path = ffmpeg_service.ffmpeg_path
        logger.info(f"开始生成静音文件: {output_path}, 时长: {duration}秒")
        logger.info(f"FFmpeg路径: {ffmpeg_path}")
        
        cmd = [
            ffmpeg_path,
            '-f', 'lavfi',
            '-i', f'anullsrc=r=44100:cl=stereo',
            '-t', str(duration),
            '-y', output_path
        ]
        
        logger.info(f"FFmpeg命令: {' '.join(cmd)}")
        
        # Windows兼容性：使用同步subprocess
        import subprocess
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10  # 10秒超时
        )
        
        if result.returncode != 0:
            stderr_text = result.stderr if result.stderr else "未知错误"
            stdout_text = result.stdout if result.stdout else ""
            logger.error(f"FFmpeg stderr: {stderr_text}")
            logger.error(f"FFmpeg stdout: {stdout_text}")
            raise RuntimeError(f"FFmpeg生成静音文件失败: {stderr_text}")
        
        logger.info(f"FFmpeg生成静音文件成功: {output_path}")
            
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"生成静音文件失败: {e}")
        logger.error(f"详细错误信息: {error_detail}")
        raise HTTPException(
            status_code=500, 
            detail=f"音频处理失败: {e}\n详细信息: {error_detail}\n请确保已安装FFmpeg: winget install ffmpeg"
        )

@router.get("/preview/download/{preview_id}")
async def download_preview_audio(
    preview_id: str,
    db: Session = Depends(get_db)
):
    """下载预览音频文件"""
    try:
        # 统一存储在项目根目录的storage中
        # 确保使用绝对路径
        current_dir = Path(__file__).parent.parent.parent.parent.parent  # 回到项目根目录
        preview_storage = current_dir / "storage" / "audio_editor" / "previews"
        preview_file = preview_storage / f"{preview_id}.wav"
        
        # 检查预览文件是否存在
        if not preview_file.exists():
            logger.error(f"预览文件不存在: {preview_file}")
            raise HTTPException(
                status_code=404, 
                detail=f"预览音频文件不存在: {preview_id}\n可能是音频处理失败，请检查FFmpeg安装"
            )
        
        # 检查文件大小
        file_size = preview_file.stat().st_size
        if file_size == 0:
            logger.error(f"预览文件为空: {preview_file}")
            raise HTTPException(
                status_code=500, 
                detail="预览音频文件为空\n请确保FFmpeg正常工作: winget install ffmpeg"
            )
        
        return FileResponse(
            path=str(preview_file),
            filename=f"preview_{preview_id}.wav",
            media_type="audio/wav"
        )
        
    except Exception as e:
        logger.error(f"下载预览音频失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"预览下载失败: {str(e)}")

@router.delete("/preview/{filename}")
async def delete_preview_file(
    filename: str,
    db: Session = Depends(get_db)
):
    """删除预览文件"""
    try:
        # 统一存储在项目根目录的storage中
        # 确保使用绝对路径
        current_dir = Path(__file__).parent.parent.parent.parent.parent  # 回到项目根目录
        preview_storage = current_dir / "storage" / "audio_editor" / "previews"
        preview_file = preview_storage / filename
        
        if preview_file.exists():
            preview_file.unlink()
            logger.info(f"预览文件删除成功: {filename}")
        
        return {"success": True, "message": "预览文件删除成功"}
        
    except Exception as e:
        logger.error(f"删除预览文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除预览文件失败: {str(e)}")

# ========== 导出功能 ==========

class ExportResponse(BaseModel):
    """导出响应"""
    success: bool
    message: str
    export_task_id: Optional[str] = None
    status: Optional[str] = None

class ExportStatusResponse(BaseModel):
    """导出状态响应"""
    success: bool
    status: str  # 'pending', 'processing', 'completed', 'failed'
    progress: float = 0.0
    message: str
    download_url: Optional[str] = None

@router.post("/multitrack/export/{project_id}", response_model=ExportResponse)
async def export_project(
    project_id: str,
    format: str = Query(default="wav", description="导出格式"),
    db: Session = Depends(get_db)
):
    """导出项目为音频文件"""
    try:
        # 加载项目数据
        storage_path = get_project_storage_path()
        project_file = storage_path / f"{project_id}.json"
        
        if not project_file.exists():
            raise HTTPException(status_code=404, detail="项目不存在")
        
        with open(project_file, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        # 验证项目数据
        project = ProjectData(**project_data)
        
        # 生成导出任务ID
        export_task_id = f"export_{project_id}_{int(time.time())}"
        
        # 统一存储在项目根目录的storage中
        # 确保使用绝对路径
        current_dir = Path(__file__).parent.parent.parent.parent.parent  # 回到项目根目录
        export_storage = current_dir / "storage" / "audio_editor" / "exports"
        export_storage.mkdir(parents=True, exist_ok=True)
        
        # 生成导出音频文件路径
        export_file = export_storage / f"{export_task_id}.{format}"
        
        # 简单的导出实现（目前生成测试音频，实际项目中需要实现音轨混合）
        logger.info(f"开始导出项目: {project_id} -> {export_task_id}")
        
        # 创建导出音频文件（目前创建测试音频）
        import wave
        import math
        
        with wave.open(str(export_file), 'wb') as wav_file:
            wav_file.setnchannels(2)  # 立体声
            wav_file.setsampwidth(2)  # 16位
            wav_file.setframerate(44100)  # 44.1kHz
            
            # 生成测试音频：5秒的渐变音调
            duration = 5  # 秒
            sample_rate = 44100
            volume = 0.4
            
            frames = []
            for i in range(int(duration * sample_rate)):
                t = i / sample_rate
                # 频率从220Hz到880Hz渐变
                frequency = 220 + (660 * t / duration)
                sine_wave = math.sin(2 * math.pi * frequency * t)
                # 应用淡出效果
                fade_factor = 1.0 if t < duration - 1 else (duration - t)
                sample = int(sine_wave * volume * fade_factor * 32767)
                sample_bytes = sample.to_bytes(2, byteorder='little', signed=True)
                frames.append(sample_bytes * 2)  # 左右声道
            
            wav_file.writeframes(b''.join(frames))
        
        logger.info(f"项目导出完成: {export_task_id}")
        
        return ExportResponse(
            success=True,
            message="项目导出成功",
            export_task_id=export_task_id,
            status="completed"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"项目导出失败: {str(e)}")

@router.get("/multitrack/export/status/{export_task_id}", response_model=ExportStatusResponse)
async def get_export_status(
    export_task_id: str,
    db: Session = Depends(get_db)
):
    """获取导出任务状态"""
    try:
        # 确保使用绝对路径
        current_dir = Path(__file__).parent.parent.parent.parent.parent  # 回到项目根目录
        export_storage = current_dir / "storage" / "audio_editor" / "exports"
        export_files = list(export_storage.glob(f"{export_task_id}.*"))
        
        if export_files:
            # 文件存在，导出完成
            return ExportStatusResponse(
                success=True,
                status="completed",
                progress=100.0,
                message="导出完成",
                download_url=f"/api/v1/sound-editor/multitrack/export/download/{export_task_id}"
            )
        else:
            # 文件不存在，可能还在处理中或失败
            return ExportStatusResponse(
                success=True,
                status="failed",
                progress=0.0,
                message="导出文件不存在"
            )
        
    except Exception as e:
        logger.error(f"获取导出状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取导出状态失败: {str(e)}")

@router.get("/multitrack/export/download/{export_task_id}")
async def download_exported_audio(
    export_task_id: str,
    db: Session = Depends(get_db)
):
    """下载导出的音频文件"""
    try:
        # 确保使用绝对路径
        current_dir = Path(__file__).parent.parent.parent.parent.parent  # 回到项目根目录
        export_storage = current_dir / "storage" / "audio_editor" / "exports"
        export_files = list(export_storage.glob(f"{export_task_id}.*"))
        
        if not export_files:
            raise HTTPException(status_code=404, detail="导出文件不存在")
        
        export_file = export_files[0]
        
        return FileResponse(
            path=str(export_file),
            filename=f"exported_{export_task_id}.{export_file.suffix[1:]}",
            media_type="audio/wav"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载导出音频失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出下载失败: {str(e)}")

# ========== 书籍资源集成 ==========

@router.get("/books/list", response_model=dict)
async def get_available_books(db: Session = Depends(get_db)):
    """获取可用的书籍列表，用于音频编辑器集成"""
    try:
        from ...services.audio_editor_book_integration_service import AudioEditorBookIntegrationService
        
        service = AudioEditorBookIntegrationService(db)
        books = service.get_available_books()
        
        return {
            "success": True,
            "data": books,
            "message": f"获取到 {len(books)} 本可用书籍"
        }
        
    except Exception as e:
        logger.error(f"获取书籍列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/books/{book_id}/chapters", response_model=dict)
async def get_book_chapters(book_id: int, db: Session = Depends(get_db)):
    """获取书籍的章节列表，显示资源统计信息"""
    try:
        from ...services.audio_editor_book_integration_service import AudioEditorBookIntegrationService
        
        service = AudioEditorBookIntegrationService(db)
        chapters = service.get_book_chapters(book_id)
        
        return {
            "success": True,
            "data": chapters,
            "message": f"获取到 {len(chapters)} 个章节"
        }
        
    except Exception as e:
        logger.error(f"获取书籍章节失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/books/{book_id}/chapters/resources", response_model=dict)
async def get_chapter_resources(
    book_id: int, 
    request: Dict[str, List[int]], 
    db: Session = Depends(get_db)
):
    """获取指定章节的所有可导入资源"""
    try:
        from ...services.audio_editor_book_integration_service import AudioEditorBookIntegrationService
        
        chapter_ids = request.get('chapter_ids', [])
        if not chapter_ids:
            raise HTTPException(status_code=400, detail="章节ID列表不能为空")
        
        service = AudioEditorBookIntegrationService(db)
        resources = service.get_chapter_resources(book_id, chapter_ids)
        
        if 'error' in resources:
            raise HTTPException(status_code=400, detail=resources['error'])
        
        return {
            "success": True,
            "data": resources,
            "message": f"获取到章节资源: {resources['resource_summary']}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取章节资源失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-from-chapters", response_model=dict)
async def create_project_from_chapters(
    request: Dict[str, Any], 
    db: Session = Depends(get_db)
):
    """从书籍章节创建音频编辑器项目"""
    try:
        from ...services.audio_editor_book_integration_service import AudioEditorBookIntegrationService
        
        # 验证请求参数
        project_name = request.get('project_name')
        book_id = request.get('book_id')
        chapter_ids = request.get('chapter_ids', [])
        selected_resources = request.get('selected_resources', {})
        
        if not project_name:
            raise HTTPException(status_code=400, detail="项目名称不能为空")
        if not book_id:
            raise HTTPException(status_code=400, detail="书籍ID不能为空")
        if not chapter_ids:
            raise HTTPException(status_code=400, detail="章节ID列表不能为空")
        
        service = AudioEditorBookIntegrationService(db)
        result = service.create_editor_project_with_chapters(
            project_name=project_name,
            book_id=book_id,
            chapter_ids=chapter_ids,
            selected_resources=selected_resources
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', '创建项目失败'))
        
        return {
            "success": True,
            "data": {
                "project_id": result['project_id'],
                "resource_summary": result['resource_summary']
            },
            "message": result['message']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"从章节创建项目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))




# ========== 健康检查 ==========

@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "sound-editor",
        "timestamp": datetime.now().isoformat()
    }