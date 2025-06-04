#!/usr/bin/env python3
"""
测试修复后的TTS配置
"""
import requests
import sys
import os
sys.path.append('app')

def test_tts_fix():
    print("🔧 === 测试TTS配置修复 ===")
    
    # 1. 测试健康检查
    print("\n1. 测试MegaTTS3健康状态...")
    try:
        response = requests.get("http://localhost:9880/health", timeout=5)
        if response.status_code == 200:
            print("✅ MegaTTS3服务正常")
            print(f"   响应: {response.json()}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接MegaTTS3: {e}")
        return False
    
    # 2. 测试简单合成
    print("\n2. 测试简单TTS合成...")
    
    # 检查是否有可用的声音文件
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'uploads')
    if os.path.exists(data_dir):
        wav_files = [f for f in os.listdir(data_dir) if f.endswith('.wav')]
        if wav_files:
            test_audio = os.path.join(data_dir, wav_files[0])
            print(f"   使用测试音频: {test_audio}")
            
            # 构建测试请求
            test_data = {
                'text': '你好，这是TTS测试。',
                'time_step': '20',
                'p_w': '1.0',
                't_w': '1.0'
            }
            
            try:
                with open(test_audio, 'rb') as f:
                    files = {
                        'audio_file': (os.path.basename(test_audio), f, 'audio/wav')
                    }
                    
                    response = requests.post(
                        "http://localhost:9880/synthesize",
                        data=test_data,
                        files=files,
                        timeout=30
                    )
                
                if response.status_code == 200:
                    print("✅ TTS合成测试成功！")
                    
                    # 保存测试音频
                    output_path = os.path.join(data_dir, 'tts_test_output.wav')
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    print(f"   测试音频已保存: {output_path}")
                    return True
                else:
                    print(f"❌ TTS合成失败: {response.status_code}")
                    try:
                        error_data = response.json()
                        print(f"   错误信息: {error_data}")
                    except:
                        print(f"   原始响应: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ TTS合成异常: {e}")
                return False
        else:
            print("⚠️  没有找到测试音频文件")
            return False
    else:
        print("⚠️  数据目录不存在")
        return False

if __name__ == "__main__":
    success = test_tts_fix()
    if success:
        print("\n🎉 TTS配置修复成功！可以重新尝试音频生成。")
    else:
        print("\n❌ TTS配置仍有问题，需要进一步调试。")