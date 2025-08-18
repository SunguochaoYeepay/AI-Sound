#!/usr/bin/env python3
"""
调试分析API原始响应
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def debug_analysis():
    body = {
        "chapter_ids": [836],  # 只分析第一章
        "analysis_options": {
            "existing_project_id": 100,
            "force_reanalyze": True
        }
    }
    
    print("🔍 调用分析API...")
    r = requests.post(f"{BASE_URL}/api/v1/environment-generation/chapters/analyze", json=body)
    
    print(f"状态码: {r.status_code}")
    print(f"响应头: {dict(r.headers)}")
    
    try:
        resp = r.json()
        print("\n📄 完整响应:")
        print(json.dumps(resp, ensure_ascii=False, indent=2))
        
        # 检查关键字段
        if 'analysis_result' in resp:
            tracks = resp['analysis_result'].get('environment_tracks', [])
            print(f"\n🎯 轨道数量: {len(tracks)}")
            if tracks:
                print(f"第一个轨道: {tracks[0]}")
        else:
            print("❌ 没有analysis_result字段")
            
    except Exception as e:
        print(f"❌ 解析响应失败: {e}")
        print(f"原始响应: {r.text}")

if __name__ == "__main__":
    debug_analysis()
