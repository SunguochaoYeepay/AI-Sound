#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json

def check_task_status():
    """查询当前任务状态"""
    task_id = "1bc668fa-f456-4e1a-a547-d656a6bcecec"
    
    print(f"🔍 查询任务状态: {task_id}")
    print("=" * 50)
    
    try:
        # 查询健康状态
        health = requests.get('http://localhost:7862/health').json()
        print(f"📊 服务状态: {health.get('status')}")
        print(f"🤖 模型状态: {health.get('model', {}).get('loaded')}")
        
        # 检查输出目录是否有生成的文件
        try:
            import os
            output_dir = "../../MegaTTS/Song-Generation/output/api_generated"
            if os.path.exists(output_dir):
                files = [f for f in os.listdir(output_dir) if f.startswith(task_id[:8])]
                if files:
                    print(f"📁 发现输出文件: {files}")
                else:
                    print("📁 暂无输出文件 (生成中...)")
            else:
                print("📁 输出目录不存在")
        except Exception as e:
            print(f"📁 检查文件失败: {e}")
            
    except Exception as e:
        print(f"❌ 查询失败: {e}")

if __name__ == "__main__":
    check_task_status()