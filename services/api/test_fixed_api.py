#!/usr/bin/env python3
"""
测试修复后的API接口
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:9930"

async def test_api_endpoints():
    """测试API端点"""
    
    async with aiohttp.ClientSession() as session:
        
        # 测试基础端点
        endpoints_to_test = [
            ("GET", "/health", "健康检查"),
            ("GET", "/info", "系统信息"),
            ("GET", "/api/engines/", "引擎列表"),
            ("GET", "/api/voices/", "声音列表"),
            ("GET", "/api/characters/", "角色列表"),
            ("GET", "/api/tts/engines", "TTS引擎"),
            ("GET", "/api/tts/formats", "音频格式"),
            ("GET", "/api/voices/stats/languages", "语言统计"),
            ("GET", "/api/voices/stats/engines", "引擎统计"),
            ("GET", "/api/engines/stats/summary", "引擎摘要"),
            ("POST", "/api/engines/discover", "发现引擎"),
        ]
        
        results = []
        
        for method, endpoint, description in endpoints_to_test:
            try:
                url = f"{BASE_URL}{endpoint}"
                
                if method == "GET":
                    async with session.get(url) as response:
                        status = response.status
                        if status == 200:
                            data = await response.json()
                            results.append(f"✅ {description} ({endpoint}) - 成功")
                        else:
                            results.append(f"❌ {description} ({endpoint}) - 状态码: {status}")
                
                elif method == "POST":
                    async with session.post(url, json={}) as response:
                        status = response.status
                        if status in [200, 201]:
                            data = await response.json()
                            results.append(f"✅ {description} ({endpoint}) - 成功")
                        else:
                            results.append(f"❌ {description} ({endpoint}) - 状态码: {status}")
                            
            except Exception as e:
                results.append(f"❌ {description} ({endpoint}) - 错误: {str(e)}")
        
        # 输出结果
        print("\n" + "="*80)
        print(f"🚀 API修复测试结果 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        success_count = 0
        for result in results:
            print(result)
            if result.startswith("✅"):
                success_count += 1
        
        print("="*80)
        print(f"📊 测试摘要: {success_count}/{len(results)} 个端点通过测试")
        print(f"🎯 成功率: {success_count/len(results)*100:.1f}%")
        
        if success_count == len(results):
            print("🎉 所有API端点测试通过！")
        elif success_count > len(results) * 0.8:
            print("✨ 大部分API端点正常工作！")
        else:
            print("⚠️  仍有一些API端点需要修复")
        
        print("="*80)

async def main():
    """主函数"""
    print("🔧 开始测试修复后的API...")
    await test_api_endpoints()

if __name__ == "__main__":
    asyncio.run(main()) 