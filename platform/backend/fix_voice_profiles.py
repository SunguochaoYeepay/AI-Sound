#!/usr/bin/env python3
"""
修复声音档案的文件路径问题
将现有的wav和npy文件与数据库记录关联
"""
import sys
import os
import glob
sys.path.append('app')

from database import get_db
from models import VoiceProfile

def fix_voice_profiles():
    print("🔧 === 修复声音档案文件路径 ===")
    
    db = next(get_db())
    voices = db.query(VoiceProfile).all()
    
    if not voices:
        print("❌ 没有找到任何声音档案")
        return
    
    # 查找所有可用的音频文件
    wav_files = glob.glob("../data/uploads/ref_*.wav")
    npy_files = glob.glob("../data/uploads/latent_*.npy")
    
    print(f"📋 找到 {len(wav_files)} 个WAV文件")
    print(f"📋 找到 {len(npy_files)} 个NPY文件")
    
    if not wav_files or not npy_files:
        print("❌ 没有找到足够的文件")
        return
    
    # 为每个声音档案分配文件
    updated_count = 0
    
    for i, voice in enumerate(voices):
        if voice.reference_audio_path and voice.latent_file_path:
            print(f"✅ 声音档案 {voice.name} 已有文件路径，跳过")
            continue
        
        # 分配WAV文件
        if i < len(wav_files):
            voice.reference_audio_path = wav_files[i]
            print(f"🎵 为 {voice.name} 分配WAV: {os.path.basename(wav_files[i])}")
        
        # 分配NPY文件
        if i < len(npy_files):
            voice.latent_file_path = npy_files[i]
            print(f"🧠 为 {voice.name} 分配NPY: {os.path.basename(npy_files[i])}")
        
        updated_count += 1
    
    # 提交更改
    db.commit()
    print(f"\n✅ 成功更新了 {updated_count} 个声音档案")
    
    # 验证结果
    print("\n🔍 验证结果:")
    for voice in voices:
        db.refresh(voice)  # 刷新数据
        print(f"\n声音档案: {voice.name}")
        print(f"  WAV: {voice.reference_audio_path}")
        print(f"  NPY: {voice.latent_file_path}")
        
        # 检查文件是否存在
        if voice.reference_audio_path:
            wav_exists = os.path.exists(voice.reference_audio_path)
            print(f"  WAV存在: {'✅' if wav_exists else '❌'}")
        
        if voice.latent_file_path:
            npy_exists = os.path.exists(voice.latent_file_path)
            print(f"  NPY存在: {'✅' if npy_exists else '❌'}")

if __name__ == "__main__":
    fix_voice_profiles() 