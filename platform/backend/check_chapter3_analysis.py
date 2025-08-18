#!/usr/bin/env python3
"""
检查第三章的分析结果
"""

import requests
import json

def check_chapter3_analysis():
    """检查第三章的分析结果"""
    
    # 检查第三章的分析结果
    analysis_url = "http://localhost:8001/api/v1/books/58/analysis-results"
    
    try:
        response = requests.get(analysis_url)
        print(f"分析结果API状态码: {response.status_code}")
        
        if response.status_code == 200:
            analysis_data = response.json()
            
            if 'data' in analysis_data:
                results = analysis_data['data']
                
                # 查找第三章的分析结果
                chapter3_result = None
                for result in results:
                    if result.get('chapter_id') == 838:
                        chapter3_result = result
                        break
                
                if chapter3_result:
                    print(f"\n第三章分析结果:")
                    print(f"  章节ID: {chapter3_result.get('chapter_id')}")
                    print(f"  章节标题: {chapter3_result.get('chapter_title')}")
                    print(f"  分析ID: {chapter3_result.get('analysis_id')}")
                    
                    synthesis_json = chapter3_result.get('synthesis_json', {})
                    synthesis_plan = synthesis_json.get('synthesis_plan', [])
                    print(f"  合成计划段落数: {len(synthesis_plan)}")
                    
                    if synthesis_plan:
                        print(f"\n前3个段落:")
                        for i, segment in enumerate(synthesis_plan[:3]):
                            print(f"  段落{i+1}:")
                            print(f"    text: {segment.get('text', '')[:50]}...")
                            print(f"    speaker: {segment.get('speaker')}")
                            print(f"    text_type: {segment.get('text_type')}")
                    else:
                        print(f"\n❌ 合成计划为空！")
                else:
                    print(f"\n❌ 未找到第三章的分析结果")
            else:
                print("❌ 没有data字段")
        else:
            print(f"❌ 分析结果API失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 检查第三章分析结果失败: {e}")

if __name__ == "__main__":
    print("=== 检查第三章的分析结果 ===")
    check_chapter3_analysis()