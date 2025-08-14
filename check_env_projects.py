#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models.environment_generation import EnvironmentProject

def check_environment_projects():
    """查看环境音项目详情"""
    print("🔍 环境音项目状态分析")
    print("=" * 50)
    
    db = next(get_db())
    
    try:
        # 获取所有环境音项目
        projects = db.query(EnvironmentProject).all()
        
        print(f"📊 环境音项目总数: {len(projects)}")
        print()
        
        if not projects:
            print("❌ 没有找到任何环境音项目")
            return
        
        for i, project in enumerate(projects, 1):
            print(f"📋 项目 {i}:")
            print(f"   ID: {project.id}")
            print(f"   名称: {project.name}")
            print(f"   状态: {project.status}")
            print(f"   书籍: {project.book_name}")
            print(f"   章节: {project.chapter_name}")
            print(f"   分析轨道数: {project.analysis_tracks}")
            print(f"   生成数量: {project.generation_count}")
            print(f"   匹配数量: {project.matched_count}")
            print(f"   创建时间: {project.created_at}")
            print(f"   更新时间: {project.updated_at}")
            
            # 分析结果
            if project.analysis_result:
                print(f"   📈 分析结果:")
                analysis = project.analysis_result
                if isinstance(analysis, dict):
                    if 'environment_tracks' in analysis:
                        tracks = analysis['environment_tracks']
                        print(f"      环境音轨道数: {len(tracks) if isinstance(tracks, list) else '未知'}")
                    if 'analysis_stats' in analysis:
                        stats = analysis['analysis_stats']
                        print(f"      分析统计: {stats}")
                else:
                    print(f"      分析结果类型: {type(analysis)}")
            else:
                print(f"   ❌ 无分析结果")
            
            # 匹配结果
            if project.matching_result:
                print(f"   🎯 匹配结果:")
                matching = project.matching_result
                if isinstance(matching, dict):
                    if 'analysis_stats' in matching:
                        stats = matching['analysis_stats']
                        print(f"      匹配统计: {stats}")
                    if 'session_stage' in matching:
                        print(f"      会话阶段: {matching['session_stage']}")
                else:
                    print(f"      匹配结果类型: {type(matching)}")
            else:
                print(f"   ❌ 无匹配结果")
            
            print("-" * 50)
        
        # 统计状态分布
        status_counts = {}
        for project in projects:
            status = project.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("📊 状态分布统计:")
        for status, count in status_counts.items():
            print(f"   {status}: {count} 个项目")
        
        print()
        print("✅ 环境音项目分析完成")
        
    except Exception as e:
        print(f"❌ 查询失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_environment_projects()
