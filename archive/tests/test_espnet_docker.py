#!/usr/bin/env python3
"""
测试ESPnet Docker服务状态
"""

import subprocess
import json
import urllib.request
import urllib.error

def check_docker_containers():
    """检查Docker容器状态"""
    print("🐳 检查Docker容器状态")
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            print("当前运行的容器:")
            for line in lines:
                if 'espnet' in line.lower():
                    print(f"  🎯 ESPnet容器: {line}")
                else:
                    print(f"  📦 {line}")
            
            # 检查是否有ESPnet容器
            has_espnet = any('espnet' in line.lower() for line in lines[1:])
            if not has_espnet:
                print("  ⚠️ 未发现ESPnet容器运行")
                return False
            return True
        else:
            print(f"❌ Docker命令失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 检查Docker失败: {e}")
        return False

def check_docker_images():
    """检查Docker镜像"""
    print("\n🖼️ 检查ESPnet Docker镜像")
    try:
        result = subprocess.run(['docker', 'images'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            espnet_images = [line for line in lines if 'espnet' in line.lower()]
            if espnet_images:
                print("发现ESPnet镜像:")
                for img in espnet_images:
                    print(f"  🖼️ {img}")
                return True
            else:
                print("  ⚠️ 未发现ESPnet Docker镜像")
                return False
        else:
            print(f"❌ 检查镜像失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 检查镜像失败: {e}")
        return False

def test_espnet_endpoint():
    """测试ESPnet端点"""
    print("\n🌐 测试ESPnet端点连接")
    base_url = "http://127.0.0.1:9001"
    
    try:
        req = urllib.request.Request(f"{base_url}/health")
        with urllib.request.urlopen(req, timeout=5) as response:
            health_data = json.loads(response.read().decode())
            print(f"  ✅ ESPnet API响应: {health_data}")
            return True
    except urllib.error.URLError as e:
        print(f"  ❌ ESPnet API连接失败: {e}")
        return False
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🔍 ESPnet Docker服务诊断")
    print("=" * 50)
    
    # 检查Docker容器
    containers_ok = check_docker_containers()
    
    # 检查Docker镜像
    images_ok = check_docker_images()
    
    # 测试API端点
    api_ok = test_espnet_endpoint()
    
    print("\n📊 诊断结果:")
    print(f"  Docker容器: {'✅' if containers_ok else '❌'}")
    print(f"  Docker镜像: {'✅' if images_ok else '❌'}")
    print(f"  API端点: {'✅' if api_ok else '❌'}")
    
    if not any([containers_ok, api_ok]):
        print("\n💡 建议:")
        if images_ok:
            print("  1. ESPnet镜像存在，但容器未运行")
            print("  2. 需要启动ESPnet Docker容器")
            print("  3. 命令示例:")
            print("     docker run -d --name espnet-service --gpus all -p 9001:9001 -v D:/AI-Sound/MegaTTS/espnet:/workspace espnet-image")
        else:
            print("  1. 需要构建ESPnet Docker镜像")
            print("  2. 在MegaTTS/espnet目录运行:")
            print("     docker build -t espnet-service .")

if __name__ == "__main__":
    main()