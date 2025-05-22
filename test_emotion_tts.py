#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import sys
import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("emotion_tts_test")

# 添加api路径到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "services", "api", "src"))

# 导入TTS引擎
from tts.engine import MegaTTSEngine

def save_audio_with_plot(audio, filename, sample_rate=22050, title=None):
    """保存音频并生成波形图"""
    # 确保输出目录存在
    output_dir = os.path.dirname(filename)
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存音频
    wavfile.write(filename, sample_rate, audio.astype(np.float32))
    
    # 生成波形图
    plt.figure(figsize=(10, 4))
    plt.plot(audio)
    plt.title(title or os.path.basename(filename))
    plt.xlabel('Sample')
    plt.ylabel('Amplitude')
    plt.tight_layout()
    
    # 保存波形图
    plot_filename = f"{os.path.splitext(filename)[0]}.png"
    plt.savefig(plot_filename)
    plt.close()
    
    return filename, plot_filename

def test_emotions():
    """测试不同情感类型的语音合成"""
    logger.info("=== 测试不同情感类型的语音合成 ===")
    
    # 创建输出目录
    output_dir = "emotion_test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建TTS引擎
    engine = MegaTTSEngine()
    
    # 测试文本
    test_text = "这是一段测试文本，用于测试不同情感类型的语音合成效果。"
    
    # 测试的声音IDs
    voices = ["范闲", "周杰伦", "female_young", "male_young"]
    
    # 测试的情感类型
    emotions = [
        {"type": "neutral", "intensity": 0.5, "desc": "中性"},
        {"type": "happy", "intensity": 0.8, "desc": "开心"},
        {"type": "sad", "intensity": 0.7, "desc": "悲伤"},
        {"type": "angry", "intensity": 0.9, "desc": "愤怒"},
        {"type": "surprise", "intensity": 0.8, "desc": "惊讶"}
    ]
    
    # 测试结果
    results = []
    
    # 对每个声音和情感组合进行测试
    for voice_id in voices:
        logger.info(f"测试声音: {voice_id}")
        
        for emotion in emotions:
            emotion_type = emotion["type"]
            emotion_intensity = emotion["intensity"]
            emotion_desc = emotion["desc"]
            
            logger.info(f"  情感: {emotion_desc} (类型={emotion_type}, 强度={emotion_intensity})")
            
            # 生成音频
            audio = engine.synthesize(
                text=test_text,
                voice_id=voice_id,
                emotion_type=emotion_type,
                emotion_intensity=emotion_intensity
            )
            
            # 文件名
            filename = os.path.join(
                output_dir, 
                f"{voice_id}_{emotion_type}_{int(emotion_intensity*100)}.wav"
            )
            
            # 保存音频并生成波形图
            audio_file, plot_file = save_audio_with_plot(
                audio, 
                filename, 
                title=f"{voice_id} - {emotion_desc} (强度: {emotion_intensity})"
            )
            
            # 记录结果
            file_size_kb = os.path.getsize(audio_file) / 1024
            logger.info(f"  已保存到: {audio_file} (大小: {file_size_kb:.2f} KB)")
            
            results.append({
                "voice_id": voice_id,
                "emotion_type": emotion_type,
                "emotion_desc": emotion_desc,
                "emotion_intensity": emotion_intensity,
                "file_size": file_size_kb,
                "audio_file": audio_file,
                "plot_file": plot_file
            })
    
    # 打印测试汇总
    logger.info("\n=== 测试结果汇总 ===")
    logger.info(f"总测试组合: {len(results)}")
    logger.info(f"生成的音频文件: {len(results)}")
    logger.info(f"输出目录: {output_dir}")
    
    return results

if __name__ == "__main__":
    logger.info("开始情感语音合成测试")
    results = test_emotions()
    logger.info("测试完成") 