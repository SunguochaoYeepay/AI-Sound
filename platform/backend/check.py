# 🚀 新架构：check.py已更新为AudioFile模式
from app.database import get_db
from app.models import NovelProject, AudioFile
from collections import Counter

db = next(get_db())
project = db.query(NovelProject).filter(NovelProject.id == 38).first()
print(f"项目状态: {project.status}")

# 新架构：基于AudioFile统计
audio_files = db.query(AudioFile).filter(
    AudioFile.project_id == 38,
    AudioFile.audio_type == 'segment'
).all()

print(f"已完成段落数: {len(audio_files)}")
print(f"项目总段落数: {project.total_segments}")
if project.total_segments:
    failed_count = max(0, project.total_segments - len(audio_files))
    print(f"失败段落数: {failed_count}")
    print(f"进度: {len(audio_files)}/{project.total_segments} ({len(audio_files)/project.total_segments*100:.1f}%)")
else:
    print("项目尚未设置总段落数")

print("# 🚀 TextSegment已删除，新架构使用AudioFile统计")