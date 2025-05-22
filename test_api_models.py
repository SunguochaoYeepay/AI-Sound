#!/usr/bin/env python3
"""
API响应模型测试脚本
用于验证API返回数据是否符合Pydantic模型定义
"""

import requests
import json
import sys
import os
from typing import Dict, Any

# API端点基础URL
API_BASE_URL = "http://localhost:9930"

# 要测试的端点和对应的响应模型类型
ENDPOINTS = [
    {
        "url": "/api/voices/list",
        "method": "GET",
        "payload": None,
        "model_name": "VoiceFeatureListResponse"
    },
    {
        "url": "/api/voices/tags",
        "method": "GET",
        "payload": None,
        "model_name": "VoiceTagsResponse"
    },
    {
        "url": "/api/characters",
        "method": "GET",
        "payload": None,
        "model_name": "CharacterListResponse"
    }
]

def test_endpoint(endpoint: Dict[str, Any]) -> bool:
    """测试单个端点响应是否符合模型规范"""
    url = f"{API_BASE_URL}{endpoint['url']}"
    method = endpoint["method"]
    payload = endpoint["payload"]
    model_name = endpoint["model_name"]
    
    print(f"\n测试端点: {method} {url}")
    print(f"预期模型: {model_name}")
    
    try:
        # 发送请求
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=payload)
        else:
            print(f"不支持的HTTP方法: {method}")
            return False
        
        # 检查响应状态
        if response.status_code != 200:
            print(f"错误: HTTP状态码 {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
        
        # 解析JSON响应
        data = response.json()
        
        # 检查响应基本结构
        if "success" not in data:
            print("错误: 响应缺少'success'字段")
            return False
        
        # 保存响应用于调试
        with open(f"test_response_{model_name}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"响应有效，已保存到test_response_{model_name}.json")
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False

def main():
    """主函数"""
    print("API响应模型测试")
    print("=" * 40)
    
    success_count = 0
    total_count = len(ENDPOINTS)
    
    for endpoint in ENDPOINTS:
        if test_endpoint(endpoint):
            success_count += 1
    
    print("\n测试结果汇总")
    print("=" * 40)
    print(f"成功: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("所有测试通过!")
        return 0
    else:
        print(f"有 {total_count - success_count} 个测试失败!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 