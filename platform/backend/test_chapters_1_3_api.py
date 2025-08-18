#!/usr/bin/env python3
"""
一次性测试：创建环境音项目并分析第1~3章，输出每章环境轨道统计
"""

import requests
import json

BASE_URL = "http://localhost:8001"
BOOK_ID = 58           # 古玉2
CHAPTERS = [836, 837, 838]  # 第1~3章


def create_project() -> int:
    payload = {
        "name": "古玉2环境音分析 自动测试",
        "description": "自动测试创建",
        "book_id": BOOK_ID
    }
    r = requests.post(f"{BASE_URL}/api/v1/environment-generation/projects", json=payload)
    r.raise_for_status()
    data = r.json()
    project_id = data.get("data", {}).get("id")
    if not project_id:
        raise RuntimeError(f"创建项目失败: {data}")
    return project_id


def analyze_chapter(project_id: int, chapter_id: int):
    body = {
        "chapter_ids": [chapter_id],
        "analysis_options": {
            "existing_project_id": project_id,
            "force_reanalyze": False
        }
    }
    r = requests.post(f"{BASE_URL}/api/v1/environment-generation/chapters/analyze", json=body)
    r.raise_for_status()
    resp = r.json()
    # 扁平后的返回：analysis_result.environment_tracks
    tracks = resp.get("analysis_result", {}).get("environment_tracks", [])
    with_env = [t for t in tracks if t.get("environment_keywords")] 
    return {
        "chapter_id": chapter_id,
        "tracks_total": len(tracks),
        "tracks_with_env": len(with_env),
        "keywords_samples": [t.get("environment_keywords") for t in with_env[:3]]
    }


def get_project_detail(project_id: int):
    r = requests.get(f"{BASE_URL}/api/v1/environment-generation/projects/{project_id}")
    r.raise_for_status()
    return r.json()


def main():
    print("🧪 开始1~3章环境音分析测试")
    project_id = create_project()
    print(f"✅ 新项目ID: {project_id}")

    results = []
    for cid in CHAPTERS:
        stat = analyze_chapter(project_id, cid)
        print(f"- 章节{cid}: 轨道{stat['tracks_total']}，含环境音{stat['tracks_with_env']}")
        results.append(stat)

    detail = get_project_detail(project_id)
    total_tracks = len(detail.get("data", {}).get("project", {}).get("analysis_result", {}).get("environment_tracks", []))

    print("\n📊 汇总")
    print(json.dumps({
        "project_id": project_id,
        "per_chapter": results,
        "project_total_tracks": total_tracks
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
