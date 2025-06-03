#!/usr/bin/env python3
"""
urllib调试脚本
测试不同HTTP客户端的行为差异
"""

import urllib.request
import urllib.error
import json

def test_urllib():
    """测试urllib请求"""
    print("=== urllib测试 ===")
    
    urls = [
        "http://127.0.0.1:7929/health",
        "http://127.0.0.1:9001/health"
    ]
    
    for url in urls:
        try:
            print(f"\n测试URL: {url}")
            
            request = urllib.request.Request(url)
            request.add_header('Accept', 'application/json')
            
            with urllib.request.urlopen(request, timeout=30) as response:
                status = response.status
                content = response.read().decode('utf-8')
                headers = dict(response.headers)
                
                print(f"状态码: {status}")
                print(f"响应头: {headers}")
                print(f"响应内容: {content}")
                
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP错误: {e.code} {e.reason}")
            print(f"响应内容: {e.read().decode('utf-8') if hasattr(e, 'read') else 'N/A'}")
        except Exception as e:
            print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    test_urllib() 