#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json
import time

def test_sync_api():
    """同步测试API"""
    print("🔧 同步API测试")
    print("=" * 30)
    
    # 1. 健康检查
    try:
        health_response = requests.get('http://localhost:7862/health', timeout=10)
        print(f"✅ 健康检查: {health_response.status_code}")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   状态: {health_data.get('status')}")
            print(f"   模型: {health_data.get('model', {}).get('loaded', False)}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return
    
    # 2. 测试异步生成端点
    request_data = {
        'lyrics': '[intro-short]\n\n[verse]\n夜晚的街灯闪烁\n温柔的光芒洒向大地',
        'description': '一首关于夜晚的温柔民谣',
        'genre': 'Pop',
        'cfg_coef': 1.5,
        'temperature': 0.9,
        'top_k': 50
    }
    
    print(f"\n🚀 测试异步生成...")
    print(f"📝 歌词: {request_data['lyrics'][:30]}...")
    
    try:
        response = requests.post(
            'http://localhost:7862/generate_async',
            json=request_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📡 响应状态: {response.status_code}")
        print(f"📄 响应内容: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 任务启动成功!")
            print(f"🔗 任务ID: {data.get('task_id')}")
            print(f"🌐 WebSocket URL: {data.get('websocket_url')}")
        else:
            print(f"❌ 任务启动失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    print("🎼 简单同步API测试")
    print("=" * 40)
    test_sync_api()