#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import httpx
import json
import websockets
import time
from datetime import datetime

async def test_websocket_progress():
    """测试WebSocket进度监控功能"""
    
    print("🎯 AI-Sound WebSocket进度测试")
    print("=" * 50)
    
    # 步骤1: 启动异步生成任务
    request_data = {
        'lyrics': '[intro-short]\n\n[verse]\n夜晚的街灯闪烁\n温柔的光芒洒向大地',
        'description': '一首关于夜晚的温柔民谣',
        'genre': 'Pop',
        'cfg_coef': 1.5,
        'temperature': 0.9,
        'top_k': 50
    }
    
    print(f"📝 测试歌词: {request_data['lyrics'][:30]}...")
    print(f"🎵 音乐风格: {request_data['genre']}")
    print(f"⚙️  CFG系数: {request_data['cfg_coef']}")
    print("-" * 50)
    
    try:
        print("🚀 步骤1: 启动异步音乐生成...")
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                'http://localhost:7862/generate_async',
                json=request_data,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"📡 HTTP响应状态: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ 启动失败: {response.text}")
                return
            
            data = response.json()
            task_id = data.get('task_id')
            websocket_url = data.get('websocket_url')
            
            print(f"✅ 任务启动成功!")
            print(f"🔗 任务ID: {task_id}")
            print(f"🌐 WebSocket URL: {websocket_url}")
            print("-" * 50)
            
            # 步骤2: 连接WebSocket监控进度
            print("🔌 步骤2: 连接WebSocket进度监控...")
            
            try:
                async with websockets.connect(websocket_url) as websocket:
                    print("✅ WebSocket连接成功！开始监控进度...")
                    print("-" * 50)
                    
                    progress_count = 0
                    last_progress = -1
                    
                    while True:
                        try:
                            # 等待进度消息
                            message = await asyncio.wait_for(websocket.recv(), timeout=600)
                            progress_data = json.loads(message)
                            
                            progress = progress_data.get('progress', 0)
                            msg = progress_data.get('message', '')
                            timestamp = progress_data.get('timestamp', time.time())
                            
                            progress_count += 1
                            current_time = datetime.now().strftime("%H:%M:%S")
                            elapsed = time.time() - start_time
                            
                            # 详细的进度日志
                            print(f"📊 进度更新 #{progress_count:02d}")
                            print(f"   ⏰ 时间: {current_time} (已耗时: {elapsed:.1f}秒)")
                            print(f"   📈 进度: {progress:.1%} ({progress:.3f})")
                            print(f"   💬 消息: {msg}")
                            print(f"   🔢 原始数据: {progress_data}")
                            
                            # 进度变化检测
                            if progress != last_progress:
                                change = progress - last_progress if last_progress >= 0 else progress
                                print(f"   📊 进度变化: +{change:.1%}")
                                last_progress = progress
                            
                            print("-" * 30)
                            
                            # 检查是否完成
                            if progress >= 1.0:
                                total_time = time.time() - start_time
                                print("🎉 音乐生成完成！")
                                print(f"⏱️  总耗时: {total_time:.2f}秒")
                                print(f"📈 进度更新次数: {progress_count}")
                                print("=" * 50)
                                break
                            elif progress < 0:
                                print(f"❌ 生成失败: {msg}")
                                print("=" * 50)
                                break
                                
                        except asyncio.TimeoutError:
                            elapsed = time.time() - start_time
                            print(f"⏰ WebSocket接收超时 (已等待 {elapsed:.1f}秒)，继续等待...")
                            continue
                        except json.JSONDecodeError as e:
                            print(f"⚠️  JSON解析错误: {e}")
                            print(f"   原始消息: {message}")
                            continue
                            
            except websockets.exceptions.ConnectionClosed:
                print("🔌 WebSocket连接已关闭")
            except Exception as ws_error:
                print(f"❌ WebSocket连接错误: {ws_error}")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_simple_connection():
    """简单连接测试"""
    print("🔗 简单连接测试...")
    
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get('http://localhost:7862/health')
            print(f"✅ SongGeneration健康检查: {response.status_code}")
            
            if response.status_code == 200:
                health_data = response.json()
                print(f"   状态: {health_data.get('status')}")
                print(f"   GPU可用: {health_data.get('gpu', {}).get('available', False)}")
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")

if __name__ == "__main__":
    print("🎼 AI-Sound WebSocket进度监控测试")
    print("=" * 60)
    
    # 先测试连接
    asyncio.run(test_simple_connection())
    print()
    
    # 运行完整测试
    asyncio.run(test_websocket_progress())