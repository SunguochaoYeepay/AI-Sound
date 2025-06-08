import requests
import os

# 测试所有配对正确的文件
def test_paired_audio():
    audio_files = [
        '/app/data/voice_profiles/温柔女声_03b26e12ab7c47dab52bafa420812701.wav',
        '/app/data/voice_profiles/专业主播_2b5ec67bdf934261b4475b9f928cf8dd.wav',
        '/app/data/voice_profiles/活泼少女_ff16bfd4d23340ba89ffc7d1adb2484d.wav'
    ]
    
    for audio_file in audio_files:
        # 提取hash用于查找对应的npy文件
        base_name = os.path.basename(audio_file)
        voice_name = base_name.split('_')[0]
        hash_part = base_name.split('_')[1].replace('.wav', '')
        npy_file = f'/app/data/voice_profiles/{voice_name}_{hash_part}.npy'
        
        print(f"\n测试音频: {base_name}")
        print(f"查找npy: {os.path.basename(npy_file)}")
        
        if os.path.exists(npy_file):
            print(f"  ✅ 找到配对的npy文件")
            
            # 测试API
            try:
                with open(audio_file, 'rb') as f:
                    files = {'audio_file': f}
                    data = {'text': '你好世界'}
                    response = requests.post(
                        'http://host.docker.internal:7929/api/v1/tts/synthesize_file', 
                        files=files, data=data, timeout=20
                    )
                    
                    print(f"  状态码: {response.status_code}")
                    if response.status_code == 200:
                        print(f"  🎉 成功！使用配对文件可以工作！")
                        return True
                    else:
                        print(f"  ❌ 仍然失败: {response.text[:100]}")
                        
            except Exception as e:
                print(f"  ❌ 请求异常: {e}")
        else:
            print(f"  ❌ 没有找到配对的npy文件")
    
    return False

# 检查文件配对情况  
def check_file_pairing():
    voice_profiles_dir = '/app/data/voice_profiles'
    wav_files = [f for f in os.listdir(voice_profiles_dir) if f.endswith('.wav')]
    npy_files = [f for f in os.listdir(voice_profiles_dir) if f.endswith('.npy')]
    
    print("文件配对情况检查:")
    print(f"总计 .wav 文件: {len(wav_files)}")
    print(f"总计 .npy 文件: {len(npy_files)}")
    
    paired = 0
    unpaired_wav = []
    unpaired_npy = []
    
    for wav_file in wav_files:
        hash_part = wav_file.replace('.wav', '')
        corresponding_npy = hash_part + '.npy'
        
        if corresponding_npy in npy_files:
            paired += 1
            print(f"  ✅ {wav_file} <-> {corresponding_npy}")
        else:
            unpaired_wav.append(wav_file)
            print(f"  ❌ {wav_file} (无对应npy)")
    
    for npy_file in npy_files:
        hash_part = npy_file.replace('.npy', '')
        corresponding_wav = hash_part + '.wav'
        
        if corresponding_wav not in wav_files:
            unpaired_npy.append(npy_file)
            print(f"  ❌ {npy_file} (无对应wav)")
    
    print(f"\n配对成功: {paired}")
    print(f"未配对wav: {len(unpaired_wav)}")
    print(f"未配对npy: {len(unpaired_npy)}")

if __name__ == "__main__":
    check_file_pairing()
    print("\n" + "="*50)
    test_paired_audio() 