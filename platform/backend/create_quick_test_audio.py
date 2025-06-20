#!/usr/bin/env python3
"""
快速创建环境音测试文件
手动合并最短的几个segment并添加环境音
"""

import os
from pydub import AudioSegment
import requests
import time

def create_quick_test_audio():
    """创建快速测试音频"""
    print("🎯 创建快速环境音测试音频...")
    
    # 最短的几个segment文件
    segments = [
        "outputs/projects/42/segment_0034_导师_15.wav",  # 1.28秒
        "outputs/projects/42/segment_0007_旁白_21.wav",   # 2.16秒  
        "outputs/projects/42/segment_0027_导师_15.wav",   # 1.92秒
    ]
    
    # 检查文件是否存在
    existing_segments = []
    total_duration = 0
    
    for segment_path in segments:
        if os.path.exists(segment_path):
            try:
                audio = AudioSegment.from_wav(segment_path)
                duration = len(audio) / 1000.0  # 转换为秒
                existing_segments.append((segment_path, audio, duration))
                total_duration += duration
                print(f"✅ 找到: {os.path.basename(segment_path)} ({duration:.1f}秒)")
            except Exception as e:
                print(f"❌ 加载失败: {segment_path} - {str(e)}")
        else:
            print(f"❌ 文件不存在: {segment_path}")
    
    if not existing_segments:
        print("❌ 没有找到可用的segment文件")
        return None
    
    print(f"📊 总时长: {total_duration:.1f}秒")
    
    # 合并音频
    print("\n🔧 合并音频...")
    combined_audio = AudioSegment.empty()
    
    for i, (path, audio, duration) in enumerate(existing_segments):
        combined_audio += audio
        if i < len(existing_segments) - 1:  # 不是最后一个，添加短暂停顿
            combined_audio += AudioSegment.silent(duration=300)  # 0.3秒停顿
        print(f"   添加: {os.path.basename(path)}")
    
    # 生成环境音
    print("\n🌧️ 生成环境音...")
    environment_audio = generate_environment_audio(len(combined_audio) / 1000.0)
    
    if environment_audio:
        # 混合音频
        print("🎵 混合音频...")
        
        # 调整环境音音量 (30%)
        environment_audio = environment_audio - 10  # 降低10dB大约是30%音量
        
        # 确保环境音长度匹配
        if len(environment_audio) > len(combined_audio):
            environment_audio = environment_audio[:len(combined_audio)]
        elif len(environment_audio) < len(combined_audio):
            # 如果环境音太短，循环播放
            loops_needed = (len(combined_audio) // len(environment_audio)) + 1
            environment_audio = environment_audio * loops_needed
            environment_audio = environment_audio[:len(combined_audio)]
        
        # 混合
        final_audio = combined_audio.overlay(environment_audio)
        
        # 保存文件
        output_path = "outputs/projects/42/quick_test_with_environment.wav"
        final_audio.export(output_path, format="wav")
        
        print(f"✅ 环境音混合版本已保存:")
        print(f"   路径: {os.path.abspath(output_path)}")
        print(f"   大小: {os.path.getsize(output_path) / 1024:.1f} KB")
        print(f"   时长: {len(final_audio) / 1000.0:.1f}秒")
        
        return output_path
    else:
        # 保存纯对话版本用于对比
        output_path = "outputs/projects/42/quick_test_dialogue_only.wav"
        combined_audio.export(output_path, format="wav")
        
        print(f"⚠️ 只保存了对话版本（无环境音）:")
        print(f"   路径: {os.path.abspath(output_path)}")
        print(f"   大小: {os.path.getsize(output_path) / 1024:.1f} KB")
        print(f"   时长: {len(combined_audio) / 1000.0:.1f}秒")
        
        return output_path

def generate_environment_audio(duration_seconds):
    """生成环境音"""
    try:
        # 调用TangoFlux生成雨夜环境音
        print(f"   调用TangoFlux生成 {duration_seconds:.1f} 秒雨夜环境音...")
        
        url = "http://localhost:7930/generate_audio"
        data = {
            "prompt": "gentle rain falling at night, peaceful ambient sound, soft raindrops on leaves",
            "duration": max(int(duration_seconds), 1),
            "steps": 50,
            "guidance": 3.0
        }
        
        response = requests.post(url, json=data, timeout=60)
        
        if response.status_code == 200:
            # 保存临时环境音文件
            temp_env_path = "outputs/projects/42/temp_environment.wav"
            with open(temp_env_path, 'wb') as f:
                f.write(response.content)
            
            # 加载环境音
            environment_audio = AudioSegment.from_wav(temp_env_path)
            
            # 删除临时文件
            try:
                os.remove(temp_env_path)
            except:
                pass
            
            print(f"   ✅ 环境音生成成功 ({len(environment_audio)/1000.0:.1f}秒)")
            return environment_audio
        else:
            print(f"   ❌ TangoFlux调用失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ 环境音生成异常: {str(e)}")
        return None

def check_tangoflux_service():
    """检查TangoFlux服务"""
    try:
        response = requests.get("http://localhost:7930/health", timeout=5)
        if response.status_code == 200:
            print("✅ TangoFlux服务正常")
            return True
        else:
            print(f"❌ TangoFlux服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ TangoFlux服务连接失败: {str(e)}")
        return False

def main():
    print("🚀 快速环境音测试音频生成")
    print("   使用现有segment文件快速创建测试")
    
    # 检查TangoFlux服务
    tangoflux_available = check_tangoflux_service()
    if not tangoflux_available:
        print("⚠️ TangoFlux不可用，将只生成对话音频")
    
    # 创建测试音频
    result_path = create_quick_test_audio()
    
    if result_path:
        print(f"\n🎉 快速测试音频创建完成！")
        print(f"🎵 播放文件:")
        print(f"   {result_path}")
        
        if tangoflux_available and "environment" in result_path:
            print(f"\n💡 这个文件应该包含:")
            print(f"   📢 角色对话（导师和旁白）")
            print(f"   🌧️ 雨夜环境音")
            print(f"   🔊 混合后的完整体验")
        else:
            print(f"\n💡 这个文件包含:")
            print(f"   📢 纯角色对话")
            print(f"   ⏱️ 总时长约5-6秒")
    else:
        print(f"❌ 测试音频创建失败")

if __name__ == "__main__":
    main() 