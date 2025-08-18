#!/usr/bin/env python3
"""
检查项目85的分析历史，看看第三章的分析结果是否丢失
"""

import requests
import json

def check_project_85_analysis_history():
    """检查项目85的分析历史"""
    
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
                print(f"  书籍ID: {project_info.get('book_id')}")
                print(f"  状态: {project_info.get('status')}")
                
                # 检查分析结果
                if 'analysis_result' in project_info:
                    analysis_result = project_info['analysis_result']
                    
                    if 'environment_tracks' in analysis_result:
                        tracks = analysis_result['environment_tracks']
                        print(f"\n当前分析结果:")
                        print(f"  轨道总数: {len(tracks)}")
                        
                        # 检查是否有章节信息
                        chapter_info = analysis_result.get('chapter_info', {})
                        print(f"  章节信息: {chapter_info}")
                        
                        # 检查分析元数据
                        metadata = analysis_result.get('analysis_metadata', {})
                        print(f"  分析元数据: {metadata}")
                        
                        # 检查是否有多个章节的轨道
                        chapter_tracks = {}
                        for track in tracks:
                            segment_id = track.get('segment_id')
                            chapter_num = track.get('chapter_number') or track.get('chapter_id') or 'unknown'
                            if chapter_num not in chapter_tracks:
                                chapter_tracks[chapter_num] = 0
                            chapter_tracks[chapter_num] += 1
                        
                        print(f"\n  各章节轨道数量: {chapter_tracks}")
                        
                        # 检查轨道的时间范围
                        if tracks:
                            start_times = [track.get('start_time', 0) for track in tracks]
                            end_times = [track.get('start_time', 0) + track.get('duration', 0) for track in tracks]
                            print(f"\n  时间范围: {min(start_times):.1f}s - {max(end_times):.1f}s")
                        
                    else:
                        print("\n❌ 项目85没有environment_tracks字段")
                else:
                    print("\n❌ 项目85没有analysis_result字段")
            else:
                print("❌ 项目85没有data字段")
        else:
            print(f"❌ 项目85详情API失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 检查项目85分析历史失败: {e}")

if __name__ == "__main__":
    print("=== 检查项目85分析历史 ===")
    check_project_85_analysis_history()