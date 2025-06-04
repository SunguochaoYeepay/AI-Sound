#!/usr/bin/env python3
"""
带详细日志的测试脚本
"""
import sys
import requests
import json
import time
sys.path.append('app')

BASE_URL = "http://localhost:8000"

def detailed_test():
    print("🔍 === 带详细日志的完整测试 ===")
    
    # 1. 测试项目19详情获取
    print("\n📋 Step 1: 获取项目19详情...")
    try:
        response = requests.get(f"{BASE_URL}/api/novel-reader/projects/19")
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   响应: {data.get('success', False)}")
            
            if data.get('success'):
                project = data.get('data', {})
                print(f"   项目名: {project.get('name')}")
                print(f"   状态: {project.get('status')}")
                print(f"   角色映射: {project.get('characterMapping')}")
                print(f"   段落数: {project.get('totalSegments')}")
            else:
                print(f"   错误: {data.get('message')}")
        else:
            print(f"   HTTP错误: {response.status_code}")
            print(f"   响应: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 2. 尝试启动音频生成
    print("\n🎤 Step 2: 启动音频生成...")
    try:
        form_data = {
            'parallel_tasks': '1'  # 使用单任务测试
        }
        
        response = requests.post(
            f"{BASE_URL}/api/novel-reader/projects/19/start-generation",
            data=form_data
        )
        
        print(f"   状态码: {response.status_code}")
        print(f"   响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   成功: {data.get('success', False)}")
            print(f"   消息: {data.get('message')}")
            print(f"   总段落: {data.get('totalSegments')}")
            print(f"   并行任务: {data.get('parallelTasks')}")
            print("   ✅ 音频生成启动成功")
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   错误详情: {error_data}")
            except:
                print(f"   错误文本: {response.text}")
                
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 3. 检查进度
    print("\n📊 Step 3: 检查生成进度...")
    time.sleep(2)  # 等待2秒
    
    try:
        response = requests.get(f"{BASE_URL}/api/novel-reader/projects/19/progress")
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                progress = data.get('data', {})
                print(f"   项目状态: {progress.get('status')}")
                print(f"   进度: {progress.get('progress', 0)}%")
                print(f"   已处理: {progress.get('processedSegments', 0)}")
                print(f"   总计: {progress.get('totalSegments', 0)}")
            else:
                print(f"   错误: {data.get('message')}")
        else:
            print(f"   HTTP错误: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")

if __name__ == "__main__":
    detailed_test() 