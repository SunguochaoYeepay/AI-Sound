#!/usr/bin/env python3
"""
创建丰富复杂的环境音效
多层次音效，确保用户能明显听到差异
"""

import os
from pydub import AudioSegment
from pydub.generators import Sine, Triangle, Sawtooth, WhiteNoise
import random
import math

def create_complex_rain_sound(duration_ms):
    """创建复杂的雨声效果"""
    print(f"   🌧️ 创建复杂雨声效果 ({duration_ms/1000:.1f}秒)...")
    
    # 1. 基础雨声 - 白噪音
    base_rain = WhiteNoise().to_audio_segment(duration=duration_ms) - 20
    
    # 2. 大雨滴声 - 低频撞击
    heavy_drops = AudioSegment.empty()
    for i in range(0, duration_ms, 800):  # 每800ms一次
        if random.random() < 0.8:
            drop = Sine(150 + random.randint(-30, 30)).to_audio_segment(duration=200)
            drop = drop.fade_in(50).fade_out(100) - 15
            heavy_drops = heavy_drops.overlay(drop, position=i)
    
    # 3. 小雨滴声 - 高频
    light_drops = AudioSegment.empty()
    for i in range(0, duration_ms, 300):  # 更频繁
        if random.random() < 0.9:
            freq = random.randint(800, 1200)
            drop = Sine(freq).to_audio_segment(duration=100)
            drop = drop.fade_in(20).fade_out(50) - 25
            light_drops = light_drops.overlay(drop, position=i)
    
    # 4. 雷声效果
    thunder = create_thunder_sound(duration_ms)
    
    # 混合所有雨声元素
    complex_rain = base_rain.overlay(heavy_drops).overlay(light_drops).overlay(thunder)
    
    print(f"   ✅ 复杂雨声效果完成")
    return complex_rain

def create_thunder_sound(duration_ms):
    """创建雷声效果"""
    thunder_track = AudioSegment.silent(duration=duration_ms)
    
    # 在音频中间添加一声雷
    thunder_position = duration_ms // 2
    
    # 低频轰鸣 (雷声主体)
    rumble_duration = 1500
    rumble = AudioSegment.empty()
    
    for freq in [60, 80, 100, 120]:
        wave = Sine(freq).to_audio_segment(duration=rumble_duration)
        # 添加音量包络
        wave = wave.fade_in(300).fade_out(700)
        rumble = rumble.overlay(wave)
    
    # 高频爆裂声 (雷击声)
    crack_duration = 200
    crack = WhiteNoise().to_audio_segment(duration=crack_duration) - 10
    crack = crack.fade_in(10).fade_out(100)
    
    # 组合雷声
    thunder_sound = rumble.overlay(crack, position=100) - 12  # 降低音量
    
    # 添加到轨道
    if thunder_position + len(thunder_sound) < duration_ms:
        thunder_track = thunder_track.overlay(thunder_sound, position=thunder_position)
    
    return thunder_track

def create_wind_sound(duration_ms):
    """创建风声效果"""
    print(f"   💨 创建风声效果...")
    
    # 基础风声 - 低频白噪音
    wind_base = WhiteNoise().to_audio_segment(duration=duration_ms)
    wind_base = wind_base.low_pass_filter(400) - 25  # 低通滤波，降低音量
    
    # 风的强弱变化
    wind_with_gusts = AudioSegment.empty()
    chunk_size = 500  # 500ms chunks
    
    for i in range(0, duration_ms, chunk_size):
        chunk = wind_base[i:i+chunk_size]
        # 随机风力强度 (-10dB 到 +5dB)
        wind_strength = random.uniform(-10, 5)
        chunk = chunk + wind_strength
        
        # 添加风的呼啸声
        if random.random() < 0.3:  # 30%概率有呼啸
            whistle_freq = random.randint(200, 600)
            whistle = Sine(whistle_freq).to_audio_segment(duration=300)
            whistle = whistle.fade_in(100).fade_out(100) - 30
            chunk = chunk.overlay(whistle)
        
        wind_with_gusts += chunk
    
    print(f"   ✅ 风声效果完成")
    return wind_with_gusts

def create_forest_ambience(duration_ms):
    """创建森林环境音"""
    print(f"   🌲 创建森林环境音...")
    
    # 鸟叫声
    birds = AudioSegment.empty()
    bird_times = random.sample(range(0, duration_ms - 500, 200), 8)  # 8次鸟叫
    
    for bird_time in bird_times:
        bird_freq = random.choice([800, 1200, 1600, 2000])
        bird_duration = random.randint(150, 400)
        
        # 创建鸟叫声 (频率调制)
        bird_call = AudioSegment.empty()
        for ms in range(0, bird_duration, 20):
            freq_mod = bird_freq + 100 * math.sin(ms / 50)  # 频率调制
            note = Sine(freq_mod).to_audio_segment(duration=20)
            bird_call += note
        
        bird_call = bird_call.fade_in(50).fade_out(50) - 20
        birds = birds.overlay(bird_call, position=bird_time)
    
    # 树叶沙沙声
    leaves = WhiteNoise().to_audio_segment(duration=duration_ms)
    leaves = leaves.high_pass_filter(1000) - 30  # 高通滤波，很轻的声音
    
    forest = birds.overlay(leaves)
    print(f"   ✅ 森林环境音完成")
    return forest

