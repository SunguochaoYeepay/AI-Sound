#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试SongGeneration异步接口和探活功能
"""

import asyncio
import httpx
import json
import time
import os
from datetime import datetime

class AsyncMusicGenerationTester:
    def __init__(self, base_url: str = "http://localhost:7862"):
        self.base_url = base_url
        
    async def test_health_check(self):
        """测试健康检查接口"""
        print(f"\n🔍 [健康检查] 开始检查 {self.base_url}")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 测试ping接口
                print("📡 测试 /ping 接口...")
                ping_response = await client.get(f"{self.base_url}/ping")
                print(f"   状态码: {ping_response.status_code}")
                if ping_response.status_code == 200:
                    ping_data = ping_response.json()
                    print(f"   响应: {ping_data}")
                else:
                    print(f"   错误: {ping_response.text}")
                
                # 测试health接口
                print("📊 测试 /health 接口...")
                health_response = await client.get(f"{self.base_url}/health")
                print(f"   状态码: {health_response.status_code}")
                if health_response.status_code == 200:
                    health_data = health_response.json()
                    print(f"   服务状态: {health_data.get('status', 'unknown')}")
                    print(f"   模型状态: {health_data.get('model', {}).get('loaded', 'unknown')}")
                    print(f"   GPU状态: {health_data.get('gpu', {}).get('available', 'unknown')}")
                    if health_data.get('gpu', {}).get('available'):
                        print(f"   GPU显存: 已分配 {health_data.get('gpu', {}).get('memory_allocated', '0')}")
                else:
                    print(f"   错误: {health_response.text}")
                    
        except Exception as e:
            print(f"❌ 健康检查失败: {e}")
            return False
            
        return True
    
    async def test_async_generation(self):
        """测试异步音乐生成"""
        print(f"\n🎵 [异步生成] 开始测试异步音乐生成")
        
        # 测试歌词
        test_lyrics = """[intro-short]

[verse]
夜晚的街灯闪烁
我漫步在熟悉的角落
回忆像潮水般涌来
你的笑容如此清晰

[chorus]
回忆的温度还在
你却已不在
我的心被爱填满
却又被思念刺痛

[outro-short]"""
        
        request_data = {
            "lyrics": test_lyrics,
            "description": "测试异步接口的温馨音乐",
            "genre": "Pop",
            "cfg_coef": 1.5,
            "temperature": 0.9,
            "top_k": 50
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                print("📤 发送异步生成请求...")
                print(f"   歌词长度: {len(test_lyrics)} 字符")
                print(f"   风格: {request_data['genre']}")
                
                start_time = time.time()
                response = await client.post(
                    f"{self.base_url}/generate_async",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"   状态码: {response.status_code}")
                print(f"   请求耗时: {time.time() - start_time:.2f}秒")
                
                if response.status_code == 200:
                    data = response.json()
                    task_id = data.get("task_id")
                    print(f"✅ 异步任务已启动!")
                    print(f"   任务ID: {task_id}")
                    print(f"   消息: {data.get('message', 'No message')}")
                    
                    # 等待一段时间，然后测试健康检查是否还能正常工作
                    await self.monitor_generation_progress(task_id)
                    
                    return True
                else:
                    print(f"❌ 异步请求失败: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ 异步生成测试失败: {e}")
            return False
    
    async def monitor_generation_progress(self, task_id: str):
        """监控生成过程中的服务状态"""
        print(f"\n📈 [进度监控] 监控任务 {task_id} 的生成进度")
        
        max_wait_time = 120  # 最大等待2分钟
        start_time = time.time()
        check_interval = 5   # 每5秒检查一次
        
        while time.time() - start_time < max_wait_time:
            elapsed = time.time() - start_time
            print(f"\n⏱️  已等待 {elapsed:.0f}秒...")
            
            # 在生成过程中测试健康检查
            print("   测试生成过程中的健康检查...")
            health_ok = await self.test_health_during_generation()
            
            # 检查是否有生成的文件
            if await self.check_for_generated_files():
                print("🎉 发现生成的音频文件！")
                return True
            
            await asyncio.sleep(check_interval)
        
        print(f"⏰ 等待超时 ({max_wait_time}秒)")
        return False
    
    async def test_health_during_generation(self) -> bool:
        """在生成过程中测试健康检查"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # 快速ping测试
                ping_response = await client.get(f"{self.base_url}/ping")
                ping_ok = ping_response.status_code == 200
                
                # 健康检查测试
                health_response = await client.get(f"{self.base_url}/health")
                health_ok = health_response.status_code == 200
                
                status = "✅" if (ping_ok and health_ok) else "❌"
                print(f"   {status} ping: {ping_response.status_code}, health: {health_response.status_code}")
                
                return ping_ok and health_ok
                
        except Exception as e:
            print(f"   ❌ 健康检查异常: {e}")
            return False
    
    async def check_for_generated_files(self) -> bool:
        """检查是否有新生成的音频文件"""
        possible_paths = [
            "MegaTTS/Song-Generation/output/api_generated",
            "output/api_generated"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    files = [f for f in os.listdir(path) if f.endswith('.flac')]
                    if files:
                        # 按修改时间排序
                        files.sort(key=lambda x: os.path.getmtime(os.path.join(path, x)), reverse=True)
                        latest_file = files[0]
                        file_path = os.path.join(path, latest_file)
                        
                        # 检查是否是最近生成的（2分钟内）
                        if time.time() - os.path.getmtime(file_path) < 120:
                            print(f"   📁 找到最新文件: {file_path}")
                            file_size = os.path.getsize(file_path) / 1024 / 1024  # MB
                            print(f"   📏 文件大小: {file_size:.2f} MB")
                            return True
                except Exception as e:
                    print(f"   ⚠️  检查路径 {path} 时出错: {e}")
                    
        return False
    
    async def run_comprehensive_test(self):
        """运行综合测试"""
        print("=" * 60)
        print("🧪 SongGeneration异步接口综合测试")
        print("=" * 60)
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 步骤1: 基础健康检查
        health_ok = await self.test_health_check()
        if not health_ok:
            print("\n❌ 健康检查失败，无法继续测试")
            return False
        
        # 步骤2: 异步生成测试
        generation_ok = await self.test_async_generation()
        
        print("\n" + "=" * 60)
        if generation_ok:
            print("🎉 异步接口测试成功！音乐生成正常工作")
        else:
            print("❌ 异步接口测试失败")
        print("=" * 60)
        
        return generation_ok

async def main():
    tester = AsyncMusicGenerationTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main()) 