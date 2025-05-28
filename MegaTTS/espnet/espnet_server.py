#!/usr/bin/env python3
"""
ESPnet TTS服务器
为AI-Sound系统提供ESPnet TTS引擎服务
"""

from flask import Flask, request, send_file, jsonify
import os
import tempfile
import traceback
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 全局变量
text2speech = None
model_loaded = False

def load_model():
    """加载ESPnet模型"""
    global text2speech, model_loaded
    
    try:
        # 检查模型文件是否存在
        config_path = "exp/tts_train_vits_raw_phn_pypinyin_g2p_phone/config.yaml"
        model_path = "exp/tts_train_vits_raw_phn_pypinyin_g2p_phone/train.total_count.ave_10best.pth"
        
        if not os.path.exists(config_path) or not os.path.exists(model_path):
            logger.warning(f"模型文件不存在: {config_path} 或 {model_path}")
            return False
        
        from espnet2.bin.tts_inference import Text2Speech
        import torch
        
        text2speech = Text2Speech(
            train_config=config_path,
            model_file=model_path,
            device="cuda" if torch.cuda.is_available() else "cpu"
        )
        
        model_loaded = True
        logger.info("ESPnet模型加载成功")
        return True
        
    except Exception as e:
        logger.error(f"模型加载失败: {e}")
        logger.error(traceback.format_exc())
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy" if model_loaded else "error",
        "model_loaded": model_loaded,
        "service": "espnet-tts",
        "version": "1.0.0"
    })

@app.route('/synthesize', methods=['POST'])
def synthesize():
    """文本合成端点"""
    try:
        if not model_loaded:
            return jsonify({
                'success': False,
                'error': 'ESPnet模型未加载'
            }), 500
        
        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        text = data.get('text')
        if not text:
            return jsonify({
                'success': False,
                'error': '文本参数为空'
            }), 400
        
        voice_id = data.get('voice_id', 'default')
        speed = data.get('speed', 1.0)
        pitch = data.get('pitch', 0.0)
        output_path = data.get('output_path')
        
        logger.info(f"合成请求: text='{text}', voice_id='{voice_id}'")
        
        # 执行TTS合成
        result = text2speech(text)
        wav = result["wav"].view(-1).cpu().numpy()
        
        # 计算音频时长
        sample_rate = 24000
        duration = len(wav) / sample_rate
        
        logger.info(f"合成完成: 长度={len(wav)}, 采样率={sample_rate}, 时长={duration:.2f}s")
        
        if output_path:
            # 保存到指定路径
            import soundfile as sf
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            sf.write(str(output_file), wav, sample_rate)
            
            return jsonify({
                'success': True,
                'output_path': str(output_file),
                'duration': duration,
                'sample_rate': sample_rate
            })
        else:
            # 返回音频文件
            import soundfile as sf
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                sf.write(f.name, wav, sample_rate)
                return send_file(
                    f.name, 
                    mimetype="audio/wav", 
                    as_attachment=True, 
                    download_name="espnet_output.wav"
                )
        
    except Exception as e:
        logger.error(f"合成失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/voices', methods=['GET'])
def get_voices():
    """获取可用声音列表"""
    return jsonify({
        "voices": [
            {
                "id": "espnet_zh_female_001",
                "name": "ESPnet中文女声",
                "language": "zh-CN",
                "gender": "female",
                "description": "ESPnet训练的中文女声模型"
            }
        ]
    })

@app.route('/info', methods=['GET'])
def get_info():
    """获取服务信息"""
    return jsonify({
        "service": "espnet-tts",
        "version": "1.0.0",
        "model_loaded": model_loaded,
        "supported_languages": ["zh-CN"],
        "supported_formats": ["wav"]
    })

if __name__ == '__main__':
    logger.info("启动ESPnet TTS服务器...")
    
    # 尝试加载模型
    if load_model():
        logger.info("模型加载成功，启动服务器")
    else:
        logger.warning("模型加载失败，但仍启动服务器（仅提供健康检查）")
    
    # 启动Flask服务器
    app.run(host='0.0.0.0', port=9001, debug=False) 