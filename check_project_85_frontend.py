#!/usr/bin/env python3
"""
检查项目85前端API响应
验证前端显示的环境音分析结果是否正确
"""

import requests
import json

def check_project_85_frontend():
    """检查项目85的前端API响应"""
    
    # 检查项目85的详情
    project_url = "http://localhost:8001/api/v1/environment-generation/projects/85"
    
    try:
        response = requests.get(project_url)
        print(f"项目85详情API状态码: {response.status_code}")
        
        if response.status_code == 200:
            project_data = response.json()
            print(f"项目85数据: {json.dumps(project_data, ensure_ascii=False, indent=2)}")
            
            # 检查分析结果
            if 'analysis_result' in project_data:
                analysis_result = project_data['analysis_result']
                if 'environment_tracks' in analysis_result:
                    tracks = analysis_result['environment_tracks']
                    print(f"\n项目85环境音轨道数量: {len(tracks)}")
                    
                    # 统计各章节的轨道数量
                    chapter_tracks = {}
                    for track in tracks:
                        chapter_num = track.get('chapter_number', 'unknown')
                        if chapter_num not in chapter_tracks:
                            chapter_tracks[chapter_num] = 0
                        chapter_tracks[chapter_num] += 1
                    
                    print(f"各章节轨道数量: {chapter_tracks}")
                    
                    # 统计有环境音的轨道
                    env_tracks = [t for t in tracks if t.get('environment_keywords', [])]
                    print(f"有环境音的轨道数量: {len(env_tracks)}")
                    
                    # 按章节统计有环境音的轨道
                    chapter_env_tracks = {}
                    for track in env_tracks:
                        chapter_num = track.get('chapter_number', 'unknown')
                        if chapter_num not in chapter_env_tracks:
                            chapter_env_tracks[chapter_num] = 0
                        chapter_env_tracks[chapter_num] += 1
                    
                    print(f"各章节有环境音的轨道数量: {chapter_env_tracks}")
                else:
                    print("❌ 项目85没有environment_tracks字段")
            else:
                print("❌ 项目85没有analysis_result字段")
        else:
            print(f"❌ 项目85详情API失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 检查项目85失败: {e}")

if __name__ == "__main__":
    print("=== 检查项目85前端API响应 ===")
    check_project_85_frontend()
