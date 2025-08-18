#!/usr/bin/env python3
"""
测试环境音项目删除和新增的修复效果
"""

import asyncio
import aiohttp
import json

API_BASE = "http://localhost:8001"
BOOK_ID = 58
CHAPTER_IDS = [836, 837, 838]

async def test_environment_fix():
    async with aiohttp.ClientSession() as session:
        print("=== 测试环境音项目删除和新增修复效果 ===")
        
        # 1. 检查当前环境音项目
        print("\n1. 检查当前环境音项目...")
        projects_url = f"{API_BASE}/api/v1/environment-generation/projects"
        async with session.get(projects_url) as resp:
            print(f"GET {projects_url} -> {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                projects = data.get("data", {}).get("data", {}).get("projects", [])
                print(f"当前环境音项目数量: {len(projects)}")
                for project in projects:
                    if project.get("book_id") == BOOK_ID:
                        print(f"  项目ID: {project['id']}, 状态: {project['status']}, 创建时间: {project['created_at']}")
        
        # 2. 删除一个环境音项目
        print("\n2. 删除一个环境音项目...")
        if projects:
            project_to_delete = projects[0]['id']
            delete_url = f"{API_BASE}/api/v1/environment-generation/projects/{project_to_delete}"
            async with session.delete(delete_url) as resp:
                print(f"DELETE {delete_url} -> {resp.status}")
                if resp.status == 200:
                    result = await resp.json()
                    print(f"删除结果: {result.get('message', '')}")
                else:
                    print(f"删除失败: {resp.status}")
        
        # 3. 重新分析环境音（新增项目）
        print("\n3. 重新分析环境音（新增项目）...")
        analyze_url = f"{API_BASE}/api/v1/environment-generation/chapters/analyze"
        analyze_data = {
            "chapter_ids": CHAPTER_IDS,
            "analysis_options": {
                "create_project": True,
                "force_reanalyze": True
            }
        }
        
        async with session.post(analyze_url, json=analyze_data) as resp:
            print(f"POST {analyze_url} -> {resp.status}")
            if resp.status == 200:
                result = await resp.json()
                print(f"分析结果: {result.get('message', '')}")
                print(f"项目ID: {result.get('project_id', 'N/A')}")
                
                # 检查分析结果
                analysis_result = result.get('analysis_result', {})
                if isinstance(analysis_result, dict):
                    for chapter_id, chapter_data in analysis_result.items():
                        if isinstance(chapter_data, dict):
                            tracks = chapter_data.get('environment_tracks', [])
                            print(f"  章节{chapter_id}: {len(tracks)}个环境音轨道")
                            for i, track in enumerate(tracks[:2], 1):  # 只显示前2个轨道
                                keywords = track.get('environment_keywords', [])
                                duration = track.get('duration', 0)
                                print(f"    轨道{i}: {keywords}, 时长: {duration:.2f}s")
            else:
                error_text = await resp.text()
                print(f"分析失败: {resp.status}, {error_text}")
        
        # 4. 再次检查环境音项目
        print("\n4. 再次检查环境音项目...")
        async with session.get(projects_url) as resp:
            print(f"GET {projects_url} -> {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                projects = data.get("data", {}).get("data", {}).get("projects", [])
                print(f"当前环境音项目数量: {len(projects)}")
                for project in projects:
                    if project.get("book_id") == BOOK_ID:
                        print(f"  项目ID: {project['id']}, 状态: {project['status']}, 创建时间: {project['created_at']}")
        
        print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_environment_fix())
