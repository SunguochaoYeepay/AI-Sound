#!/usr/bin/env python3
"""
在既有环境音项目上分析第1~3章并汇总结果（不创建新项目）
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8001"
PROJECT_ID = 100
CHAPTERS = [836, 837, 838]


def analyze_chapter(project_id: int, chapter_id: int):
    body = {
        "chapter_ids": [chapter_id],
        "analysis_options": {
            "existing_project_id": project_id,
            "force_reanalyze": True  # 🚨 强制重新分析
        }
    }
    r = requests.post(f"{BASE_URL}/api/v1/environment-generation/chapters/analyze", json=body)
    try:
        r.raise_for_status()
    except Exception:
        print(f"❌ 章节{chapter_id} 分析失败: {r.status_code} {r.text}")
        return {"chapter_id": chapter_id, "tracks_total": -1, "tracks_with_env": -1}
    resp = r.json()
    tracks = resp.get("analysis_result", {}).get("environment_tracks", [])
    with_env = [t for t in tracks if t.get("environment_keywords")] 
    return {
        "chapter_id": chapter_id,
        "tracks_total": len(tracks),
        "tracks_with_env": len(with_env),
        "sample_keywords": [t.get("environment_keywords") for t in with_env[:3]]
    }


def get_project_total_tracks(project_id: int) -> int:
    r = requests.get(f"{BASE_URL}/api/v1/environment-generation/projects/{project_id}")
    try:
        r.raise_for_status()
    except Exception:
        print(f"❌ 获取项目{project_id}详情失败: {r.status_code} {r.text}")
        return -1
    data = r.json()
    return len(data.get("data", {}).get("project", {}).get("analysis_result", {}).get("environment_tracks", []))


def main():
    print("🧪 在既有项目上测试 1~3 章：项目ID=", PROJECT_ID)
    results = []
    for cid in CHAPTERS:
        stat = analyze_chapter(PROJECT_ID, cid)
        print(f"- 章节{cid}: 轨道{stat['tracks_total']}，含环境音{stat['tracks_with_env']}")
        results.append(stat)
    total_tracks = get_project_total_tracks(PROJECT_ID)
    print("\n📊 汇总")
    print(json.dumps({
        "project_id": PROJECT_ID,
        "per_chapter": results,
        "project_total_tracks": total_tracks
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
