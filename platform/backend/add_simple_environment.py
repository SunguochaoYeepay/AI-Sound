#!/usr/bin/env python3
"""
为测试音频添加简单环境音
使用预置雨声效果
"""

import os
from pydub import AudioSegment
from pydub.generators import Sine, WhiteNoise
import random
import numpy as np

def create_simple_rain_sound(duration_ms):
    """创建简单的雨声效果"""
    print(f"   🌧️ 创建 {duration_ms/1000:.1f} 秒雨声效果...")
    
    # 基础白噪音
    base_noise = WhiteNoise().to_audio_segment(duration=duration_ms)
    
    # 降低音量作为基础雨声
    rain_base = base_noise - 25  # 降低25dB
    
    # 添加随机的雨滴声
    rain_with_drops = rain_base
    
    # 每500ms添加一些随机雨滴
    drop_interval = 500
    for i in range(0, duration_ms, drop_interval):
        if random.random() < 0.7:  # 70%概率有雨滴
            # 创建雨滴声 (短暂的高频音)
            drop_freq = random.randint(800, 1500)
            drop_duration = random.randint(50, 150)
            drop_sound = Sine(drop_freq).to_audio_segment(duration=drop_duration)
            drop_sound = drop_sound - 30  # 降低音量
            
            # 添加到随机位置
            drop_position = i + random.randint(0, min(drop_interval, duration_ms - i - drop_duration))
            if drop_position + drop_duration < duration_ms:
                rain_with_drops = rain_with_drops.overlay(drop_sound, position=drop_position)
    
    # 应用低通滤波器效果 (模拟雨声的自然感)
    # 简单的音量调制来模拟雨声变化
    result = AudioSegment.empty()
    chunk_size = 100  # 100ms chunks
    
    for i in range(0, len(rain_with_drops), chunk_size):
        chunk = rain_with_drops[i:i+chunk_size]
        # 随机音量变化 (-5dB 到 +2dB)
        volume_change = random.uniform(-5, 2)
        chunk = chunk + volume_change
        result += chunk
    
    print(f"   ✅ 雨声效果生成完成")
    return result

def add_environment_to_dialogue():
    """为对话添加环境音"""
    print("🎵 为快速测试音频添加环境音...")
    
    dialogue_path = "outputs/projects/42/quick_test_dialogue_only.wav"
    
    if not os.path.exists(dialogue_path):
        print(f"❌ 对话文件不存在: {dialogue_path}")
        return None
    
    # 加载对话音频
    dialogue_audio = AudioSegment.from_wav(dialogue_path)
    print(f"✅ 加载对话音频: {len(dialogue_audio)/1000:.1f}秒")
    
    # 创建雨声环境音
    rain_audio = create_simple_rain_sound(len(dialogue_audio))
    
    # 调整环境音音量 (40%音量，便于测试)
    rain_audio = rain_audio - 8  # 降低8dB大约是40%音量
    
    # 混合音频
    print("🔧 混合音频...")
    final_audio = dialogue_audio.overlay(rain_audio)
    
    # 保存混合后的音频
    output_path = "outputs/projects/42/quick_test_with_rain.wav"
    final_audio.export(output_path, format="wav")
    
    # 显示结果
    dialogue_size = os.path.getsize(dialogue_path) / 1024
    mixed_size = os.path.getsize(output_path) / 1024
    
    print(f"✅ 环境音混合完成:")
    print(f"   对话版本: {dialogue_size:.1f} KB")
    print(f"   混合版本: {mixed_size:.1f} KB")
    print(f"   增加大小: {mixed_size - dialogue_size:.1f} KB")
    print(f"   完整路径: {os.path.abspath(output_path)}")
    
    return output_path

def main():
    print("🌧️ 快速环境音测试 - 添加雨声效果")
    
    result_path = add_environment_to_dialogue()
    
    if result_path:
        print(f"\n🎉 环境音测试文件创建成功！")
        print(f"\n🎵 现在您有两个文件可以对比:")
        print(f"   1️⃣ 纯对话: outputs/projects/42/quick_test_dialogue_only.wav")
        print(f"   2️⃣ 含环境音: {result_path}")
        print(f"\n💡 请先播放对话版本，再播放环境音版本")
        print(f"   您应该能明显听出差异:")
        print(f"   📢 相同的角色对话")
        print(f"   🌧️ 新增的雨声背景")
        print(f"   🔊 整体更丰富的听觉体验")
        
        print(f"\n📍 完整路径:")
        print(f"   对话版: {os.path.abspath('outputs/projects/42/quick_test_dialogue_only.wav')}")
        print(f"   环境版: {os.path.abspath(result_path)}")
    else:
        print("❌ 环境音添加失败")

if __name__ == "__main__":
    main() 