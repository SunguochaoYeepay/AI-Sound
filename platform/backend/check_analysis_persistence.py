#!/usr/bin/env python3
"""
检查分析结果持久化问题
"""

import requests
import json

def check_analysis_persistence():
    """检查分析结果持久化问题"""
    
    # 1. 检查项目85当前状态
    project_url = "http://localhost:8001/api/v1/environment-generation/projects/85"
    
    try:
        response = requests.get(project_url)
        print(f"项目85详情API状态码: {response.status_code}")
        
        if response.status_code == 200:
            project_data = response.json()
            
            if 'data' in project_data:
                data_obj = project_data['data']
                project_info = data_obj.get('project') or data_obj
                
                print(f"\n项目85当前状态:")
                print(f"  项目ID: {project_info.get('id')}")
                print(f"  项目名称: {project_info.get('name')}")
                print(f"  更新时间: {project_info.get('updated_at')}")
                
                if 'analysis_result' in project_info:
                    analysis_result = project_info['analysis_result']
                    tracks = analysis_result.get('environment_tracks', [])
                    print(f"  当前轨道数: {len(tracks)}")
                    
                    # 检查是否有第三章的轨道
                    chapter3_tracks = []
                    for track in tracks:
                        segment_id = track.get('segment_id')
                        if isinstance(segment_id, int) and segment_id > 20:  # 假设第三章从第20个段落开始
                            chapter3_tracks.append(track)
                    
                    print(f"  第三章轨道数: {len(chapter3_tracks)}")
                    
                    if chapter3_tracks:
                        print(f"  ✅ 第三章分析结果已保存")
                    else:
                        print(f"  ❌ 第三章分析结果未保存")
                else:
                    print(f"  ❌ 没有analysis_result字段")
            else:
                print("❌ 项目85没有data字段")
        else:
            print(f"❌ 项目85详情API失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 检查项目85失败: {e}")

if __name__ == "__main__":
    print("=== 检查分析结果持久化问题 ===")
    check_analysis_persistence()