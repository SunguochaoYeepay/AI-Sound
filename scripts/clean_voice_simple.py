#!/usr/bin/env python3
"""
简化的声音档案数据清理脚本
只清理文件系统，不涉及数据库操作
"""
import os
import glob
import shutil

def clean_voice_files():
    print("🧹 === 清理声音档案文件 ===")
    
    # 获取项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    
    # 清理voice_profiles目录
    voice_profiles_dir = os.path.join(project_dir, "data", "voice_profiles")
    print(f"\n📁 清理voice_profiles目录: {voice_profiles_dir}")
    
    if os.path.exists(voice_profiles_dir):
        files = glob.glob(os.path.join(voice_profiles_dir, "*"))
        print(f"  📊 找到 {len(files)} 个文件")
        
        deleted_count = 0
        for file_path in files:
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"  🗑️ 删除: {os.path.basename(file_path)}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    deleted_count += 1
                    print(f"  🗑️ 删除目录: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"  ❌ 删除失败 {os.path.basename(file_path)}: {str(e)}")
        
        print(f"  ✅ 成功删除 {deleted_count}/{len(files)} 个文件/目录")
    else:
        print(f"  ✅ voice_profiles目录不存在")
        os.makedirs(voice_profiles_dir, exist_ok=True)
        print(f"  ✅ 已创建voice_profiles目录")
    
    # 清理uploads目录中的声音相关文件
    uploads_dir = os.path.join(project_dir, "data", "uploads")
    print(f"\n📁 清理uploads目录中的声音文件: {uploads_dir}")
    
    if os.path.exists(uploads_dir):
        # 声音相关文件模式
        patterns = [
            "ref_*.wav", "ref_*.mp3", "ref_*.flac",
            "latent_*.npy",
            "*主播*.wav", "*女声*.wav", "*男声*.wav",
            "*_reference.*", "*_latent.*", "*_sample.*"
        ]
        
        cleanup_files = []
        for pattern in patterns:
            cleanup_files.extend(glob.glob(os.path.join(uploads_dir, pattern)))
        
        # 去重
        cleanup_files = list(set(cleanup_files))
        print(f"  📊 找到声音相关文件: {len(cleanup_files)} 个")
        
        deleted_count = 0
        for file_path in cleanup_files:
            try:
                os.remove(file_path)
                deleted_count += 1
                print(f"  🗑️ 删除: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"  ❌ 删除失败 {os.path.basename(file_path)}: {str(e)}")
        
        print(f"  ✅ 成功删除 {deleted_count} 个声音相关文件")
    else:
        print(f"  ✅ uploads目录不存在")
    
    # 确保目录结构存在
    print(f"\n📁 确保目录结构...")
    dirs_to_create = [
        os.path.join(project_dir, "data", "voice_profiles"),
        os.path.join(project_dir, "data", "audio"),
        os.path.join(project_dir, "data", "uploads")
    ]
    
    for dir_path in dirs_to_create:
        os.makedirs(dir_path, exist_ok=True)
        print(f"  ✅ 目录存在: {os.path.relpath(dir_path, project_dir)}")
    
    print(f"\n🎉 文件清理完成！")
    print(f"")
    print(f"下一步：")
    print(f"1. 重启Docker容器清理数据库缓存")
    print(f"2. 通过前端界面重新创建声音档案")

if __name__ == "__main__":
    clean_voice_files()