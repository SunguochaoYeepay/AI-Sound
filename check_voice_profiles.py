import psycopg2
import os

# 检查voice_profiles表
conn = psycopg2.connect('postgresql://ai_sound_user:ai_sound_password@database:5432/ai_sound')
cur = conn.cursor()

# 查看所有表
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
tables = cur.fetchall()
print('数据库表:')
for table in tables:
    print(f'  {table[0]}')

print()

# 检查voice_profiles表
cur.execute('SELECT id, name, audio_file, latent_file FROM voice_profiles WHERE status = %s', ('active',))
results = cur.fetchall()

print('当前声音配置:')
for row in results:
    profile_id, name, audio_file, latent_file = row
    print(f'  ID {profile_id}: {name}')
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

# 按声音名称分组
voice_groups = {}
for wav in wav_files:
    voice_name = wav.split('_')[0]
    if voice_name not in voice_groups:
        voice_groups[voice_name] = {'wav': [], 'npy': []}
    voice_groups[voice_name]['wav'].append(wav)

for npy in npy_files:
    voice_name = npy.split('_')[0]
    if voice_name not in voice_groups:
        voice_groups[voice_name] = {'wav': [], 'npy': []}
    voice_groups[voice_name]['npy'].append(npy)

for voice_name, files in voice_groups.items():
    print(f"\n{voice_name}:")
    print(f"  WAV: {files['wav']}")
    print(f"  NPY: {files['npy']}")
    
    if files['wav'] and files['npy']:
        print(f"  💡 建议使用:")
        print(f"    WAV: {files['wav'][0]}")
        print(f"    NPY: {files['npy'][0]}") 