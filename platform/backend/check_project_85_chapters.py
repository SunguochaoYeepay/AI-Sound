#!/usr/bin/env python3
"""
检查项目85关联的章节信息
"""

import requests
import json

def check_project_85_chapters():
    """检查项目85关联的章节信息"""
    
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
                print(f"  书籍名称: {project_info.get('book_name')}")
                print(f"  章节ID: {project_info.get('chapter_ids')}")
                print(f"  章节名称: {project_info.get('chapter_name')}")
                print(f"  状态: {project_info.get('status')}")
                
                # 检查分析结果中的章节信息
                if 'analysis_result' in project_info:
                    analysis_result = project_info['analysis_result']
                    
                    if 'environment_tracks' in analysis_result:
                        tracks = analysis_result['environment_tracks']
                        print(f"\n分析结果信息:")
                        print(f"  轨道总数: {len(tracks)}")
                        
                        # 统计各章节的轨道
                        chapter_tracks = {}
                        for track in tracks:
                            segment_id = track.get('segment_id')
                            if segment_id not in chapter_tracks:
                                chapter_tracks[segment_id] = 0
                            chapter_tracks[segment_id] += 1
                        
                        print(f"  各段落轨道数量: {dict(list(chapter_tracks.items())[:10])}")  # 只显示前10个
                        
                    else:
                        print("\n❌ 项目85没有environment_tracks字段")
                else:
                    print("\n❌ 项目85没有analysis_result字段")
            else:
                print("❌ 项目85没有data字段")
        else:
            print(f"❌ 项目85详情API失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 检查项目85章节信息失败: {e}")

if __name__ == "__main__":
    print("=== 检查项目85章节信息 ===")
    check_project_85_chapters()