# 检查项目34的数据
from app.database import get_db
from app.models import NovelProject, AudioFile
from collections import Counter

db = next(get_db())
project = db.query(NovelProject).filter(NovelProject.id == 34).first()
print(f"项目34状态: {project.status}")
print(f"项目总段落数: {project.total_segments}")
print(f"项目已处理段落数: {project.processed_segments}")

# 新架构：基于AudioFile统计
audio_files = db.query(AudioFile).filter(
    AudioFile.project_id == 34,
    AudioFile.audio_type == 'segment'
).all()

print(f"实际已完成段落数: {len(audio_files)}")

# 检查AudioFile详情
if audio_files:
    print(f"前5个AudioFile详情:")
    for i, af in enumerate(audio_files[:5]):
        print(f"  {i+1}: id={af.id}, paragraph_index={af.paragraph_index}, speaker={af.speaker}, status={af.status}")

# 检查是否有其他类型的AudioFile
all_audio_files = db.query(AudioFile).filter(AudioFile.project_id == 34).all()
print(f"所有AudioFile数量: {len(all_audio_files)}")

audio_types = Counter(af.audio_type for af in all_audio_files)
print(f"AudioFile类型统计: {dict(audio_types)}")

# 检查进度计算
if project.total_segments and project.total_segments > 0:
    progress = len(audio_files) / project.total_segments * 100
    print(f"实际进度: {len(audio_files)}/{project.total_segments} = {progress:.1f}%")
else:
    print("项目total_segments为0或None，需要修复")