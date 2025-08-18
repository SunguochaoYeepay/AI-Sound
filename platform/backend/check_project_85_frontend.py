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
            # 仅打印关键信息，避免输出过长
            if 'data' in project_data:
                data_obj = project_data['data']
                project_info = data_obj.get('project') or data_obj
                if 'analysis_result' in project_info:
                    analysis_result = project_info['analysis_result']
                    metadata = analysis_result.get('analysis_metadata', {})
                    print(f"track_count(all): {metadata.get('track_count')} total_duration: {metadata.get('total_duration')}")
                    
                    if 'environment_tracks' in analysis_result:
                        tracks = analysis_result['environment_tracks']
                        print(f"tracks(total): {len(tracks)}")
                        
                        # 统计有环境音的轨道
                        env_tracks = [t for t in tracks if t.get('environment_keywords')]
                        print(f"tracks(with_env): {len(env_tracks)}")
                        
                        # 统计瞬时与持续
                        instant = sum(1 for t in env_tracks if t.get('duration_type') == 'instant')
                        continuous = sum(1 for t in env_tracks if t.get('duration_type') == 'continuous')
                        print(f"instant: {instant} continuous: {continuous}")
                        
                        # 统计各章节（若有chapter_number字段）
                        chapter_tracks = {}
                        chapter_env_tracks = {}
                        for t in tracks:
                            chap = t.get('chapter_number') or t.get('chapter_title') or 'unknown'
                            chapter_tracks[chap] = chapter_tracks.get(chap, 0) + 1
                        for t in env_tracks:
                            chap = t.get('chapter_number') or t.get('chapter_title') or 'unknown'
                            chapter_env_tracks[chap] = chapter_env_tracks.get(chap, 0) + 1
                        print(f"by_chapter(all): {chapter_tracks}")
                        print(f"by_chapter(with_env): {chapter_env_tracks}")
                    else:
                        print("❌ 项目85没有environment_tracks字段")
                else:
                    print("❌ 项目85没有analysis_result字段")
            else:
                print("❌ 项目85没有data字段")
        else:
            print(f"❌ 项目85详情API失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 检查项目85失败: {e}")

if __name__ == "__main__":
    print("=== 检查项目85前端API响应 ===")
    check_project_85_frontend()