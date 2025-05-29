#!/usr/bin/env python3
"""
测试覆盖率分析脚本
"""

import json
import os
import glob

def count_api_endpoints():
    """统计API端点总数"""
    try:
        with open('openapi_full.json', 'r', encoding='utf-16') as f:
            openapi_data = json.load(f)
    except:
        try:
            with open('openapi_full.json', 'r', encoding='utf-8') as f:
                openapi_data = json.load(f)
        except Exception as e:
            print(f"无法读取OpenAPI文档: {e}")
            return 0
    
    endpoint_count = 0
    endpoints = []
    
    for path, methods in openapi_data['paths'].items():
        for method, details in methods.items():
            endpoint_count += 1
            endpoints.append({
                'method': method.upper(),
                'path': path,
                'summary': details.get('summary', ''),
                'tags': details.get('tags', [])
            })
    
    return endpoint_count, endpoints

def count_test_coverage():
    """统计测试覆盖的端点"""
    test_files = [
        'super_comprehensive_test.py',
        'tests/test_full_api.py',
        'tests/test_api.py',
        'tests/quick_test.py',
        'tests/simple_api_test.py'
    ]
    
    tested_endpoints = set()
    
    for test_file in test_files:
        if os.path.exists(test_file):
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 查找API端点引用
                import re
                # 查找 /api/ 开头的路径
                api_paths = re.findall(r'["\'](/api/[^"\']*)["\']', content)
                # 查找系统端点
                system_paths = re.findall(r'["\'](/(?:health|info|docs|openapi\.json))["\']', content)
                
                all_paths = api_paths + system_paths
                tested_endpoints.update(all_paths)
                
            except Exception as e:
                print(f"读取测试文件 {test_file} 失败: {e}")
    
    return tested_endpoints

def main():
    print("=== AI-Sound TTS系统 API测试覆盖率分析 ===\n")
    
    # 统计总端点数
    total_count, all_endpoints = count_api_endpoints()
    print(f"📊 总API端点数量: {total_count}")
    
    # 统计测试覆盖
    tested_endpoints = count_test_coverage()
    print(f"🧪 测试脚本中发现的端点: {len(tested_endpoints)}")
    
    # 计算覆盖率
    if total_count > 0:
        coverage_rate = (len(tested_endpoints) / total_count) * 100
        print(f"📈 估算测试覆盖率: {coverage_rate:.1f}%")
    
    print("\n=== 端点分类统计 ===")
    tags_count = {}
    for endpoint in all_endpoints:
        tags = endpoint['tags'] if endpoint['tags'] else ['系统端点']
        for tag in tags:
            tags_count[tag] = tags_count.get(tag, 0) + 1
    
    for tag, count in sorted(tags_count.items()):
        print(f"  {tag}: {count} 个端点")
    
    print(f"\n=== 测试脚本中发现的端点列表 ===")
    for i, endpoint in enumerate(sorted(tested_endpoints), 1):
        print(f"  {i:2d}. {endpoint}")
    
    print(f"\n=== 所有API端点列表 ===")
    for i, endpoint in enumerate(all_endpoints, 1):
        tags_str = ', '.join(endpoint['tags']) if endpoint['tags'] else '系统端点'
        tested_mark = "✅" if endpoint['path'] in tested_endpoints else "❌"
        print(f"  {tested_mark} {i:2d}. {endpoint['method']} {endpoint['path']} [{tags_str}] {endpoint['summary']}")

if __name__ == "__main__":
    main() 