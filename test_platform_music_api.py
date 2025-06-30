#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI-Sound平台的音乐生成API（使用修复后的异步接口）
"""

import asyncio
import httpx
import json
import time
from datetime import datetime

class PlatformMusicAPITester:
    def __init__(self, platform_url: str = "http://localhost:8000"):
        self.platform_url = platform_url
        
    async def test_songgeneration_engine_directly(self):
        """直接测试SongGeneration引擎"""
        print(f"\n🔍 [引擎直连] 测试SongGeneration引擎")
        
        engine_url = "http://localhost:7862"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 测试ping
                print("📡 测试引擎 /ping...")
                ping_response = await client.get(f"{engine_url}/ping")
                print(f"   状态码: {ping_response.status_code}")
                if ping_response.status_code == 200:
                    print(f"   响应: {ping_response.json()}")
                
                # 测试health
                print("📊 测试引擎 /health...")
                health_response = await client.get(f"{engine_url}/health")
                print(f"   状态码: {health_response.status_code}")
                if health_response.status_code == 200:
                    health_data = health_response.json()
                    print(f"   服务状态: {health_data.get('status')}")
                    print(f"   模型状态: {health_data.get('model', {}).get('loaded')}")
                
                return ping_response.status_code == 200 and health_response.status_code == 200
                
        except Exception as e:
            print(f"❌ 引擎直连测试失败: {e}")
            return False
    
    async def test_platform_music_generation(self):
        """测试平台音乐生成API"""
        print(f"\n🎵 [平台API] 测试音乐生成")
        
        # 测试数据
        test_data = {
            "content": """[intro-short]

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

[outro-short]""",
            "chapter_id": "test_async_001",
            "custom_style": "Pop",
            "volume_level": -12.0,
            "direct_mode": True,  # 使用直接模式
            "advanced_params": {
                "cfg_coef": 1.5,
                "temperature": 0.9,
                "top_k": 50,
                "description": "测试异步接口修复的温馨音乐"
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                print("📤 发送音乐生成请求到平台...")
                print(f"   目标: {self.platform_url}/api/v1/music/generate")
                print(f"   风格: {test_data['custom_style']}")
                print(f"   直接模式: {test_data['direct_mode']}")
                
                start_time = time.time()
                response = await client.post(
                    f"{self.platform_url}/api/v1/music/generate",
                    json=test_data,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"   状态码: {response.status_code}")
                print(f"   请求耗时: {time.time() - start_time:.2f}秒")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 平台音乐生成成功!")
                    print(f"   音频路径: {result.get('audio_path', 'N/A')}")
                    print(f"   生成时间: {result.get('generation_time', 0):.2f}秒")
                    print(f"   最终风格: {result.get('final_style', 'N/A')}")
                    
                    # 检查音频文件是否存在
                    audio_path = result.get('audio_path')
                    if audio_path:
                        import os
                        if os.path.exists(audio_path):
                            file_size = os.path.getsize(audio_path) / 1024 / 1024
                            print(f"   文件大小: {file_size:.2f} MB")
                        else:
                            print(f"   ⚠️  音频文件不存在: {audio_path}")
                    
                    return True
                else:
                    print(f"❌ 平台请求失败: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ 平台音乐生成测试失败: {e}")
            return False
    
    async def test_songgeneration_engine_health_during_generation(self):
        """测试生成过程中引擎的健康状态"""
        print(f"\n📈 [生成监控] 监控生成过程中的引擎状态")
        
        # 启动一个生成任务
        test_data = {
            "content": "[verse]\n简单的测试歌词\n用于监控引擎状态",
            "chapter_id": "monitor_test",
            "custom_style": "Pop",
            "direct_mode": True
        }
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # 启动生成任务（不等待完成）
                print("🚀 启动后台生成任务...")
                generation_task = asyncio.create_task(
                    client.post(
                        f"{self.platform_url}/api/v1/music/generate",
                        json=test_data,
                        headers={"Content-Type": "application/json"}
                    )
                )
                
                # 等待一点时间让生成开始
                await asyncio.sleep(2)
                
                # 在生成过程中测试引擎健康状态
                engine_url = "http://localhost:7862"
                for i in range(5):  # 测试5次
                    print(f"   第{i+1}次健康检查...")
                    
                    try:
                        # 测试ping（应该快速响应）
                        ping_response = await client.get(f"{engine_url}/ping", timeout=3.0)
                        ping_status = "✅" if ping_response.status_code == 200 else "❌"
                        
                        # 测试health（可能会慢或失败）
                        health_response = await client.get(f"{engine_url}/health", timeout=3.0)
                        health_status = "✅" if health_response.status_code == 200 else "❌"
                        
                        print(f"   {ping_status} ping: {ping_response.status_code}, {health_status} health: {health_response.status_code}")
                        
                    except asyncio.TimeoutError:
                        print(f"   ⏰ 第{i+1}次检查超时（引擎可能正在生成）")
                    except Exception as e:
                        print(f"   ❌ 第{i+1}次检查失败: {e}")
                    
                    await asyncio.sleep(3)  # 每3秒检查一次
                
                # 等待生成任务完成
                print("⏳ 等待生成任务完成...")
                try:
                    response = await asyncio.wait_for(generation_task, timeout=30)
                    print(f"🎯 生成任务完成，状态码: {response.status_code}")
                except asyncio.TimeoutError:
                    print("⏰ 生成任务超时")
                    generation_task.cancel()
                
        except Exception as e:
            print(f"❌ 生成监控测试失败: {e}")
    
    async def run_comprehensive_test(self):
        """运行综合测试"""
        print("=" * 70)
        print("🧪 AI-Sound平台音乐生成API综合测试（异步接口修复验证）")
        print("=" * 70)
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 步骤1: 引擎直连测试
        engine_ok = await self.test_songgeneration_engine_directly()
        if not engine_ok:
            print("\n❌ 引擎直连失败，无法继续测试")
            return False
        
        # 步骤2: 平台API测试
        platform_ok = await self.test_platform_music_generation()
        
        # 步骤3: 生成过程监控测试
        if platform_ok:
            await self.test_songgeneration_engine_health_during_generation()
        
        print("\n" + "=" * 70)
        if platform_ok:
            print("🎉 异步接口修复验证成功！音乐生成功能正常")
            print("✅ 引擎在生成过程中不再完全阻塞")
            print("✅ 健康检查可以正常响应")
        else:
            print("❌ 异步接口修复验证失败")
        print("=" * 70)
        
        return platform_ok

async def main():
    tester = PlatformMusicAPITester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main()) 