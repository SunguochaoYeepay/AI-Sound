#!/usr/bin/env python3
"""
强制重启API服务以应用新配置
"""

import os
import time
import requests

def check_api_status():
    """检查API服务状态"""
    try:
        response = requests.get('http://localhost:9930/health', timeout=5)
        return response.status_code == 200
    except:
        return False

def check_espnet_status():
    """检查ESPnet服务状态"""
    try:
        response = requests.get('http://localhost:9001/health', timeout=5)
        return response.status_code == 200
    except:
        return False

def test_api_espnet_connection():
    """测试API网关到ESPnet的连接"""
    try:
        print("🔍 测试API网关到ESPnet的连接...")
        response = requests.post(
            'http://localhost:9930/api/tts/synthesize',
            json={
                "text": "测试连接",
                "voice_id": "espnet_zh_female_001", 
                "engine": "espnet"
            },
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ API网关成功连接到ESPnet！")
            return True
        else:
            print(f"❌ 连接失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False

def restart_using_docker_commands():
    """使用Docker命令重启"""
    try:
        print("🔄 使用Docker命令重启API服务...")
        
        # 停止API容器
        os.system("docker stop services-api-1")
        time.sleep(3)
        
        # 启动API容器
        os.system("docker start services-api-1")
        time.sleep(10)
        
        # 检查状态
        if check_api_status():
            print("✅ API服务重启成功！")
            return True
        else:
            print("❌ API服务重启失败")
            return False
            
    except Exception as e:
        print(f"❌ 重启失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始强制重启API服务...")
    print("=" * 50)
    
    # 检查ESPnet服务状态
    if check_espnet_status():
        print("✅ ESPnet服务正常运行")
    else:
        print("❌ ESPnet服务不可用")
        exit(1)
    
    # 检查当前API状态
    if check_api_status():
        print("✅ API服务当前正常运行")
    else:
        print("❌ API服务当前不可用")
        exit(1)
    
    # 测试当前连接
    print("\n🧪 测试当前API网关到ESPnet的连接...")
    if test_api_espnet_connection():
        print("🎉 连接已经正常，无需重启！")
        exit(0)
    
    # 需要重启
    print("\n🔄 需要重启API服务以应用新配置...")
    if restart_using_docker_commands():
        print("\n⏳ 等待服务稳定...")
        time.sleep(5)
        
        # 重新测试连接
        print("\n🧪 重新测试连接...")
        if test_api_espnet_connection():
            print("\n🎉 重启成功！API网关现在可以连接到ESPnet了！")
        else:
            print("\n❌ 重启后仍然无法连接，需要进一步调试")
    else:
        print("\n❌ 重启失败") 