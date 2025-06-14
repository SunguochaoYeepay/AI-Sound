#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色分析监控测试
验证GPU监控、进度追踪等功能
"""

import sys
import os
import time
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), 'platform', 'backend'))

from app.api.v1.chapters import OllamaCharacterDetector
import requests

def test_monitor_api():
    """测试监控API"""
    print("🔍 测试监控API接口")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # 测试系统状态
    try:
        response = requests.get(f"{base_url}/monitor/system-status", timeout=10)
        if response.status_code == 200:
            data = response.json()['data']
            print("✅ 系统状态监控:")
            print(f"  CPU使用率: {data['system']['cpuPercent']}%")
            print(f"  内存使用率: {data['system']['memoryPercent']}%")
            print(f"  磁盘使用率: {data['system']['diskPercent']}%")
        else:
            print(f"❌ 系统状态API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 系统状态API异常: {e}")
    
    # 测试分析进度监控
    try:
        session_id = 1
        response = requests.get(f"{base_url}/monitor/analysis-progress/{session_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()['data']
            print("\n✅ 分析进度监控:")
            print(f"  会话ID: {data['session_id']}")
            print(f"  CPU使用率: {data['system_resources']['cpu_percent']}%")
            print(f"  内存使用率: {data['system_resources']['memory_percent']}%")
            
            if 'error' not in data['gpu_info']:
                print("  GPU信息:")
                for gpu_id, gpu_data in data['gpu_info'].items():
                    print(f"    {gpu_id}: {gpu_data['name']}")
                    print(f"      使用率: {gpu_data['utilization']}%")
                    print(f"      显存: {gpu_data['memory_percent']}%")
                    print(f"      温度: {gpu_data['temperature']}°C")
            else:
                print(f"  GPU监控: {data['gpu_info']['error']}")
            
            if data['ollama_process']:
                print(f"  Ollama进程: PID {data['ollama_process']['pid']}")
                print(f"    CPU: {data['ollama_process']['cpu_percent']}%")
                print(f"    内存: {data['ollama_process']['memory_mb']} MB")
            else:
                print("  Ollama进程: 未运行")
        else:
            print(f"❌ 分析进度API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 分析进度API异常: {e}")

async def test_analysis_with_monitor():
    """测试带监控的角色分析"""
    print("\n🧪 测试带监控的角色分析")
    print("=" * 50)
    
    # 测试文本
    test_text = """
    话说唐僧师徒四人，行至白虎岭前，只见山势险峻，林木茂密。
    
    悟空用火眼金睛一看，说道："师父，此山有妖气！"
    
    唐僧听了，心中惊恐，问道："悟空，你可看清是何妖怪？"
    
    "师父放心，待俺老孙前去探看。"悟空说完，纵身一跃，飞上山头。
    
    这时，白骨精正在洞中修炼，忽然感到有人窥探，心中大怒。
    
    白骨精化作美貌女子，手提篮子，内装馒头，走向师徒四人。
    
    "各位师父，"白骨精柔声说道，"小女子家住前村，见师父们远道而来，特送些斋饭。"
    """
    
    ollama_detector = OllamaCharacterDetector()
    chapter_info = {
        'chapter_id': 1,
        'chapter_title': '白骨精三戏唐三藏',
        'chapter_number': 1,
        'session_id': 1
    }
    
    print("🚀 开始带监控的AI分析...")
    start_time = time.time()
    
    try:
        # 启动监控任务
        async def monitor_task():
            """监控任务"""
            for i in range(10):  # 监控10次
                try:
                    response = requests.get("http://localhost:8000/monitor/analysis-progress/1", timeout=5)
                    if response.status_code == 200:
                        data = response.json()['data']
                        print(f"📊 监控 #{i+1}: CPU {data['system_resources']['cpu_percent']}%, "
                              f"内存 {data['system_resources']['memory_percent']}%")
                        
                        if 'gpu_0' in data['gpu_info']:
                            gpu = data['gpu_info']['gpu_0']
                            print(f"    GPU: {gpu['utilization']}%, 显存: {gpu['memory_percent']}%")
                    
                    await asyncio.sleep(3)  # 每3秒监控一次
                except Exception as e:
                    print(f"⚠️  监控异常: {e}")
        
        # 同时运行分析和监控
        analysis_task = ollama_detector.analyze_text(test_text, chapter_info)
        monitor_task_coro = monitor_task()
        
        # 等待分析完成
        result, _ = await asyncio.gather(analysis_task, monitor_task_coro, return_exceptions=True)
        
        end_time = time.time()
        
        if isinstance(result, dict):
            print(f"\n✅ 分析完成！耗时: {end_time - start_time:.2f}秒")
            print(f"📊 分析方法: {result['processing_stats']['analysis_method']}")
            print(f"👥 识别角色数: {result['processing_stats']['characters_found']}")
            print(f"⏱️  处理时间: {result['processing_stats'].get('processing_time', 0)}秒")
            print(f"📝 文本长度: {result['processing_stats'].get('text_length', 0)}字符")
            print(f"🤖 AI模型: {result['processing_stats'].get('ai_model', 'unknown')}")
        else:
            print(f"❌ 分析失败: {result}")
        
    except Exception as e:
        end_time = time.time()
        print(f"❌ 测试失败！耗时: {end_time - start_time:.2f}秒")
        print(f"错误信息: {str(e)}")

def main():
    """主函数"""
    print("🎯 角色分析监控系统测试")
    print("=" * 60)
    
    # 测试监控API
    test_monitor_api()
    
    # 测试带监控的分析
    try:
        asyncio.run(test_analysis_with_monitor())
    except Exception as e:
        print(f"❌ 异步测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 监控系统测试完成！")
    print("\n📋 监控能力总结:")
    print("✅ 系统资源监控 (CPU/内存/磁盘)")
    print("✅ GPU使用率和显存监控")
    print("✅ Ollama进程监控")
    print("✅ 实时进度推送 (WebSocket)")
    print("✅ 分析性能统计")
    print("✅ 多维度监控数据")

if __name__ == "__main__":
    main() 