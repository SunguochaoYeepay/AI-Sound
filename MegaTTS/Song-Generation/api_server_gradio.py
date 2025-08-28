#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于官方Gradio逻辑的SongGeneration FastAPI服务器
"""

import os
import sys
import time
import uuid
import json
import yaml
import re
import torch
import torchaudio
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append('codeclm/tokenizer/')
sys.path.append('codeclm/tokenizer/Flow1dVAE/')

# 直接导入LeVoInference的实现
import torch
import numpy as np
from omegaconf import OmegaConf
from codeclm.trainer.codec_song_pl import CodecLM_PL
from codeclm.models import CodecLM
from codeclm.models import builders
from separator import Separator

class LeVoInference(torch.nn.Module):
    def __init__(self, ckpt_path):
        super().__init__()
        torch.backends.cudnn.enabled = False 
        OmegaConf.register_new_resolver("eval", lambda x: eval(x))
        OmegaConf.register_new_resolver("concat", lambda *x: [xxx for xx in x for xxx in xx])
        OmegaConf.register_new_resolver("get_fname", lambda: 'default')
        OmegaConf.register_new_resolver("load_yaml", lambda x: list(OmegaConf.load(x)))

        cfg_path = os.path.join(ckpt_path, 'config.yaml')
        self.pt_path = os.path.join(ckpt_path, 'model.pt')
        self.cfg = OmegaConf.load(cfg_path)
        self.cfg.mode = 'inference'
        self.max_duration = self.cfg.max_dur
        self.default_params = dict(
            top_p = 0.0,
            record_tokens = True,
            record_window = 50,
            extend_stride = 5,
            duration = self.max_duration,
        )

    def forward(self, lyric: str, description: str = None, prompt_audio_path: os.PathLike = None, genre: str = None, auto_prompt_path: os.PathLike = None, params = dict()):
        if prompt_audio_path is not None and os.path.exists(prompt_audio_path):
            separator = Separator()
            audio_tokenizer = builders.get_audio_tokenizer_model(self.cfg.audio_tokenizer_checkpoint, self.cfg)
            audio_tokenizer = audio_tokenizer.eval().cuda()
            seperate_tokenizer = builders.get_audio_tokenizer_model(self.cfg.audio_tokenizer_checkpoint_sep, self.cfg)
            seperate_tokenizer = seperate_tokenizer.eval().cuda()
            pmt_wav, vocal_wav, bgm_wav = separator.run(prompt_audio_path)
            pmt_wav = pmt_wav.cuda()
            vocal_wav = vocal_wav.cuda()
            bgm_wav = bgm_wav.cuda()
            pmt_wav, _ = audio_tokenizer.encode(pmt_wav)
            vocal_wav, bgm_wav = seperate_tokenizer.encode(vocal_wav, bgm_wav)
            melody_is_wav = False
            del audio_tokenizer
            del seperate_tokenizer
            del separator
        elif genre is not None and auto_prompt_path is not None and os.path.exists(auto_prompt_path):
            auto_prompt = torch.load(auto_prompt_path)
            merge_prompt = [item for sublist in auto_prompt.values() for item in sublist]
            if genre == "Auto": 
                prompt_token = merge_prompt[np.random.randint(0, len(merge_prompt))]
            else:
                prompt_token = auto_prompt[genre][np.random.randint(0, len(auto_prompt[genre]))]
            pmt_wav = prompt_token[:,[0],:]
            vocal_wav = prompt_token[:,[1],:]
            bgm_wav = prompt_token[:,[2],:]
            melody_is_wav = False
        else:
            pmt_wav = None
            vocal_wav = None
            bgm_wav = None
            melody_is_wav = True

        model_light = CodecLM_PL(self.cfg, self.pt_path)
        model_light = model_light.eval()
        model_light.audiolm.cfg = self.cfg
        model = CodecLM(name = "tmp",
            lm = model_light.audiolm,
            audiotokenizer = None,
            max_duration = self.max_duration,
            seperate_tokenizer = None,
        )
        del model_light
        model.lm = model.lm.cuda().to(torch.float16)
        params = {**self.default_params, **params}
        model.set_generation_params(**params)

        generate_inp = {
            'lyrics': [lyric.replace("  ", " ")],
            'descriptions': [description],
            'melody_wavs': pmt_wav,
            'vocal_wavs': vocal_wav,
            'bgm_wavs': bgm_wav,
            'melody_is_wav': melody_is_wav,
        }

        with torch.autocast(device_type="cuda", dtype=torch.float16):
            tokens = model.generate(**generate_inp, return_tokens=True)

        del model
        torch.cuda.empty_cache()

        seperate_tokenizer = builders.get_audio_tokenizer_model(self.cfg.audio_tokenizer_checkpoint_sep, self.cfg)
        seperate_tokenizer = seperate_tokenizer.eval().cuda()
        model = CodecLM(name = "tmp",
            lm = None,
            audiotokenizer = None,
            max_duration = self.max_duration,
            seperate_tokenizer = seperate_tokenizer,
        )

        if tokens.shape[-1] > 3000:
            tokens = tokens[..., :3000]
            
        with torch.no_grad():
            if melody_is_wav:
                wav_seperate = model.generate_audio(tokens, pmt_wav, vocal_wav, bgm_wav)
            else:
                wav_seperate = model.generate_audio(tokens)

        del seperate_tokenizer
        del model
        torch.cuda.empty_cache()
        return wav_seperate[0]

# 设置环境变量
os.environ['USER'] = 'root'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['TRANSFORMERS_CACHE'] = f"{os.getcwd()}/third_party/hub"
os.environ['NCCL_HOME'] = '/usr/local/tccl'
os.environ['PYTHONPATH'] = f"{os.getcwd()}/codeclm/tokenizer/:{os.getcwd()}:{os.getcwd()}/codeclm/tokenizer/Flow1dVAE/:{os.getcwd()}/codeclm/tokenizer/:{os.environ.get('PYTHONPATH', '')}"

# FastAPI应用
app = FastAPI(
    title="SongGeneration API Server", 
    description="基于官方Gradio逻辑的音乐生成API服务",
    version="2.0.0"
)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="templates"), name="static")

# 全局变量
MODEL = None
STRUCTS = None
AUTO_PROMPT = None

# 支持的音乐风格
SUPPORTED_GENRES = ["Pop", "R&B", "Dance", "Jazz", "Folk", "Rock", "Chinese Style", "Chinese Tradition", "Metal", "Reggae", "Chinese Opera", "Auto"]

# 默认歌词示例
EXAMPLE_LYRICS = """
[intro-short]

