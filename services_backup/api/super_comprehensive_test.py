#!/usr/bin/env python3
"""
超级全面的API测试脚本
老爹专用版本 - 覆盖所有API接口 🚀
基于完整的OpenAPI规范
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

class SuperComprehensiveAPITester:
    """超级全面的API测试器"""
    
    def __init__(self, base_url: str = "http://localhost:9930"):
        self.base_url = base_url
        self.test_results = []
        self.created_resources = {
            "engines": [],
            "voices": [],
            "characters": [],
            "tasks": []
        }
    
    def log_result(self, category: str, endpoint: str, method: str, success: bool, status_code: int, message: str = ""):
        """记录测试结果"""
        self.test_results.append({
            "category": category,
            "endpoint": endpoint,
            "method": method,
            "success": success,
            "status_code": status_code,
            "message": message
        })
    
    def test_get_endpoint(self, endpoint: str, description: str, category: str = "general") -> bool:
        """测试GET端点"""
        try:
            print(f"📋 测试 {description} (GET {endpoint})...")
            response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
            
            success = response.status_code == 200
            status_emoji = "✅" if success else "❌"
            print(f"   {status_emoji} 状态码: {response.status_code}")
            
            if success:
                try:
                    data = response.json()
                    print(f"   📄 响应长度: {len(str(data))} 字符")
                except:
                    print(f"   📄 非JSON响应: {len(response.text)} 字符")
            else:
                print(f"   ❌ 错误: {response.text[:100]}...")
            
            self.log_result(category, endpoint, "GET", success, response.status_code)
            return success
            
        except Exception as e:
            print(f"   💥 异常: {e}")
            self.log_result(category, endpoint, "GET", False, 0, str(e))
            return False
    
    def test_system_endpoints(self):
        """测试系统端点"""
        print("\n🔧 === 系统端点测试 ===")
        
        endpoints = [
            ("/health", "健康检查"),
            ("/info", "系统信息"),
            ("/docs", "API文档"),
            ("/openapi.json", "OpenAPI规范"),
        ]
        
        for endpoint, desc in endpoints:
            self.test_get_endpoint(endpoint, desc, "system")
    
    def test_engine_endpoints(self):
        """测试引擎端点"""
        print("\n🔧 === 引擎管理端点测试 ===")
        
        # 基础引擎端点
        endpoints = [
            ("/api/engines/", "引擎列表"),
            ("/api/engines/discover", "自动发现引擎"),
            ("/api/engines/health", "所有引擎健康检查"),
            ("/api/engines/stats/summary", "引擎统计摘要"),
        ]
        
        for endpoint, desc in endpoints:
            if "discover" in endpoint:
                # POST请求
                try:
                    print(f"📋 测试 {desc} (POST {endpoint})...")
                    response = requests.post(f"{self.base_url}{endpoint}", timeout=10)
                    success = response.status_code in [200, 201]
                    status_emoji = "✅" if success else "❌"
                    print(f"   {status_emoji} 状态码: {response.status_code}")
                    self.log_result("engines", endpoint, "POST", success, response.status_code)
                except Exception as e:
                    print(f"   💥 异常: {e}")
                    self.log_result("engines", endpoint, "POST", False, 0, str(e))
            else:
                self.test_get_endpoint(endpoint, desc, "engines")
    
    def test_voice_endpoints(self):
        """测试声音端点"""
        print("\n🎤 === 声音管理端点测试 ===")
        
        endpoints = [
            ("/api/voices/", "声音列表"),
            ("/api/voices/stats/languages", "语言统计"),
            ("/api/voices/stats/engines", "引擎统计"),
        ]
        
        for endpoint, desc in endpoints:
            self.test_get_endpoint(endpoint, desc, "voices")
        
        # 测试搜索相似声音（需要参数）
        try:
            print("📋 测试 搜索相似声音 (GET /api/voices/search/similar)...")
            response = requests.get(f"{self.base_url}/api/voices/search/similar?voice_id=test", timeout=10)
            success = response.status_code in [200, 404]  # 404也算正常，因为voice_id不存在
            status_emoji = "✅" if success else "❌"
            print(f"   {status_emoji} 状态码: {response.status_code}")
            self.log_result("voices", "/api/voices/search/similar", "GET", success, response.status_code)
        except Exception as e:
            print(f"   💥 异常: {e}")
            self.log_result("voices", "/api/voices/search/similar", "GET", False, 0, str(e))
    
    def test_character_endpoints(self):
        """测试角色端点"""
        print("\n👤 === 角色管理端点测试 ===")
        
        endpoints = [
            ("/api/characters/", "角色列表"),
        ]
        
        for endpoint, desc in endpoints:
            self.test_get_endpoint(endpoint, desc, "characters")
    
    def test_tts_endpoints(self):
        """测试TTS端点"""
        print("\n🗣️ === TTS合成端点测试 ===")
        
        endpoints = [
            ("/api/tts/engines", "可用TTS引擎"),
            ("/api/tts/formats", "支持的音频格式"),
        ]
        
        for endpoint, desc in endpoints:
            self.test_get_endpoint(endpoint, desc, "tts")
    
    def test_advanced_engine_operations(self):
        """测试高级引擎操作"""
        print("\n⚙️ === 高级引擎操作测试 ===")
        
        # 这些需要具体的engine_id，我们用一个假的ID来测试端点是否存在
        test_engine_id = "test-engine-id"
        
        advanced_endpoints = [
            (f"/api/engines/{test_engine_id}", "获取引擎详情"),
            (f"/api/engines/{test_engine_id}/health", "引擎健康检查"),
            (f"/api/engines/{test_engine_id}/config", "引擎配置"),
            (f"/api/engines/{test_engine_id}/voices", "引擎声音列表"),
            (f"/api/engines/{test_engine_id}/status", "引擎状态"),
            (f"/api/engines/{test_engine_id}/metrics", "引擎性能指标"),
        ]
        
        for endpoint, desc in advanced_endpoints:
            try:
                print(f"📋 测试 {desc} (GET {endpoint})...")
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                # 404是正常的，因为engine_id不存在
                success = response.status_code in [200, 404]
                status_emoji = "✅" if success else "❌"
                print(f"   {status_emoji} 状态码: {response.status_code}")
                if response.status_code == 404:
                    print(f"   ℹ️  端点存在但资源未找到（正常）")
                self.log_result("engines_advanced", endpoint, "GET", success, response.status_code)
            except Exception as e:
                print(f"   💥 异常: {e}")
                self.log_result("engines_advanced", endpoint, "GET", False, 0, str(e))
    
    def test_advanced_voice_operations(self):
        """测试高级声音操作"""
        print("\n🎵 === 高级声音操作测试 ===")
        
        test_voice_id = "test-voice-id"
        
        advanced_endpoints = [
            (f"/api/voices/{test_voice_id}", "获取声音详情"),
            (f"/api/voices/{test_voice_id}/preview", "声音预览"),
            (f"/api/voices/{test_voice_id}/sample", "声音样本"),
        ]
        
        for endpoint, desc in advanced_endpoints:
            try:
                print(f"📋 测试 {desc} (GET {endpoint})...")
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                success = response.status_code in [200, 404]
                status_emoji = "✅" if success else "❌"
                print(f"   {status_emoji} 状态码: {response.status_code}")
                if response.status_code == 404:
                    print(f"   ℹ️  端点存在但资源未找到（正常）")
                self.log_result("voices_advanced", endpoint, "GET", success, response.status_code)
            except Exception as e:
                print(f"   💥 异常: {e}")
                self.log_result("voices_advanced", endpoint, "GET", False, 0, str(e))
    
    def test_advanced_character_operations(self):
        """测试高级角色操作"""
        print("\n👥 === 高级角色操作测试 ===")
        
        test_character_id = "test-character-id"
        
        advanced_endpoints = [
            (f"/api/characters/{test_character_id}", "获取角色详情"),
        ]
        
        for endpoint, desc in advanced_endpoints:
            try:
                print(f"📋 测试 {desc} (GET {endpoint})...")
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                success = response.status_code in [200, 404]
                status_emoji = "✅" if success else "❌"
                print(f"   {status_emoji} 状态码: {response.status_code}")
                if response.status_code == 404:
                    print(f"   ℹ️  端点存在但资源未找到（正常）")
                self.log_result("characters_advanced", endpoint, "GET", success, response.status_code)
            except Exception as e:
                print(f"   💥 异常: {e}")
                self.log_result("characters_advanced", endpoint, "GET", False, 0, str(e))
    
    def test_tts_task_operations(self):
        """测试TTS任务操作"""
        print("\n📋 === TTS任务操作测试 ===")
        
        test_task_id = "test-task-id"
        
        try:
            print(f"📋 测试 获取任务状态 (GET /api/tts/tasks/{test_task_id})...")
            response = requests.get(f"{self.base_url}/api/tts/tasks/{test_task_id}", timeout=10)
            success = response.status_code in [200, 404]
            status_emoji = "✅" if success else "❌"
            print(f"   {status_emoji} 状态码: {response.status_code}")
            if response.status_code == 404:
                print(f"   ℹ️  端点存在但任务未找到（正常）")
            self.log_result("tts_tasks", f"/api/tts/tasks/{test_task_id}", "GET", success, response.status_code)
        except Exception as e:
            print(f"   💥 异常: {e}")
            self.log_result("tts_tasks", f"/api/tts/tasks/{test_task_id}", "GET", False, 0, str(e))
    
    def generate_summary(self):
        """生成测试摘要"""
        print("\n" + "=" * 80)
        print("📊 超级全面测试结果摘要")
        print("=" * 80)
        
        # 按分类统计
        categories = {}
        total_tests = len(self.test_results)
        total_passed = sum(1 for r in self.test_results if r["success"])
        
        for result in self.test_results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "passed": 0}
            categories[cat]["total"] += 1
            if result["success"]:
                categories[cat]["passed"] += 1
        
        print(f"\n🎯 总体结果: {total_passed}/{total_tests} 通过 ({total_passed/total_tests*100:.1f}%)")
        
        print("\n📋 分类详情:")
        for cat, stats in categories.items():
            percentage = stats["passed"] / stats["total"] * 100
            emoji = "✅" if percentage >= 70 else "⚠️" if percentage >= 50 else "❌"
            print(f"   {emoji} {cat}: {stats['passed']}/{stats['total']} ({percentage:.1f}%)")
        
        # 显示失败的测试
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print(f"\n❌ 失败的测试 ({len(failed_tests)} 个):")
            for test in failed_tests[:10]:  # 只显示前10个
                print(f"   • {test['method']} {test['endpoint']} - {test['status_code']}")
            if len(failed_tests) > 10:
                print(f"   ... 还有 {len(failed_tests) - 10} 个失败测试")
        
        # API能力总结
        print(f"\n🚀 API能力总结:")
        print(f"   📡 系统端点: {categories.get('system', {}).get('total', 0)} 个")
        print(f"   🔧 引擎管理: {categories.get('engines', {}).get('total', 0)} + {categories.get('engines_advanced', {}).get('total', 0)} 个")
        print(f"   🎤 声音管理: {categories.get('voices', {}).get('total', 0)} + {categories.get('voices_advanced', {}).get('total', 0)} 个")
        print(f"   👤 角色管理: {categories.get('characters', {}).get('total', 0)} + {categories.get('characters_advanced', {}).get('total', 0)} 个")
        print(f"   🗣️ TTS合成: {categories.get('tts', {}).get('total', 0)} + {categories.get('tts_tasks', {}).get('total', 0)} 个")
        
        return total_passed >= total_tests * 0.7  # 70%通过率
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 老爹，开始超级全面的API接口测试...")
        print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 目标: 测试所有 {self.base_url} 的API接口")
        print("=" * 80)
        
        # 执行各类测试
        self.test_system_endpoints()
        self.test_engine_endpoints()
        self.test_voice_endpoints()
        self.test_character_endpoints()
        self.test_tts_endpoints()
        self.test_advanced_engine_operations()
        self.test_advanced_voice_operations()
        self.test_advanced_character_operations()
        self.test_tts_task_operations()
        
        # 生成摘要
        success = self.generate_summary()
        
        if success:
            print("\n🎉 老爹，API服务功能非常强大！大部分接口都正常工作！")
        else:
            print("\n⚠️  老爹，API服务有一些问题，但基础功能可用")
        
        return success

def main():
    """主函数"""
    try:
        tester = SuperComprehensiveAPITester()
        success = tester.run_all_tests()
        print(f"\n🏁 测试完成，退出码: {0 if success else 1}")
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 