#!/usr/bin/env python3
import asyncio
import httpx
import json
import websockets

async def test_async_generation():
    """测试异步音乐生成和WebSocket进度监控"""
    
    print("🎯 测试WebSocket进度音乐生成...")
    
    # 步骤1: 启动异步生成任务
    request_data = {
        'lyrics': '[intro-short]\n\n[verse]\n夜晚的街灯闪烁',
        'description': '',
        'genre': 'Pop',
        'cfg_coef': 1.5,
        'temperature': 0.9,
        'top_k': 50
    }
    
    print('发送异步生成请求...')
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            'http://localhost:7862/generate_async',
            json=request_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f'响应状态码: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id')
            print(f'✅ 异步任务已启动，task_id: {task_id}')
            
            # 步骤2: 连接WebSocket监控进度
            websocket_url = f"ws://localhost:7862/ws/progress/{task_id}"
            print(f'连接WebSocket: {websocket_url}')
            
            try:
                async with websockets.connect(websocket_url) as websocket:
                    print('✅ WebSocket连接成功，开始监控进度...')
                    
                    while True:
                        try:
                            # 等待进度消息
                            message = await asyncio.wait_for(websocket.recv(), timeout=600)
                            progress_data = json.loads(message)
                            
                            progress = progress_data.get('progress', 0)
                            msg = progress_data.get('message', '')
                            
                            print(f'📊 进度: {progress:.1%} - {msg}')
                            
                            # 检查是否完成
                            if progress >= 1.0:
                                print('🎉 音乐生成完成！')
                                break
                            elif progress < 0:
                                print(f'❌ 生成失败: {msg}')
                                break
                                
                        except asyncio.TimeoutError:
                            print('⏰ WebSocket接收超时，继续等待...')
                            continue
                            
            except Exception as e:
                print(f'❌ WebSocket连接错误: {e}')
        else:
            print(f'❌ 启动异步生成失败: {response.text}')

if __name__ == "__main__":
    asyncio.run(test_async_generation()) 