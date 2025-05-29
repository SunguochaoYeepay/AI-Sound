#!/usr/bin/env python3
"""
最终测试脚本 - 验证之前失败的API接口
"""

import requests
import time
import sys

def test_api():
    base_url = "http://127.0.0.1:9930"
    
    # 等待服务器启动
    print("等待API服务器启动...")
    time.sleep(5)
    
    # 测试之前失败的接口
    tests = [
        ("GET", "/api/engines/health", "所有引擎健康检查"),
        ("GET", "/api/voices/", "声音列表"),
        ("GET", "/api/tts/engines", "TTS引擎列表"),
        ("GET", "/api/voices/voice_001/preview", "声音预览 (使用正确ID)")
    ]
    
    print("\n🔍 测试之前失败的API接口...")
    print("=" * 60)
    
    success_count = 0
    
    for method, path, description in tests:
        url = f"{base_url}{path}"
        print(f"\n测试: {method} {path}")
        print(f"描述: {description}")
        
        try:
            response = requests.get(url, timeout=10)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ 成功!")
                success_count += 1
                
                # 尝试解析JSON响应
                try:
                    data = response.json()
                    if isinstance(data, dict) and 'data' in data:
                        print(f"返回数据类型: {type(data['data'])}")
                    elif isinstance(data, dict) and 'engines' in data:
                        print(f"引擎数量: {len(data['engines'])}")
                    else:
                        print(f"响应格式: {type(data)}")
                except:
                    print("响应不是JSON格式")
            else:
                print(f"❌ 失败 - HTTP {response.status_code}")
                print(f"错误信息: {response.text[:100]}...")
                
        except requests.exceptions.ConnectionError:
            print("❌ 连接失败 - API服务器可能未启动")
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 最终结果: {success_count}/{len(tests)} 个接口修复成功")
    
    if success_count == len(tests):
        print("🎉 恭喜！所有之前失败的接口都已修复！")
        return 0
    else:
        print(f"⚠️ 还有 {len(tests) - success_count} 个接口需要继续修复")
        return 1

if __name__ == "__main__":
    sys.exit(test_api()) 