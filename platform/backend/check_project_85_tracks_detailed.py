#!/usr/bin/env python3
"""
详细检查项目85的轨道信息
"""

import requests
import json

def check_project_85_tracks_detailed():
    """详细检查项目85的轨道信息"""
    
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
                print(f"  更新时间: {project_info.get('updated_at')}")
                
                if 'analysis_result' in project_info:
                    analysis_result = project_info['analysis_result']
                    tracks = analysis_result.get('environment_tracks', [])
                    print(f"\n轨道详情:")
                    print(f"  轨道总数: {len(tracks)}")
                    
                    # 显示所有轨道的segment_id
                    segment_ids = [track.get('segment_id') for track in tracks]
                    print(f"  所有segment_id: {segment_ids}")
                    
                    # 检查是否有新的轨道（segment_id > 24）
                    new_tracks = [track for track in tracks if track.get('segment_id', 0) > 24]
                    print(f"  新轨道数量: {len(new_tracks)}")
                    
                    if new_tracks:
                        print(f"\n新轨道详情:")
                        for i, track in enumerate(new_tracks[:3]):  # 只显示前3个
                            print(f"  新轨道{i+1}:")
                            print(f"    segment_id: {track.get('segment_id')}")
                            print(f"    narration_text: {track.get('narration_text', '')[:50]}...")
                            print(f"    environment_keywords: {track.get('environment_keywords')}")
                    else:
                        print(f"\n❌ 没有找到新轨道")
                        
                        # 显示最后几个轨道的segment_id
                        if tracks:
                            last_tracks = tracks[-5:]
                            print(f"\n最后5个轨道:")
                            for track in last_tracks:
                                print(f"  segment_id: {track.get('segment_id')}, keywords: {track.get('environment_keywords')}")
                else:
                    print(f"\n❌ 没有analysis_result字段")
            else:
                print("❌ 项目85没有data字段")
        else:
            print(f"❌ 项目85详情API失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 检查项目85轨道详情失败: {e}")

if __name__ == "__main__":
    print("=== 详细检查项目85的轨道信息 ===")
    check_project_85_tracks_detailed()