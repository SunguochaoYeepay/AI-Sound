#!/usr/bin/env python3
"""
全面修复声音档案路径问题
1. 检查数据库中的路径
2. 统一修正文件路径格式
3. 确保文件存在性
4. 清理无效记录
"""
import sys
import os
import glob
sys.path.append('../platform/backend/app')

from database import get_db
from models import VoiceProfile

def fix_voice_paths():
    print("🔧 === 全面修复声音档案路径 ===")
    
    db = next(get_db())
    voices = db.query(VoiceProfile).all()
    
    if not voices:
        print("❌ 没有找到任何声音档案")
        return
    
    print(f"📋 找到 {len(voices)} 个声音档案需要检查")
    
    # 扫描实际文件
    voice_profiles_dir = "../data/voice_profiles"
    uploads_dir = "../data/uploads"
    
    # 检查目录是否存在
    if not os.path.exists(voice_profiles_dir):
        print(f"❌ 目录不存在: {voice_profiles_dir}")
        return
        
    # 获取所有可用的文件
    wav_files_vp = glob.glob(f"{voice_profiles_dir}/*.wav")
    npy_files_vp = glob.glob(f"{voice_profiles_dir}/*.npy")
    wav_files_up = glob.glob(f"{uploads_dir}/*.wav") if os.path.exists(uploads_dir) else []
    npy_files_up = glob.glob(f"{uploads_dir}/*.npy") if os.path.exists(uploads_dir) else []
    
    print(f"📁 voice_profiles目录: {len(wav_files_vp)} WAV, {len(npy_files_vp)} NPY")
    print(f"📁 uploads目录: {len(wav_files_up)} WAV, {len(npy_files_up)} NPY")
    
    # 创建文件名到路径的映射
    all_files = {}
    for file_path in wav_files_vp + npy_files_vp + wav_files_up + npy_files_up:
        filename = os.path.basename(file_path)
        all_files[filename] = file_path
    
    updated_count = 0
    fixed_count = 0
    
    for voice in voices:
        print(f"\n🔍 检查声音档案: {voice.name}")
        voice_updated = False
        
        # 处理reference_audio_path
        if voice.reference_audio_path:
            print(f"  原始WAV路径: {voice.reference_audio_path}")
            
            # 检查文件是否存在
            if os.path.exists(voice.reference_audio_path):
                print(f"  ✅ WAV文件存在")
            else:
                print(f"  ❌ WAV文件不存在，尝试修复...")
                
                # 尝试从文件名查找
                filename = os.path.basename(voice.reference_audio_path)
                if filename in all_files:
                    new_path = all_files[filename]
                    # 转换为容器内路径
                    if "voice_profiles" in new_path:
                        container_path = f"/app/data/voice_profiles/{filename}"
                    else:
                        container_path = f"/app/data/uploads/{filename}"
                    
                    voice.reference_audio_path = container_path
                    voice_updated = True
                    print(f"  🔧 已修复WAV路径: {container_path}")
                else:
                    print(f"  ❌ 未找到对应的WAV文件: {filename}")
        
        # 处理latent_file_path
        if voice.latent_file_path:
            print(f"  原始NPY路径: {voice.latent_file_path}")
            
            if os.path.exists(voice.latent_file_path):
                print(f"  ✅ NPY文件存在")
            else:
                print(f"  ❌ NPY文件不存在，尝试修复...")
                
                filename = os.path.basename(voice.latent_file_path)
                if filename in all_files:
                    new_path = all_files[filename]
                    if "voice_profiles" in new_path:
                        container_path = f"/app/data/voice_profiles/{filename}"
                    else:
                        container_path = f"/app/data/uploads/{filename}"
                    
                    voice.latent_file_path = container_path
                    voice_updated = True
                    print(f"  🔧 已修复NPY路径: {container_path}")
                else:
                    print(f"  ❌ 未找到对应的NPY文件: {filename}")
        else:
            print(f"  ⚠️ 没有NPY文件路径")
        
        # 处理sample_audio_path
        if voice.sample_audio_path:
            print(f"  原始Sample路径: {voice.sample_audio_path}")
            
            if not os.path.exists(voice.sample_audio_path):
                filename = os.path.basename(voice.sample_audio_path)
                if filename in all_files:
                    new_path = all_files[filename]
                    if "voice_profiles" in new_path:
                        container_path = f"/app/data/voice_profiles/{filename}"
                    else:
                        container_path = f"/app/data/uploads/{filename}"
                    
                    voice.sample_audio_path = container_path
                    voice_updated = True
                    print(f"  🔧 已修复Sample路径: {container_path}")
        
        if voice_updated:
            updated_count += 1
            fixed_count += 1
    
    # 提交所有更改
    if updated_count > 0:
        db.commit()
        print(f"\n✅ 成功修复了 {updated_count} 个声音档案的路径")
    else:
        print(f"\n✅ 所有声音档案路径都正确，无需修复")
    
    # 最终验证
    print(f"\n🔍 === 最终验证 ===")
    for voice in voices:
        db.refresh(voice)
        print(f"\n声音档案: {voice.name}")
        
        if voice.reference_audio_path:
            exists = os.path.exists(voice.reference_audio_path)
            print(f"  WAV: {voice.reference_audio_path} - {'✅' if exists else '❌'}")
        
        if voice.latent_file_path:
            exists = os.path.exists(voice.latent_file_path)
            print(f"  NPY: {voice.latent_file_path} - {'✅' if exists else '❌'}")
        
        # 检查to_dict()转换结果
        voice_dict = voice.to_dict()
        print(f"  API返回的WAV URL: {voice_dict.get('referenceAudioUrl')}")
        print(f"  API返回的NPY URL: {voice_dict.get('latentFileUrl')}")
    
    print(f"\n🎉 路径修复完成！")

if __name__ == "__main__":
    fix_voice_paths()