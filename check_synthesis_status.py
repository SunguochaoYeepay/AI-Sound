#!/usr/bin/env python3
import sys, os
sys.path.append('.')
from app.database import get_db
from app.models import SynthesisTask, AudioFile

db = next(get_db())

# 检查最新的合成任务
task = db.query(SynthesisTask).filter(SynthesisTask.project_id == 22).order_by(SynthesisTask.id.desc()).first()
if task:
    print(f'任务状态: {task.status}')
    print(f'完成段落: {task.completed_segments}/{task.total_segments}')
    print(f'最终音频路径: {task.final_audio_path}')
    print(f'输出文件: {task.output_files}')
    
    # 检查音频文件记录
    audio_files = db.query(AudioFile).filter(AudioFile.project_id == 22).all()
    print(f'音频文件数量: {len(audio_files)}')
    for af in audio_files[-3:]:  # 显示最后3个
        print(f'  - {af.filename}: {af.file_path}')
        if af.file_path:
            print(f'    存在: {os.path.exists(af.file_path)}')
            if os.path.exists(af.file_path):
                print(f'    大小: {os.path.getsize(af.file_path)} bytes')
else:
    print('未找到合成任务') 