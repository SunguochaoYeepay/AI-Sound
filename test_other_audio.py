import requests
import os

# 测试其他音频文件
audio_files = [
    '/app/data/voice_profiles/专业主播_2b5ec67bdf934261b4475b9f928cf8dd.wav',
    '/app/data/voice_profiles/活泼少女_ff16bfd4d23340ba89ffc7d1adb2484d.wav',
    '/app/data/voice_profiles/温柔女声_03b26e12ab7c47dab52bafa420812701.wav'
]

for audio_file_path in audio_files:
    if os.path.exists(audio_file_path):
        print(f"\n测试音频文件: {os.path.basename(audio_file_path)}")
        file_size = os.path.getsize(audio_file_path)
        print(f"文件大小: {file_size} bytes")
        
        try:
            with open(audio_file_path, 'rb') as f:
                files = {'audio_file': f}
                data = {'text': '你好'}
                response = requests.post('http://host.docker.internal:7929/api/v1/tts/synthesize_file', 
                                       files=files, data=data, timeout=30)
                print(f'状态码: {response.status_code}')
                if response.status_code == 200:
                    print('✅ 成功！')
                    break
                else:
                    print(f'❌ 失败: {response.text[:100]}')
        except Exception as e:
            print(f'❌ 错误: {e}')
    else:
        print(f"音频文件不存在: {audio_file_path}") 