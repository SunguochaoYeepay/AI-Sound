#!/usr/bin/env python3
"""
使用Python执行Docker重启命令
"""

import subprocess
import time
import sys

def run_command(command, description):
    """运行命令并显示结果"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ {description}成功")
            if result.stdout.strip():
                print(f"输出: {result.stdout.strip()}")
        else:
            print(f"❌ {description}失败")
            if result.stderr.strip():
                print(f"错误: {result.stderr.strip()}")
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"⏰ {description}超时")
        return False
    except Exception as e:
        print(f"💥 {description}异常: {e}")
        return False

def main():
    print("🚀 重启API服务以应用ESPnet配置")
    print("=" * 50)
    
    # 停止API容器
    if not run_command("docker stop services-api-1", "停止API容器"):
        print("❌ 停止容器失败，退出")
        return False
    
    # 等待3秒
    print("⏳ 等待3秒...")
    time.sleep(3)
    
    # 启动API容器
    if not run_command("docker start services-api-1", "启动API容器"):
        print("❌ 启动容器失败，退出")
        return False
    
    # 等待10秒让服务启动
    print("⏳ 等待10秒让服务启动...")
    time.sleep(10)
    
    # 检查容器状态
    run_command("docker ps | findstr services-api-1", "检查容器状态")
    
    print("\n✅ 重启完成！")
    print("现在可以运行 python check_config.py 来验证配置")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 