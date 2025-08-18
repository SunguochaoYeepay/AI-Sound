#!/usr/bin/env python3
"""
Full test via API for project 91 (book 58, chapters 836 & 837):
- POST analyze (re-analyze to get fresh result)
- Summarize total tracks and tracks with environment keywords
- Validate chapter_info includes both chapters
- Attempt to GET project details (optional; skip if 500)
"""
from __future__ import annotations
import requests
from typing import Any, Dict, List

BASE = "http://localhost:8001/api/v1"


def analyze_and_summarize(project_id: int, book_id: int, chapter_ids: List[int]) -> None:
    url = f"{BASE}/environment-generation/chapters/analyze"
    payload = {
        "project_id": project_id,
        "book_id": book_id,
        "chapter_ids": chapter_ids,
        "options": {"existing_project_id": project_id, "create_project": False, "force_reanalyze": True}
    }
    r = requests.post(url, json=payload, timeout=60)
    print(f"POST {url} -> {r.status_code}")
    if r.status_code != 200:
        print(r.text)
        return
    body = r.json()
    result = body.get("analysis_result", {})

    # unwrap nested structure if needed
    if isinstance(result, dict) and result.get("success"):
        analysis = result.get("analysis_result", {})
    else:
        analysis = result

    tracks: List[Dict[str, Any]] = analysis.get("environment_tracks", [])
    chapter_info: List[Dict[str, Any]] = analysis.get("chapter_info", [])

    print(f"Total tracks: {len(tracks)}")
    env_tracks = [t for t in tracks if t.get("environment_keywords")]  # non-empty keywords
    print(f"Tracks with env: {len(env_tracks)}")

    chap_ids = {c.get('id') for c in (chapter_info or [])}
    print(f"chapter_info ids: {sorted(list(chap_ids))}")
    print(f"includes 836: {836 in chap_ids}, includes 837: {837 in chap_ids}")

    # sample
    for i, t in enumerate(env_tracks[:5]):
        print(f"  sample#{i+1}: seg={t.get('segment_id')} kws={t.get('environment_keywords')} dur={t.get('duration')}")

    # Try GET project details
    detail_url = f"{BASE}/environment-generation/projects/{project_id}"
    dr = requests.get(detail_url, timeout=20)
    print(f"GET {detail_url} -> {dr.status_code}")
    if dr.status_code == 200:
        pdata = dr.json().get("data", {})
        project = pdata.get("project", {})
        print(f"Project status: {project.get('status')}")
        # summarize saved tracks if any
        pr = project.get("analysis_result", {})
        if isinstance(pr, dict) and 'success' in pr:
            saved = pr.get('analysis_result', {}).get('environment_tracks', [])
        else:
            saved = pr.get('environment_tracks', [])
        if saved is not None:
            print(f"Saved tracks count: {len(saved)}")
    else:
        print(dr.text)


if __name__ == "__main__":
    analyze_and_summarize(91, 58, [836, 837])
