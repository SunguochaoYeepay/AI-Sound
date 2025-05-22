#!/usr/bin/env python3
"""
测试角色声音映射功能
"""

import os
import sys
import json
import requests
import argparse
from pathlib import Path

def test_analyze_characters(text_path, api_url="http://127.0.0.1:9930"):
    """
    测试小说角色分析功能
    
    Args:
        text_path: 小说文本路径
        api_url: API服务地址
    """
    print("\n===== 测试小说角色分析 =====")
    print(f"小说文件: {text_path}")
    
    # 检查文件是否存在
    if not os.path.exists(text_path):
        print(f"❌ 文件不存在: {text_path}")
        return None
    
    try:
        # 读取文件内容
        with open(text_path, 'r', encoding='utf-8') as f:
            novel_text = f.read()
        
        print(f"成功读取文件，内容长度: {len(novel_text)} 字符")
        
        # 发送请求
        response = requests.post(
            f"{api_url}/api/characters/analyze",
            json={"text": novel_text},
            timeout=60
        )
        
        # 检查响应
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                characters = result.get("characters", [])
                print(f"分析结果: 共 {len(characters)} 个角色")
                
                # 显示主要角色（出现频率前5）
                print("\n主要角色:")
                for i, char in enumerate(characters[:5]):
                    name = char.get("name")
                    count = char.get("count")
                    voices = char.get("suggested_voices", [])
                    
                    print(f"{i+1}. {name} (出现 {count} 次)")
                    if voices:
                        print(f"   建议声音: {', '.join(voices)}")
                
                return characters
            else:
                print(f"❌ 分析角色返回错误: {result}")
        else:
            print(f"❌ 分析角色请求失败: HTTP {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ 分析角色请求异常: {str(e)}")
    
    return None

def test_map_character(character_name, voice_id, api_url="http://127.0.0.1:9930"):
    """
    测试映射角色到声音
    
    Args:
        character_name: 角色名称
        voice_id: 声音ID
        api_url: API服务地址
    """
    print(f"\n===== 测试映射角色到声音 =====")
    print(f"角色: {character_name}")
    print(f"声音ID: {voice_id}")
    
    try:
        # 发送请求
        response = requests.post(
            f"{api_url}/api/characters/map",
            json={
                "character": character_name,
                "voice_id": voice_id,
                "attributes": {
                    "type": "novel_character",
                    "description": f"小说中的角色 - {character_name}"
                }
            },
            timeout=30
        )
        
        # 检查响应
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✅ 角色映射成功: {result.get('message')}")
                
                # 显示角色信息
                character = result.get("character", {})
                print(f"角色信息:")
                print(f"  名称: {character.get('name')}")
                print(f"  声音ID: {character.get('voice_id')}")
                print(f"  声音名称: {character.get('voice_name')}")
                
                return character
            else:
                print(f"❌ 角色映射返回错误: {result}")
        else:
            print(f"❌ 角色映射请求失败: HTTP {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ 角色映射请求异常: {str(e)}")
    
    return None

def test_list_characters(api_url="http://127.0.0.1:9930"):
    """
    测试获取所有角色
    
    Args:
        api_url: API服务地址
    """
    print(f"\n===== 测试获取所有角色 =====")
    
    try:
        # 发送请求
        response = requests.get(
            f"{api_url}/api/characters",
            timeout=30
        )
        
        # 检查响应
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                characters = result.get("characters", [])
                print(f"共 {len(characters)} 个角色")
                
                for i, character in enumerate(characters):
                    print(f"{i+1}. {character.get('name')} (声音: {character.get('voice_name')})")
                
                return characters
            else:
                print(f"❌ 获取角色列表返回错误: {result}")
        else:
            print(f"❌ 获取角色列表请求失败: HTTP {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ 获取角色列表请求异常: {str(e)}")
    
    return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试角色声音映射功能")
    parser.add_argument("--analyze", help="要分析的小说文本路径")
    parser.add_argument("--map", help="要映射的角色名称")
    parser.add_argument("--voice", help="映射的声音ID")
    parser.add_argument("--list", action="store_true", help="列出所有角色")
    parser.add_argument("--url", default="http://127.0.0.1:9930", help="API服务地址")
    args = parser.parse_args()
    
    api_url = args.url
    
    # 根据参数执行不同操作
    if args.analyze:
        characters = test_analyze_characters(args.analyze, api_url)
        
        # 如果同时指定了映射参数，则测试映射
        if characters and args.map and args.voice:
            test_map_character(args.map, args.voice, api_url)
    elif args.map and args.voice:
        test_map_character(args.map, args.voice, api_url)
    elif args.list:
        test_list_characters(api_url)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 