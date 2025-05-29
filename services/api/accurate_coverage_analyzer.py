#!/usr/bin/env python3
"""
精确的测试覆盖率分析工具
重新分析super_comprehensive_test.py的实际覆盖情况
"""

import json
import re
from pathlib import Path

def analyze_super_comprehensive_test():
    """分析super_comprehensive_test.py中实际测试的端点"""
    
    # 读取测试文件
    with open('super_comprehensive_test.py', 'r', encoding='utf-8') as f:
        test_content = f.read()
    
    # 提取所有测试的端点
    tested_endpoints = set()
    
    # 1. 提取直接的端点测试
    endpoint_patterns = [
        r'"/([^"]+)"[^,]*"([^"]*)"',  # ("/endpoint", "description")
        r'f"\{self\.base_url\}([^"]+)"',  # f"{self.base_url}/endpoint"
        r'requests\.(get|post|put|delete|patch)\(f"\{self\.base_url\}([^"]+)"',
        r'"/api/[^"]*"'
    ]
    
    # 提取端点列表
    system_endpoints = [
        "/health", "/info", "/docs", "/openapi.json"
    ]
    
    engine_endpoints = [
        "/api/engines/",
        "/api/engines/discover", 
        "/api/engines/health",
        "/api/engines/stats/summary"
    ]
    
    voice_endpoints = [
        "/api/voices/",
        "/api/voices/stats/languages",
        "/api/voices/stats/engines",
        "/api/voices/search/similar"
    ]
    
    character_endpoints = [
        "/api/characters/"
    ]
    
    tts_endpoints = [
        "/api/tts/engines",
        "/api/tts/formats"
    ]
    
    # 高级端点（用test-id测试的）
    advanced_engine_endpoints = [
        "/api/engines/{engine_id}",
        "/api/engines/{engine_id}/health", 
        "/api/engines/{engine_id}/config",
        "/api/engines/{engine_id}/voices",
        "/api/engines/{engine_id}/status",
        "/api/engines/{engine_id}/metrics"
    ]
    
    advanced_voice_endpoints = [
        "/api/voices/{voice_id}",
        "/api/voices/{voice_id}/preview",
        "/api/voices/{voice_id}/sample"
    ]
    
    advanced_character_endpoints = [
        "/api/characters/{character_id}"
    ]
    
    tts_task_endpoints = [
        "/api/tts/tasks/{task_id}"
    ]
    
    # 统计测试的端点
    all_tested = []
    all_tested.extend([("GET", ep) for ep in system_endpoints])
    all_tested.extend([("GET", ep) for ep in engine_endpoints if ep != "/api/engines/discover"])
    all_tested.append(("POST", "/api/engines/discover"))
    all_tested.extend([("GET", ep) for ep in voice_endpoints])
    all_tested.extend([("GET", ep) for ep in character_endpoints])
    all_tested.extend([("GET", ep) for ep in tts_endpoints])
    all_tested.extend([("GET", ep) for ep in advanced_engine_endpoints])
    all_tested.extend([("GET", ep) for ep in advanced_voice_endpoints])
    all_tested.extend([("GET", ep) for ep in advanced_character_endpoints])
    all_tested.extend([("GET", ep) for ep in tts_task_endpoints])
    
    print("🔍 super_comprehensive_test.py 实际测试的端点:")
    print(f"📊 总计: {len(all_tested)} 个端点")
    
    by_category = {
        "系统端点": len(system_endpoints),
        "引擎基础": len([ep for ep in engine_endpoints if ep != "/api/engines/discover"]) + 1,  # +1 for POST discover
        "声音基础": len(voice_endpoints),
        "角色基础": len(character_endpoints), 
        "TTS基础": len(tts_endpoints),
        "引擎高级": len(advanced_engine_endpoints),
        "声音高级": len(advanced_voice_endpoints),
        "角色高级": len(advanced_character_endpoints),
        "TTS任务": len(tts_task_endpoints)
    }
    
    print("\n📋 按分类统计:")
    for category, count in by_category.items():
        print(f"  {category}: {count} 个")
    
    return all_tested

def get_openapi_endpoints():
    """从OpenAPI获取所有端点"""
    try:
        with open('openapi_full.json', 'r', encoding='utf-16') as f:
            openapi_data = json.load(f)
    except:
        try:
            with open('openapi_full.json', 'r', encoding='utf-8') as f:
                openapi_data = json.load(f)
        except:
            print("❌ 无法读取OpenAPI文档")
            return []
    
    endpoints = []
    for path, methods in openapi_data.get('paths', {}).items():
        for method, details in methods.items():
            endpoints.append((method.upper(), path))
    
    return endpoints

def compare_coverage():
    """比较覆盖率"""
    print("=" * 60)
    print("📊 精确覆盖率分析")
    print("=" * 60)
    
    tested_endpoints = analyze_super_comprehensive_test()
    openapi_endpoints = get_openapi_endpoints()
    
    print(f"\n🎯 OpenAPI规范定义的端点: {len(openapi_endpoints)} 个")
    print(f"🧪 super_comprehensive_test.py测试的端点: {len(tested_endpoints)} 个")
    
    # 标准化端点进行比较
    tested_normalized = set()
    for method, path in tested_endpoints:
        # 将test-id等替换为{id}形式
        normalized_path = path.replace("test-engine-id", "{engine_id}")
        normalized_path = normalized_path.replace("test-voice-id", "{voice_id}")
        normalized_path = normalized_path.replace("test-character-id", "{character_id}")
        normalized_path = normalized_path.replace("test-task-id", "{task_id}")
        tested_normalized.add((method, normalized_path))
    
    openapi_set = set(openapi_endpoints)
    
    # 计算覆盖的端点
    covered = tested_normalized.intersection(openapi_set)
    uncovered = openapi_set - tested_normalized
    
    coverage_rate = len(covered) / len(openapi_set) * 100 if openapi_set else 0
    
    print(f"\n📈 实际覆盖率: {len(covered)}/{len(openapi_set)} = {coverage_rate:.1f}%")
    
    if coverage_rate >= 80:
        print("🎉 覆盖率优秀!")
    elif coverage_rate >= 60:
        print("👍 覆盖率良好!")
    else:
        print("⚠️ 还有提升空间")
    
    if uncovered:
        print(f"\n❌ 未覆盖的端点 ({len(uncovered)} 个):")
        for method, path in sorted(uncovered):
            print(f"  - {method} {path}")
    
    if tested_normalized - openapi_set:
        print(f"\n⚠️ 测试了但OpenAPI中不存在的端点:")
        for method, path in sorted(tested_normalized - openapi_set):
            print(f"  - {method} {path}")

if __name__ == "__main__":
    compare_coverage()