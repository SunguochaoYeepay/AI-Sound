#!/usr/bin/env python3
"""
直接测试TTS合成功能
"""
import asyncio
import sys
import os
sys.path.append('app')

from tts_client import MegaTTS3Client, TTSRequest

async def test_tts_direct():
    print("🎙️ === 直接测试TTS合成 ===")
    
    # 检查健康状态
    client = MegaTTS3Client()
    health = await client.health_check()
    print(f"1. 健康检查: {health}")
    
    if health['status'] != 'healthy':
        print("❌ TTS服务不健康，无法测试")
        return
    
    # 查找可用的参考音频
    print("\n2. 查找参考音频文件...")
    
    # 可能的音频文件路径
    possible_audio_paths = [
        "../data/uploads/ref_0f47c098738b4e5988d4c3d18c129807.wav",
        "../data/uploads/ref_14ec72125ea14cd78dcd1b8463fd1018.wav", 
        "../data/voice_profiles/voice_1.wav",
        "../data/voices/voice_1.wav", 
        "../data/test_voice.wav",
        "../data/voice_profiles/demo.wav"
    ]
    
    # 对应的latent文件路径
    possible_latent_paths = [
        "../data/uploads/latent_0904480606644380bec6b1747d9a5cdb.npy",
        "../data/uploads/latent_16382e3155e749c8af2c9a5cabcddc7b.npy",
        "../data/voice_profiles/voice_1.npy",
        "../data/voices/voice_1.npy",
        "../data/test_voice.npy",
        "../data/voice_profiles/demo.npy"
    ]
    
    reference_audio = None
    reference_latent = None
    
    for i, audio_path in enumerate(possible_audio_paths):
        if os.path.exists(audio_path):
            reference_audio = audio_path
            # 查找对应的latent文件
            if i < len(possible_latent_paths) and os.path.exists(possible_latent_paths[i]):
                reference_latent = possible_latent_paths[i]
                print(f"✅ 找到音频配对: WAV={reference_audio}")
                print(f"✅ 找到Latent配对: NPY={reference_latent}")
                break
            else:
                print(f"⚠️ 找到音频但无latent: {reference_audio}")
    
    if not reference_audio:
        print("❌ 找不到参考音频文件")
        return
        
    if not reference_latent:
        print("❌ 找不到对应的latent文件")
        print("💡 MegaTTS3在decoder-only模式下需要latent文件")
        return

    # 测试合成
    print("\n3. 测试TTS合成...")
    
    test_request = TTSRequest(
        text="你好，这是一个测试。",
        reference_audio_path=reference_audio,
        output_audio_path="../data/test_output.wav",
        time_step=20,
        p_weight=1.0,
        t_weight=1.0,
        latent_file_path=reference_latent
    )
    
    print(f"   文本: {test_request.text}")
    print(f"   参考音频: {test_request.reference_audio_path}")
    print(f"   Latent文件: {test_request.latent_file_path}")
    print(f"   输出路径: {test_request.output_audio_path}")
    
    try:
        response = await client.synthesize_speech(test_request)
        
        if response.success:
            print("✅ TTS合成成功")
            print(f"   输出文件: {response.audio_path}")
            print(f"   处理时间: {response.processing_time:.2f}秒")
            
            # 检查输出文件
            if os.path.exists(response.audio_path):
                file_size = os.path.getsize(response.audio_path)
                print(f"   文件大小: {file_size} 字节")
                print("🎉 TTS测试完全成功！")
            else:
                print("❌ 输出文件不存在")
        else:
            print("❌ TTS合成失败")
            print(f"   错误: {response.message}")
            print(f"   错误码: {response.error_code}")
            
    except Exception as e:
        print(f"❌ TTS测试异常: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_tts_direct()) 