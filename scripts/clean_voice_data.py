#!/usr/bin/env python3
"""
清理声音档案历史数据
重置数据库和文件系统，为重新创建声音档案做准备
"""
import sys
import os
import glob
import shutil
sys.path.append('../platform/backend/app')

from database import get_db
from models import VoiceProfile

def clean_voice_data():
    print("🧹 === 清理声音档案历史数据 ===")
    
    # 1. 清理数据库
    print("\n📋 第一步：清理数据库...")
    try:
        db = next(get_db())
        
        # 获取现有数据统计
        voice_count = db.query(VoiceProfile).count()
        print(f"  📊 找到 {voice_count} 个现有声音档案")
        
        if voice_count > 0:
            # 删除所有声音档案记录
            db.query(VoiceProfile).delete()
            db.commit()
            print(f"  ✅ 已删除 {voice_count} 个声音档案记录")
        else:
            print(f"  ✅ 数据库中没有声音档案，无需清理")
        
    except Exception as e:
        print(f"  ❌ 数据库清理失败: {str(e)}")
        return False
    
    # 2. 清理voice_profiles目录
    print("\n📁 第二步：清理voice_profiles目录...")
    voice_profiles_dir = "../data/voice_profiles"
    
    if os.path.exists(voice_profiles_dir):
        # 统计文件
        wav_files = glob.glob(f"{voice_profiles_dir}/*.wav")
        npy_files = glob.glob(f"{voice_profiles_dir}/*.npy")
        other_files = glob.glob(f"{voice_profiles_dir}/*")
        other_files = [f for f in other_files if not f.endswith(('.wav', '.npy'))]
        
        total_files = len(wav_files) + len(npy_files) + len(other_files)
        print(f"  📊 找到文件: {len(wav_files)} WAV, {len(npy_files)} NPY, {len(other_files)} 其他")
        
        if total_files > 0:
            # 删除所有文件
            deleted_count = 0
            for file_path in wav_files + npy_files + other_files:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"  🗑️ 删除: {os.path.basename(file_path)}")
                except Exception as e:
                    print(f"  ❌ 删除失败 {os.path.basename(file_path)}: {str(e)}")
            
            print(f"  ✅ 成功删除 {deleted_count}/{total_files} 个文件")
        else:
            print(f"  ✅ voice_profiles目录为空，无需清理")
    else:
        print(f"  ✅ voice_profiles目录不存在，将自动创建")
        os.makedirs(voice_profiles_dir, exist_ok=True)
    
    # 3. 清理uploads目录中的相关文件（可选）
    print("\n📁 第三步：清理uploads目录中的声音相关文件...")
    uploads_dir = "../data/uploads"
    
    if os.path.exists(uploads_dir):
        # 只清理明显是声音档案相关的文件
        ref_files = glob.glob(f"{uploads_dir}/ref_*.wav")
        latent_files = glob.glob(f"{uploads_dir}/latent_*.npy")
        voice_files = glob.glob(f"{uploads_dir}/*主播*.wav") + glob.glob(f"{uploads_dir}/*女声*.wav") + glob.glob(f"{uploads_dir}/*男声*.wav")
        
        cleanup_files = ref_files + latent_files + voice_files
        print(f"  📊 找到声音相关文件: {len(cleanup_files)} 个")
        
        if cleanup_files:
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
            print(f"  ✅ uploads目录中没有声音相关文件")
    else:
        print(f"  ✅ uploads目录不存在")
    
    # 4. 重置相关日志（可选）
    print("\n📝 第四步：清理相关日志...")
    try:
        from models import SystemLog
        
        # 删除声音克隆相关的日志
        voice_logs = db.query(SystemLog).filter(
            SystemLog.module.in_(['voice_clone', 'characters'])
        ).count()
        
        if voice_logs > 0:
            db.query(SystemLog).filter(
                SystemLog.module.in_(['voice_clone', 'characters'])
            ).delete()
            db.commit()
            print(f"  ✅ 已删除 {voice_logs} 条相关日志")
        else:
            print(f"  ✅ 没有相关日志需要清理")
            
    except Exception as e:
        print(f"  ⚠️ 日志清理失败（可忽略）: {str(e)}")
    
    # 5. 验证清理结果
    print("\n🔍 第五步：验证清理结果...")
    
    # 检查数据库
    remaining_voices = db.query(VoiceProfile).count()
    print(f"  📊 数据库剩余声音档案: {remaining_voices}")
    
    # 检查文件系统
    remaining_vp_files = len(glob.glob(f"{voice_profiles_dir}/*"))
    print(f"  📊 voice_profiles目录剩余文件: {remaining_vp_files}")
    
    if remaining_voices == 0 and remaining_vp_files == 0:
        print(f"  ✅ 清理完成！所有历史数据已删除")
    else:
        print(f"  ⚠️ 还有部分数据未清理，请手动检查")
    
    # 6. 创建基础目录结构
    print("\n📁 第六步：重建目录结构...")
    dirs_to_create = [
        "../data/voice_profiles",
        "../data/audio",
        "../data/uploads"
    ]
    
    for dir_path in dirs_to_create:
        os.makedirs(dir_path, exist_ok=True)
        print(f"  ✅ 确保目录存在: {dir_path}")
    
    print(f"\n🎉 === 清理完成！===")
    print(f"现在可以重新创建声音档案了！")
    print(f"")
    print(f"下一步建议：")
    print(f"1. 重启后端服务确保数据库连接正常")
    print(f"2. 通过前端界面重新创建声音档案")
    print(f"3. 新建的档案将使用正确的路径结构")
    
    return True

if __name__ == "__main__":
    success = clean_voice_data()
    if not success:
        sys.exit(1)