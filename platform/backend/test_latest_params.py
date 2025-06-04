#!/usr/bin/env python3
"""测试修复后的TTS参数"""

import asyncio
import sys
import os
import logging

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

from app.tts_client import MegaTTS3Client, TTSRequest

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_fixed_params():
    """测试修复后的参数配置"""
    
    # 检查声音文件
    voice_files = []
    data_dir = "./data/uploads"
    if os.path.exists(data_dir):
        for file in os.listdir(data_dir):
            if file.endswith('.wav'):
                voice_files.append(os.path.join(data_dir, file))
    
    if not voice_files:
        print("❌ 没有找到.wav声音文件")
        return
    
    # 使用第一个声音文件
    reference_audio = voice_files[0]
    print(f"✅ 使用参考音频: {reference_audio}")
    
    # 创建TTS客户端
    client = MegaTTS3Client()
    
    # 健康检查
    print("\n=== 健康检查 ===")
    health = await client.health_check()
    print(f"健康状态: {health}")
    
    if health.get('status') != 'healthy':
        print("❌ MegaTTS3服务不健康")
        return
    
    # 测试请求 - 使用修复后的参数
    test_text = "你好，我是智能语音助手，这是一个测试。"
    output_path = "./data/test_fixed_params.wav"
    
    print(f"\n=== TTS合成测试 ===")
    print(f"文本: {test_text}")
    print(f"参考音频: {os.path.basename(reference_audio)}")
    print(f"使用新参数: time_step=32, p_w=1.4, t_w=3.0")
    
    request = TTSRequest(
        text=test_text,
        reference_audio_path=reference_audio,
        output_audio_path=output_path,
        time_step=32,      # 修复：使用MegaTTS3默认值
        p_weight=1.4,      # 修复：使用MegaTTS3默认值  
        t_weight=3.0       # 修复：使用MegaTTS3默认值
    )
    
    response = await client.synthesize_speech(request)
    
    print(f"\n=== 结果 ===")
    print(f"成功: {response.success}")
    print(f"消息: {response.message}")
    
    if response.success:
        print(f"✅ 音频已生成: {response.audio_path}")
        print(f"处理时间: {response.processing_time:.2f}秒")
        
        # 检查文件
        if os.path.exists(response.audio_path):
            file_size = os.path.getsize(response.audio_path)
            print(f"文件大小: {file_size} bytes")
        
    else:
        print(f"❌ 合成失败")
        print(f"错误代码: {response.error_code}")

if __name__ == "__main__":
    asyncio.run(test_fixed_params()) 