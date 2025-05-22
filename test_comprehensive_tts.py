"""
综合测试脚本：测试不同声音、不同语言文本和TTS输出质量
"""

import requests
import time
import os
import json
import wave
import numpy as np
from datetime import datetime
import argparse

# 确保输出目录存在
os.makedirs("test_results", exist_ok=True)

# 默认API端点
DEFAULT_API_URL = "http://127.0.0.1:9970/api/tts/text"

# 测试用例
TEST_CASES = [
    # 中文测试
    {
        "name": "中文数字",
        "text": "一二三四五六七八九十",
        "voice_id": "范闲",
        "language": "zh"
    },
    {
        "name": "中文短句",
        "text": "今天天气真好，我很开心。",
        "voice_id": "范闲",
        "language": "zh"
    },
    {
        "name": "中文中句",
        "text": "人工智能正在改变我们的生活方式，语音合成技术让机器可以说话。",
        "voice_id": "周杰伦",
        "language": "zh"
    },
    
    # 英文测试
    {
        "name": "英文短句",
        "text": "Hello, nice to meet you.",
        "voice_id": "english_talk",
        "language": "en"
    },
    {
        "name": "英文中句",
        "text": "Artificial intelligence is transforming the way we live and work.",
        "voice_id": "english_talk", 
        "language": "en"
    },
    
    # 混合语言测试
    {
        "name": "中英混合",
        "text": "我正在学习AI技术，包括Machine Learning和Deep Learning。",
        "voice_id": "范闲",
        "language": "mixed"
    },
    
    # 情感测试
    {
        "name": "开心情感",
        "text": "今天是我的生日，我收到了很多礼物，非常开心！",
        "voice_id": "范闲",
        "emotion_type": "happy",
        "emotion_intensity": 0.8,
        "language": "zh"
    },
    {
        "name": "悲伤情感",
        "text": "他离开了，再也不会回来了，这让我很难过。",
        "voice_id": "周杰伦",
        "emotion_type": "sad",
        "emotion_intensity": 0.7,
        "language": "zh"
    },
    
    # 不同声音测试相同文本
    {
        "name": "范闲声音",
        "text": "这是一个语音合成测试，测试不同的声音效果。",
        "voice_id": "范闲",
        "language": "zh"
    },
    {
        "name": "周杰伦声音",
        "text": "这是一个语音合成测试，测试不同的声音效果。",
        "voice_id": "周杰伦",
        "language": "zh"
    }
]

def run_test(test_case, api_url, output_dir):
    """运行单个测试用例"""
    print(f"\n测试: {test_case['name']}")
    print(f"  文本: {test_case['text']}")
    print(f"  声音ID: {test_case['voice_id']}")
    print(f"  语言: {test_case['language']}")
    
    # 构建请求
    payload = {
        "text": test_case['text'],
        "voice_id": test_case['voice_id'],
        "return_base64": False,
        "output_format": "wav"
    }
    
    # 添加情感参数（如果有）
    if "emotion_type" in test_case:
        payload["emotion_type"] = test_case["emotion_type"]
        print(f"  情感类型: {test_case['emotion_type']}")
        
    if "emotion_intensity" in test_case:
        payload["emotion_intensity"] = test_case["emotion_intensity"]
        print(f"  情感强度: {test_case['emotion_intensity']}")
    
    try:
        # 发送请求
        start_time = time.time()
        response = requests.post(
            api_url,
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
        output_path = os.path.join(output_dir, filename)
        
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

def analyze_results(results, output_dir):
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
    
    # 统计每种声音的结果
    voice_stats = {}
    for i, result in enumerate(results):
        if not result.get("success"):
            continue
            
        test_case = TEST_CASES[i]
        voice_id = test_case["voice_id"]
        
        if voice_id not in voice_stats:
            voice_stats[voice_id] = {"total": 0, "real": 0, "mock": 0}
            
        voice_stats[voice_id]["total"] += 1
        if result.get("is_mock"):
            voice_stats[voice_id]["mock"] += 1
        else:
            voice_stats[voice_id]["real"] += 1
    
    # 打印每种声音的统计
    print("\n声音统计:")
    for voice_id, stats in voice_stats.items():
        print(f"  {voice_id}: 总共 {stats['total']}, 真实 {stats['real']}, 模拟 {stats['mock']}")
    
    # 计算平均处理时间
    if success_count > 0:
        avg_time = sum(r.get("process_time", 0) for r in results if r.get("success")) / success_count
        print(f"\n平均处理时间: {avg_time:.2f}秒")
    
    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "total": len(results),
        "success": success_count,
        "fail": fail_count,
        "mock_audio": mock_count,
        "real_audio": real_count,
        "voice_stats": voice_stats,
        "details": results
    }
    
    report_path = os.path.join(output_dir, f"report_{int(time.time())}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n报告已保存到: {report_path}")
    
    # 提供进一步建议
    if mock_count == len(results):
        print("\n🔴 所有测试都生成了模拟音频，这表明TTS系统未正确加载模型。")
        print("建议: ")
        print("1. 运行check_model_load.py进行诊断")
        print("2. 确保正确设置系统路径和模型文件")
        print("3. 检查engine.py中是否强制使用模拟模式")
    elif real_count > 0:
        print("\n🟢 成功生成了真实音频，请认真听取音频检查文本与发音是否匹配。")
        print("建议: 分别听取每个音频文件，检查以下问题:")
        print("1. 发音是否与文本内容匹配")
        print("2. 不同角色的声音是否有区别")
        print("3. 情感参数是否有效果")
        print("4. 是否有明显的噪音或异常")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="TTS综合测试工具")
    parser.add_argument("--api", default=DEFAULT_API_URL, help="TTS API端点URL")
    parser.add_argument("--output", default="test_results", help="输出目录")
    parser.add_argument("--subset", type=int, help="只测试前N个用例")
    args = parser.parse_args()
    
    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)
    
    print("===== TTS综合测试 =====")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API端点: {args.api}")
    print(f"输出目录: {args.output}")
    
    # 获取要测试的用例
    cases_to_test = TEST_CASES
    if args.subset and args.subset > 0:
        cases_to_test = TEST_CASES[:args.subset]
        print(f"测试前 {args.subset} 个用例，共 {len(cases_to_test)} 个")
    else:
        print(f"测试所有 {len(cases_to_test)} 个用例")
    
    results = []
    for i, test_case in enumerate(cases_to_test):
        print(f"\n[{i+1}/{len(cases_to_test)}] 测试: {test_case['name']}")
        result = run_test(test_case, args.api, args.output)
        results.append(result)
        
        # 避免连续请求
        if i < len(cases_to_test) - 1:
            time.sleep(1)
    
    analyze_results(results, args.output)
    
    print("\n测试完成。请手动检查生成的音频文件，判断文本与语音是否匹配。")

if __name__ == "__main__":
    main()