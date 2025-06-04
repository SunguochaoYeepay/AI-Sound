#!/usr/bin/env python3
"""
修复MegaTTS3 CUDA错误
"""
import requests
import json
import time

def test_simple_text():
    """使用最简单的文本测试TTS"""
    print("🔍 === 测试最简单文本 ===")
    
    # 使用最基础的测试文本
    simple_texts = [
        "你好",
        "测试", 
        "hello"
    ]
    
    for text in simple_texts:
        print(f"\n测试文本: '{text}'")
        try:
            # 创建最简单的测试项目
            project_data = {
                "name": f"CUDA测试_{int(time.time())}",
                "originalText": text
            }
            
            response = requests.post('http://localhost:8000/api/novel-reader/projects', 
                                   json=project_data, timeout=10)
            
            if response.status_code == 200:
                project_id = response.json()['data']['id']
                print(f"✅ 项目创建成功: {project_id}")
                
                # 尝试开始生成（这里会触发TTS）
                start_response = requests.post(
                    f'http://localhost:8000/api/novel-reader/projects/{project_id}/start-generation',
                    timeout=30
                )
                
                if start_response.status_code == 200:
                    print("✅ TTS合成成功！CUDA问题已解决")
                    return True
                else:
                    error_info = start_response.json()
                    print(f"❌ TTS失败: {error_info.get('error', '未知错误')}")
                    
                    # 检查是否还是CUDA错误
                    if 'CUDA' in str(error_info):
                        print("⚠️  仍然是CUDA错误，需要进一步诊断")
                    
            else:
                print(f"❌ 项目创建失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    return False

def docker_cuda_reset():
    """重置Docker容器的CUDA状态"""
    print("🔧 === 重置Docker CUDA状态 ===")
    
    # 这里需要用户手动执行Docker命令
    print("请以管理员身份运行以下命令:")
    print("1. docker exec megatts3-api nvidia-smi")
    print("2. docker restart megatts3-api")
    print("3. 等待30秒让服务完全启动")

if __name__ == "__main__":
    print("🚨 === MegaTTS3 CUDA错误修复工具 ===")
    
    # 先测试简单文本
    if not test_simple_text():
        print("\n💡 建议操作:")
        print("1. 重启MegaTTS3 Docker容器")
        print("2. 检查GPU内存使用情况") 
        print("3. 如果问题持续，可能需要重启整个系统")
        docker_cuda_reset() 