import os
import sys
import time
import json
import uuid
import tempfile
from pathlib import Path
from typing import Optional, List
import torch
import torchaudio
import numpy as np
from omegaconf import OmegaConf

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

from codeclm.trainer.codec_song_pl import CodecLM_PL
from codeclm.models import CodecLM
from tools.gradio.separator import Separator

# 设置环境变量
os.environ['USER'] = 'root'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['TRANSFORMERS_CACHE'] = f"{os.getcwd()}/third_party/hub"
os.environ['NCCL_HOME'] = '/usr/local/tccl'
os.environ['PYTHONPATH'] = f"{os.getcwd()}/codeclm/tokenizer/:{os.getcwd()}:{os.getcwd()}/codeclm/tokenizer/Flow1dVAE/:{os.getcwd()}/codeclm/tokenizer/:{os.environ.get('PYTHONPATH', '')}"

app = FastAPI(title="SongGeneration API", description="高质量歌曲生成API", version="1.0.0")

# 全局变量
model = None
separator = None
auto_prompt = None
cfg = None
device = None

class SongRequest(BaseModel):
    lyrics: str
    descriptions: Optional[str] = None
    auto_prompt_audio_type: Optional[str] = None
    cfg_coef: Optional[float] = 1.5
    temperature: Optional[float] = 0.9
    top_k: Optional[int] = 50

class SongResponse(BaseModel):
    success: bool
    message: str
    file_id: Optional[str] = None
    file_path: Optional[str] = None
    generation_time: Optional[float] = None

# 支持的自动提示类型
AUTO_PROMPT_TYPES = ['Pop', 'R&B', 'Dance', 'Jazz', 'Folk', 'Rock', 'Chinese Style', 'Chinese Tradition', 'Metal', 'Reggae', 'Chinese Opera', 'Auto']

def initialize_model(ckpt_path: str):
    """初始化模型"""
    global model, separator, auto_prompt, cfg
    
    print("🚀 正在初始化SongGeneration模型...")
    
    # 设置OmegaConf解析器
    torch.backends.cudnn.enabled = False
    OmegaConf.register_new_resolver("eval", lambda x: eval(x))
    OmegaConf.register_new_resolver("concat", lambda *x: [xxx for xx in x for xxx in xx])
    OmegaConf.register_new_resolver("get_fname", lambda: 'api_server')
    OmegaConf.register_new_resolver("load_yaml", lambda x: list(OmegaConf.load(x)))
    
    # 加载配置
    cfg_path = os.path.join(ckpt_path, 'config.yaml')
    model_path = os.path.join(ckpt_path, 'model.pt')
    cfg = OmegaConf.load(cfg_path)
    cfg.mode = 'inference'
    max_duration = cfg.max_dur
    
    # 初始化模型
    model_light = CodecLM_PL(cfg, model_path)
    
    # 自动检测设备（支持CPU/GPU兼容）
    global device
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"🖥️  使用设备: {device}")
    
    model_light = model_light.eval().to(device)
    model_light.audiolm.cfg = cfg
    
    model = CodecLM(
        name="song_generation_api",
        lm=model_light.audiolm,
        audiotokenizer=model_light.audio_tokenizer,
        max_duration=max_duration,
        seperate_tokenizer=model_light.seperate_tokenizer,
    )
    
    # 初始化分离器
    separator = Separator()
    
    # 加载自动提示
    auto_prompt = torch.load('ckpt/ckpt/prompt.pt')
    
    print("✅ 模型初始化完成!")

@app.on_event("startup")
async def startup_event():
    """启动时初始化模型"""
    ckpt_path = sys.argv[1] if len(sys.argv) > 1 else "ckpt/songgeneration_base"
    initialize_model(ckpt_path)

@app.get("/")
async def root():
    """API根路径"""
    return {"message": "SongGeneration API Server", "status": "running", "version": "1.0.0"}

@app.get("/ping")
async def ping():
    """简单存活检查"""
    return {"status": "pong", "timestamp": time.time()}

