import sys
sys.path.append('/app')
from app.models import NovelProject
from app.database import get_session

with get_session() as session:
    project = session.query(NovelProject).filter(NovelProject.id == 11).first()
    if project:
        # 获取所有段落的检测角色
        segments = project.segments
        detected_speakers = set(s.detected_speaker for s in segments if s.detected_speaker)
        print('检测到的所有角色:', list(detected_speakers))
        print('当前角色映射:', project.get_character_mapping())
        
        unmapped = detected_speakers - set(project.get_character_mapping().keys())
        print('未映射的角色:', list(unmapped))
        
        # 统计每个角色的段落数
        speaker_counts = {}
        for s in segments:
            speaker = s.detected_speaker or 'Unknown'
            speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
        
        print('角色段落统计:')
        for speaker, count in sorted(speaker_counts.items(), key=lambda x: x[1], reverse=True):
            mapped = speaker in project.get_character_mapping()
            print(f'  {speaker}: {count} 段落 (映射: {mapped})') 