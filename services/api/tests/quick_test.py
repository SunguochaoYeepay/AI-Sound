"""
快速接口测试脚本
用于验证核心API接口是否正常工作
"""

import asyncio
import httpx
import json
import sys
from typing import Dict, Any


class QuickAPITester:
    """快速API测试器"""
    
    def __init__(self, base_url: str = "http://localhost:9930"):
        self.base_url = base_url
        self.client = None
        self.test_data = {}
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def test_health_check(self) -> bool:
        """测试健康检查"""
        try:
            response = await self.client.get("/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 健康检查通过: {data.get('status', 'unknown')}")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            return False
    
    async def test_root_endpoint(self) -> bool:
        """测试根端点"""
        try:
            response = await self.client.get("/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 根端点正常: {data.get('name', 'AI-Sound')} v{data.get('version', 'unknown')}")
                return True
            else:
                print(f"❌ 根端点失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 根端点异常: {e}")
            return False
    
    async def test_engines_api(self) -> bool:
        """测试引擎API"""
        try:
            # 获取引擎列表
            response = await self.client.get("/api/engines")
            if response.status_code != 200:
                print(f"❌ 获取引擎列表失败: {response.status_code}")
                return False
            
            engines_data = response.json()
            print(f"✅ 引擎列表获取成功: {len(engines_data.get('engines', []))} 个引擎")
            
            # 创建测试引擎
            test_engine = {
                "name": "quick-test-engine",
                "type": "megatts3",
                "description": "快速测试引擎",
                "url": "http://localhost:7929",
                "config": {
                    "model_path": "/test/model.pth",
                    "use_gpu": False
                }
            }
            
            create_response = await self.client.post("/api/engines", json=test_engine)
            if create_response.status_code == 201:
                engine_data = create_response.json()
                engine_id = engine_data["id"]
                self.test_data["engine_id"] = engine_id
                print(f"✅ 引擎创建成功: {engine_id}")
                
                # 获取引擎详情
                get_response = await self.client.get(f"/api/engines/{engine_id}")
                if get_response.status_code == 200:
                    print("✅ 引擎详情获取成功")
                    return True
                else:
                    print(f"❌ 引擎详情获取失败: {get_response.status_code}")
                    return False
            else:
                print(f"❌ 引擎创建失败: {create_response.status_code}")
                if create_response.status_code == 422:
                    print(f"   错误详情: {create_response.json()}")
                return False
                
        except Exception as e:
            print(f"❌ 引擎API测试异常: {e}")
            return False
    
    async def test_voices_api(self) -> bool:
        """测试声音API"""
        try:
            # 获取声音列表
            response = await self.client.get("/api/voices")
            if response.status_code != 200:
                print(f"❌ 获取声音列表失败: {response.status_code}")
                return False
            
            voices_data = response.json()
            print(f"✅ 声音列表获取成功: {len(voices_data.get('voices', []))} 个声音")
            
            # 如果有测试引擎，创建测试声音
            if "engine_id" in self.test_data:
                test_voice = {
                    "name": "quick-test-voice",
                    "display_name": "快速测试声音",
                    "engine_id": self.test_data["engine_id"],
                    "gender": "female",
                    "style": "neutral",
                    "language": "zh-CN",
                    "config": {
                        "speaker_id": "speaker_001"
                    }
                }
                
                create_response = await self.client.post("/api/voices", json=test_voice)
                if create_response.status_code == 201:
                    voice_data = create_response.json()
                    voice_id = voice_data["id"]
                    self.test_data["voice_id"] = voice_id
                    print(f"✅ 声音创建成功: {voice_id}")
                    return True
                else:
                    print(f"❌ 声音创建失败: {create_response.status_code}")
                    return False
            else:
                print("⚠️  跳过声音创建测试（无可用引擎）")
                return True
                
        except Exception as e:
            print(f"❌ 声音API测试异常: {e}")
            return False
    
    async def test_characters_api(self) -> bool:
        """测试角色API"""
        try:
            # 获取角色列表
            response = await self.client.get("/api/characters")
            if response.status_code != 200:
                print(f"❌ 获取角色列表失败: {response.status_code}")
                return False
            
            characters_data = response.json()
            print(f"✅ 角色列表获取成功: {len(characters_data.get('characters', []))} 个角色")
            
            # 创建测试角色
            test_character = {
                "name": "quick-test-character",
                "display_name": "快速测试角色",
                "description": "用于快速测试的角色",
                "gender": "female",
                "type": "protagonist"
            }
            
            create_response = await self.client.post("/api/characters", json=test_character)
            if create_response.status_code == 201:
                character_data = create_response.json()
                character_id = character_data["id"]
                self.test_data["character_id"] = character_id
                print(f"✅ 角色创建成功: {character_id}")
                return True
            else:
                print(f"❌ 角色创建失败: {create_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 角色API测试异常: {e}")
            return False
    
    async def test_tts_api(self) -> bool:
        """测试TTS API"""
        try:
            # 获取支持的格式
            formats_response = await self.client.get("/api/tts/formats")
            if formats_response.status_code == 200:
                formats = formats_response.json()
                print(f"✅ 支持的格式: {len(formats.get('formats', []))} 种")
            
            # 如果有测试数据，尝试创建TTS任务
            if "voice_id" in self.test_data and "engine_id" in self.test_data:
                tts_request = {
                    "text": "这是一个快速测试文本",
                    "voice_id": self.test_data["voice_id"],
                    "engine_id": self.test_data["engine_id"],
                    "format": "wav"
                }
                
                tts_response = await self.client.post("/api/tts/synthesize", json=tts_request)
                if tts_response.status_code == 200:
                    task_data = tts_response.json()
                    task_id = task_data["task_id"]
                    self.test_data["task_id"] = task_id
                    print(f"✅ TTS任务创建成功: {task_id}")
                    
                    # 检查任务状态
                    status_response = await self.client.get(f"/api/tts/tasks/{task_id}")
                    if status_response.status_code == 200:
                        print("✅ TTS任务状态查询成功")
                        return True
                    else:
                        print(f"❌ TTS任务状态查询失败: {status_response.status_code}")
                        return False
                else:
                    print(f"❌ TTS任务创建失败: {tts_response.status_code}")
                    return False
            else:
                print("⚠️  跳过TTS测试（缺少必要的测试数据）")
                return True
                
        except Exception as e:
            print(f"❌ TTS API测试异常: {e}")
            return False
    
    async def cleanup(self):
        """清理测试数据"""
        print("\n🧹 清理测试数据...")
        
        # 删除TTS任务
        if "task_id" in self.test_data:
            try:
                await self.client.delete(f"/api/tts/tasks/{self.test_data['task_id']}")
                print("✅ TTS任务已删除")
            except Exception as e:
                print(f"⚠️  删除TTS任务失败: {e}")
        
        # 删除角色
        if "character_id" in self.test_data:
            try:
                await self.client.delete(f"/api/characters/{self.test_data['character_id']}")
                print("✅ 测试角色已删除")
            except Exception as e:
                print(f"⚠️  删除角色失败: {e}")
        
        # 删除声音
        if "voice_id" in self.test_data:
            try:
                await self.client.delete(f"/api/voices/{self.test_data['voice_id']}")
                print("✅ 测试声音已删除")
            except Exception as e:
                print(f"⚠️  删除声音失败: {e}")
        
        # 删除引擎
        if "engine_id" in self.test_data:
            try:
                await self.client.delete(f"/api/engines/{self.test_data['engine_id']}")
                print("✅ 测试引擎已删除")
            except Exception as e:
                print(f"⚠️  删除引擎失败: {e}")
    
    async def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("🚀 开始快速API接口测试...\n")
        
        tests = [
            ("健康检查", self.test_health_check),
            ("根端点", self.test_root_endpoint),
            ("引擎API", self.test_engines_api),
            ("声音API", self.test_voices_api),
            ("角色API", self.test_characters_api),
            ("TTS API", self.test_tts_api),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 测试 {test_name}...")
            try:
                if await test_func():
                    passed += 1
                else:
                    print(f"❌ {test_name} 测试失败")
            except Exception as e:
                print(f"❌ {test_name} 测试异常: {e}")
        
        await self.cleanup()
        
        print(f"\n📊 测试结果: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有测试通过！API接口工作正常")
            return True
        else:
            print("⚠️  部分测试失败，请检查API服务")
            return False


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI-Sound API快速测试")
    parser.add_argument(
        "--url", "-u",
        default="http://localhost:9930",
        help="API服务地址 (默认: http://localhost:9930)"
    )
    
    args = parser.parse_args()
    
    async with QuickAPITester(args.url) as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())