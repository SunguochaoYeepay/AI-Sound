#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'platform', 'backend'))

from app.database import get_db
from app.models import VoiceProfile

def fix_voice_paths():
    print("=== 修复声音档案路径映射 ===")
    
    db = next(get_db())
    
    # 获取所有声音档案
    voices = db.query(VoiceProfile).all()
    
    print(f"📊 找到 {len(voices)} 个声音档案")
    
    fixed_count = 0
    
    for voice in voices:
        print(f"\n🎤 处理声音档案: {voice.name} (ID: {voice.id})")
        
        updated = False
        
        # 修复参考音频路径
        if voice.reference_audio_path and voice.reference_audio_path.startswith('/app/'):
            old_path = voice.reference_audio_path
            # 将 /app/data 转换为 D:\AI-Sound\data
            new_path = voice.reference_audio_path.replace('/app/', 'D:/AI-Sound/').replace('/', '\\')
            
            # 检查文件是否存在
            if os.path.exists(new_path):
                voice.reference_audio_path = new_path
                print(f"   ✅ 修复参考音频路径: {old_path} -> {new_path}")
                updated = True
            else:
                print(f"   ❌ 新路径不存在: {new_path}")
        
        # 修复Latent文件路径
        if voice.latent_file_path and voice.latent_file_path.startswith('/app/'):
            old_path = voice.latent_file_path
            new_path = voice.latent_file_path.replace('/app/', 'D:/AI-Sound/').replace('/', '\\')
            
            if os.path.exists(new_path):
                voice.latent_file_path = new_path
                print(f"   ✅ 修复Latent文件路径: {old_path} -> {new_path}")
                updated = True
            else:
                print(f"   ❌ 新路径不存在: {new_path}")
        
        # 修复示例音频路径
        if voice.sample_audio_path and voice.sample_audio_path.startswith('/app/'):
            old_path = voice.sample_audio_path
            new_path = voice.sample_audio_path.replace('/app/', 'D:/AI-Sound/').replace('/', '\\')
            
            if os.path.exists(new_path):
                voice.sample_audio_path = new_path
                print(f"   ✅ 修复示例音频路径: {old_path} -> {new_path}")
                updated = True
            else:
                print(f"   ❌ 新路径不存在: {new_path}")
        
        if updated:
            fixed_count += 1
    
    # 提交更改
    if fixed_count > 0:
        try:
            db.commit()
            print(f"\n✅ 成功修复 {fixed_count} 个声音档案的路径")
        except Exception as e:
            db.rollback()
            print(f"\n❌ 提交更改失败: {e}")
    else:
        print(f"\n📝 没有需要修复的路径")
    
    # 验证声音ID 5的状态
    print(f"\n🔍 验证声音ID 5的状态:")
    voice_5 = db.query(VoiceProfile).filter(VoiceProfile.id == 5).first()
    if voice_5:
        print(f"   参考音频: {voice_5.reference_audio_path}")
        print(f"   文件存在: {'✅' if os.path.exists(voice_5.reference_audio_path) else '❌'}")
        print(f"   Latent文件: {voice_5.latent_file_path}")
        print(f"   文件存在: {'✅' if os.path.exists(voice_5.latent_file_path) else '❌'}")

if __name__ == "__main__":
    fix_voice_paths() 