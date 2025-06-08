import requests
import os
import json

# 分析音频文件的基本属性
def analyze_audio_properties():
    audio_file = '/app/data/voice_profiles/温柔女声_5a0159820339423581502556bccc8b94.wav'
    
    try:
        import wave
        with wave.open(audio_file, 'rb') as wav_file:
            frames = wav_file.getnframes()
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            duration = frames / sample_rate
            
            print(f"音频属性分析:")
            print(f"  采样率: {sample_rate} Hz")
            print(f"  声道数: {channels}")
            print(f"  位深: {sample_width * 8} bit")
            print(f"  时长: {duration:.2f} 秒")
            print(f"  总帧数: {frames}")
            
            # 检查是否符合常见标准
            if sample_rate not in [16000, 22050, 44100, 48000]:
                print(f"⚠️  非标准采样率: {sample_rate}")
            
            if channels != 1:
                print(f"⚠️  非单声道: {channels}")
                
            if sample_width != 2:
                print(f"⚠️  非16位: {sample_width * 8}位")
                
            if duration < 0.5:
                print(f"⚠️  音频过短: {duration}秒")
            elif duration > 30:
                print(f"⚠️  音频过长: {duration}秒")
                
    except Exception as e:
        print(f"音频分析失败: {e}")

# 测试不同长度的文本
def test_text_lengths():
    texts = [
        "a",
        "你",
        "你好",
        "测试文本",
        "这是一个较长的测试文本",
        "林晓站在镜子前，看着自己因长期熬夜而略显苍白的脸，重重地叹了口气。"
    ]
    
    audio_file = '/app/data/voice_profiles/温柔女声_5a0159820339423581502556bccc8b94.wav'
    
    for i, text in enumerate(texts):
        print(f"\n测试文本 {i+1}: '{text}' (长度: {len(text)})")
        
        try:
            with open(audio_file, 'rb') as f:
                files = {'audio_file': f}
                data = {'text': text}
                response = requests.post(
                    'http://host.docker.internal:7929/api/v1/tts/synthesize_file', 
                    files=files, data=data, timeout=10
                )
                
                if response.status_code == 200:
                    print(f"  ✅ 成功")
                    return text  # 找到第一个成功的就返回
                else:
                    print(f"  ❌ 失败: {response.status_code}")
                    if "index out of bounds" in response.text:
                        print(f"    索引越界错误")
                    elif "CUDA error" in response.text:
                        print(f"    CUDA错误")
                        
        except Exception as e:
            print(f"  ❌ 异常: {e}")
    
    return None

if __name__ == "__main__":
    analyze_audio_properties()
    print("\n" + "="*50)
    successful_text = test_text_lengths()
    
    if successful_text:
        print(f"\n找到可工作的文本: '{successful_text}'")
    else:
        print("\n所有文本都失败了") 