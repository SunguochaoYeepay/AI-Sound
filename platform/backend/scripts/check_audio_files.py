from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import NovelProject, BookChapter, AudioFile, AnalysisResult
from app.config import settings

def check_project_audio_files(project_id: int):
    """检查指定项目的音频文件分布情况"""
    # 创建数据库连接
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # 1. 获取项目信息
        project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            print(f"项目 {project_id} 不存在！")
            return
        
        print(f"\n=== 项目 {project_id} 音频文件检查报告 ===")
        print(f"项目名称: {project.name}")
        
        # 2. 获取所有章节
        chapters = db.query(BookChapter).filter(
            BookChapter.book_id == project.book_id
        ).order_by(BookChapter.chapter_number).all()
        
        print(f"\n总章节数: {len(chapters)}")
        
        # 3. 检查每个章节的音频文件
        for chapter in chapters:
            print(f"\n第 {chapter.chapter_number} 章:")
            
            # 3.1 获取章节的分析结果（应该有多少段落）
            analysis_result = db.query(AnalysisResult).filter(
                AnalysisResult.chapter_id == chapter.id,
                AnalysisResult.status == 'completed'
            ).order_by(AnalysisResult.created_at.desc()).first()
            
            expected_segments = 0
            if analysis_result and analysis_result.synthesis_plan:
                expected_segments = len(analysis_result.synthesis_plan)
            
            # 3.2 获取实际的音频文件数量
            audio_files = db.query(AudioFile).filter(
                AudioFile.project_id == project_id,
                AudioFile.chapter_id == chapter.id
            ).all()
            
            # 3.3 按状态统计
            status_count = {
                'active': len([af for af in audio_files if af.status == 'active']),
                'pending': len([af for af in audio_files if af.status == 'pending']),
                'failed': len([af for af in audio_files if af.status == 'failed'])
            }
            
            print(f"  - 预期段落数: {expected_segments}")
            print(f"  - 实际音频文件: {len(audio_files)}")
            print(f"    * 已完成: {status_count['active']}")
            print(f"    * 等待中: {status_count['pending']}")
            print(f"    * 失败: {status_count['failed']}")
            
            # 3.4 检查文件是否实际存在
            for audio_file in audio_files:
                if audio_file.file_path and not os.path.exists(audio_file.file_path):
                    print(f"  ! 警告: 文件不存在: {audio_file.file_path}")
            
            # 3.5 检查synthesis_status
            print(f"  - 合成状态: {chapter.synthesis_status}")
            
    except Exception as e:
        print(f"检查过程中出错: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    project_id = 75  # 检查项目75
    check_project_audio_files(project_id) 