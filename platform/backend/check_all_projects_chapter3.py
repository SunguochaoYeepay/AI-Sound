#!/usr/bin/env python3
"""
检查所有环境音项目，看看哪个项目包含第三章的分析结果
"""

import requests
import json

def check_all_projects_chapter3():
    """检查所有环境音项目"""
    
    # 获取所有环境音项目
    projects_url = "http://localhost:8001/api/v1/environment-generation/projects"
    
    try:
        response = requests.get(projects_url)
        print(f"获取项目列表API状态码: {response.status_code}")
        
        if response.status_code == 200:
            projects_data = response.json()
            
            if 'data' in projects_data:
                projects_data_obj = projects_data['data']
                if 'projects' in projects_data_obj:
                    projects = projects_data_obj['projects']
                else:
                    projects = projects_data_obj
                
                print(f"\n找到 {len(projects)} 个环境音项目")
                
                # 检查每个项目
                for project in projects:
                    if isinstance(project, dict):
                        project_id = project.get('id')
                        project_name = project.get('name')
                        book_id = project.get('book_id')
                    else:
                        # 如果project是字符串或其他类型
                        project_id = project
                        project_name = str(project)
                        book_id = None
                    
                    print(f"\n检查项目 {project_id}: {project_name} (书籍ID: {book_id})")
                    
                    # 获取项目详情
                    detail_url = f"http://localhost:8001/api/v1/environment-generation/projects/{project_id}"
                    detail_response = requests.get(detail_url)
                    
                    if detail_response.status_code == 200:
                        detail_data = detail_response.json()
                        
                        if 'data' in detail_data:
                            data_obj = detail_data['data']
                            project_info = data_obj.get('project') or data_obj
                            
                            if 'analysis_result' in project_info:
                                analysis_result = project_info['analysis_result']
                                
                                if 'environment_tracks' in analysis_result:
                                    tracks = analysis_result['environment_tracks']
                                    print(f"  轨道总数: {len(tracks)}")
                                    
                                    # 检查是否有第三章的轨道
                                    chapter3_tracks = []
                                    for track in tracks:
                                        segment_id = track.get('segment_id')
                                        chapter_num = track.get('chapter_number') or track.get('chapter_id')
                                        
                                        # 根据segment_id或chapter_num判断是否为第三章
                                        if (isinstance(segment_id, str) and segment_id.startswith('3')) or \
                                           (isinstance(segment_id, int) and segment_id >= 20) or \
                                           chapter_num == 3:
                                            chapter3_tracks.append(track)
                                    
                                    if chapter3_tracks:
                                        print(f"  ✅ 找到第三章轨道: {len(chapter3_tracks)} 个")
                                        return project_id  # 找到包含第三章的项目
                                    else:
                                        print(f"  ❌ 没有第三章轨道")
                                else:
                                    print(f"  ❌ 没有environment_tracks字段")
                            else:
                                print(f"  ❌ 没有analysis_result字段")
                        else:
                            print(f"  ❌ 没有data字段")
                    else:
                        print(f"  ❌ 获取项目详情失败: {detail_response.status_code}")
                
                print(f"\n❌ 没有找到包含第三章分析结果的项目")
            else:
                print("❌ 没有data字段")
        else:
            print(f"❌ 获取项目列表失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 检查所有项目失败: {e}")

if __name__ == "__main__":
    print("=== 检查所有环境音项目的第三章分析结果 ===")
    check_all_projects_chapter3()