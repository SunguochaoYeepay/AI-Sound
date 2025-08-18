#!/usr/bin/env python3
"""
检查项目85第三章的环境音分析结果
"""

import requests
import json

def check_project_85_chapter3():
    """检查项目85第三章的环境音分析结果"""
    
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
                
                if 'analysis_result' in project_info:
                    analysis_result = project_info['analysis_result']
                    
                    if 'environment_tracks' in analysis_result:
                        tracks = analysis_result['environment_tracks']
                        print(f"\n项目85环境音轨道总数: {len(tracks)}")
                        
                        # 查找第三章的轨道
                        chapter3_tracks = []
                        for track in tracks:
                            # 根据segment_id判断章节（假设第三章的segment_id从某个范围开始）
                            segment_id = track.get('segment_id')
                            if isinstance(segment_id, str) and segment_id.startswith('3'):
                                chapter3_tracks.append(track)
                            elif isinstance(segment_id, int) and segment_id >= 20:  # 假设第三章从第20个段落开始
                                chapter3_tracks.append(track)
                        
                        print(f"第三章轨道数量: {len(chapter3_tracks)}")
                        
                        if chapter3_tracks:
                            print("\n第三章轨道详情:") 
                            for i, track in enumerate(chapter3_tracks[:3]):  # 只显示前3个
                                print(f"  轨道{i+1}: segment_id={track.get('segment_id')}, keywords={track.get('environment_keywords')}, has_environment={track.get('has_environment')}")
                        else:
                            print("\n❌ 未找到第三章的轨道数据")
                            
                        # 显示所有轨道的segment_id分布
                        segment_ids = [track.get('segment_id') for track in tracks]
                        print(f"\n所有轨道的segment_id分布: {segment_ids[:10]}...")  # 只显示前10个
                        
                    else:
                        print("❌ 项目85没有environment_tracks字段")
                else:
                    print("❌ 项目85没有analysis_result字段")
            else:
                print("❌ 项目85没有data字段")
        else:
            print(f"❌ 项目85详情API失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 检查项目85第三章失败: {e}")

if __name__ == "__main__":
    print("=== 检查项目85第三章环境音分析结果 ===")
    check_project_85_chapter3()