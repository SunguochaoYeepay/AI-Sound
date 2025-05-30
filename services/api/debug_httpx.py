#!/usr/bin/env python3
"""
httpx调试脚本
模拟适配器的请求方式，调试502错误
"""

import asyncio
import httpx
import time
import traceback

async def test_direct_request():
    """测试直接请求"""
    print("=== 直接httpx请求测试 ===")
    
    urls = [
        "http://127.0.0.1:7929/health",
        "http://127.0.0.1:9001/health"
    ]
    
    for url in urls:
        try:
            print(f"\n测试URL: {url}")
            
            # 模拟适配器的配置
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers=headers,
                follow_redirects=True
            ) as client:
                start_time = time.time()
                response = await client.get(url)
                end_time = time.time()
                
                print(f"状态码: {response.status_code}")
                print(f"响应时间: {(end_time - start_time) * 1000:.2f}ms")
                print(f"响应头: {dict(response.headers)}")
                print(f"响应内容: {response.text}")
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            traceback.print_exc()

async def test_different_configs():
    """测试不同的httpx配置"""
    print("\n=== 不同配置测试 ===")
    
    url = "http://127.0.0.1:7929/health"
    
    configs = [
        {
            "name": "最简配置",
            "config": {}
        },
        {
            "name": "无请求头",
            "config": {"timeout": httpx.Timeout(30.0)}
        },
        {
            "name": "最简请求头",
            "config": {
                "timeout": httpx.Timeout(30.0),
                "headers": {"Accept": "application/json"}
            }
        },
        {
            "name": "标准浏览器头",
            "config": {
                "timeout": httpx.Timeout(30.0),
                "headers": {"User-Agent": "Mozilla/5.0"}
            }
        }
    ]
    
    for config_test in configs:
        try:
            print(f"\n--- {config_test['name']} ---")
            
            async with httpx.AsyncClient(**config_test['config']) as client:
                response = await client.get(url)
                print(f"✅ 成功: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 失败: {e}")

async def test_timing():
    """测试时序问题"""
    print("\n=== 时序测试 ===")
    
    urls = [
        "http://127.0.0.1:7929/health",
        "http://127.0.0.1:9001/health"
    ]
    
    # 模拟API服务启动时的并发请求
    print("模拟并发请求...")
    tasks = []
    
    for url in urls:
        for i in range(3):  # 每个URL发送3个并发请求
            task = asyncio.create_task(make_request(url, f"请求{i+1}"))
            tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    print("并发请求结果:")
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"任务{i+1}: ❌ {result}")
        else:
            print(f"任务{i+1}: ✅ {result}")

async def make_request(url, name):
    """发送单个请求"""
    try:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers=headers,
            follow_redirects=True
        ) as client:
            response = await client.get(url)
            return f"{name} -> {url} -> {response.status_code}"
            
    except Exception as e:
        return f"{name} -> {url} -> ERROR: {e}"

async def main():
    """主函数"""
    print("🔍 httpx 502错误调试脚本")
    print("=" * 50)
    
    await test_direct_request()
    await test_different_configs()  
    await test_timing()
    
    print("\n🏁 调试完成")

if __name__ == "__main__":
    asyncio.run(main()) 