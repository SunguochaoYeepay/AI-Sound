import requests
import os

# 测试音频文件
audio_file_path = '/app/data/voice_profiles/温柔女声_5a0159820339423581502556bccc8b94.wav'
latent_file_path = '/app/data/voice_profiles/温柔女声_0f6aa03fedf54a5caca91515b606e2ad.npy'

if os.path.exists(audio_file_path) and os.path.exists(latent_file_path):
    print(f"音频文件存在: {audio_file_path}")
    print(f"Latent文件存在: {latent_file_path}")
    file_size = os.path.getsize(audio_file_path)
    latent_size = os.path.getsize(latent_file_path)
    print(f"音频文件大小: {file_size} bytes")
    print(f"Latent文件大小: {latent_size} bytes")
    
    # 测试API调用
    try:
        with open(audio_file_path, 'rb') as audio_f, open(latent_file_path, 'rb') as latent_f:
            files = {
                'audio_file': audio_f,
                'latent_file': latent_f
            }
            data = {'text': '测试'}
            response = requests.post('http://host.docker.internal:7929/api/v1/tts/synthesize_file', 
                                   files=files, data=data, timeout=30)
            print(f'状态码: {response.status_code}')
            print(f'响应: {response.text[:500]}')
    except Exception as e:
        print(f'错误: {e}')
else:
    print(f"文件缺失:")
    print(f"  音频: {audio_file_path} - {'存在' if os.path.exists(audio_file_path) else '不存在'}")
    print(f"  Latent: {latent_file_path} - {'存在' if os.path.exists(latent_file_path) else '不存在'}") 