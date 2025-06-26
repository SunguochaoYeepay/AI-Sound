#!/usr/bin/env python3
"""
检查项目42和相关章节状态的脚本
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models import NovelProject, BookChapter, AnalysisResult, AudioFile

def main():
    try:
        # 获取数据库连接
        db = next(get_db())

        print("=" * 60)
        print("🔍 AI-Sound 项目42状态检查")
        print("=" * 60)

        # 检查项目42的状态
        project = db.query(NovelProject).filter(NovelProject.id == 42).first()
        if project:
            print(f'📊 项目42状态:')
            print(f'  项目名称: {project.name}')
            print(f'  项目状态: {project.status}')
            print(f'  总段落数: {project.total_segments}')
            print(f'  已处理段落: {project.processed_segments}')
            print(f'  当前段落: {project.current_segment}')
            print(f'  错误信息: {getattr(project, "error_message", "无")}')
            print(f'  创建时间: {project.created_at}')
            print(f'  更新时间: {project.updated_at}')
            print()
        else:
            print("❌ 未找到项目42")
            return

        # 检查项目42的所有章节
        chapters = db.query(BookChapter).filter(BookChapter.book_id == project.book_id).order_by(BookChapter.chapter_number).all()
        print(f'📖 项目42的章节: {len(chapters)} 个')
        
        for chapter in chapters[:5]:  # 显示前5个章节
            print(f'  章节{chapter.chapter_number}: {chapter.chapter_title}')
            print(f'    章节ID: {chapter.id}')
            print(f'    分析状态: {getattr(chapter, "analysis_status", "未知")}')
            print(f'    合成状态: {getattr(chapter, "synthesis_status", "未知")}')
            
            # 检查智能准备结果
            analysis_results = db.query(AnalysisResult).filter(AnalysisResult.chapter_id == chapter.id).all()
            print(f'    智能准备结果: {len(analysis_results)} 条')
            
            for result in analysis_results:
                print(f'      结果ID: {result.id}, 状态: {result.status}')
                if result.synthesis_plan:
                    plan = result.synthesis_plan
                    if isinstance(plan, dict) and 'synthesis_plan' in plan:
                        segments_count = len(plan['synthesis_plan'])
                        print(f'      合成段落数: {segments_count}')
            print()

        # 检查项目42的音频文件
        audio_files = db.query(AudioFile).filter(AudioFile.project_id == 42).all()
        print(f'🎵 项目42的音频文件: {len(audio_files)} 个')
        
        segment_files = [af for af in audio_files if af.audio_type == 'segment']
        chapter_files = [af for af in audio_files if af.audio_type == 'chapter']
        full_files = [af for af in audio_files if af.audio_type == 'full']
        
        print(f'  段落音频: {len(segment_files)} 个')
        print(f'  章节音频: {len(chapter_files)} 个')
        print(f'  完整音频: {len(full_files)} 个')
        
        # 显示前几个段落音频文件的详情
        if segment_files:
            print(f'  段落音频文件示例:')
            for af in segment_files[:5]:
                print(f'    {af.filename} - 章节{af.chapter_id} - 段落{af.segment_id} - {af.file_size or "未知大小"}')

        # 特别检查第一章（假设是章节106）
        chapter_106 = db.query(BookChapter).filter(BookChapter.id == 106).first()
        if chapter_106:
            print(f'\n🎯 重点检查第1章 (ID: 106):')
            print(f'  章节标题: {chapter_106.chapter_title}')
            print(f'  章节号: {chapter_106.chapter_number}')
            print(f'  书籍ID: {chapter_106.book_id}')
            print(f'  分析状态: {getattr(chapter_106, "analysis_status", "未知")}')
            print(f'  合成状态: {getattr(chapter_106, "synthesis_status", "未知")}')
            
            # 检查该章节的智能准备结果
            analysis_results = db.query(AnalysisResult).filter(AnalysisResult.chapter_id == 106).all()
            print(f'  智能准备结果: {len(analysis_results)} 条')
            
            for result in analysis_results:
                print(f'    结果ID: {result.id}')
                print(f'    状态: {result.status}')
                print(f'    创建时间: {result.created_at}')
                if result.synthesis_plan:
                    plan = result.synthesis_plan
                    if isinstance(plan, dict):
                        if 'synthesis_plan' in plan:
                            segments_count = len(plan['synthesis_plan'])
                            print(f'    合成段落数: {segments_count}')
                            # 显示前2个段落示例
                            for i, segment in enumerate(plan['synthesis_plan'][:2]):
                                text_preview = segment.get('text', '')[:30] + '...' if segment.get('text') else '无文本'
                                print(f'      段落{i+1}: {text_preview}')
                        else:
                            print(f'    合成配置键: {list(plan.keys())}')
            
            # 检查该章节的音频文件
            chapter_106_audio = db.query(AudioFile).filter(
                AudioFile.project_id == 42,
                AudioFile.chapter_id == 106
            ).all()
            print(f'  音频文件: {len(chapter_106_audio)} 个')

        db.close()
        
    except Exception as e:
        print(f"❌ 检查过程中发生错误: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main() 