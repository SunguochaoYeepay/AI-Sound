#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.analysis_result import AnalysisResult
from app.database import get_db
import json

def debug_chapter_703():
    """调试章节703的分析结果"""
    db = next(get_db())
    
    try:
        # 查找章节703的分析结果
        result = db.query(AnalysisResult).filter(AnalysisResult.chapter_id == 703).first()
        
        if not result:
            print("❌ 未找到章节703的分析结果")
            return
        
        print(f"✅ 找到章节703的分析结果，ID: {result.id}")
        print(f"创建时间: {result.created_at}")
        print(f"状态: {result.status}")
        
        # 检查原始数据字段
        print("\n🔍 检查原始数据字段:")
        print(f"synthesis_plan 是否存在: {result.synthesis_plan is not None}")
        print(f"final_config 是否存在: {result.final_config is not None}")
        # print(f"detection_result 是否存在: {result.detection_result is not None}")  # 该字段不存在
        
        # 检查 synthesis_plan 详细结构
        if result.synthesis_plan:
            print(f"\n📋 synthesis_plan 类型: {type(result.synthesis_plan)}")
            if isinstance(result.synthesis_plan, dict):
                print(f"synthesis_plan 键: {list(result.synthesis_plan.keys())}")
                
                # 检查是否有segments
                if 'segments' in result.synthesis_plan:
                    segments = result.synthesis_plan['segments']
                    print(f"synthesis_plan.segments 长度: {len(segments) if segments else 0}")
                
                # 检查是否有synthesis_plan嵌套结构
                if 'synthesis_plan' in result.synthesis_plan:
                    nested_plan = result.synthesis_plan['synthesis_plan']
                    print(f"嵌套 synthesis_plan 键: {list(nested_plan.keys()) if isinstance(nested_plan, dict) else 'Not a dict'}")
                    
                    # 检查嵌套计划中的 segments
                    if isinstance(nested_plan, dict) and 'segments' in nested_plan:
                        segments = nested_plan['segments']
                        print(f"🎯 在嵌套 synthesis_plan 中找到 segments: {len(segments)} 个")
                        
                        # 显示前3个段落
                        for i, segment in enumerate(segments[:3]):
                            print(f"\n段落 {i+1}:")
                            print(f"  文本: {segment.get('text', '')[:80]}...")
                            print(f"  类型: {segment.get('text_type', 'unknown')}")
                            print(f"  长度: {len(segment.get('text', ''))}")
            else:
                print(f"synthesis_plan 内容预览: {str(result.synthesis_plan)[:200]}...")
        
        # 检查 final_config
        if result.final_config:
            print(f"\n⚙️ final_config 类型: {type(result.final_config)}")
            if isinstance(result.final_config, str):
                try:
                    final_config_data = json.loads(result.final_config)
                    print(f"final_config JSON 键: {list(final_config_data.keys())}")
                    
                    if 'synthesis_json' in final_config_data:
                        synthesis_json = final_config_data['synthesis_json']
                        print(f"synthesis_json 键: {list(synthesis_json.keys()) if isinstance(synthesis_json, dict) else 'Not a dict'}")
                        
                        # 检查 synthesis_json 中的 segments
                        if isinstance(synthesis_json, dict) and 'segments' in synthesis_json:
                            segments = synthesis_json['segments']
                            print(f"🎯 在 synthesis_json 中找到 segments: {len(segments)} 个")
                        
                        if isinstance(synthesis_json, dict) and 'synthesis_plan' in synthesis_json:
                            plan = synthesis_json['synthesis_plan']
                            print(f"final_config.synthesis_json.synthesis_plan 长度: {len(plan) if plan else 0}")
                            
                            if plan and len(plan) > 0:
                                print(f"\n📝 第一个段落示例:")
                                first_segment = plan[0]
                                print(f"  类型: {first_segment.get('text_type', 'unknown')}")
                                print(f"  文本: {first_segment.get('text', '')[:100]}...")
                                print(f"  说话人: {first_segment.get('speaker', '')}")
                                
                except json.JSONDecodeError as e:
                    print(f"final_config JSON 解析失败: {e}")
            elif isinstance(result.final_config, dict):
                print(f"final_config 键: {list(result.final_config.keys())}")
                
                # 检查 synthesis_json
                if 'synthesis_json' in result.final_config:
                    synthesis_json = result.final_config['synthesis_json']
                    print(f"synthesis_json 键: {list(synthesis_json.keys()) if isinstance(synthesis_json, dict) else 'Not a dict'}")
                    
                    # 检查 synthesis_json 中的 segments
                    if isinstance(synthesis_json, dict) and 'segments' in synthesis_json:
                        segments = synthesis_json['segments']
                        print(f"🎯 在 synthesis_json 中找到 segments: {len(segments)} 个")
            else:
                print(f"final_config 内容预览: {str(result.final_config)[:200]}...")
        
        # 使用 get_analysis_data() 方法
        print("\n🔄 使用 get_analysis_data() 方法:")
        data = result.get_analysis_data()
        
        if data:
            print(f"get_analysis_data() 返回键: {list(data.keys())}")
            segments = data.get('segments', [])
            print(f"直接从 'segments' 键获取的段落数: {len(segments)}")
            
            # 检查是否在 synthesis_plan 子键中
            synthesis_plan_segments = data.get('synthesis_plan', [])
            print(f"从 'synthesis_plan' 键获取的段落数: {len(synthesis_plan_segments)}")
            
            # 这是问题所在！图片生成服务期望 segments 字段，但数据在 synthesis_plan 字段中
            print("\n❌ 问题发现:")
            print(f"  图片生成服务期望: data.get('segments', [])")
            print(f"  实际数据位置: data.get('synthesis_plan', [])")
            
            if synthesis_plan_segments:
                print(f"\n📝 前3个段落 (从synthesis_plan获取):")
                for i, segment in enumerate(synthesis_plan_segments[:3]):
                    print(f"段落 {i+1}: {segment.get('text_type', 'unknown')} - {segment.get('text', '')[:50]}...")
                    
                # 模拟图片生成筛选逻辑
                print(f"\n🎨 模拟图片生成筛选:")
                suitable_count = 0
                for i, segment in enumerate(synthesis_plan_segments):
                    text = segment.get('text', '')
                    text_type = segment.get('text_type', 'dialogue')
                    
                    # 模拟 _is_segment_image_worthy 逻辑
                    if len(text) >= 10 and text_type in ['narrative', 'description', 'scene', 'narration']:
                        suitable_count += 1
                        if suitable_count <= 3:  # 只显示前3个
                            print(f"  ✅ 段落{i}: {text_type} - {text[:50]}...")
                            
                print(f"\n📊 筛选结果: {suitable_count}/{len(synthesis_plan_segments)} 个段落适合生成图片")
        else:
            print("get_analysis_data() 返回 None")
        
    except Exception as e:
        print(f"❌ 调试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_chapter_703()