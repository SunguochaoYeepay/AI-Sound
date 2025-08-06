#!/usr/bin/env python3
"""测试头像API和角色数据"""

import requests
import json

def test_character_data():
    """测试角色数据"""
    print("🔍 测试角色数据...")
    
    # 获取角色列表
    response = requests.get('http://localhost:8000/api/v1/characters?page=1&page_size=5&avatar_filter=has_avatar')
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        characters = data.get('characters', [])
        print(f"返回角色数量: {len(characters)}")
        
        for char in characters:
            print(f"\n角色: {char.get('name')}")
            print(f"  ID: {char.get('id')}")
            print(f"  头像路径: {char.get('avatar_path')}")
            print(f"  avatarUrl: {char.get('avatarUrl')}")
            print(f"  has_avatar: {char.get('has_avatar')}")

def test_avatar_api():
    """测试头像API"""
    print("\n🔍 测试头像API...")
    
    # 测试有头像的角色
    character_id = 1015  # 妇女们
    response = requests.get(f'http://localhost:8000/api/v1/characters/avatar/{character_id}')
    print(f"头像API状态码: {response.status_code}")
    print(f"内容类型: {response.headers.get('content-type', 'N/A')}")
    print(f"内容长度: {len(response.content)}")
    
    if response.status_code != 200:
        print(f"错误信息: {response.text}")

def test_default_avatar():
    """测试默认头像API"""
    print("\n🔍 测试默认头像API...")
    
    response = requests.get('http://localhost:8000/api/v1/characters/avatar/default?name=测试角色&voice_type=custom')
    print(f"默认头像API状态码: {response.status_code}")
    print(f"内容类型: {response.headers.get('content-type', 'N/A')}")
    print(f"内容长度: {len(response.content)}")

if __name__ == "__main__":
    test_character_data()
    test_avatar_api()
    test_default_avatar() 