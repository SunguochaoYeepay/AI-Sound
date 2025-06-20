#!/usr/bin/env python3
"""
检查项目42的最终音频文件设置
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models import NovelProject, AudioFile
from pathlib import Path

def main():
    print("🔍 检查项目42的最终音频文件状态...")
    
    db = next(get_db())
    
    # 获取项目信息
    project = db.get(NovelProject, 42)
    if not project:
        print("❌ 项目42不存在")
        return
    
    print(f"📊 项目信息:")
    print(f"   ID: {project.id}")
    print(f"   名称: {project.name}")
    print(f"   状态: {project.status}")
    print(f"   最终音频路径: {project.final_audio_path}")
    
    # 检查输出目录中的最终音频文件
    project_dir = Path("outputs/projects/42")
    if project_dir.exists():
        print(f"\n📁 输出目录中的最终音频文件:")
        
        # 查找所有最终音频文件
        final_files = list(project_dir.glob("final_*.wav"))
        mixed_files = list(project_dir.glob("final_mixed_*.wav"))
        
        print(f"   普通最终文件: {len(final_files)}")
        for f in sorted(final_files):
            size_mb = f.stat().st_size / 1024 / 1024
            print(f"     - {f.name} ({size_mb:.1f} MB)")
        
        print(f"   混合最终文件: {len(mixed_files)}")
        for f in sorted(mixed_files):
            size_mb = f.stat().st_size / 1024 / 1024
            print(f"     - {f.name} ({size_mb:.1f} MB)")
        
        # 推荐最佳文件
        if mixed_files:
            latest_mixed = max(mixed_files, key=lambda x: x.stat().st_mtime)
            print(f"\n✅ 推荐使用混合音频文件:")
            print(f"   文件: {latest_mixed.name}")
            print(f"   大小: {latest_mixed.stat().st_size / 1024 / 1024:.1f} MB")
            print(f"   路径: {latest_mixed}")
            
            # 检查是否需要更新数据库
            expected_path = str(latest_mixed)
            if project.final_audio_path != expected_path:
                print(f"\n🔧 需要更新数据库中的最终音频路径:")
                print(f"   当前: {project.final_audio_path}")
                print(f"   应为: {expected_path}")
                
                # 更新数据库
                try:
                    project.final_audio_path = expected_path
                    db.commit()
                    print(f"✅ 数据库已更新")
                except Exception as e:
                    print(f"❌ 数据库更新失败: {str(e)}")
        elif final_files:
            latest_final = max(final_files, key=lambda x: x.stat().st_mtime)
            print(f"\n⚠️ 只有普通音频文件（无环境音）:")
            print(f"   文件: {latest_final.name}")
            print(f"   大小: {latest_final.stat().st_size / 1024 / 1024:.1f} MB")
        else:
            print(f"\n❌ 没有找到最终音频文件")
    
    # 检查数据库中的AudioFile记录
    print(f"\n💾 数据库中的AudioFile记录:")
    
    final_audio_files = db.query(AudioFile).filter(
        AudioFile.project_id == 42,
        AudioFile.audio_type == 'final'
    ).all()
    
    if final_audio_files:
        print(f"   找到 {len(final_audio_files)} 个最终音频记录:")
        for audio in final_audio_files:
            print(f"     - ID: {audio.id}, 文件名: {audio.filename}")
            print(f"       路径: {audio.file_path}")
            print(f"       大小: {audio.file_size} bytes")
            print(f"       时长: {audio.duration} 秒")
    else:
        print(f"   ❌ 没有找到最终音频记录")
    
    # 建议操作
    print(f"\n💡 建议操作:")
    if mixed_files:
        print(f"   1. 项目42已经有环境音混合文件，应该能正常播放")
        print(f"   2. 前端播放时会使用数据库中的final_audio_path")
        print(f"   3. 如果还是听不到环境音，检查前端播放逻辑")
    else:
        print(f"   1. 重新启动一次环境音合成")
        print(f"   2. 检查TangoFlux服务状态")
        print(f"   3. 检查顺序合成协调器的混合逻辑")

if __name__ == "__main__":
    main() 