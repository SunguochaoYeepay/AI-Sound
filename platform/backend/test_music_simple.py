#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的音乐生成测试
"""

import requests
import json

print("🎼 AI-Sound音乐生成功能演示")
print("=" * 50)

# 测试数据
test_data = {
    "description": "peaceful countryside morning with birds singing, acoustic folk style", 
    "duration": 30,
    "style": "acoustic folk"
}

print(f"📝 测试场景: {test_data['description']}")
print(f"⏱️  时长: {test_data['duration']}秒")
print(f"🎵 风格: {test_data['style']}")
print()

try:
    print("🚀 开始调用音乐生成API...")
    
    response = requests.post(
        "http://localhost:8000/api/v1/music-generation/generate-direct",
        json=test_data,
        timeout=120
    )
    
    print(f"⏰ API响应状态: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ 音乐生成API调用成功！")
        print("📄 响应数据:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get('success'):
            print("\n🎉 音乐生成功能完全正常！")
        else:
            print(f"\n❌ 生成失败: {result.get('message', '未知错误')}")
    else:
        print("❌ API调用失败")
        print(f"错误信息: {response.text}")

except Exception as e:
    print(f"❌ 发生异常: {e}")