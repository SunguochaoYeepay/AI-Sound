#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models import AnalysisResult

def check_analysis_results():
    """检查分析结果表"""
    print("🔍 检查分析结果表")
    print("=" * 50)
    
    db = next(get_db())
    
    try:
        # 查询所有分析结果
        results = db.query(AnalysisResult).order_by(AnalysisResult.created_at.desc()).all()
        
        print(f"📊 分析结果总数: {len(results)}")
        print()
        
        for i, result in enumerate(results, 1):
            print(f"📋 分析结果 {i}:")
            print(f"   ID: {result.id}")
            print(f"   创建时间: {result.created_at}")
            
            # 检查结果内容
            if result.result:
                try:
                    result_data = json.loads(result.result)
                    print(f"   ✅ 有结果数据")
                    
                    # 检查是否包含环境音轨道
                    if 'environment_tracks' in result_data:
                        tracks = result_data['environment_tracks']
                        print(f"   环境音轨道数: {len(tracks)}")
                        
                        for j, track in enumerate(tracks, 1):
                            keywords = track.get('environment_keywords', [])
                            start_time = track.get('start_time', 0)
                            end_time = track.get('end_time', 0)
                            print(f"     轨道{j}: {keywords} ({start_time:.1f}-{end_time:.1f}秒)")
                    
                    # 检查章节信息
                    if 'chapter_info' in result_data:
                        chapter_info = result_data['chapter_info']
                        if chapter_info and len(chapter_info) > 0:
                            chapter_title = chapter_info[0].get('title', '未知标题')
                            print(f"   章节标题: {chapter_title}")
                    
                except json.JSONDecodeError:
                    print(f"   ❌ 结果数据格式错误")
            else:
                print(f"   ❌ 无结果数据")
            
            print("-" * 30)
        
        print("✅ 分析结果检查完成")
        
    except Exception as e:
        print(f"❌ 查询失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_analysis_results()
