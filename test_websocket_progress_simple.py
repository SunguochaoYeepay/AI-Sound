#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket进度测试脚本
测试合成进度是否能正常获取
"""

import asyncio
import websockets
import json
import time

async def test_websocket_progress():
    """测试WebSocket进度获取"""
    uri = "ws://localhost:8000/ws"
    
    try:
        print("🔌 连接WebSocket服务器...")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功!")
            
            # 订阅进度更新
            subscribe_message = {
                "action": "subscribe",
                "topic": "synthesis_1",  # 假设项目ID为1
                "data": {}
            }
            
            print(f"📡 发送订阅消息: {subscribe_message}")
            await websocket.send(json.dumps(subscribe_message))
            
            # 监听消息
            print("👂 开始监听进度消息...")
            timeout_count = 0
            max_timeout = 30  # 30秒超时
            
            while timeout_count < max_timeout:
                try:
                    # 等待消息，超时时间1秒
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    print(f"📨 收到消息: {message}")
                    
                    try:
                        data = json.loads(message)
                        if data.get("type") == "topic_message":
                            topic_data = data.get("data", {})
                            progress_data = topic_data.get("data", {})
                            
                            print(f"🎯 进度更新: {progress_data}")
                            
                            # 检查是否有合成统计信息
                            if "statistics" in progress_data:
                                stats = progress_data["statistics"]
                                print(f"📊 合成统计: {stats}")
                                
                    except json.JSONDecodeError:
                        print(f"⚠️ 无法解析JSON消息: {message}")
                        
                except asyncio.TimeoutError:
                    timeout_count += 1
                    print(f"⏰ 等待消息中... ({timeout_count}/{max_timeout})")
                    
                    if timeout_count % 5 == 0:
                        print("💡 提示: 请在网页中启动一个合成任务来测试进度获取")
                        
            print("⏰ 测试超时结束")
            
    except Exception as e:
        print(f"❌ WebSocket连接失败: {e}")
        print("💡 请确保后端服务已启动在 http://localhost:8000")

def main():
    print("🧪 开始WebSocket进度获取测试")
    print("=" * 50)
    
    try:
        asyncio.run(test_websocket_progress())
    except KeyboardInterrupt:
        print("\n👋 用户中断测试")
    except Exception as e:
        print(f"❌ 测试异常: {e}")
    
    print("=" * 50)
    print("🏁 测试结束")

if __name__ == "__main__":
    main() 