def create_rich_environment_audio():
    """创建丰富的环境音"""
    print("🎵 创建丰富复杂的环境音效...")
    
    dialogue_path = "outputs/projects/42/quick_test_dialogue_only.wav"
    
    if not os.path.exists(dialogue_path):
        print(f"❌ 对话文件不存在: {dialogue_path}")
        return None
    
    # 加载对话音频
    dialogue_audio = AudioSegment.from_wav(dialogue_path)
    duration_ms = len(dialogue_audio)
    print(f"✅ 加载对话音频: {duration_ms/1000:.1f}秒")
    
    # 创建多种环境音效
    rain_sound = create_complex_rain_sound(duration_ms)
    wind_sound = create_wind_sound(duration_ms)
    forest_sound = create_forest_ambience(duration_ms)
    
    # 分层混合环境音
    print("🔧 分层混合环境音...")
    
    # 主要环境音：雨声 (较明显)
    environment_base = rain_sound - 5  # 稍微降低但保持明显
    
    # 次要环境音：风声 (中等音量)
    environment_base = environment_base.overlay(wind_sound - 3)
    
    # 背景环境音：森林 (较轻)
    environment_base = environment_base.overlay(forest_sound - 2)
    
    # 添加整体音量包络变化
    environment_final = AudioSegment.empty()
    chunk_size = 1000  # 1秒chunks
    
    for i in range(0, duration_ms, chunk_size):
        chunk = environment_base[i:i+chunk_size]
        # 音量在-3dB到+3dB之间变化
        volume_change = 3 * math.sin(i / 1000)  # 平滑的音量变化
        chunk = chunk + volume_change
        environment_final += chunk
    
    # 与对话混合
    print("🎭 与对话音频混合...")
    
    # 确保对话清晰可听，环境音明显但不盖过对话
    dialogue_boosted = dialogue_audio + 2  # 稍微提升对话音量
    final_audio = dialogue_boosted.overlay(environment_final)
    
    # 保存不同版本
    outputs = []
    
    # 1. 纯环境音版本 (用于测试)
    env_only_path = "outputs/projects/42/rich_environment_only.wav"
    environment_final.export(env_only_path, format="wav")
    outputs.append(("纯环境音", env_only_path))
    
    # 2. 混合版本
    mixed_path = "outputs/projects/42/rich_test_with_complex_environment.wav"
    final_audio.export(mixed_path, format="wav")
    outputs.append(("丰富混合", mixed_path))
    
    # 3. 超明显版本 (环境音更大声)
    obvious_environment = environment_final + 5  # 增加5dB
    obvious_mixed = dialogue_audio.overlay(obvious_environment)
    obvious_path = "outputs/projects/42/obvious_environment_test.wav"
    obvious_mixed.export(obvious_path, format="wav")
    outputs.append(("超明显版", obvious_path))
    
    # 显示结果
    dialogue_size = os.path.getsize(dialogue_path) / 1024
    
    print(f"\n✅ 丰富环境音创建完成:")
    print(f"   原对话: {dialogue_size:.1f} KB")
    
    for name, path in outputs:
        size = os.path.getsize(path) / 1024
        print(f"   {name}: {size:.1f} KB (+{size-dialogue_size:.1f} KB)")
        print(f"     路径: {os.path.abspath(path)}")
    
    return outputs

def main():
    print("🎯 创建丰富复杂的环境音测试")
    print("   包含：雨声、雷声、风声、鸟叫、树叶沙沙声")
    print("   多个版本：从清晰到超明显")
    
    outputs = create_rich_environment_audio()
    
    if outputs:
        print(f"\n🎉 丰富环境音测试文件创建成功！")
        print(f"\n🎵 现在您有多个版本可以测试:")
        print(f"   0️⃣ 基准: outputs/projects/42/quick_test_dialogue_only.wav")
        
        for i, (name, path) in enumerate(outputs, 1):
            print(f"   {i}️⃣ {name}: {os.path.basename(path)}")
        
        print(f"\n💡 建议测试顺序:")
        print(f"   1. 先听基准对话版本")
        print(f"   2. 听纯环境音版本（了解背景音）")
        print(f"   3. 听丰富混合版本（完整体验）")
        print(f"   4. 听超明显版本（如果还不够清楚）")
        
        print(f"\n🔊 您应该能听到:")
        print(f"   🌧️ 复杂分层雨声（大雨滴+小雨滴+基础雨声）")
        print(f"   ⚡ 中间的雷声（低频轰鸣+高频爆裂）")
        print(f"   💨 变化的风声（强弱不一+偶尔呼啸）")
        print(f"   🐦 随机鸟叫声（多种频率的调制音）")
        print(f"   🌿 轻微的树叶沙沙声")
        print(f"   🎵 整体音量的动态变化")
        
    else:
        print("❌ 丰富环境音创建失败")

if __name__ == "__main__":
    main() 