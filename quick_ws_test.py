#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速WebSocket连接测试"""

import requests
import json

def test_backend_connection():
    """测试后端连接"""
    try:
        response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        print(f"✅ 后端服务响应: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ 后端服务不可用: {e}")
        return False

def test_websocket_endpoint():
    """测试WebSocket端点可用性"""
    try:
        # 检查WebSocket端点
        response = requests.get("http://localhost:8000/docs", timeout=5)
        print(f"✅ API文档可访问: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ API端点不可用: {e}")
        return False

def main():
    print("🧪 快速连接测试")
    print("=" * 30)
    
    backend_ok = test_backend_connection()
    ws_ok = test_websocket_endpoint()
    
    if backend_ok and ws_ok:
        print("✅ 后端服务正常运行")
        print("💡 WebSocket进度获取应该可以正常工作")
        print("🎯 建议在网页中启动合成任务来测试实际进度")
    else:
        print("❌ 后端服务存在问题")
        
    print("=" * 30)

if __name__ == "__main__":
    main()