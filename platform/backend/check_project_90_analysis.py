#!/usr/bin/env python3
"""
检查项目90的分析结果
"""

import requests
import json

def check_project_90_analysis():
    """检查项目90的分析结果"""
    
    # 检查项目90的详情
    project_url = "http://localhost:8001/api/v1/environment-generation/projects/90"
    
    try:
        response = requests.get(project_url)
        print(f"项目90详情API状态码: {response.status_code}")
        
        if response.status_code == 200:
            project_data = response.json()
            
            if 'data' in project_data:
                data_obj = project_data['data']
                project_info = data_obj.get('project') or data_obj
                
                print(f"\n项目90基本信息:")
                print(f"  项目ID: {project_info.get('id')}")
                print(f"  项目名称: {project_info.get('name')}")
                print(f"  状态: {project_info.get('status')}")
                print(f"  更新时间: {project_info.get('updated_at')}")
                
                if 'analysis_result' in project_info:
                    analysis_result = project_info['analysis_result']
                    
                    if isinstance(analysis_result, dict) and 'success' in analysis_result:
                        # 新格式
                        tracks = analysis_result.get('analysis_result', {}).get('environment_tracks', [])
                    else:
                        # 旧格式
                        tracks = analysis_result.get('environment_tracks', [])
                    
                    print(f"\n轨道详情:")
                    print(f"  轨道总数: {len(tracks)}")
                    
                    # 显示所有轨道的segment_id
                    segment_ids = [track.get('segment_id') for track in tracks]
                    print(f"  所有segment_id: {segment_ids}")
                    
                    # 统计有环境音的轨道
                    env_tracks = [track for track in tracks if track.get('environment_keywords')]
                    print(f"  有环境音的轨道数: {len(env_tracks)}")
                    
                    # 显示有环境音的轨道详情
                    if env_tracks:
                        print(f"\n有环境音的轨道详情:")
                        for i, track in enumerate(env_tracks):
                            print(f"  轨道{i+1}:")
                            print(f"    segment_id: {track.get('segment_id')}")
                            print(f"    start_time: {track.get('start_time')}")
                            print(f"    duration: {track.get('duration')}")
                            print(f"    narration_text: {track.get('narration_text', '')[:50]}...")
                            print(f"    environment_keywords: {track.get('environment_keywords')}")
                            print(f"    english_prompt: {track.get('english_prompt', '')[:50]}...")
                            print(f"    chinese_description: {track.get('chinese_description', '')[:50]}...")
                            print(f"    duration_type: {track.get('duration_type')}")
                    else:
                        print(f"\n❌ 没有找到有环境音的轨道")
                        
                        # 显示前3个轨道的详细信息
                        if tracks:
                            print(f"\n前3个轨道详情:")
                            for i, track in enumerate(tracks[:3]):
                                print(f"  轨道{i+1}:")
                                print(f"    segment_id: {track.get('segment_id')}")
                                print(f"    narration_text: {track.get('narration_text', '')[:50]}...")
                                print(f"    environment_keywords: {track.get('environment_keywords')}")
                else:
                    print(f"\n❌ 没有analysis_result字段")
            else:
                print("❌ 项目90没有data字段")
        else:
            print(f"❌ 项目90详情API失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 检查项目90分析结果失败: {e}")

if __name__ == "__main__":
    print("=== 检查项目90的分析结果 ===")
    check_project_90_analysis()