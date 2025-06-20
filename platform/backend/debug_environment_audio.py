#!/usr/bin/env python3
"""
调试环境音问题
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models import NovelProject, AudioFile

def check_project_config():
    """检查项目配置"""
    db = next(get_db())
    
    project = db.get(NovelProject, 42)
    if not project:
        print("❌ 项目42不存在")
        return
    
    print(f"📊 项目42 ({project.name}) 配置检查:")
    print(f"   状态: {project.status}")
    print(f"   配置: {json.dumps(project.config, indent=2, ensure_ascii=False) if project.config else 'None'}")
    
    # 检查是否有环境音设置
    if project.config and "environment_settings" in project.config:
        env_settings = project.config["environment_settings"]
        print(f"✅ 环境音配置存在:")
        print(f"   启用: {env_settings.get('enable_environment', False)}")
        print(f"   音量: {env_settings.get('environment_volume', 0)}")
        print(f"   自动检测: {env_settings.get('auto_scene_detection', False)}")
    else:
        print("❌ 环境音配置不存在")
    
    return project

def check_audio_files():
    """检查音频文件"""
    db = next(get_db())
    
    print(f"\n🎵 项目42的音频文件:")
    audio_files = db.query(AudioFile).filter(AudioFile.project_id == 42).all()
    
    if not audio_files:
        print("❌ 没有找到音频文件")
        return
    
    for audio in audio_files:
        print(f"   ID: {audio.id}")
        print(f"   文件名: {audio.filename}")
        print(f"   类型: {audio.type}")
        print(f"   音频类型: {audio.audio_type}")
        print(f"   路径: {audio.file_path}")
        print(f"   大小: {audio.file_size} bytes")
        print(f"   时长: {audio.duration} 秒")
        
        # 检查文件是否存在
        if audio.file_path:
            full_path = os.path.join("outputs", audio.file_path)
            exists = os.path.exists(full_path)
            print(f"   文件存在: {'✅' if exists else '❌'}")
            if exists:
                actual_size = os.path.getsize(full_path)
                print(f"   实际大小: {actual_size} bytes")
        print()

def check_outputs_directory():
    """检查输出目录"""
    print(f"\n📁 输出目录检查:")
    
    project_output_dir = Path("outputs/projects/42")
    if project_output_dir.exists():
        print(f"✅ 项目输出目录存在: {project_output_dir}")
        
        # 列出所有文件
        files = list(project_output_dir.rglob("*"))
        print(f"   文件数量: {len(files)}")
        
        for file in files:
            if file.is_file():
                print(f"   📄 {file.name} ({file.stat().st_size} bytes)")
    else:
        print(f"❌ 项目输出目录不存在: {project_output_dir}")

def check_environment_functionality():
    """检查环境音功能状态"""
    print(f"\n🔧 环境音功能检查:")
    
    # 检查顺序合成协调器
    coordinator_path = Path("app/services/sequential_synthesis_coordinator.py")
    if coordinator_path.exists():
        print("✅ 顺序合成协调器存在")
    else:
        print("❌ 顺序合成协调器不存在")
    
    # 检查时间轴生成器
    timeline_path = Path("app/services/sequential_timeline_generator.py")
    if timeline_path.exists():
        print("✅ 时间轴生成器存在")
    else:
        print("❌ 时间轴生成器不存在")
    
    # 检查TangoFlux连接
    try:
        import requests
        response = requests.get("http://localhost:7930/health", timeout=5)
        if response.status_code == 200:
            print("✅ TangoFlux服务正常")
        else:
            print(f"⚠️ TangoFlux服务响应异常: {response.status_code}")
    except Exception as e:
        print(f"❌ TangoFlux服务连接失败: {str(e)}")

def main():
    print("🔍 环境音功能调试检查...")
    
    try:
        check_project_config()
        check_audio_files()
        check_outputs_directory()
        check_environment_functionality()
        
        print(f"\n💡 可能的问题和解决方案:")
        print(f"   1. 如果环境音配置不存在 → 重新运行配置脚本")
        print(f"   2. 如果没有音频文件 → 检查合成过程是否正常完成")
        print(f"   3. 如果TangoFlux服务异常 → 重启Docker容器")
        print(f"   4. 如果文件路径错误 → 检查路径映射")
        print(f"   5. 如果合成时没有调用环境音 → 检查前端传参")
        
    except Exception as e:
        print(f"❌ 检查过程出错: {str(e)}")

if __name__ == "__main__":
    main() 