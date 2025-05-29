#!/usr/bin/env python3
"""
简单核心功能测试
专门测试最关键的TTS合成功能
"""

import requests
import json
import sys
from datetime import datetime

def test_core_functions(base_url="http://localhost:9930"):
    """测试核心功能"""
    print("🔥 测试最核心的API功能...")
    print(f"⏰ 测试时间: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 50)
    
    results = []
    
    # 1. 测试系统健康检查
    print("\n1. 📋 测试系统健康检查...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        success = response.status_code == 200
        print(f"   {'✅' if success else '❌'} 健康检查: {response.status_code}")
        results.append(("系统健康检查", success))
    except Exception as e:
        print(f"   ❌ 健康检查异常: {e}")
        results.append(("系统健康检查", False))
    
    # 2. 测试引擎列表
    print("\n2. 🔧 测试引擎列表...")
    try:
        response = requests.get(f"{base_url}/api/engines/", timeout=5)
        success = response.status_code == 200
        print(f"   {'✅' if success else '❌'} 引擎列表: {response.status_code}")
        if success:
            data = response.json()
            print(f"   📊 引擎数量: {len(data.get('engines', []))}")
        results.append(("引擎列表", success))
    except Exception as e:
        print(f"   ❌ 引擎列表异常: {e}")
        results.append(("引擎列表", False))
    
    # 3. 测试声音列表
    print("\n3. 🎤 测试声音列表...")
    try:
        response = requests.get(f"{base_url}/api/voices/", timeout=5)
        success = response.status_code == 200
        print(f"   {'✅' if success else '❌'} 声音列表: {response.status_code}")
        if success:
            data = response.json()
            print(f"   📊 声音数量: {len(data.get('voices', []))}")
        results.append(("声音列表", success))
    except Exception as e:
        print(f"   ❌ 声音列表异常: {e}")
        results.append(("声音列表", False))
    
    # 4. 测试异步TTS合成（最关键）
    print("\n4. 🗣️ 测试异步TTS合成...")
    try:
        tts_data = {
            "text": "老爹，这是核心功能测试",
            "voice_id": "default",
            "format": "wav"
        }
        response = requests.post(f"{base_url}/api/tts/synthesize-async", json=tts_data, timeout=10)
        success = response.status_code in [200, 201, 202]
        print(f"   {'✅' if success else '❌'} 异步TTS合成: {response.status_code}")
        if success:
            data = response.json()
            task_id = data.get('task_id')
            if task_id:
                print(f"   ✨ 任务ID: {task_id[:8]}...")
        results.append(("异步TTS合成", success))
    except Exception as e:
        print(f"   ❌ 异步TTS合成异常: {e}")
        results.append(("异步TTS合成", False))
    
    # 5. 测试同步TTS合成（问题功能）
    print("\n5. 🚨 测试同步TTS合成（已知问题）...")
    try:
        tts_data = {
            "text": "同步测试文本",
            "voice_id": "default",
            "format": "wav"
        }
        response = requests.post(f"{base_url}/api/tts/synthesize", json=tts_data, timeout=10)
        success = response.status_code == 200
        print(f"   {'✅' if success else '❌'} 同步TTS合成: {response.status_code}")
        if not success:
            print(f"   📄 错误信息: {response.text[:100]}...")
        results.append(("同步TTS合成", success))
    except Exception as e:
        print(f"   ❌ 同步TTS合成异常: {e}")
        results.append(("同步TTS合成", False))
    
    # 6. 测试批量TTS
    print("\n6. 📦 测试批量TTS合成...")
    try:
        batch_data = {
            "texts": ["批量测试1", "批量测试2"],
            "voice_id": "default",
            "format": "wav"
        }
        response = requests.post(f"{base_url}/api/tts/batch", json=batch_data, timeout=10)
        success = response.status_code in [200, 201, 202]
        print(f"   {'✅' if success else '❌'} 批量TTS合成: {response.status_code}")
        results.append(("批量TTS合成", success))
    except Exception as e:
        print(f"   ❌ 批量TTS合成异常: {e}")
        results.append(("批量TTS合成", False))
    
    # 生成摘要
    print("\n" + "=" * 50)
    print("📊 核心功能测试摘要")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    failed_tests = total_tests - passed_tests
    
    print(f"✅ 通过: {passed_tests}/{total_tests}")
    print(f"❌ 失败: {failed_tests}/{total_tests}")
    print(f"📈 通过率: {passed_tests/total_tests*100:.1f}%")
    
    # 显示详细结果
    print(f"\n📋 详细结果:")
    for test_name, success in results:
        emoji = "✅" if success else "❌"
        print(f"   {emoji} {test_name}")
    
    # 核心业务评估
    core_functions = ["异步TTS合成", "批量TTS合成", "引擎列表", "声音列表"]
    core_results = [success for test_name, success in results if test_name in core_functions]
    core_passed = sum(core_results)
    
    print(f"\n🚀 核心业务功能: {core_passed}/{len(core_results)} 正常")
    
    if core_passed >= len(core_results) * 0.75:
        print("🎉 核心功能基本正常！")
        return True
    else:
        print("🚨 核心功能存在重大问题！")
        return False

if __name__ == "__main__":
    try:
        success = test_core_functions()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ 测试被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试异常: {e}")
        sys.exit(1)