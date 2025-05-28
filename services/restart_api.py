#!/usr/bin/env python3
"""
重启API服务
"""

import subprocess
import time
import requests

def restart_api_service():
    """重启API服务"""
    try:
        print("🔄 重启API服务...")
        
        # 停止API服务
        result = subprocess.run(['docker-compose', 'stop', 'api'], 
                              capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            print("✅ API服务已停止")
        else:
            print(f"⚠️ 停止API服务时出现警告: {result.stderr}")
        
        # 启动API服务
        result = subprocess.run(['docker-compose', 'start', 'api'], 
                              capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            print("✅ API服务已启动")
        else:
            print(f"❌ 启动API服务失败: {result.stderr}")
            return False
        
        # 等待服务启动
        print("⏳ 等待API服务启动...")
        time.sleep(10)
        
        # 测试服务是否可用
        for i in range(5):
            try:
                response = requests.get('http://localhost:9930/health', timeout=5)
                if response.status_code == 200:
                    print("✅ API服务启动成功！")
                    return True
            except:
                print(f"⏳ 等待中... ({i+1}/5)")
                time.sleep(3)
        
        print("❌ API服务启动超时")
        return False
        
    except Exception as e:
        print(f"❌ 重启失败: {e}")
        return False

if __name__ == "__main__":
    restart_api_service() 