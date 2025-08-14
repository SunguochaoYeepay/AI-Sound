#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def check_project20():
    """查看项目20的环境音分析状态"""
    print("🔍 项目20环境音分析状态检查")
    print("=" * 50)
    
    try:
        # 获取项目20详情
        response = requests.get('http://localhost:8000/api/v1/environment-generation/projects/20')
        data = response.json()
        
        project = data['data']['project']
        analysis_result = data['data']['analysis_result']
        
        print(f"📋 项目基本信息:")
        print(f"   ID: {project['id']}")
        print(f"   名称: {project['name']}")
        print(f"   状态: {project['status']}")
        print(f"   书籍: {project['book_name']}")
        print(f"   章节: {project['chapter_name']}")
        print()
        
        print(f"📈 分析结果状态:")
        if analysis_result:
            print(f"   ✅ 有分析结果")
            print(f"   分析章节数: {len(analysis_result)}")
            print()
            
            print("📖 各章节分析详情:")
            for chapter_id, chapter_data in analysis_result.items():
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
        
        print("✅ 项目20分析状态检查完成")
        
    except Exception as e:
        print(f"❌ 查询失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_project20()