@app.get("/health")
async def health_check():
    """健康检查接口"""
    import psutil
    import platform
    
    # 检查模型状态
    model_status = model is not None
    
    # 检查GPU状态
    gpu_info = {}
    if torch.cuda.is_available():
        gpu_info = {
            "available": True,
            "device_count": torch.cuda.device_count(),
            "current_device": torch.cuda.current_device(),
            "device_name": torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else "Unknown",
            "memory_allocated": f"{torch.cuda.memory_allocated(0) / 1024**3:.2f} GB" if torch.cuda.device_count() > 0 else "0 GB",
            "memory_reserved": f"{torch.cuda.memory_reserved(0) / 1024**3:.2f} GB" if torch.cuda.device_count() > 0 else "0 GB"
        }
    else:
        gpu_info = {"available": False}
    
    # 系统信息
    system_info = {
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent if platform.system() != 'Windows' else psutil.disk_usage('C:').percent
    }
    
    # 整体状态
    overall_status = "healthy" if model_status and torch.cuda.is_available() else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": time.time(),
        "model": {
            "loaded": model_status,
            "ready": model_status
        },
        "gpu": gpu_info,
        "system": system_info,
        "api_version": "1.0.0",
        "endpoints": {
            "generate": "/generate",
            "generate_with_audio": "/generate_with_audio", 
            "download": "/download/{file_id}",
            "supported_genres": "/supported_genres"
        }
    }

@app.get("/supported_genres")
async def get_supported_genres():
    """获取支持的音乐风格"""
    return {"genres": AUTO_PROMPT_TYPES}

@app.post("/generate", response_model=SongResponse)
async def generate_song(request: SongRequest, background_tasks: BackgroundTasks):
    """生成歌曲"""
    if model is None:
        raise HTTPException(status_code=503, detail="模型未初始化")
    
    try:
        start_time = time.time()
        
        # 验证输入
        if not request.lyrics.strip():
            raise HTTPException(status_code=400, detail="歌词不能为空")
        
        if request.auto_prompt_audio_type and request.auto_prompt_audio_type not in AUTO_PROMPT_TYPES:
            raise HTTPException(status_code=400, detail=f"不支持的音乐风格: {request.auto_prompt_audio_type}")
        
        # 生成唯一文件ID
        file_id = str(uuid.uuid4())
        output_dir = "output/api_generated"
        os.makedirs(output_dir, exist_ok=True)
        target_wav_path = f"{output_dir}/{file_id}.flac"
        
        # 准备生成参数
        lyric = request.lyrics.replace("  ", " ")
        descriptions = request.descriptions
        
        # 处理音频提示
        pmt_wav = None
        vocal_wav = None
        bgm_wav = None
        melody_is_wav = True
        
        if request.auto_prompt_audio_type:
            merge_prompt = [item for sublist in auto_prompt.values() for item in sublist]
            if request.auto_prompt_audio_type == "Auto":
                prompt_token = merge_prompt[np.random.randint(0, len(merge_prompt))]
            else:
                prompt_token = auto_prompt[request.auto_prompt_audio_type][np.random.randint(0, len(auto_prompt[request.auto_prompt_audio_type]))]
            
            pmt_wav = prompt_token[:,[0],:]
            vocal_wav = prompt_token[:,[1],:]
            bgm_wav = prompt_token[:,[2],:]
            melody_is_wav = False
        
        # 设置生成参数
        model.set_generation_params(
            duration=cfg.max_dur,
            extend_stride=5,
            temperature=request.temperature,
            cfg_coef=request.cfg_coef,
            top_k=request.top_k,
            top_p=0.0,
            record_tokens=True,
            record_window=50
        )
        
        # 准备生成输入
        generate_inp = {
            'lyrics': [lyric],
            'descriptions': [descriptions],
            'melody_wavs': pmt_wav,
            'vocal_wavs': vocal_wav,
            'bgm_wavs': bgm_wav,
            'melody_is_wav': melody_is_wav,
        }
        
        print(f"🎵 开始生成歌曲 (ID: {file_id})...")
        
        # 生成tokens
        if device == 'cuda':
            with torch.autocast(device_type="cuda", dtype=torch.float16):
                tokens = model.generate(**generate_inp, return_tokens=True)
        else:
            tokens = model.generate(**generate_inp, return_tokens=True)
        
        # 生成音频
        with torch.no_grad():
            if melody_is_wav:
                wav_seperate = model.generate_audio(tokens, pmt_wav, vocal_wav, bgm_wav)
            else:
                wav_seperate = model.generate_audio(tokens)
        
        # 保存音频文件
        torchaudio.save(target_wav_path, wav_seperate[0].cpu().float(), cfg.sample_rate)
        
        generation_time = time.time() - start_time
        print(f"✅ 歌曲生成完成 (ID: {file_id}), 耗时: {generation_time:.2f}秒")
        
        # 添加后台任务清理临时文件（1小时后）
        background_tasks.add_task(cleanup_file, target_wav_path, delay=3600)
        
        return SongResponse(
            success=True,
            message="歌曲生成成功",
            file_id=file_id,
            file_path=target_wav_path,
            generation_time=generation_time
        )
        
    except Exception as e:
        print(f"❌ 生成歌曲时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")

