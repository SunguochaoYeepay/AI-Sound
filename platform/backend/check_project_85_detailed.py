#!/usr/bin/env python3
"""
详细检查项目85，看看我之前的测试记录是否正确
"""

import requests
import json

def check_project_85_detailed():
    """详细检查项目85"""
    
    # 检查项目85的详情
    project_url = "http://localhost:8001/api/v1/environment-generation/projects/85"
    
    try:
        response = requests.get(project_url)
        print(f"项目85详情API状态码: {response.status_code}")
        
        if response.status_code == 200:
            project_data = response.json()
            
            if 'data' in project_data:
                data_obj = project_data['data']
                project_info = data_obj.get('project') or data_obj
                
                print(f"\n项目85基本信息:")
                print(f"  项目ID: {project_info.get('id')}")
                print(f"  项目名称: {project_info.get('name')}")
                print(f"  描述: {project_info.get('description')}")
                print(f"  书籍ID: {project_info.get('book_id')}")
                print(f"  章节ID: {project_info.get('chapter_ids')}")
                print(f"  状态: {project_info.get('status')}")
                print(f"  创建时间: {project_info.get('created_at')}")
                print(f"  更新时间: {project_info.get('updated_at')}")
                
                # 检查分析结果
                if 'analysis_result' in project_info:
                    analysis_result = project_info['analysis_result']
                    
                    if 'environment_tracks' in analysis_result:
                        tracks = analysis_result['environment_tracks']
                        print(f"\n分析结果详情:")
                        print(f"  轨道总数: {len(tracks)}")
                        
                        # 检查每个轨道的详细信息
                        print(f"\n轨道详情 (前5个):")
                        for i, track in enumerate(tracks[:5]):
                            print(f"  轨道{i+1}:")
                            print(f"    segment_id: {track.get('segment_id')}")
                            print(f"    start_time: {track.get('start_time')}")
                            print(f"    duration: {track.get('duration')}")
                            print(f"    narration_text: {track.get('narration_text', '')[:50]}...")
                            print(f"    environment_keywords: {track.get('environment_keywords')}")
                            print(f"    has_environment: {track.get('has_environment')}")
                            print(f"    chapter_number: {track.get('chapter_number')}")
                            print(f"    chapter_id: {track.get('chapter_id')}")
                        
                        # 检查时间范围
                        if tracks:
                            start_times = [track.get('start_time', 0) for track in tracks]
                            end_times = [track.get('start_time', 0) + track.get('duration', 0) for track in tracks]
                            print(f"\n时间范围: {min(start_times):.1f}s - {max(end_times):.1f}s")
                            print(f"总时长: {max(end_times):.1f}s")
                        
                    else:
                        print("\n❌ 项目85没有environment_tracks字段")
                else:
                    print("\n❌ 项目85没有analysis_result字段")
            else:
                print("❌ 项目85没有data字段")
        else:
            print(f"❌ 项目85详情API失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 检查项目85详情失败: {e}")

if __name__ == "__main__":
    print("=== 详细检查项目85 ===")
    check_project_85_detailed()