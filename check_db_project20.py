#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models.environment_generation import EnvironmentProject

def check_project20_in_db():
    """查询数据库中的项目20详细信息"""
    print("🔍 查询数据库中的项目20")
    print("=" * 50)
    
    db = next(get_db())
    
    try:
        # 查询项目20
        project = db.query(EnvironmentProject).filter(EnvironmentProject.id == 20).first()
        
        if not project:
            print("❌ 项目20不存在")
            return
        
        print(f"📋 项目基本信息:")
        print(f"   ID: {project.id}")
        print(f"   名称: {project.name}")
        print(f"   状态: {project.status}")
        print(f"   书籍: {project.book_name}")
        print(f"   章节: {project.chapter_name}")
        print(f"   创建时间: {project.created_at}")
        print(f"   更新时间: {project.updated_at}")
        print()
        
        print(f"📈 分析结果状态:")
        if project.analysis_result:
            print(f"   ✅ 有分析结果")
            print(f"   分析结果类型: {type(project.analysis_result)}")
            print(f"   分析结果章节数: {len(project.analysis_result)}")
            print()
            
            print("📖 各章节详情:")
            for chapter_id, chapter_data in project.analysis_result.items():
                print(f"   章节ID: {chapter_id}")
                
                # 获取章节信息
                if 'chapter_info' in chapter_data:
                    chapter_info = chapter_data['chapter_info']
                    if chapter_info and len(chapter_info) > 0:
                        chapter_title = chapter_info[0].get('title', '未知标题')
                        print(f"   标题: {chapter_title}")
                
                # 获取环境音轨道
                if 'environment_tracks' in chapter_data:
                    tracks = chapter_data['environment_tracks']
                    print(f"   环境音轨道数: {len(tracks)}")
                    
                    for i, track in enumerate(tracks, 1):
                        keywords = track.get('environment_keywords', [])
                        start_time = track.get('start_time', 0)
                        end_time = track.get('end_time', 0)
                        duration = track.get('duration', 0)
                        print(f"     轨道{i}: {keywords} ({start_time:.1f}-{end_time:.1f}秒, 时长{duration:.1f}秒)")
                
                # 获取分析元数据
                if 'analysis_metadata' in chapter_data:
                    metadata = chapter_data['analysis_metadata']
                    total_duration = metadata.get('total_duration', 0)
                    track_count = metadata.get('track_count', 0)
                    print(f"   总时长: {total_duration:.1f}秒")
                    print(f"   轨道总数: {track_count}")
                
                print()
        else:
            print(f"   ❌ 无分析结果")
        
        print("✅ 数据库查询完成")
        
    except Exception as e:
        print(f"❌ 查询失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_project20_in_db()
