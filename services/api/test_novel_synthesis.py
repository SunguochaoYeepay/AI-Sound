#!/usr/bin/env python3
"""
测试小说合成功能
"""

import os
import sys
import json
import time
import requests
import argparse
from pathlib import Path

def test_novel_processing(novel_path, api_url="http://127.0.0.1:9930", output_dir=None, auto_character_mapping=True):
    """
    测试小说处理功能
    
    Args:
        novel_path: 小说文件路径
        api_url: API服务地址
        output_dir: 输出目录
        auto_character_mapping: 是否自动映射角色
    """
    print(f"\n===== 测试小说语音合成 =====")
    print(f"小说文件: {novel_path}")
    
    # 检查文件是否存在
    if not os.path.exists(novel_path):
        print(f"❌ 文件不存在: {novel_path}")
        return None
    
    try:
        # 发送请求
        response = requests.post(
            f"{api_url}/api/tts/novel",
            json={
                "novel_path": novel_path,
                "output_dir": output_dir,
                "auto_character_mapping": auto_character_mapping,
                "with_emotion": True,
                "resume_if_exists": True
            },
            timeout=60
        )
        
        # 检查响应
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                task_id = result.get("task_id")
                print(f"✅ 小说处理任务已创建, 任务ID: {task_id}")
                print(f"任务状态查询URL: {result.get('status_url')}")
                
                # 等待任务处理
                return wait_for_task(task_id, api_url)
            else:
                print(f"❌ 创建处理任务返回错误: {result}")
        else:
            print(f"❌ 创建处理任务请求失败: HTTP {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ 创建处理任务请求异常: {str(e)}")
    
    return None

def wait_for_task(task_id, api_url="http://127.0.0.1:9930", timeout=3600, interval=5):
    """
    等待任务完成
    
    Args:
        task_id: 任务ID
        api_url: API服务地址
        timeout: 超时时间(秒)
        interval: 轮询间隔(秒)
    """
    print(f"等待任务 {task_id} 处理完成...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # 查询任务状态
            response = requests.get(
                f"{api_url}/api/tasks/{task_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get("status")
                progress = result.get("progress", 0) * 100
                message = result.get("message", "")
                
                print(f"任务状态: {status}, 进度: {progress:.1f}%, 消息: {message}")
                
                if status == "completed":
                    print(f"✅ 任务处理完成!")
                    return result
                elif status == "failed":
                    print(f"❌ 任务处理失败: {result.get('error')}")
                    return result
            else:
                print(f"❌ 查询任务状态失败: HTTP {response.status_code}")
        
        except Exception as e:
            print(f"❌ 查询任务状态异常: {str(e)}")
        
        # 等待一段时间后再次查询
        time.sleep(interval)
    
    print(f"❌ 等待任务超时")
    return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试小说合成功能")
    parser.add_argument("novel_path", help="小说文件路径")
    parser.add_argument("--url", default="http://127.0.0.1:9930", help="API服务URL")
    parser.add_argument("--output", help="输出目录，默认为空")
    parser.add_argument("--no-auto-mapping", action="store_true", help="禁用自动角色映射")
    args = parser.parse_args()
    
    # 调用测试函数
    test_novel_processing(
        novel_path=args.novel_path,
        api_url=args.url,
        output_dir=args.output,
        auto_character_mapping=not args.no_auto_mapping
    )

if __name__ == "__main__":
    main() 