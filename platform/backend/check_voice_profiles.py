#!/usr/bin/env python3
"""
检查声音档案中的latent_file_path
"""
import sys
sys.path.append('app')

from database import get_db
from models import VoiceProfile

def check_voice_profiles():
    print("🔍 === 检查声音档案信息 ===")
    
    db = next(get_db())
    voices = db.query(VoiceProfile).all()
    
    if not voices:
        print("❌ 没有找到任何声音档案")
        return
    
    print(f"📋 共找到 {len(voices)} 个声音档案:")
    
    for voice in voices:
        print(f"\n声音档案 ID: {voice.id}")
        print(f"  名称: {voice.name}")
        print(f"  WAV文件: {voice.reference_audio_path}")
        print(f"  PNY文件: {voice.latent_file_path}")
        
        # 检查文件是否存在
        if voice.reference_audio_path:
            import os
            wav_exists = os.path.exists(voice.reference_audio_path)
            print(f"  WAV存在: {wav_exists}")
        
        if voice.latent_file_path:
            pny_exists = os.path.exists(voice.latent_file_path)
            print(f"  PNY存在: {pny_exists}")
        else:
            print(f"  PNY存在: ❌ 未设置")

if __name__ == "__main__":
    check_voice_profiles() 