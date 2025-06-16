#!/usr/bin/env python3
"""
测试基于选中章节的智能分析功能
"""
import requests
import json

# 配置
BASE_URL = "http://localhost:8000"
PROJECT_ID = 22

def test_intelligent_analysis_with_chapters():
    """测试基于选中章节的智能分析"""
    
    print("=== 测试基于选中章节的智能分析 ===")
    
    # 1. 首先获取项目的章节列表
    print("\n1. 获取项目章节列表...")
    try:
        # 先获取项目详情，找到关联的书籍
        project_response = requests.get(f"{BASE_URL}/api/v1/novel-reader/projects/{PROJECT_ID}")
        if project_response.status_code == 200:
            project_data = project_response.json()
            if project_data.get('success') and project_data.get('data', {}).get('book'):
                book_id = project_data['data']['book']['id']
                print(f"项目关联的书籍ID: {book_id}")
                
                # 获取书籍的章节列表
                chapters_response = requests.get(f"{BASE_URL}/api/v1/books/{book_id}/chapters")
                if chapters_response.status_code == 200:
                    chapters_data = chapters_response.json()
                    if chapters_data.get('success'):
                        chapters = chapters_data.get('data', [])
                        print(f"找到 {len(chapters)} 个章节")
                        
                        # 显示前几个章节
                        for i, chapter in enumerate(chapters[:5]):
                            print(f"  章节{i+1}: ID={chapter['id']}, 第{chapter['chapter_number']}章 - {chapter.get('chapter_title', '未命名')}")
                        
                        if len(chapters) >= 2:
                            # 选择前两个章节进行测试
                            selected_chapter_ids = [chapters[0]['id'], chapters[1]['id']]
                            print(f"\n选择章节进行分析: {selected_chapter_ids}")
                            
                            # 2. 测试基于选中章节的智能分析
                            print("\n2. 执行基于选中章节的智能分析...")
                            analysis_params = {
                                "chapter_ids": selected_chapter_ids
                            }
                            
                            analysis_response = requests.post(
                                f"{BASE_URL}/api/v1/intelligent-analysis/analyze/{PROJECT_ID}",
                                json=analysis_params
                            )
                            
                            print(f"分析请求状态码: {analysis_response.status_code}")
                            
                            if analysis_response.status_code == 200:
                                result = analysis_response.json()
                                print(f"分析成功: {result.get('success')}")
                                print(f"消息: {result.get('message')}")
                                print(f"数据源: {result.get('source')}")
                                
                                if result.get('success') and result.get('data'):
                                    data = result['data']
                                    print(f"\n分析结果统计:")
                                    print(f"  - 角色数量: {len(data.get('characters', []))}")
                                    print(f"  - 合成段落: {len(data.get('synthesis_plan', []))}")
                                    
                                    # 显示角色信息
                                    characters = data.get('characters', [])
                                    if characters:
                                        print(f"\n检测到的角色:")
                                        for char in characters[:5]:
                                            print(f"  - {char.get('name')}: 声音ID={char.get('voice_id')}, 声音名={char.get('voice_name')}")
                                    
                                    # 显示合成计划示例
                                    synthesis_plan = data.get('synthesis_plan', [])
                                    if synthesis_plan:
                                        print(f"\n合成计划示例 (前3个):")
                                        for segment in synthesis_plan[:3]:
                                            print(f"  段落{segment.get('segment_id')}: {segment.get('speaker')} - {segment.get('text', '')[:50]}...")
                                    
                                    # 检查章节映射
                                    chapter_mapping = data.get('chapter_mapping', {})
                                    if chapter_mapping:
                                        print(f"\n章节映射:")
                                        for chapter_id, chapter_info in chapter_mapping.items():
                                            print(f"  章节{chapter_id}: 第{chapter_info.get('chapter_number')}章 - {chapter_info.get('chapter_title')}")
                                    
                                    print("\n✅ 基于选中章节的智能分析测试成功！")
                                    return True
                                else:
                                    print(f"❌ 分析失败: {result.get('message')}")
                                    if result.get('data', {}).get('status') == 'pending_analysis':
                                        pending_chapters = result['data'].get('pending_chapter_list', [])
                                        print(f"待分析章节数量: {len(pending_chapters)}")
                                        for ch in pending_chapters[:3]:
                                            print(f"  - 第{ch.get('chapter_number')}章: {ch.get('chapter_title')}")
                            else:
                                print(f"❌ 分析请求失败: {analysis_response.text}")
                        else:
                            print("❌ 章节数量不足，无法进行测试")
                    else:
                        print(f"❌ 获取章节失败: {chapters_data.get('message')}")
                else:
                    print(f"❌ 获取章节请求失败: {chapters_response.status_code}")
            else:
                print(f"❌ 项目未关联书籍或获取项目失败: {project_data}")
        else:
            print(f"❌ 获取项目详情失败: {project_response.status_code}")
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {str(e)}")
        return False
    
    # 3. 测试不指定章节的分析（应该分析所有章节）
    print("\n3. 测试不指定章节的智能分析（分析所有章节）...")
    try:
        analysis_response = requests.post(f"{BASE_URL}/api/v1/intelligent-analysis/analyze/{PROJECT_ID}")
        print(f"全章节分析状态码: {analysis_response.status_code}")
        
        if analysis_response.status_code == 200:
            result = analysis_response.json()
            print(f"全章节分析成功: {result.get('success')}")
            if result.get('success') and result.get('data'):
                data = result['data']
                print(f"全章节分析结果: {len(data.get('characters', []))} 个角色, {len(data.get('synthesis_plan', []))} 个段落")
        else:
            print(f"全章节分析失败: {analysis_response.text}")
    except Exception as e:
        print(f"全章节分析异常: {str(e)}")
    
    return False

if __name__ == "__main__":
    test_intelligent_analysis_with_chapters() 