@app.post("/generate_with_audio", response_model=SongResponse)
async def generate_song_with_audio(
    lyrics: str,
    descriptions: Optional[str] = None,
    audio_file: UploadFile = File(...),
    cfg_coef: float = 1.5,
    temperature: float = 0.9,
    top_k: int = 50,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """使用音频提示生成歌曲"""
    if model is None:
        raise HTTPException(status_code=503, detail="模型未初始化")
    
    try:
        start_time = time.time()
        
        # 验证音频文件
        if not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="请上传音频文件")
        
        # 保存上传的音频文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            content = await audio_file.read()
            temp_audio.write(content)
            temp_audio_path = temp_audio.name
        
        try:
            # 分离音频
            pmt_wav, vocal_wav, bgm_wav = separator.run(temp_audio_path)
            melody_is_wav = True
            
            # 生成唯一文件ID
            file_id = str(uuid.uuid4())
            output_dir = "output/api_generated"
            os.makedirs(output_dir, exist_ok=True)
            target_wav_path = f"{output_dir}/{file_id}.flac"
            
            # 设置生成参数
            model.set_generation_params(
                duration=cfg.max_dur,
                extend_stride=5,
                temperature=temperature,
                cfg_coef=cfg_coef,
                top_k=top_k,
                top_p=0.0,
                record_tokens=True,
                record_window=50
            )
            
            # 准备生成输入
            generate_inp = {
                'lyrics': [lyrics.replace("  ", " ")],
                'descriptions': [descriptions],
                'melody_wavs': pmt_wav,
                'vocal_wavs': vocal_wav,
                'bgm_wavs': bgm_wav,
                'melody_is_wav': melody_is_wav,
            }
            
            print(f"🎵 开始生成歌曲 (ID: {file_id}), 使用音频提示...")
            
            # 生成tokens
            if device == 'cuda':
                with torch.autocast(device_type="cuda", dtype=torch.float16):
                    tokens = model.generate(**generate_inp, return_tokens=True)
            else:
                tokens = model.generate(**generate_inp, return_tokens=True)
            
            # 生成音频
            with torch.no_grad():
                wav_seperate = model.generate_audio(tokens, pmt_wav, vocal_wav, bgm_wav)
            
            # 保存音频文件
            torchaudio.save(target_wav_path, wav_seperate[0].cpu().float(), cfg.sample_rate)
            
            generation_time = time.time() - start_time
            print(f"✅ 歌曲生成完成 (ID: {file_id}), 耗时: {generation_time:.2f}秒")
            
            # 添加后台任务清理文件
            background_tasks.add_task(cleanup_file, target_wav_path, delay=3600)
            background_tasks.add_task(cleanup_file, temp_audio_path, delay=10)
            
            return SongResponse(
                success=True,
                message="歌曲生成成功",
                file_id=file_id,
                file_path=target_wav_path,
                generation_time=generation_time
            )
            
        finally:
            # 清理临时音频文件
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
                
    except Exception as e:
        print(f"❌ 生成歌曲时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")

@app.get("/download/{file_id}")
async def download_song(file_id: str):
    """下载生成的歌曲"""
    file_path = f"output/api_generated/{file_id}.flac"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=file_path,
        filename=f"song_{file_id}.flac",
        media_type="audio/flac"
    )

async def cleanup_file(file_path: str, delay: int = 0):
    """清理文件的后台任务"""
    if delay > 0:
        await asyncio.sleep(delay)
    
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            print(f"🗑️ 已清理文件: {file_path}")
    except Exception as e:
        print(f"⚠️ 清理文件失败: {e}")

if __name__ == "__main__":
    import asyncio
    
    if len(sys.argv) < 2:
        print("用法: python api_server.py <ckpt_path> [port]")
        print("示例: python api_server.py ckpt/songgeneration_base 8000")
        sys.exit(1)
    
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    
    print(f"🎵 SongGeneration API Server 启动中...")
    print(f"📁 模型路径: {sys.argv[1]}")
    print(f"🌐 端口: {port}")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    ) 