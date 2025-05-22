"""
TTS文本发音匹配度测试脚本
用于测试TTS的文本内容是否匹配生成的语音
"""

import requests
import time
import os
import json
import wave
import numpy as np
from datetime import datetime

# 确保输出目录存在
os.makedirs("test_pronunciation", exist_ok=True)

# API端点
API_URL = "http://127.0.0.1:9930/api/tts/text"

# 测试用例 - 简单且易于判断的短句
TEST_CASES = [
    {
        "name": "数字1-10",
        "text": "一二三四五六七八九十",
        "voice_id": "范闲"
    },
    {
        "name": "简单句1",
        "text": "今天天气真好",
        "voice_id": "范闲"
    },
    {
        "name": "简单句2",
        "text": "我喜欢吃苹果",
        "voice_id": "周杰伦"
    },
    {
        "name": "问候语",
        "text": "你好，很高兴认识你",
        "voice_id": "范闲"
    },
    {
        "name": "英文句子",
        "text": "Hello, nice to meet you",
        "voice_id": "english_talk"
    }
]

def run_test(test_case):
    """运行单个测试"""
    print(f"\n测试: {test_case['name']}")
    print(f"  文本: {test_case['text']}")
    print(f"  声音ID: {test_case['voice_id']}")
    
    # 构建请求
    payload = {
        "text": test_case['text'],
        "voice_id": test_case['voice_id'],
        "return_base64": False,
        "output_format": "wav"
    }
    
    try:
        # 发送请求
        start_time = time.time()
        response = requests.post(
            API_URL,
            json=payload,
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        process_time = time.time() - start_time
        
        # 处理响应
        if response.status_code != 200:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            print(f"  响应: {response.text[:100]}")
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text[:100]}"
            }
        
        # 保存文件
        timestamp = int(time.time())
        filename = f"{test_case['voice_id']}_{test_case['name'].replace(' ', '_')}_{timestamp}.wav"
        output_path = os.path.join("test_pronunciation", filename)
        
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        # 分析音频
        file_size = len(response.content) / 1024  # KB
        is_mock = file_size < 10  # 如果小于10KB，可能是模拟音频
        
        if is_mock:
            print(f"⚠️ 生成的是模拟音频 (大小: {file_size:.2f} KB)")
        else:
            print(f"✅ 生成了真实音频 (大小: {file_size:.2f} KB)")
        
        print(f"  处理时间: {process_time:.2f}秒")
        print(f"  文件保存为: {output_path}")
        
        # 返回结果
        return {
            "success": True,
            "filename": output_path,
            "size": file_size,
            "is_mock": is_mock,
            "process_time": process_time
        }
        
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def analyze_results(results):
    """分析结果并生成报告"""
    print("\n===== 测试结果分析 =====")
    
    # 统计成功/失败
    success_count = sum(1 for r in results if r.get("success", False))
    fail_count = len(results) - success_count
    
    # 统计模拟音频
    mock_count = sum(1 for r in results if r.get("success") and r.get("is_mock", False))
    real_count = success_count - mock_count
    
    print(f"总测试用例: {len(results)}")
    print(f"成功: {success_count}, 失败: {fail_count}")
    print(f"模拟音频: {mock_count}, 真实音频: {real_count}")
    
    # 计算平均处理时间
    if success_count > 0:
        avg_time = sum(r.get("process_time", 0) for r in results if r.get("success")) / success_count
        print(f"平均处理时间: {avg_time:.2f}秒")
    
    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "total": len(results),
        "success": success_count,
        "fail": fail_count,
        "mock_audio": mock_count,
        "real_audio": real_count,
        "details": results
    }
    
    report_path = os.path.join("test_pronunciation", f"report_{int(time.time())}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n报告已保存到: {report_path}")
    
    # 提供进一步建议
    if mock_count == len(results):
        print("\n🔴 所有测试都生成了模拟音频，这表明TTS系统未正确加载模型。")
        print("建议: 运行check_model_load.py进行诊断，并确保正确设置系统路径和模型文件。")
    elif real_count > 0:
        print("\n🟢 成功生成了真实音频，请认真听取音频检查文本与发音是否匹配。")
        print("建议: 分别听取每个音频文件，检查以下问题:")
        print("1. 发音是否与文本内容匹配")
        print("2. 不同角色的声音是否有区别")
        print("3. 是否有明显的噪音或异常")

def main():
    """主函数"""
    print("===== TTS文本发音匹配度测试 =====")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试用例数: {len(TEST_CASES)}")
    
    results = []
    for i, test_case in enumerate(TEST_CASES):
        print(f"\n[{i+1}/{len(TEST_CASES)}] 测试: {test_case['name']}")
        result = run_test(test_case)
        result["test_case"] = test_case
        results.append(result)
        
        # 避免连续请求
        if i < len(TEST_CASES) - 1:
            time.sleep(1)
    
    analyze_results(results)
    
    print("\n测试完成。请手动检查生成的音频文件，判断文本与语音是否匹配。")

if __name__ == "__main__":
    main() 