#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import websockets
import json
import time
from datetime import datetime

async def test_websocket_connection():
    """测试WebSocket连接和进度监控"""
    
    # 这里需要一个有效的task_id（从前面的测试中获取）
    task_id = "56811276-fab1-40bc-9b66-ab425d559f07"
    websocket_url = f"ws://localhost:7862/ws/progress/{task_id}"
    
    print(f"🔌 连接WebSocket进度监控")
    print(f"🌐 URL: {websocket_url}")
    print("=" * 50)
    
    try:
        async with websockets.connect(websocket_url) as websocket:
            print("✅ WebSocket连接成功！等待进度数据...")
            print("-" * 50)
            
            progress_count = 0
            start_time = time.time()
            
            # 监听进度消息
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=300)
                    progress_data = json.loads(message)
                    
                    progress = progress_data.get('progress', 0)
                    msg = progress_data.get('message', '')
                    timestamp = progress_data.get('timestamp', time.time())
                    
                    progress_count += 1
                    current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    elapsed = time.time() - start_time
                    
                    print(f"📊 进度 #{progress_count:02d} - {current_time}")
                    print(f"   📈 进度值: {progress:.1%} ({progress:.6f})")
                    print(f"   💬 消息: {msg}")
                    print(f"   ⏱️  耗时: {elapsed:.2f}秒")
                    print(f"   🔢 完整数据: {progress_data}")
                    print("-" * 30)
                    
                    # 检查完成状态
                    if progress >= 1.0:
                        print("🎉 生成完成!")
                        break
                    elif progress < 0:
                        print(f"❌ 生成失败: {msg}")
                        break
                        
                except asyncio.TimeoutError:
                    elapsed = time.time() - start_time
                    print(f"⏰ 等待进度数据超时 (已等待 {elapsed:.1f}秒)")
                    break
                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON解析错误: {e}")
                    print(f"   原始消息: {message}")
                    continue
                    
    except websockets.exceptions.ConnectionClosed:
        print("🔌 WebSocket连接已关闭")
    except Exception as e:
        print(f"❌ WebSocket错误: {e}")

if __name__ == "__main__":
    print("🎼 WebSocket进度监控专项测试")
    print("=" * 60)
    asyncio.run(test_websocket_connection())