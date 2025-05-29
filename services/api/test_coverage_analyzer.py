#!/usr/bin/env python3
"""
接口测试脚本覆盖率分析工具
"""

import json
import os
import re
from pathlib import Path
import glob

def analyze_test_coverage():
    """分析测试覆盖率"""
    
    # 1. 解析OpenAPI文档获取所有端点
    print("🔍 正在分析OpenAPI文档...")
    api_endpoints = get_api_endpoints()
    
    # 2. 扫描测试文件获取已测试端点
    print("🧪 正在扫描测试文件...")
    tested_endpoints = get_tested_endpoints()
    
    # 3. 计算覆盖率
    print("📊 正在计算覆盖率...")
    calculate_coverage(api_endpoints, tested_endpoints)

def get_api_endpoints():
    """从OpenAPI文档提取所有端点"""
    endpoints = []
    
    try:
        # 尝试读取OpenAPI文档
        openapi_files = ['openapi_full.json', 'openapi.json', 'swagger.json']
        openapi_data = None
        
        for file_name in openapi_files:
            if os.path.exists(file_name):
                try:
                    with open(file_name, 'r', encoding='utf-8') as f:
                        openapi_data = json.load(f)
                    break
                except:
                    try:
                        with open(file_name, 'r', encoding='utf-16') as f:
                            openapi_data = json.load(f)
                        break
                    except:
                        continue
        
        if not openapi_data:
            print("❌ 未找到OpenAPI文档")
            return endpoints
            
        # 解析端点
        paths = openapi_data.get('paths', {})
        for path, methods in paths.items():
            for method, details in methods.items():
                endpoint = {
                    'path': path,
                    'method': method.upper(),
                    'operationId': details.get('operationId', ''),
                    'summary': details.get('summary', ''),
                    'tags': details.get('tags', [])
                }
                endpoints.append(endpoint)
                
    except Exception as e:
        print(f"❌ 解析OpenAPI文档失败: {e}")
    
    print(f"✅ 发现 {len(endpoints)} 个API端点")
    return endpoints

def get_tested_endpoints():
    """扫描测试文件获取已测试的端点"""
    tested = set()
    
    # 扫描测试文件
    test_patterns = [
        'tests/**/*.py',
        'test/**/*.py', 
        '**/test_*.py',
        '**/*_test.py',
        'super_comprehensive_test.py'
    ]
    
    test_files = []
    for pattern in test_patterns:
        test_files.extend(glob.glob(pattern, recursive=True))
    
    print(f"📁 发现 {len(test_files)} 个测试文件")
    
    # 分析测试文件内容
    for test_file in test_files:
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 提取HTTP请求
            patterns = [
                r'requests\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                r'client\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                r'test_client\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                r'self\.client\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                r'app\.test_client\(\)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for method, path in matches:
                    # 清理路径参数
                    clean_path = re.sub(r'/\d+', '/{id}', path)
                    clean_path = re.sub(r'/[a-f0-9-]{36}', '/{id}', clean_path)
                    tested.add(f"{method.upper()} {clean_path}")
                    
        except Exception as e:
            print(f"⚠️  读取测试文件失败 {test_file}: {e}")
    
    print(f"✅ 发现 {len(tested)} 个已测试端点")
    return tested

def calculate_coverage(api_endpoints, tested_endpoints):
    """计算并显示覆盖率报告"""
    
    if not api_endpoints:
        print("❌ 无法获取API端点信息")
        return
    
    # 创建端点映射
    api_set = set()
    for endpoint in api_endpoints:
        api_key = f"{endpoint['method']} {endpoint['path']}"
        api_set.add(api_key)
    
    # 计算覆盖率
    total_endpoints = len(api_set)
    covered_endpoints = 0
    uncovered_endpoints = []
    
    for api_key in api_set:
        is_covered = False
        for tested_key in tested_endpoints:
            if api_key == tested_key or similar_endpoint(api_key, tested_key):
                is_covered = True
                break
        
        if is_covered:
            covered_endpoints += 1
        else:
            uncovered_endpoints.append(api_key)
    
    coverage_rate = (covered_endpoints / total_endpoints) * 100 if total_endpoints > 0 else 0
    
    # 显示报告
    print("\n" + "="*60)
    print("📋 接口测试覆盖率报告")
    print("="*60)
    print(f"📊 总端点数量: {total_endpoints}")
    print(f"✅ 已测试端点: {covered_endpoints}")
    print(f"❌ 未测试端点: {len(uncovered_endpoints)}")
    print(f"📈 覆盖率: {coverage_rate:.1f}%")
    
    if coverage_rate >= 80:
        print("🎉 覆盖率优秀!")
    elif coverage_rate >= 60:
        print("👍 覆盖率良好!")
    elif coverage_rate >= 40:
        print("⚠️  覆盖率一般，建议增加测试")
    else:
        print("🚨 覆盖率较低，需要大量补充测试")
    
    # 显示未覆盖的端点
    if uncovered_endpoints:
        print(f"\n🔍 未测试的端点 ({len(uncovered_endpoints)}个):")
        for endpoint in sorted(uncovered_endpoints):
            print(f"  - {endpoint}")
    
    # 按模块分组显示
    print(f"\n📊 按模块统计:")
    module_stats = {}
    for endpoint in api_endpoints:
        module = endpoint.get('tags', ['Unknown'])[0] if endpoint.get('tags') else 'Unknown'
        if module not in module_stats:
            module_stats[module] = {'total': 0, 'covered': 0}
        
        module_stats[module]['total'] += 1
        api_key = f"{endpoint['method']} {endpoint['path']}"
        
        for tested_key in tested_endpoints:
            if api_key == tested_key or similar_endpoint(api_key, tested_key):
                module_stats[module]['covered'] += 1
                break
    
    for module, stats in sorted(module_stats.items()):
        rate = (stats['covered'] / stats['total']) * 100 if stats['total'] > 0 else 0
        print(f"  {module}: {stats['covered']}/{stats['total']} ({rate:.1f}%)")

def similar_endpoint(api_endpoint, test_endpoint):
    """判断两个端点是否相似（考虑路径参数差异）"""
    # 简单的相似性判断
    api_parts = api_endpoint.split()
    test_parts = test_endpoint.split()
    
    if len(api_parts) != 2 or len(test_parts) != 2:
        return False
    
    if api_parts[0] != test_parts[0]:  # HTTP方法必须相同
        return False
    
    # 路径相似性判断
    api_path = api_parts[1]
    test_path = test_parts[1]
    
    # 替换路径参数进行比较
    api_normalized = re.sub(r'\{[^}]+\}', '{param}', api_path)
    test_normalized = re.sub(r'\{[^}]+\}', '{param}', test_path)
    test_normalized = re.sub(r'/\d+', '/{param}', test_normalized)
    test_normalized = re.sub(r'/[a-f0-9-]{36}', '/{param}', test_normalized)
    
    return api_normalized == test_normalized

if __name__ == "__main__":
    analyze_test_coverage()