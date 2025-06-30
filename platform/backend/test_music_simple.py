#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的音乐生成测试
"""

import requests
import json

# ✅ 使用正确的异步接口
test_url = "http://localhost:8000/api/v1/music-generation-async/generate"

print("🎵 测试异步音乐生成接口...")

test_data = {
    "lyrics": "[verse]\n测试歌词内容\n验证异步接口",
    "genre": "Pop",
    "cfg_coef": 1.5,
    "temperature": 0.9,
    "top_k": 50
}

try:
    response = requests.post(test_url, json=test_data, timeout=30)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 异步任务启动成功!")
        print(f"Task ID: {result.get('task_id')}")
        print(f"消息: {result.get('message')}")
    else:
        print(f"❌ 请求失败: {response.text}")
        
except Exception as e:
    print(f"❌ 测试异常: {e}")