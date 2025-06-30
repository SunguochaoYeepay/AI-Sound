#!/usr/bin/env python3
"""
测试SongGeneration服务连接
"""
import asyncio
import httpx
import json
import sys
import os

# 添加platform/backend到路径
sys.path.append('platform/backend')

from app.clients.songgeneration_engine import SongGenerationEngineClient

async def test_connection():
    """测试SongGeneration服务连接"""
    print("🔍 测试SongGeneration服务连接...")
    
    # 1. 测试直接连接
    print("\n=== 1. 直接测试服务端点 ===")
    urls_to_test = [
        "http://localhost:7862",
        "http://127.0.0.1:7862", 
        "http://host.docker.internal:7862"
    ]
    
    for url in urls_to_test:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                print(f"测试 {url}/ping ...")
                ping_response = await client.get(f"{url}/ping")
                print(f"  Ping: {ping_response.status_code} - {ping_response.text[:100]}")
                
                print(f"测试 {url}/health ...")
                health_response = await client.get(f"{url}/health")
                print(f"  Health: {health_response.status_code} - {health_response.text[:200]}")
                
                if health_response.status_code == 200:
                    health_data = health_response.json()
                    print(f"  ✅ 服务正常: {health_data.get('status', 'unknown')}")
                else:
                    print(f"  ❌ 服务异常: HTTP {health_response.status_code}")
                    
        except Exception as e:
            print(f"  ❌ 连接失败: {e}")
        print()
    
    # 2. 测试客户端自动检测
    print("=== 2. 测试客户端自动检测 ===")
    try:
        client = SongGenerationEngineClient()
        print(f"检测到的URL: {client.base_url}")
        
        # 测试服务检查
        service_ready = await client._check_service_ready()
        print(f"服务就绪检查: {'✅ 成功' if service_ready else '❌ 失败'}")
        
        # 测试健康检查
        health_ok = await client.health_check()
        print(f"健康检查: {'✅ 成功' if health_ok else '❌ 失败'}")
        
    except Exception as e:
        print(f"❌ 客户端测试失败: {e}")
    
    # 3. 环境信息
    print("\n=== 3. 环境信息 ===")
    print(f"SONGGENERATION_URL: {os.getenv('SONGGENERATION_URL', '未设置')}")
    print(f"DOCKER_ENV: {os.getenv('DOCKER_ENV', '未设置')}")
    print(f"/.dockerenv 存在: {os.path.exists('/.dockerenv')}")
    
    # 检查进程信息
    try:
        import psutil
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'])
                    if 'songgeneration' in cmdline.lower() or '7862' in cmdline:
                        processes.append(f"PID {proc.info['pid']}: {cmdline}")
            except:
                pass
        
        if processes:
            print("\n=== 4. 相关进程 ===")
            for proc in processes:
                print(f"  {proc}")
        else:
            print("\n=== 4. 未找到相关进程 ===")
    except ImportError:
        print("\n=== 4. 无法检查进程（需要psutil库） ===")

if __name__ == "__main__":
    asyncio.run(test_connection()) 