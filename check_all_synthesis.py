#!/usr/bin/env python3
import sys, os
sys.path.append('.')
from app.database import get_db
from app.models import SynthesisTask, AudioFile, NovelProject

db = next(get_db())

# 检查所有项目
projects = db.query(NovelProject).all()
print(f"总项目数: {len(projects)}")
for project in projects:
    print(f"项目 {project.id}: {project.name} - 状态: {project.status}")

print("\n" + "="*50)

# 检查所有合成任务
tasks = db.query(SynthesisTask).all()
print(f"总合成任务数: {len(tasks)}")
for task in tasks:
    print(f"任务 {task.id}: 项目{task.project_id} - 状态: {task.status}")
    print(f"  完成: {task.completed_segments}/{task.total_segments}")
    if task.final_audio_path:
        print(f"  最终音频: {task.final_audio_path}")
        print(f"  文件存在: {os.path.exists(task.final_audio_path)}")

print("\n" + "="*50)

# 检查所有音频文件
audio_files = db.query(AudioFile).all()
print(f"总音频文件数: {len(audio_files)}")
for af in audio_files[-5:]:  # 显示最后5个
    print(f"音频 {af.id}: {af.filename}")
    print(f"  项目: {af.project_id}")
    print(f"  路径: {af.file_path}")
    if af.file_path:
        print(f"  存在: {os.path.exists(af.file_path)}")
        if os.path.exists(af.file_path):
            print(f"  大小: {os.path.getsize(af.file_path)} bytes") 