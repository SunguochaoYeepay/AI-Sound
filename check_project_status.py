from app.database import get_db
from app.models import NovelProject, TextSegment
from collections import Counter

def check_project_status():
    db = next(get_db())
    project = db.query(NovelProject).filter(NovelProject.id == 24).first()
    
    print(f'项目状态: {project.status}')
    print(f'处理段落数: {project.processed_segments}')
    
    # 统计段落状态
    segments = db.query(TextSegment).filter(TextSegment.project_id == 24).all()
    status_counts = Counter(s.status for s in segments)
    print(f'段落状态统计: {dict(status_counts)}')
    
    # 查看失败段落
    failed_segments = [s for s in segments if s.status == 'failed']
    print(f'失败段落数: {len(failed_segments)}')
    
    if failed_segments:
        print('失败段落详情:')
        for s in failed_segments[:5]:  # 显示前5个失败段落
            print(f'  段落{s.id}: {s.error_message}')
    
    db.close()

if __name__ == "__main__":
    check_project_status() 