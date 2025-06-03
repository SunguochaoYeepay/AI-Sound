#!/usr/bin/env python3
"""
分析OpenAPI文档中的所有端点
"""

import json
import re
from pathlib import Path

def analyze_endpoints():
    # 读取OpenAPI文档
    try:
        with open('openapi_full.json', 'r', encoding='utf-8') as f:
            openapi_data = json.load(f)
    except UnicodeDecodeError:
        # 如果UTF-8失败，尝试UTF-16
        with open('openapi_full.json', 'r', encoding='utf-16') as f:
            openapi_data = json.load(f)

    # 获取所有端点
    all_endpoints = []
    for path, methods in openapi_data['paths'].items():
        for method, details in methods.items():
            endpoint_info = {
                'path': path,
                'method': method.upper(),
                'operationId': details.get('operationId', ''),
                'summary': details.get('summary', ''),
                'tags': details.get('tags', [])
            }
            all_endpoints.append(endpoint_info)

    print(f'总端点数量: {len(all_endpoints)}')
    print('')

    # 按标签分组统计
    tags_count = {}
    for endpoint in all_endpoints:
        tags = endpoint['tags'] if endpoint['tags'] else ['无标签']
        for tag in tags:
            tags_count[tag] = tags_count.get(tag, 0) + 1

    print('按标签分组的端点数量:')
    for tag, count in sorted(tags_count.items()):
        print(f'  {tag}: {count}')

    print('')
    print('所有端点列表:')
    for i, endpoint in enumerate(all_endpoints, 1):
        tags_str = ', '.join(endpoint['tags']) if endpoint['tags'] else '无标签'
        print(f'{i:2d}. {endpoint["method"]:6s} {endpoint["path"]:50s} [{tags_str}] {endpoint["summary"]}')
    
    return all_endpoints

if __name__ == "__main__":
    analyze_endpoints() 