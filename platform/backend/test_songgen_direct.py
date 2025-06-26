#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试SongGeneration服务的音乐生成功能
"""

import requests
import json

print("🎵 直接测试SongGeneration服务")
print("=" * 50)

# 第1步：测试健康检查
print("1. 检查SongGeneration服务健康状态...")
try:
    health_response = requests.get("http://localhost:7863/health", timeout=10)
    print(f"   健康检查状态: {health_response.status_code}")
    if health_response.status_code == 200:
        health_data = health_response.json()
        print(f"   服务状态: {health_data.get('status')}")
        print(f"   依赖状态: {health_data.get('dependencies')}")
    else:
        print(f"   错误: {health_response.text}")
        exit(1)
except Exception as e:
    print(f"   连接失败: {e}")
    exit(1)

print("\n2. 测试任务创建...")

# 第2步：创建音乐生成任务
task_data = {
    "description": "peaceful countryside morning with acoustic folk music",
    "duration": 30,
    "style": "acoustic folk"
}

try:
    create_response = requests.post(
        "http://localhost:7863/create_task",
        json=task_data,
        timeout=30
    )
    print(f"   任务创建状态: {create_response.status_code}")
    
    if create_response.status_code == 200:
        task_result = create_response.json()
        print(f"   任务ID: {task_result.get('task_id')}")
        task_id = task_result.get('task_id')
        
        if not task_id:
            print("   错误: 没有返回任务ID")
            exit(1)
    else:
        print(f"   创建失败: {create_response.text}")
        exit(1)
        
except Exception as e:
    print(f"   任务创建异常: {e}")
    exit(1)

print("\n3. 测试场景分析...")

# 第3步：场景分析
try:
    analyze_response = requests.post(
        f"http://localhost:7863/analyze_scene/{task_id}",
        timeout=30
    )
    print(f"   场景分析状态: {analyze_response.status_code}")
    
    if analyze_response.status_code == 200:
        analyze_result = analyze_response.json()
        print(f"   场景类型: {analyze_result.get('scene_type')}")
    else:
        print(f"   分析失败: {analyze_response.text}")
        
except Exception as e:
    print(f"   场景分析异常: {e}")

print("\n4. 测试提示词生成...")

# 第4步：生成提示词
try:
    prompt_response = requests.post(
        f"http://localhost:7863/generate_prompt/{task_id}",
        timeout=30
    )
    print(f"   提示词生成状态: {prompt_response.status_code}")
    
    if prompt_response.status_code == 200:
        prompt_result = prompt_response.json()
        print(f"   生成的歌词: {prompt_result.get('lyrics', 'N/A')[:100]}...")
        print(f"   音乐描述: {prompt_result.get('description', 'N/A')[:100]}...")
    else:
        print(f"   提示词生成失败: {prompt_response.text}")
        
except Exception as e:
    print(f"   提示词生成异常: {e}")

print("\n5. 测试音乐生成...")

# 第5步：生成音乐（这是关键步骤）
try:
    generate_response = requests.post(
        f"http://localhost:7863/generate_music/{task_id}",
        timeout=300  # 5分钟超时
    )
    print(f"   音乐生成状态: {generate_response.status_code}")
    
    if generate_response.status_code == 200:
        generate_result = generate_response.json()
        print(f"   生成结果: {generate_result}")
        print("\n🎉 音乐生成完全成功！")
    else:
        print(f"   音乐生成失败: {generate_response.text}")
        print("   这是我们需要重点调试的地方")
        
except Exception as e:
    print(f"   音乐生成异常: {e}")

print("\n=" * 50)
print("测试完成")