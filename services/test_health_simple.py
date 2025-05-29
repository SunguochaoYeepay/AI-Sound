#!/usr/bin/env python3
"""
简单的健康检查测试脚本
"""

import requests
import json
import time

def test_basic_health():
    """测试基础健康检查"""
    try:
        print("🔍 测试基础API健康检查...")
        response = requests.get("http://localhost:9930/health", timeout=5)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ 基础健康检查通过")
            return True
        else:
            print(f"❌ 基础健康检查失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 基础健康检查异常: {e}")
        return False

def test_engines_list():
    """测试引擎列表"""
    try:
        print("\n🔍 测试引擎列表...")
        response = requests.get("http://localhost:9930/api/engines", timeout=5)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ 引擎列表获取成功")
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return data
        else:
            print(f"❌ 引擎列表获取失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 引擎列表获取异常: {e}")
        return None

def test_engine_health(engine_id):
    """测试引擎健康检查"""
    try:
        print(f"\n🔍 测试引擎健康检查: {engine_id}")
        response = requests.get(f"http://localhost:9930/api/engines/{engine_id}/health", timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 引擎健康检查成功")
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ 引擎健康检查失败")
            print(f"响应内容: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 引擎健康检查异常: {e}")
        return False

def main():
    print("🚀 开始API健康检查测试...")
    
    # 1. 测试基础健康检查
    if not test_basic_health():
        print("\n❌ 基础健康检查失败，停止测试")
        return
    
    # 2. 测试引擎列表
    engines_data = test_engines_list()
    if not engines_data:
        print("\n❌ 引擎列表获取失败，停止测试")
        return
    
    # 3. 提取引擎ID
    engines = []
    if 'engines' in engines_data:
        engines = engines_data['engines']
    elif 'data' in engines_data and 'engines' in engines_data['data']:
        engines = engines_data['data']['engines']
    
    if not engines:
        print("\n❌ 没有找到引擎，停止测试")
        return
    
    # 4. 测试第一个引擎的健康检查
    engine_id = engines[0]['id']
    if test_engine_health(engine_id):
        print("\n🎉 所有测试通过！")
    else:
        print("\n❌ 引擎健康检查测试失败")

if __name__ == "__main__":
    main() 