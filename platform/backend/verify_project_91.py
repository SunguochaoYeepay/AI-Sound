#!/usr/bin/env python3
"""
Verify environment analysis for project 91 via API only (no frontend):
- Fetch project details
- Summarize total tracks
- Count tracks with environment keywords
- Validate chapter_info includes chapters 836 and 837
"""
from __future__ import annotations
import requests
from typing import Any, Dict, List

API_BASE = "http://localhost:8001/api/v1/environment-generation"


def summarize_project(project_id: int) -> None:
    url = f"{API_BASE}/projects/{project_id}"
    resp = requests.get(url, timeout=20)
    print(f"GET {url} -> {resp.status_code}")
    if resp.status_code != 200:
        print(resp.text)
        return

    data = resp.json().get("data", {})
    project = data.get("project", {})
    print(f"Project: {project.get('id')} - {project.get('name')} | status: {project.get('status')}")

    analysis_result = project.get("analysis_result", {})

    # New format may wrap again under analysis_result
    if isinstance(analysis_result, dict) and "success" in analysis_result:
        tracks: List[Dict[str, Any]] = analysis_result.get("analysis_result", {}).get("environment_tracks", [])
        chapter_info: List[Dict[str, Any]] = analysis_result.get("analysis_result", {}).get("chapter_info", [])
    else:
        tracks = analysis_result.get("environment_tracks", [])
        chapter_info = analysis_result.get("chapter_info", [])

    print(f"Total tracks: {len(tracks)}")

    env_tracks = [t for t in tracks if t.get("environment_keywords")]  # non-empty keywords
    print(f"Tracks with environment sounds: {len(env_tracks)}")

    # Show small sample
    for i, t in enumerate(env_tracks[:3]):
        print(f"  #{i+1} seg={t.get('segment_id')} keywords={t.get('environment_keywords')} dur={t.get('duration')}")

    # Validate chapter_info
    chap_ids = {c.get('id') for c in (chapter_info or [])}
    has_ch1 = 836 in chap_ids
    has_ch2 = 837 in chap_ids
    print(f"chapter_info count: {len(chapter_info)} | includes ch1(836)={has_ch1} ch2(837)={has_ch2}")


if __name__ == "__main__":
    summarize_project(91)
