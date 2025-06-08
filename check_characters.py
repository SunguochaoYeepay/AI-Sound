import psycopg2
import os

# 检查角色配置
conn = psycopg2.connect('postgresql://ai_sound_user:ai_sound_password@database:5432/ai_sound')
cur = conn.cursor()

cur.execute('SELECT id, name, audio_file, latent_file FROM characters WHERE status = %s', ('active',))
results = cur.fetchall()

print('当前角色配置:')
for row in results:
    char_id, name, audio_file, latent_file = row
    print(f'  ID {char_id}: {name}')
    print(f'    WAV: {audio_file}')
    print(f'    NPY: {latent_file}')
    
    # 检查文件是否存在
    wav_path = f'/app/data/voice_profiles/{audio_file}' if audio_file else None
    npy_path = f'/app/data/voice_profiles/{latent_file}' if latent_file else None
    
    wav_exists = os.path.exists(wav_path) if wav_path else False
    npy_exists = os.path.exists(npy_path) if npy_path else False
    
    print(f'    WAV存在: {"✅" if wav_exists else "❌"}')
    print(f'    NPY存在: {"✅" if npy_exists else "❌"}')
    print(f'    配对正确: {"✅" if wav_exists and npy_exists else "❌"}')
    print()

conn.close()

# 查找可用的配对文件
print("查找可用的配对文件:")
voice_profiles_dir = '/app/data/voice_profiles'
wav_files = [f for f in os.listdir(voice_profiles_dir) if f.endswith('.wav')]
npy_files = [f for f in os.listdir(voice_profiles_dir) if f.endswith('.npy')]

# 找到包含相同声音名称的文件
voice_names = set()
for wav in wav_files:
    voice_name = wav.split('_')[0]
    voice_names.add(voice_name)

for voice_name in sorted(voice_names):
    wav_candidates = [f for f in wav_files if f.startswith(voice_name + '_')]
    npy_candidates = [f for f in npy_files if f.startswith(voice_name + '_')]
    
    print(f"\n{voice_name}:")
    print(f"  WAV文件: {wav_candidates}")
    print(f"  NPY文件: {npy_candidates}")
    
    # 尝试找到可能的配对
    if len(wav_candidates) > 0 and len(npy_candidates) > 0:
        print(f"  💡 建议配对:")
        print(f"    WAV: {wav_candidates[0]}")  
        print(f"    NPY: {npy_candidates[0]}") 