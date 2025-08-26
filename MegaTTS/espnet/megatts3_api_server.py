#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的MegaTTS3 REST API Server - 修复FFmpeg路径
跳过pynini依赖的版本
"""

import os
import io
import base64
import traceback
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import tempfile
import numpy as np

# 修复FFmpeg路径
ffmpeg_path = os.path.expanduser("~/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-7.1.1-full_build/bin")
os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ.get("PATH", "")

# 设置pydub的FFmpeg路径
from pydub import AudioSegment
AudioSegment.converter = os.path.join(ffmpeg_path, "ffmpeg.exe")
AudioSegment.ffmpeg = os.path.join(ffmpeg_path, "ffmpeg.exe")
AudioSegment.ffprobe = os.path.join(ffmpeg_path, "ffprobe.exe")

print(f"✅ FFmpeg路径已设置: {ffmpeg_path}")

# 跳过pynini依赖
import sys
sys.path.append('.')

# 模拟text normalizer
class MockNormalizer:
    def __init__(self, **kwargs):
        pass
    
    def normalize(self, text):
        return text

# 替换导入
import builtins
original_import = builtins.__import__

def mock_import(name, *args, **kwargs):
    if name == 'tn.chinese.normalizer':
        class MockZhNormalizer:
            def __init__(self, **kwargs):
                pass
            def normalize(self, text):
                return text
        return type('MockModule', (), {'Normalizer': MockZhNormalizer})()
    elif name == 'tn.english.normalizer':
        class MockEnNormalizer:
            def __init__(self, **kwargs):
                pass
            def normalize(self, text):
                return text
        return type('MockModule', (), {'Normalizer': MockEnNormalizer})()
    else:
        return original_import(name, *args, **kwargs)

builtins.__import__ = mock_import

try:
    from tts.infer_cli import MegaTTS3DiTInfer
except ImportError as e:
    print(f"导入MegaTTS3失败: {e}")
    print("请确保所有依赖都已正确安装")
    exit(1)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局变量
tts_model = None

def init_model():
    """初始化MegaTTS3模型"""
    global tts_model
    try:
        print("正在初始化MegaTTS3模型...")
        import torch
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"检测到设备: {device}")
        if torch.cuda.is_available():
            print(f"GPU设备: {torch.cuda.get_device_name(0)}")
            print(f"CUDA版本: {torch.version.cuda}")
        tts_model = MegaTTS3DiTInfer(device=device)
        print(f"模型初始化成功，使用设备: {device}")
        return True
    except Exception as e:
        print(f"模型初始化失败: {str(e)}")
        traceback.print_exc()
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': tts_model is not None,
        'service': 'MegaTTS3 API (Fixed FFmpeg)'
    })

@app.route('/api/v1/tts/synthesize', methods=['POST'])
def synthesize_speech():
    """
    语音合成接口
    
    Parameters:
    - audio_file: 参考音频文件 (form-data)
    - text: 要合成的文本 (form-data)
    - latent_file: 可选的latent文件 (form-data)
    - time_step: 推理步数，默认32 (form-data)
    - p_w: 智能度权重，默认1.4 (form-data) 
    - t_w: 相似度权重，默认3.0 (form-data)
    
    Returns:
    - JSON格式响应，包含base64编码的音频数据
    """
    global tts_model
    
    if tts_model is None:
        return jsonify({'error': '模型未初始化'}), 500
    
    try:
        # 获取参数
        if 'audio_file' not in request.files:
            return jsonify({'error': '缺少参考音频文件'}), 400
        
        if 'text' not in request.form:
            return jsonify({'error': '缺少文本参数'}), 400
            
        audio_file = request.files['audio_file']
        text = request.form.get('text')
        time_step = int(request.form.get('time_step', 32))
        p_w = float(request.form.get('p_w', 1.4))
        t_w = float(request.form.get('t_w', 3.0))
        
        # 读取音频文件
        audio_content = audio_file.read()
        
        # 处理latent文件
        latent_file_path = None
        if 'latent_file' in request.files:
            latent_file = request.files['latent_file']
            with tempfile.NamedTemporaryFile(delete=False, suffix='.npy') as tmp_latent:
                latent_file.save(tmp_latent.name)
                latent_file_path = tmp_latent.name
        
        print(f"[TTS] 开始处理语音合成: text='{text[:50]}...', time_step={time_step}, p_w={p_w}, t_w={t_w}")
        print(f"[TTS] 参考音频文件大小: {len(audio_content)} bytes")
        
        # 预处理
        resource_context = tts_model.preprocess(audio_content, latent_file=latent_file_path)
        
        # 合成语音
        wav_bytes = tts_model.forward(resource_context, text, time_step=time_step, p_w=p_w, t_w=t_w)
        
        # 清理临时文件
        if latent_file_path and os.path.exists(latent_file_path):
            os.unlink(latent_file_path)
        
        # 清理模型内存
        import gc
        import torch
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # 返回音频文件
        return send_file(
            io.BytesIO(wav_bytes),
            mimetype='audio/wav',
            as_attachment=True,
            download_name=f'synthesized_{text[:20]}.wav'
        )
        
    except Exception as e:
        error_msg = f"语音合成失败: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

@app.route('/api/v1/info', methods=['GET'])
def get_info():
    """获取API信息"""
    return jsonify({
        'service': 'MegaTTS3 API Server (Fixed FFmpeg)',
        'version': '1.0.0',
        'model_loaded': tts_model is not None,
        'endpoints': {
            '/health': 'GET - 健康检查',
            '/api/v1/tts/synthesize': 'POST - 语音合成（返回文件）',
            '/api/v1/info': 'GET - API信息'
        }
    })

if __name__ == '__main__':
    print("启动修复了FFmpeg路径的MegaTTS3 API服务器...")
    
    # 初始化模型
    if not init_model():
        print("模型初始化失败，服务启动失败")
        exit(1)
    
    # 启动Flask服务
    port = int(os.environ.get('API_PORT', 7929))
    host = os.environ.get('API_HOST', '0.0.0.0')
    
    print(f"API服务器启动在 http://{host}:{port}")
    print("可用端点:")
    print(f"  - GET  http://{host}:{port}/health")
    print(f"  - GET  http://{host}:{port}/api/v1/info")
    print(f"  - POST http://{host}:{port}/api/v1/tts/synthesize")
    
    app.run(host=host, port=port, debug=False)
