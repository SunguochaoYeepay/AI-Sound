#!/usr/bin/env python3
import sys, os
sys.path.append('platform/backend')
from app.database import get_db
from app.models import AudioFile, NovelProject

db = next(get_db())

# 检查项目22
project = db.query(NovelProject).filter(NovelProject.id == 22).first()
if project:
    print(f"项目22: {project.name} - 状态: {project.status}")
    
    # 检查项目22的音频文件
    audio_files = db.query(AudioFile).filter(AudioFile.project_id == 22).all()
    print(f"项目22的音频文件数量: {len(audio_files)}")
    
    for af in audio_files:
        print(f"  - {af.filename}")
        print(f"    类型: {af.audio_type}")
        print(f"    路径: {af.file_path}")
        print(f"    存在: {os.path.exists(af.file_path) if af.file_path else False}")
        print(f"    大小: {af.file_size} bytes")
        print(f"    时长: {af.duration}s")
        print()
else:
    print("项目22不存在")

# 检查所有以segment_开头的音频文件
print("\n" + "="*50)
print("检查所有segment音频文件:")
segment_files = db.query(AudioFile).filter(AudioFile.audio_type == 'segment').all()
print(f"总segment音频文件数: {len(segment_files)}")

for af in segment_files[-10:]:  # 显示最后10个
    print(f"  - {af.filename} (项目: {af.project_id})")
    if af.file_path:
        print(f"    存在: {os.path.exists(af.file_path)}") 