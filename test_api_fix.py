#!/usr/bin/env python3
"""
测试API修复效果
"""

import requests
import time
import sys

def test_api_endpoints():
    """测试API端点"""
    
    base_url = "http://localhost:8000"
    
    # 测试端点列表
    test_endpoints = [
        "/health",
        "/api/health", 
        "/api/v1/books",
        "/api/v1/characters",
        "/api/v1/audio-library/files",
        "/api/v1/audio-library/stats",
        "/api/v1/novel-reader/projects"
    ]
    
    print("🔍 开始测试API端点...")
    print(f"基础URL: {base_url}")
    print("=" * 50)
    
    results = {}
    
    for endpoint in test_endpoints:
        url = f"{base_url}{endpoint}"
        print(f"测试: {endpoint}")
        
        try:
            response = requests.get(url, timeout=5)
            status = response.status_code
            
            if status == 200:
                print(f"  ✅ 成功 (200)")
                results[endpoint] = "OK"
            elif status == 404:
                print(f"  ❌ 未找到 (404)")
                results[endpoint] = "NOT_FOUND"
            else:
                print(f"  ⚠️  状态码: {status}")
                results[endpoint] = f"STATUS_{status}"
                
        except requests.exceptions.ConnectionError:
            print(f"  🔗 连接失败 - 服务未启动")
            results[endpoint] = "CONNECTION_ERROR"
        except requests.exceptions.Timeout:
            print(f"  ⏰ 请求超时")
            results[endpoint] = "TIMEOUT"
        except Exception as e:
            print(f"  💥 错误: {str(e)}")
            results[endpoint] = f"ERROR: {str(e)}"
    
    print("\n" + "=" * 50)
    print("📊 测试结果总览:")
    
    ok_count = sum(1 for v in results.values() if v == "OK")
    total_count = len(results)
    
    print(f"成功: {ok_count}/{total_count}")
    
    if ok_count == 0:
        print("\n❌ 所有API都无法访问，请检查:")
        print("1. 后端服务是否正常启动")
        print("2. 端口8000是否被占用")
        print("3. 防火墙设置")
        return False
    elif ok_count == total_count:
        print("\n✅ 所有API端点都正常工作!")
        return True
    else:
        print(f"\n⚠️  部分API端点有问题:")
        for endpoint, status in results.items():
            if status != "OK":
                print(f"  {endpoint}: {status}")
        return False

def check_server_status():
    """检查服务器状态"""
    print("🔍 检查服务器状态...")
    
    try:
        response = requests.get("http://localhost:8000/", timeout=3)
        print("✅ 服务器响应正常")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器 (localhost:8000)")
        print("请确保后端服务已启动:")
        print("  cd platform/backend")
        print("  python main.py")
        return False
    except Exception as e:
        print(f"❌ 服务器检查失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 AI-Sound API修复测试")
    print("=" * 50)
    
    # 检查服务器
    if not check_server_status():
        print("\n❌ 服务器未启动，无法进行API测试")
        sys.exit(1)
    
    # 等待服务稳定
    print("⏳ 等待服务稳定...")
    time.sleep(2)
    
    # 测试API
    success = test_api_endpoints()
    
    if success:
        print("\n🎉 API修复成功！所有端点都正常工作")
    else:
        print("\n⚠️  API修复部分成功，还有一些端点需要检查") 