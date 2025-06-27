#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import websockets
import json
import time
from datetime import datetime

async def monitor_current_task():
    """监控当前正在运行的任务进度"""
    
    # 使用刚才启动的任务ID
    task_id = "1bc668fa-f456-4e1a-a547-d656a6bcecec"
    websocket_url = f"ws://localhost:7862/ws/progress/{task_id}"
    
    print(f"🎯 监控音乐生成进度")
    print(f"🔗 任务ID: {task_id}")
    print(f"🌐 WebSocket: {websocket_url}")
    print("=" * 60)
    
    try:
        async with websockets.connect(websocket_url) as websocket:
            print("✅ WebSocket连接成功！开始监控...")
            print("-" * 60)
            
            progress_count = 0
            start_time = time.time()
            last_progress = -1
            
            while True:
                try:
                    # 接收进度消息 
                    message = await asyncio.wait_for(websocket.recv(), timeout=60)
                    progress_data = json.loads(message)
                    
                    progress = progress_data.get('progress', 0)
                    msg = progress_data.get('message', '')
                    timestamp = progress_data.get('timestamp', time.time())
                    
                    progress_count += 1
                    current_time = datetime.now().strftime("%H:%M:%S")
                    elapsed = time.time() - start_time
                    
                    # 详细进度显示
                    print(f"📊 进度更新 #{progress_count:02d} | {current_time}")
                    print(f"   🎵 进度: {progress:.1%} ({progress:.4f})")
                    print(f"   💬 状态: {msg}")
                    print(f"   ⏱️  用时: {elapsed:.1f}秒")
                    
                    # 进度变化提示
                    if progress != last_progress:
                        change = progress - last_progress if last_progress >= 0 else progress
                        print(f"   📈 变化: +{change:.1%}")
                        last_progress = progress
                    
                    print(f"   📦 原始: {progress_data}")
                    print("-" * 40)
                    
                    # 完成检查
                    if progress >= 1.0:
                        total_time = time.time() - start_time
                        print("🎉 🎵 音乐生成完成! 🎵 🎉")
                        print(f"⏱️  总耗时: {total_time:.2f}秒")
                        print(f"📊 进度次数: {progress_count}")
                        break
                    elif progress < 0:
                        print(f"❌ 生成失败: {msg}")
                        break
                        
                except asyncio.TimeoutError:
                    elapsed = time.time() - start_time
                    print(f"⏰ 60秒内无进度更新 (总计等待: {elapsed:.1f}秒)")
                    print("   可能任务已完成或出错，继续等待...")
                    continue
                    
                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON解析失败: {e}")
                    print(f"   消息内容: {message}")
                    continue
                    
    except websockets.exceptions.ConnectionClosed:
        print("🔌 WebSocket连接已关闭 (任务可能已完成)")
    except websockets.exceptions.InvalidURI:
        print("❌ 无效的WebSocket地址")
    except Exception as e:
        print(f"❌ WebSocket连接错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🎼 AI-Sound WebSocket进度实时监控")
    print("=" * 70)
    asyncio.run(monitor_current_task())