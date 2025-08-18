#!/usr/bin/env python3
"""
创建新环境项目并测试持久化
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"

def create_new_project():
    """创建新的环境项目"""
    body = {
        "name": "古玉2环境音测试项目",
        "description": "测试环境音分析持久化功能",
        "book_id": 58
    }
    
    print("🔧 创建新环境项目...")
    r = requests.post(f"{BASE_URL}/api/v1/environment-generation/projects", json=body)
    
    if r.status_code != 200:
        print(f"❌ 创建项目失败: {r.status_code} {r.text}")
        return None
    
    resp = r.json()
    project_id = resp.get('data', {}).get('id')
    print(f"✅ 创建项目成功: ID={project_id}")
    return project_id

def analyze_chapter(project_id: int, chapter_id: int):
    """分析指定章节"""
    body = {
        "chapter_ids": [chapter_id],
        "analysis_options": {
            "existing_project_id": project_id,
            "force_reanalyze": True
        }
    }
    
    print(f"🔍 分析章节 {chapter_id}...")
    r = requests.post(f"{BASE_URL}/api/v1/environment-generation/chapters/analyze", json=body)
    
    if r.status_code != 200:
        print(f"❌ 分析失败: {r.status_code} {r.text}")
        return None
    
    resp = r.json()
    tracks = resp.get("analysis_result", {}).get("environment_tracks", [])
    with_env = [t for t in tracks if t.get("environment_keywords")]
    
    print(f"✅ 分析完成: 轨道{len(tracks)}，含环境音{len(with_env)}")
    return {
        "tracks_total": len(tracks),
        "tracks_with_env": len(with_env),
        "sample_keywords": [t.get("environment_keywords") for t in with_env[:3]]
    }

def verify_persistence(project_id: int):
    """验证分析结果是否持久化到数据库"""
    print(f"🔍 验证项目 {project_id} 持久化...")
    
    r = requests.get(f"{BASE_URL}/api/v1/environment-generation/projects/{project_id}")
    
    if r.status_code != 200:
        print(f"❌ 获取项目详情失败: {r.status_code} {r.text}")
        return False
    
    resp = r.json()
    project_data = resp.get('data', {}).get('project', {})
    analysis_result = project_data.get('analysis_result', {})
    tracks = analysis_result.get('environment_tracks', [])
    
    print(f"📊 数据库中的轨道数量: {len(tracks)}")
    
    if len(tracks) > 0:
        print("✅ 持久化成功！")
        print(f"   第一个轨道: {tracks[0].get('environment_keywords', [])}")
        return True
    else:
        print("❌ 持久化失败！analysis_result为空")
        return False

def main():
    print("🧪 新项目持久化测试开始")
    
    # 1. 创建新项目
    project_id = create_new_project()
    if not project_id:
        return
    
    # 2. 分析第1章
    result = analyze_chapter(project_id, 836)
    if not result:
        return
    
    print(f"📊 分析结果: {result}")
    
    # 3. 等待一下确保数据库写入
    time.sleep(1)
    
    # 4. 验证持久化
    success = verify_persistence(project_id)
    
    print("\n" + "="*50)
    if success:
        print("🎉 测试成功：分析结果已正确持久化到数据库！")
    else:
        print("💥 测试失败：分析结果未持久化到数据库！")
    print("="*50)

if __name__ == "__main__":
    main()