[verse]
夜晚的街灯闪烁
我漫步在熟悉的角落
回忆像潮水般涌来
你的笑容如此清晰

[chorus]
回忆的温度还在
你却已不在
我的心被爱填满
却又被思念刺痛

[outro-short]
""".strip()

class SongRequest(BaseModel):
    """歌曲生成请求"""
    lyrics: str
    description: Optional[str] = None
    genre: Optional[str] = None
    cfg_coef: Optional[float] = 1.5
    temperature: Optional[float] = 0.9
    top_k: Optional[int] = 50

class SongResponse(BaseModel):
    """歌曲生成响应"""
    success: bool
    message: str
    file_id: Optional[str] = None
    file_path: Optional[str] = None
    generation_time: Optional[float] = None
    sample_rate: Optional[int] = None
    input_config: Optional[Dict[str, Any]] = None

def format_lyrics(lyric: str) -> tuple[str, Optional[str]]:
    """格式化歌词，返回(formatted_lyric, error_message)"""
    global STRUCTS
    
    # 格式化结构标签
    lyric = lyric.replace("[intro]", "[intro-short]").replace("[inst]", "[inst-short]").replace("[outro]", "[outro-short]")
    paragraphs = [p.strip() for p in lyric.strip().split('\n\n') if p.strip()]
    
    if len(paragraphs) < 1:
        return None, "歌词不能为空"
    
    paragraphs_norm = []
    vocal_flag = False
    vocal_structs = ['[verse]', '[chorus]', '[bridge]']
    
    for para in paragraphs:
        lines = para.splitlines()
        struct_tag = lines[0].strip().lower()
        
        if struct_tag not in STRUCTS:
            # 🔧 修复STRUCTS.keys()错误：STRUCTS是列表而不是字典
            return None, f"段落必须以结构标签开始，支持的标签: {STRUCTS}"
        
        if struct_tag in vocal_structs:
            vocal_flag = True
            if len(lines) < 2 or not [line.strip() for line in lines[1:] if line.strip()]:
                return None, f"以下段落需要歌词: {vocal_structs}"
            else:
                new_para_list = []
                for line in lines[1:]:
                    new_para_list.append(re.sub(r"[^\w\s\[\]\-\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af\u00c0-\u017f]", "", line))
                new_para_str = f"{struct_tag} {'.'.join(new_para_list)}"
        else:
            if len(lines) > 1:
                return None, f"以下段落不应包含歌词: [intro], [intro-short], [intro-medium], [inst], [inst-short], [inst-medium], [outro], [outro-short], [outro-medium]"
            else:
                new_para_str = struct_tag
        paragraphs_norm.append(new_para_str)
    
    if not vocal_flag:
        return None, f"歌词必须包含至少一个人声段落: {vocal_structs}"
    
    lyric_norm = " ; ".join(paragraphs_norm)
    return lyric_norm, None

def initialize_model(ckpt_path: str):
    """初始化模型"""
    global MODEL, STRUCTS, AUTO_PROMPT
    
    print("🚀 正在初始化SongGeneration模型...")
    
    # 初始化LeVoInference
    MODEL = LeVoInference(ckpt_path)
    
    # 加载结构配置
    with open('conf/vocab.yaml', 'r', encoding='utf-8') as file:
        STRUCTS = yaml.safe_load(file)
    
    # 加载自动提示
    prompt_path = os.path.join(ckpt_path, 'prompt.pt')
    if os.path.exists(prompt_path):
        AUTO_PROMPT = torch.load(prompt_path)
        print(f"✅ 自动提示加载成功: {prompt_path}")
    else:
        print(f"⚠️  自动提示文件不存在: {prompt_path}")
        AUTO_PROMPT = None
    
    print("✅ 模型初始化完成!")

async def cleanup_file(file_path: str, delay: int = 0):
    """清理临时文件"""
    if delay > 0:
        import asyncio
        await asyncio.sleep(delay)
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ 已清理临时文件: {file_path}")
    except Exception as e:
        print(f"⚠️ 清理文件失败: {e}")

@app.on_event("startup")
async def startup_event():
    """启动时初始化模型"""
    ckpt_path = sys.argv[1] if len(sys.argv) > 1 else "ckpt/songgeneration_base"
    initialize_model(ckpt_path)

@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": "SongGeneration API Server (Gradio版本)", 
        "status": "running", 
        "version": "2.0.0",
        "based_on": "Official Gradio Implementation",
        "demo_page": "/demo",
        "api_docs": "/docs"
    }

@app.get("/demo", response_class=HTMLResponse)
async def demo_page():
    """Demo演示页面"""
    try:
        with open("templates/demo.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Demo页面未找到")

@app.get("/ping")
async def ping():
    """简单存活检查"""
    return {"status": "pong", "timestamp": time.time()}

@app.get("/health")
async def health_check():
    """健康检查接口"""
    model_status = MODEL is not None
    
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
    
    # 整体状态
    overall_status = "healthy" if model_status and torch.cuda.is_available() else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": time.time(),
        "model": {
            "loaded": model_status,
            "ready": model_status,
            "implementation": "Official LeVoInference"
        },
        "gpu": gpu_info,
        "api_version": "2.0.0",
        "endpoints": {
            "generate": "/generate",
            "download": "/download/{file_id}",
            "supported_genres": "/supported_genres",
            "example_lyrics": "/example_lyrics"
        }
    }

@app.get("/supported_genres")
async def get_supported_genres():
    """获取支持的音乐风格"""
    return {"genres": SUPPORTED_GENRES}

@app.get("/example_lyrics")
async def get_example_lyrics():
    """获取示例歌词"""
    return {"example_lyrics": EXAMPLE_LYRICS, "structs": STRUCTS if STRUCTS else []}

@app.post("/generate", response_model=SongResponse)
async def generate_song(request: SongRequest, background_tasks: BackgroundTasks):
    """生成歌曲"""
    if MODEL is None:
        raise HTTPException(status_code=503, detail="模型未初始化")
    
    try:
        start_time = time.time()
        
        # 验证输入
        if not request.lyrics.strip():
            raise HTTPException(status_code=400, detail="歌词不能为空")
        
        if request.genre and request.genre not in SUPPORTED_GENRES:
            raise HTTPException(status_code=400, detail=f"不支持的音乐风格: {request.genre}")
        
        # 格式化歌词
        lyric_norm, error_msg = format_lyrics(request.lyrics)
        if error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 生成唯一文件ID
        file_id = str(uuid.uuid4())
        output_dir = "output/api_generated"
        os.makedirs(output_dir, exist_ok=True)
        target_wav_path = f"{output_dir}/{file_id}.flac"
        
        # 准备生成参数
        params = {
            'cfg_coef': request.cfg_coef,
            'temperature': request.temperature,
            'top_k': request.top_k
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        print(f"🎵 开始生成歌曲 (ID: {file_id})...")
        print(f"📝 歌词: {lyric_norm[:100]}...")
        
        # 调用官方推理引擎
        audio_data = MODEL(
            lyric=lyric_norm,
            description=request.description,
            prompt_audio_path=None,
            genre=request.genre,
            auto_prompt_path=os.path.join("ckpt/songgeneration_base", 'prompt.pt'),
            params=params
        )
        
        # 保存音频文件
        sample_rate = MODEL.cfg.sample_rate
        
        # 确保音频数据是正确的2D格式 [channels, samples]
        audio_tensor = audio_data.cpu()
        print(f"🔍 原始音频shape: {audio_tensor.shape}")
        
        # 处理不同的音频张量格式
        if audio_tensor.dim() == 1:
            # 1D -> 2D [1, samples]
            audio_tensor = audio_tensor.unsqueeze(0)
        elif audio_tensor.dim() == 3:
            # 3D -> 2D, 假设格式为 [batch, channels, samples]
            audio_tensor = audio_tensor.squeeze(0)
        elif audio_tensor.dim() > 3:
            # 高维度，取第一个batch和前两个维度
            audio_tensor = audio_tensor[0]
            if audio_tensor.dim() > 2:
                audio_tensor = audio_tensor.view(audio_tensor.shape[0], -1)
        
        print(f"🔍 处理后音频shape: {audio_tensor.shape}")
        
        # 确保是2D张量
        if audio_tensor.dim() != 2:
            # 最后的保险措施：flatten然后reshape
            audio_tensor = audio_tensor.flatten().unsqueeze(0)
            print(f"🔍 最终音频shape: {audio_tensor.shape}")
        
        torchaudio.save(target_wav_path, audio_tensor, sample_rate)
        
        generation_time = time.time() - start_time
        print(f"✅ 歌曲生成完成 (ID: {file_id}), 耗时: {generation_time:.2f}秒")
        
        # 创建输入配置记录
        input_config = {
            "lyric": lyric_norm,
            "genre": request.genre,
            "description": request.description,
            "params": params,
            "inference_duration": generation_time,
            "timestamp": datetime.now().isoformat(),
        }
        
        # 添加后台任务清理临时文件（1小时后）
        background_tasks.add_task(cleanup_file, target_wav_path, delay=3600)
        
        return SongResponse(
            success=True,
            message="歌曲生成成功",
            file_id=file_id,
            file_path=target_wav_path,
            generation_time=generation_time,
            sample_rate=sample_rate,
            input_config=input_config
        )
        
    except Exception as e:
        print(f"❌ 生成歌曲时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")

@app.websocket("/ws/progress/{task_id}")
async def websocket_progress(websocket: WebSocket, task_id: str):
    """WebSocket进度监控端点"""
    await manager.connect(websocket, task_id)
    try:
        while True:
            # 保持连接活跃
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(task_id)

async def generate_song_with_progress(request: SongRequest, task_id: str) -> SongResponse:
    """带进度报告的异步音乐生成"""
    if MODEL is None:
        raise HTTPException(status_code=503, detail="模型未初始化")
    
    try:
        start_time = time.time()
        
        # 步骤1: 验证输入 (10%)
        await manager.send_progress(task_id, 0.1, "验证输入参数...")
        
        if not request.lyrics.strip():
            raise HTTPException(status_code=400, detail="歌词不能为空")
        
        if request.genre and request.genre not in SUPPORTED_GENRES:
            raise HTTPException(status_code=400, detail=f"不支持的音乐风格: {request.genre}")
        
        # 步骤2: 格式化歌词 (20%)
        await manager.send_progress(task_id, 0.2, "格式化歌词...")
        lyric_norm, error_msg = format_lyrics(request.lyrics)
        if error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 步骤3: 准备生成 (30%)
        await manager.send_progress(task_id, 0.3, "准备音乐生成...")
        file_id = str(uuid.uuid4())
        output_dir = "output/api_generated"
        os.makedirs(output_dir, exist_ok=True)
        target_wav_path = f"{output_dir}/{file_id}.flac"
        
        params = {
            'cfg_coef': request.cfg_coef,
            'temperature': request.temperature,
            'top_k': request.top_k
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        print(f"🎵 开始生成歌曲 (ID: {file_id})...")
        print(f"📝 歌词: {lyric_norm[:100]}...")
        
        # 步骤4: 音乐生成 (30% -> 90%)
        await manager.send_progress(task_id, 0.4, "正在生成音乐...")
        
        # 由于MODEL()调用是同步的，我们在生成过程中模拟进度
        # 在实际实现中，可以修改MODEL内部来报告真实进度
        async def simulate_progress():
            for i in range(6):  # 6个阶段
                await asyncio.sleep(1)  # 每秒更新一次
                progress = 0.4 + (i + 1) * 0.08  # 从40%到88%
                await manager.send_progress(task_id, progress, f"生成中... 阶段 {i+1}/6")
        
        # 启动进度模拟任务
        progress_task = asyncio.create_task(simulate_progress())
        
        # 在另一个线程中运行MODEL生成（避免阻塞）
        def run_model():
            return MODEL(
                lyric=lyric_norm,
                description=request.description,
                prompt_audio_path=None,
                genre=request.genre,
                auto_prompt_path='ckpt/ckpt/prompt.pt',
                params=params
            )
        
        # 使用线程池执行器运行模型生成
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_model)
            
            # 等待生成完成或进度任务完成
            while not future.done():
                await asyncio.sleep(0.5)
            
            # 取消进度任务
            progress_task.cancel()
            
            # 获取生成结果
            audio_data = future.result()
        
        # 步骤5: 保存音频 (95%)
        await manager.send_progress(task_id, 0.95, "保存音频文件...")
        
        sample_rate = MODEL.cfg.sample_rate
        audio_tensor = audio_data.cpu()
        print(f"🔍 原始音频shape: {audio_tensor.shape}")
        
        # 处理音频格式
        if audio_tensor.dim() == 1:
            audio_tensor = audio_tensor.unsqueeze(0)
        elif audio_tensor.dim() == 3:
            audio_tensor = audio_tensor.squeeze(0)
        elif audio_tensor.dim() > 3:
            audio_tensor = audio_tensor[0]
            if audio_tensor.dim() > 2:
                audio_tensor = audio_tensor.view(audio_tensor.shape[0], -1)
        
        if audio_tensor.dim() != 2:
            audio_tensor = audio_tensor.flatten().unsqueeze(0)
        
        torchaudio.save(target_wav_path, audio_tensor, sample_rate)
        
        generation_time = time.time() - start_time
        print(f"✅ 歌曲生成完成 (ID: {file_id}), 耗时: {generation_time:.2f}秒")
        
        # 步骤6: 完成 (100%)
        await manager.send_progress(task_id, 1.0, f"生成完成！耗时 {generation_time:.1f}秒")
        
        input_config = {
            "lyric": lyric_norm,
            "genre": request.genre,
            "description": request.description,
            "params": params,
            "inference_duration": generation_time,
            "timestamp": datetime.now().isoformat(),
        }
        
        return SongResponse(
            success=True,
            message="歌曲生成成功",
            file_id=file_id,
            file_path=target_wav_path,
            generation_time=generation_time,
            sample_rate=sample_rate,
            input_config=input_config
        )
        
    except Exception as e:
        await manager.send_progress(task_id, -1, f"生成失败: {str(e)}")
        print(f"❌ 生成歌曲时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")

@app.post("/generate_async")
async def generate_song_async(request: SongRequest):
    """异步音乐生成（支持进度监控）"""
    task_id = str(uuid.uuid4())
    
    # 启动后台生成任务
    asyncio.create_task(generate_song_with_progress(request, task_id))
    
    return {
        "task_id": task_id,
        "message": "音乐生成任务已启动",
        "websocket_url": f"ws://localhost:7862/ws/progress/{task_id}",
        "instructions": "请连接到WebSocket URL获取实时进度"
    }

@app.get("/download/{file_id}")
async def download_song(file_id: str):
    """下载生成的歌曲文件"""
    file_path = f"output/api_generated/{file_id}.flac"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在或已过期")
    
    return FileResponse(
        path=file_path,
        media_type="audio/flac",
        filename=f"song_{file_id}.flac"
    )

# 添加WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        self.active_connections[task_id] = websocket

    def disconnect(self, task_id: str):
        if task_id in self.active_connections:
            del self.active_connections[task_id]

    async def send_progress(self, task_id: str, progress: float, message: str):
        if task_id in self.active_connections:
            try:
                await self.active_connections[task_id].send_text(
                    json.dumps({
                        "progress": progress,
                        "message": message,
                        "timestamp": time.time()
                    })
                )
            except:
                # 连接已断开，清理
                self.disconnect(task_id)

# 全局连接管理器
manager = ConnectionManager()

if __name__ == "__main__":
    print("🎵 SongGeneration API Server (Gradio版本) 启动中...")
    print("📁 模型路径:", sys.argv[1] if len(sys.argv) > 1 else "ckpt/songgeneration_base")
    print("🌐 端口:", sys.argv[2] if len(sys.argv) > 2 else "7862")
    
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 7862
    uvicorn.run(app, host="0.0.0.0", port=port) 