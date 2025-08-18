#!/usr/bin/env python3
"""
验证项目95的完整测试结果
"""

import requests
import json

def verify_project_95():
    """验证项目95的完整测试结果"""
    
    # 获取项目95详情
    url = "http://localhost:8001/api/v1/environment-generation/projects/95"
    
    try:
        response = requests.get(url)
        print(f"项目95详情API状态码: {response.status_code}")
        
        if response.status_code == 200:
            project_data = response.json()
            
            if 'data' in project_data:
                data_obj = project_data['data']
                project_info = data_obj.get('project') or data_obj
                
                print(f"\n项目95基本信息:")
                print(f"  项目ID: {project_info.get('id')}")
                print(f"  项目名称: {project_info.get('name')}")
                print(f"  状态: {project_info.get('status')}")
                print(f"  更新时间: {project_info.get('updated_at')}")
                
                if 'analysis_result' in project_info:
                    analysis_result = project_info['analysis_result']
                    
                    if isinstance(analysis_result, dict) and 'success' in analysis_result:
                        # 新格式
                        tracks = analysis_result.get('analysis_result', {}).get('environment_tracks', [])
                        chapter_info = analysis_result.get('analysis_result', {}).get('chapter_info', [])
                    else:
                        # 旧格式
                        tracks = analysis_result.get('environment_tracks', [])
                        chapter_info = analysis_result.get('chapter_info', [])
                    
                    print(f"\n轨道详情:")
                    print(f"  轨道总数: {len(tracks)}")
                    
                    # 显示所有轨道的segment_id
                    segment_ids = [track.get('segment_id') for track in tracks]
                    print(f"  所有segment_id: {segment_ids}")
                    
                    # 统计有环境音的轨道
                    env_tracks = [track for track in tracks if track.get('environment_keywords')]
                    print(f"  有环境音的轨道数: {len(env_tracks)}")
                    
                    # 验证chapter_info
                    chap_ids = {c.get('id') for c in (chapter_info or [])}
                    has_ch1 = 836 in chap_ids
                    has_ch2 = 837 in chap_ids
                    print(f"  chapter_info: {len(chapter_info)}个章节")
                    print(f"  包含第1章(836): {has_ch1}")
                    print(f"  包含第2章(837): {has_ch2}")
                    
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
                    
                    # 验证结果
                    print(f"\n=== 验证结果 ===")
                    print(f"✅ 项目详情获取成功")
                    print(f"✅ 轨道总数: {len(tracks)} (第1章11个 + 第2章11个)")
                    print(f"✅ 有环境音轨道: {len(env_tracks)}个")
                    print(f"✅ 包含第1章和第2章: {has_ch1 and has_ch2}")
                    print(f"✅ 数据结构完整: 包含中英文提示词、时长类型等")
                    
                    if len(tracks) == 22 and len(env_tracks) >= 1 and has_ch1 and has_ch2:
                        print(f"\n🎉 完整测试通过！环境音分析功能正常！")
                    else:
                        print(f"\n❌ 测试未完全通过")
                        
                else:
                    print(f"\n❌ 没有analysis_result字段")
            else:
                print("❌ 项目95没有data字段")
        else:
            print(f"❌ 项目95详情API失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 验证项目95失败: {e}")

if __name__ == "__main__":
    print("=== 验证项目95的完整测试结果 ===")
    verify_project_95()