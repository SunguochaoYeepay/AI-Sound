#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TangoFlux API Server
提供HTTP API接口用于环境音生成
"""

import os
import json
import base64
import tempfile
import logging
from typing import Dict, Any, Optional
import argparse

import torch
import torchaudio
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flasgger import Swagger, swag_from

# 导入TangoFlux推理模块
from tangoflux import TangoFluxInference

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)

# 配置Swagger文档
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "TangoFlux Environment Sound Generator API",
        "description": "AI-powered environment sound generation using TangoFlux",
        "version": "1.0.0",
        "contact": {
            "name": "AI-Sound Team"
        }
    },
    "host": "127.0.0.1:7930",
    "basePath": "/",
    "schemes": ["http"],
    "consumes": ["application/json"],
    "produces": ["application/json", "audio/wav"]
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# 全局模型实例
model = None

def load_model():
    """加载TangoFlux模型"""
    global model
    try:
        logger.info("正在加载TangoFlux模型...")
        # 创建自定义的TangoFluxInference实例，使用本地模型
        from tangoflux.model import TangoFlux
        from diffusers import AutoencoderOobleck
        from safetensors.torch import load_file
        import json
        import torch
        import os
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"使用设备: {device}")
        
        # 初始化模型
        model = type('TangoFluxLocal', (), {})()
        model.vae = AutoencoderOobleck()
        
        # 加载本地模型文件
        model_path = "./models/TangoFlux"
        logger.info(f"从本地路径加载模型: {model_path}")
        
        # 加载VAE权重
        vae_weights = load_file(f"{model_path}/vae.safetensors")
        model.vae.load_state_dict(vae_weights)
        
        # 加载主模型权重
        weights = load_file(f"{model_path}/tangoflux.safetensors")
        
        # 加载配置
        with open(f"{model_path}/config.json", "r") as f:
            config = json.load(f)
        
        # 检查是否有本地T5模型缓存
        t5_cache_path = os.path.expanduser("~/.cache/huggingface/hub")
        t5_model_path = None
        
        # 查找本地T5模型
        if os.path.exists(t5_cache_path):
            for root, dirs, files in os.walk(t5_cache_path):
                if "config.json" in files and "flan-t5-large" in root:
                    t5_model_path = root
                    logger.info(f"找到本地T5模型: {t5_model_path}")
                    break
        
        # 创建TangoFlux模型实例 - 使用本地T5模型
        t5_model_path = os.path.expanduser("~/.cache/huggingface/hub/models--google--flan-t5-large/snapshots/abc123")
        
        if os.path.exists(t5_model_path):
            logger.info(f"使用本地T5模型: {t5_model_path}")
            model.model = TangoFlux(config, text_encoder_dir=t5_model_path)
        else:
            logger.warning("未找到本地T5模型，尝试在线下载...")
            model.model = TangoFlux(config)
        
        # 加载模型权重
        model.model.load_state_dict(weights, strict=False)
        
        # 移动到设备
        model.vae.to(device)
        model.model.to(device)
        
        # 添加生成方法
        def generate(self, prompt, steps=25, duration=10, guidance_scale=4.5):
            with torch.no_grad():
                latents = self.model.inference_flow(
                    prompt,
                    duration=duration,
                    num_inference_steps=steps,
                    guidance_scale=guidance_scale,
                )
                wave = self.vae.decode(latents.transpose(2, 1)).sample.cpu()[0]
            waveform_end = int(duration * self.vae.config.sampling_rate)
            wave = wave[:, :waveform_end]
            return wave
        
        model.generate = generate.__get__(model)
        
        logger.info("TangoFlux模型加载成功")
        return True
    except Exception as e:
        logger.error(f"TangoFlux模型加载失败: {e}")
        return False

@app.route('/health', methods=['GET'])
@swag_from({
    'tags': ['Health'],
    'summary': '健康检查接口',
    'description': '检查服务状态和模型加载情况',
    'responses': {
        200: {
            'description': '服务正常',
            'schema': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'healthy'},
                    'model': {'type': 'string', 'example': 'TangoFlux'},
                    'version': {'type': 'string', 'example': '1.0.0'}
                }
            }
        },
        503: {
            'description': '服务异常',
            'schema': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'unhealthy'},
                    'error': {'type': 'string', 'example': 'Model not loaded'}
                }
            }
        }
    }
})
def health_check():
    """健康检查接口"""
    try:
        if model is None:
            return jsonify({
                'status': 'unhealthy',
                'error': 'Model not loaded'
            }), 503
        
        return jsonify({
            'status': 'healthy',
            'model': 'TangoFlux',
            'version': '1.0.0'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/api/v1/info', methods=['GET'])
@swag_from({
    'tags': ['Info'],
    'summary': '获取服务信息',
    'description': '获取TangoFlux服务的基本信息',
    'responses': {
        200: {
            'description': '服务信息',
            'schema': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string', 'example': 'TangoFlux Environment Sound Generator'},
                    'version': {'type': 'string', 'example': '1.0.0'},
                    'description': {'type': 'string'},
                    'endpoints': {'type': 'object'}
                }
            }
        }
    }
})
def get_info():
    """获取服务信息"""
    return jsonify({
        'name': 'TangoFlux Environment Sound Generator',
        'version': '1.0.0',
        'description': 'AI-powered environment sound generation using TangoFlux',
        'endpoints': {
            'health': '/health',
            'info': '/api/v1/info',
            'generate': '/api/v1/generate'
        }
    })

@app.route('/api/v1/generate', methods=['POST'])
@swag_from({
    'tags': ['Generation'],
    'summary': '生成环境音（WAV文件）',
    'description': '根据文本描述生成环境音并返回WAV音频文件',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'text': {
                        'type': 'string',
                        'description': '环境音描述',
                        'example': '雨声和雷声'
                    },
                    'steps': {
                        'type': 'integer',
                        'description': '推理步数',
                        'default': 50,
                        'example': 50
                    },
                    'duration': {
                        'type': 'integer',
                        'description': '音频时长（秒）',
                        'default': 10,
                        'example': 10
                    },
                    'sample_rate': {
                        'type': 'integer',
                        'description': '采样率',
                        'default': 44100,
                        'example': 44100
                    }
                },
                'required': ['text']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'WAV音频文件',
            'schema': {
                'type': 'file',
                'format': 'binary'
            }
        },
        400: {
            'description': '请求参数错误',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        503: {
            'description': '模型未加载',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def generate_sound():
    """生成环境音"""
    try:
        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # 提取参数
        text = data.get('text', '')
        steps = data.get('steps', 50)
        duration = data.get('duration', 10)
        sample_rate = data.get('sample_rate', 44100)
        
        if not text:
            return jsonify({'error': 'Text description is required'}), 400
        
        # 检查模型是否加载
        if model is None:
            return jsonify({'error': 'Model not loaded'}), 503
        
        logger.info(f"生成环境音: {text}, steps={steps}, duration={duration}")
        
        # 生成音频
        audio = model.generate(text, steps=steps, duration=duration)
        
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            torchaudio.save(temp_file.name, audio, sample_rate)
            temp_path = temp_file.name
        
        # 返回音频文件
        return send_file(
            temp_path,
            mimetype='audio/wav',
            as_attachment=True,
            download_name=f'tangoflux_output_{hash(text) % 10000}.wav'
        )
        
    except Exception as e:
        logger.error(f"生成环境音失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/generate_base64', methods=['POST'])
@swag_from({
    'tags': ['Generation'],
    'summary': '生成环境音（Base64）',
    'description': '根据文本描述生成环境音并返回Base64编码的音频数据',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'text': {
                        'type': 'string',
                        'description': '环境音描述',
                        'example': '雨声和雷声'
                    },
                    'steps': {
                        'type': 'integer',
                        'description': '推理步数',
                        'default': 50,
                        'example': 50
                    },
                    'duration': {
                        'type': 'integer',
                        'description': '音频时长（秒）',
                        'default': 10,
                        'example': 10
                    },
                    'sample_rate': {
                        'type': 'integer',
                        'description': '采样率',
                        'default': 44100,
                        'example': 44100
                    }
                },
                'required': ['text']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Base64编码的音频数据',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': True},
                    'audio_base64': {'type': 'string', 'description': 'Base64编码的WAV音频数据'},
                    'text': {'type': 'string', 'example': '雨声和雷声'},
                    'steps': {'type': 'integer', 'example': 50},
                    'duration': {'type': 'integer', 'example': 10},
                    'sample_rate': {'type': 'integer', 'example': 44100}
                }
            }
        },
        400: {
            'description': '请求参数错误',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        503: {
            'description': '模型未加载',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def generate_sound_base64():
    """生成环境音并返回base64编码"""
    try:
        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # 提取参数
        text = data.get('text', '')
        steps = data.get('steps', 50)
        duration = data.get('duration', 10)
        sample_rate = data.get('sample_rate', 44100)
        
        if not text:
            return jsonify({'error': 'Text description is required'}), 400
        
        # 检查模型是否加载
        if model is None:
            return jsonify({'error': 'Model not loaded'}), 503
        
        logger.info(f"生成环境音(base64): {text}, steps={steps}, duration={duration}")
        
        # 生成音频
        audio = model.generate(text, steps=steps, duration=duration)
        
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            torchaudio.save(temp_file.name, audio, sample_rate)
            temp_path = temp_file.name
        
        # 读取文件并转换为base64
        with open(temp_path, 'rb') as f:
            audio_data = f.read()
        
        # 清理临时文件
        os.unlink(temp_path)
        
        # 返回base64编码
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        return jsonify({
            'success': True,
            'audio_base64': audio_base64,
            'text': text,
            'steps': steps,
            'duration': duration,
            'sample_rate': sample_rate
        })
        
    except Exception as e:
        logger.error(f"生成环境音(base64)失败: {e}")
        return jsonify({'error': str(e)}), 500

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='TangoFlux API Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=7930, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # 加载模型
    if not load_model():
        logger.error("模型加载失败，退出服务")
        return 1
    
    # 启动服务
    logger.info(f"启动TangoFlux API服务器: {args.host}:{args.port}")
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug,
        threaded=True
    )

if __name__ == '__main__':
    main()
