#!/usr/bin/env python3
"""
诊断TTS服务问题
"""
import requests
import json

def diagnose_tts():
    print("🔍 === 诊断TTS服务状态 ===")
    
    # 1. 检查TTS服务健康状态
    print("\n1. 检查TTS服务健康状态...")
    try:
        health_response = requests.get("http://localhost:7929/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ TTS服务运行正常")
            health_data = health_response.json()
            print(f"   状态: {health_data}")
        else:
            print(f"❌ TTS服务状态异常: {health_response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ TTS服务未启动或无法连接")
        print("   请检查MegaTTS3服务是否在端口7929运行")
        return
    except Exception as e:
        print(f"❌ TTS健康检查失败: {e}")
        return
    
    # 2. 检查GPU状态
    print("\n2. 检查GPU状态...")
    try:
        gpu_response = requests.get("http://localhost:7929/gpu-info", timeout=5)
        if gpu_response.status_code == 200:
            gpu_data = gpu_response.json()
            print("✅ GPU信息获取成功")
            print(f"   GPU数量: {gpu_data.get('gpu_count', '未知')}")
            print(f"   当前GPU: {gpu_data.get('current_device', '未知')}")
            print(f"   GPU内存: {gpu_data.get('memory_info', '未知')}")
        else:
            print(f"⚠️  无法获取GPU信息: {gpu_response.status_code}")
    except Exception as e:
        print(f"⚠️  GPU信息检查失败: {e}")
    
    # 3. 尝试简单的TTS测试
    print("\n3. 进行简单TTS合成测试...")
    test_data = {
        "text": "你好，这是测试。",
        "reference_audio": "",  # 使用默认声音
        "time_step": 20,
        "p_weight": 1.0,
        "t_weight": 1.0
    }
    
    try:
        tts_response = requests.post("http://localhost:7929/synthesize", 
                                   json=test_data, timeout=30)
        if tts_response.status_code == 200:
            print("✅ TTS合成测试成功")
            result = tts_response.json()
            print(f"   合成结果: {result.get('message', '成功')}")
        else:
            print(f"❌ TTS合成测试失败: {tts_response.status_code}")
            try:
                error_data = tts_response.json()
                print(f"   错误信息: {error_data.get('error', '未知错误')}")
                
                # 分析错误类型
                error_msg = error_data.get('error', '')
                if 'CUDA' in error_msg:
                    print("\n💡 这是CUDA GPU错误，可能的解决方案:")
                    print("   1. 检查GPU驱动是否正确安装")
                    print("   2. 检查CUDA版本是否与PyTorch兼容")
                    print("   3. 检查GPU内存是否充足")
                    print("   4. 尝试重启MegaTTS3服务")
                    print("   5. 如果问题持续，可以尝试使用CPU模式")
                elif 'memory' in error_msg.lower():
                    print("\n💡 这是内存错误，建议:")
                    print("   1. 释放其他GPU进程的显存")
                    print("   2. 重启MegaTTS3服务")
                    print("   3. 减少batch_size参数")
            except:
                print(f"   原始响应: {tts_response.text}")
    except requests.exceptions.Timeout:
        print("❌ TTS合成超时")
        print("   这可能表示服务响应很慢或卡住了")
    except Exception as e:
        print(f"❌ TTS合成测试异常: {e}")
    
    # 4. 建议
    print("\n💡 建议操作:")
    print("1. 如果是CUDA错误，尝试重启MegaTTS3服务")
    print("2. 检查系统GPU内存使用情况")
    print("3. 确认MegaTTS3服务配置正确")
    print("4. 如果问题持续，可以暂时禁用GPU加速")

if __name__ == "__main__":
    diagnose_tts() 