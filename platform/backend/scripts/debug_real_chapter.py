#!/usr/bin/env python3
"""
调试真实章节的synthesis_plan结构
"""

import sys
import os
import requests
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def debug_real_chapter():
    """调试真实章节的synthesis_plan结构"""
    print("🔍 调试真实章节的synthesis_plan结构")
    print("=" * 60)
    
    # API基础URL
    base_url = "http://localhost:8000"
    chapter_id = 836  # 第一章
    
    try:
        # 1. 获取章节的synthesis_plan
        print(f"📖 获取章节 {chapter_id} 的synthesis_plan...")
        url = f"{base_url}/api/v1/books/chapters/{chapter_id}/synthesis-plan"
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success') and data.get('synthesis_plan'):
                synthesis_plan = data['synthesis_plan']
                
                print(f"✅ 获取成功，共{len(synthesis_plan)}个段落")
                print()
                
                # 分析synthesis_plan结构
                narration_segments = []
                cumulative_time = 0.0
                
                for i, segment in enumerate(synthesis_plan):
                    speaker = segment.get('speaker', '')
                    character = segment.get('character', '')
                    text = segment.get('text', '') or segment.get('content', '')
                    
                    print(f"段落 {i+1}:")
                    print(f"  - Speaker: {speaker}")
                    print(f"  - Character: {character}")
                    print(f"  - 文本: {text[:100]}...")
                    
                    # 检查是否为旁白
                    narration_speakers = ['旁白', 'narrator', '叙述者', 'narration']
                    is_narration = speaker in narration_speakers or character in narration_speakers
                    
                    if is_narration:
                        print(f"  - 类型: 旁白段落")
                        narration_segments.append({
                            'segment_id': segment.get('segment_id') or f'seg_{i+1}',
                            'text': text,
                            'start_time': cumulative_time,
                            'duration': len(text) / 300 * 60,  # 估算时长
                            'end_time': cumulative_time + len(text) / 300 * 60
                        })
                    else:
                        print(f"  - 类型: 对话段落")
                    
                    # 累加时长
                    segment_duration = len(text) / 300 * 60  # 估算
                    cumulative_time += segment_duration
                    print(f"  - 估算时长: {segment_duration:.1f}秒")
                    print()
                
                print(f"📊 旁白段落统计:")
                print(f"  - 总段落数: {len(synthesis_plan)}")
                print(f"  - 旁白段落数: {len(narration_segments)}")
                print(f"  - 总时长: {cumulative_time:.1f}秒")
                print()
                
                # 2. 测试环境音分析
                print("🎵 测试环境音分析...")
                analyze_url = f"{base_url}/api/v1/environment-generation/chapters/analyze"
                
                test_request = {
                    "chapter_ids": [chapter_id],
                    "analysis_options": {
                        "mode": "auto",
                        "environment_types": ["nature", "urban", "indoor", "action"],
                        "precision": "medium",
                        "existing_project_id": 76,
                        "force_reanalyze": True
                    }
                }
                
                analyze_response = requests.post(analyze_url, json=test_request, timeout=30)
                
                if analyze_response.status_code == 200:
                    analyze_data = analyze_response.json()
                    
                    if analyze_data.get('success') and analyze_data.get('analysis_result'):
                        analysis_result = analyze_data['analysis_result']
                        tracks = analysis_result.get('environment_tracks', [])
                        
                        print(f"✅ 分析成功，识别{len(tracks)}个轨道")
                        print()
                        
                        for i, track in enumerate(tracks, 1):
                            print(f"轨道 {i}:")
                            print(f"  - 段落ID: {track.get('segment_id', 'N/A')}")
                            print(f"  - 关键词: {track.get('environment_keywords', [])}")
                            print(f"  - 时长: {track.get('duration', 0):.1f}秒")
                            print(f"  - 开始时间: {track.get('start_time', 0):.1f}秒")
                            print(f"  - 置信度: {track.get('confidence', 0):.2f}")
                            print(f"  - 映射策略: {track.get('mapping_strategy', 'N/A')}")
                            print(f"  - 旁白文本: {track.get('narration_text', '')[:100]}...")
                            print()
                        
                        # 对比分析
                        print("🔍 对比分析:")
                        print(f"  - 旁白段落数: {len(narration_segments)}")
                        print(f"  - 识别轨道数: {len(tracks)}")
                        
                        if len(tracks) != len(narration_segments):
                            print(f"  - ⚠️ 数量不匹配！可能的原因：")
                            print(f"    1. 某些旁白段落没有环境音")
                            print(f"    2. 映射逻辑有问题")
                            print(f"    3. LLM返回了空结果")
                        
                        # 检查段落ID匹配
                        narration_ids = [seg['segment_id'] for seg in narration_segments]
                        track_ids = [track.get('segment_id') for track in tracks]
                        
                        print(f"  - 旁白段落ID: {narration_ids}")
                        print(f"  - 轨道段落ID: {track_ids}")
                        
                        missing_ids = set(narration_ids) - set(track_ids)
                        if missing_ids:
                            print(f"  - ❌ 缺失的段落ID: {missing_ids}")
                        
                    else:
                        print(f"❌ 分析失败: {analyze_data.get('message', '未知错误')}")
                else:
                    print(f"❌ API调用失败: {analyze_response.status_code}")
                    print(f"错误响应: {analyze_response.text}")
            else:
                print(f"❌ 获取synthesis_plan失败: {data.get('message', '未知错误')}")
        else:
            print(f"❌ 获取章节失败: {response.status_code}")
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 调试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_real_chapter()
