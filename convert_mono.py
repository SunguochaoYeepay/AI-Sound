import wave
import numpy as np

def convert_to_mono(input_file, output_file):
    """将双声道音频转换为单声道"""
    try:
        # 读取原始音频
        with wave.open(input_file, 'rb') as wav_in:
            frames = wav_in.readframes(-1)
            sample_rate = wav_in.getframerate()
            channels = wav_in.getnchannels()
            sample_width = wav_in.getsampwidth()
            
            print(f"原始音频: {channels}声道, {sample_rate}Hz, {sample_width*8}bit")
            
            if channels == 2:
                # 将bytes转换为numpy数组
                audio_data = np.frombuffer(frames, dtype=np.int16)
                # 重塑为立体声格式 (样本数, 2)
                stereo_data = audio_data.reshape(-1, 2)
                # 转换为单声道 (取平均值)
                mono_data = np.mean(stereo_data, axis=1, dtype=np.int16)
                
                # 写入单声道音频
                with wave.open(output_file, 'wb') as wav_out:
                    wav_out.setnchannels(1)  # 单声道
                    wav_out.setsampwidth(sample_width)
                    wav_out.setframerate(sample_rate)
                    wav_out.writeframes(mono_data.tobytes())
                
                print(f"转换完成: {output_file}")
                return True
            else:
                print(f"已经是单声道，无需转换")
                return False
                
    except Exception as e:
        print(f"转换失败: {e}")
        return False

# 转换温柔女声音频
input_file = '/app/data/voice_profiles/温柔女声_5a0159820339423581502556bccc8b94.wav'
output_file = '/app/data/voice_profiles/温柔女声_5a0159820339423581502556bccc8b94_mono.wav'

convert_to_mono(input_file, output_file)

# 测试转换后的文件
import requests

print("\n测试转换后的单声道音频:")
try:
    with open(output_file, 'rb') as f:
        files = {'audio_file': f}
        data = {'text': '你好'}
        response = requests.post(
            'http://host.docker.internal:7929/api/v1/tts/synthesize_file', 
            files=files, data=data, timeout=15
        )
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ 单声道音频测试成功！")
        else:
            print(f"❌ 仍然失败: {response.text[:200]}")
            
except Exception as e:
    print(f"测试失败: {e}") 