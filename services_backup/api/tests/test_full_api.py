#!/usr/bin/env python3
"""
完整版API测试脚本
测试所有业务功能端点
"""

import requests
import json
import sys
from typing import Dict, Any


class FullAPITester:
    """完整版API测试器"""
    
    def __init__(self, base_url: str = "http://localhost:9930"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30
    
    def test_endpoint(self, endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> tuple:
        """测试单个端点，返回(成功状态, 响应数据)"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            else:
                return False, f"不支持的HTTP方法: {method}"
            
            print(f"📋 测试 {method} {endpoint}")
            print(f"   状态码: {response.status_code}")
            
            if response.status_code in [200, 201]:
                try:
                    result = response.json()
                    print(f"   ✅ 成功")
                    if isinstance(result, dict) and len(str(result)) < 200:
                        print(f"   响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    else:
                        print(f"   响应: 数据较大，已省略显示")
                    return True, result
                except json.JSONDecodeError:
                    print(f"   ✅ 成功: {response.text[:100]}...")
                    return True, response.text
            else:
                print(f"   ❌ 失败: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   错误: {json.dumps(error_detail, ensure_ascii=False)}")
                except:
                    print(f"   错误: {response.text[:100]}")
                return False, response.text
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ 请求异常: {e}")
            return False, str(e)
    
    def test_system_endpoints(self) -> Dict[str, bool]:
        """测试系统端点"""
        results = {}
        
        print("🔧 测试系统端点...")
        print("=" * 50)
        
        # 系统端点
        system_endpoints = [
            "/health",
            "/info", 
            "/docs",
            "/openapi.json"
        ]
        
        for endpoint in system_endpoints:
            success, _ = self.test_endpoint(endpoint)
            results[endpoint] = success
            print()
        
        return results
    
    def test_engine_endpoints(self) -> Dict[str, bool]:
        """测试引擎管理端点"""
        results = {}
        
        print("🚀 测试引擎管理端点...")
        print("=" * 50)
        
        # 引擎端点
        engine_endpoints = [
            "/api/engines",
            "/api/engines/health/all",
            "/api/engines/stats/summary"
        ]
        
        for endpoint in engine_endpoints:
            success, data = self.test_endpoint(endpoint)
            results[endpoint] = success
            print()
            
            # 如果获取引擎列表成功，尝试获取第一个引擎的详情
            if success and endpoint == "/api/engines" and isinstance(data, dict):
                engines = data.get("engines", [])
                if engines:
                    engine_id = engines[0].get("id")
                    if engine_id:
                        detail_endpoint = f"/api/engines/{engine_id}"
                        success_detail, _ = self.test_endpoint(detail_endpoint)
                        results[detail_endpoint] = success_detail
                        print()
        
        return results
    
    def test_voice_endpoints(self) -> Dict[str, bool]:
        """测试声音管理端点"""
        results = {}
        
        print("🎵 测试声音管理端点...")
        print("=" * 50)
        
        # 声音端点
        voice_endpoints = [
            "/api/voices",
            "/api/voices/search",
            "/api/voices/categories"
        ]
        
        for endpoint in voice_endpoints:
            success, data = self.test_endpoint(endpoint)
            results[endpoint] = success
            print()
            
            # 如果获取声音列表成功，尝试获取第一个声音的详情
            if success and endpoint == "/api/voices" and isinstance(data, dict):
                voices = data.get("voices", [])
                if voices:
                    voice_id = voices[0].get("id")
                    if voice_id:
                        detail_endpoint = f"/api/voices/{voice_id}"
                        success_detail, _ = self.test_endpoint(detail_endpoint)
                        results[detail_endpoint] = success_detail
                        print()
        
        return results
    
    def test_character_endpoints(self) -> Dict[str, bool]:
        """测试角色管理端点"""
        results = {}
        
        print("👥 测试角色管理端点...")
        print("=" * 50)
        
        # 角色端点
        character_endpoints = [
            "/api/characters",
            "/api/characters/types"
        ]
        
        for endpoint in character_endpoints:
            success, data = self.test_endpoint(endpoint)
            results[endpoint] = success
            print()
        
        return results
    
    def test_tts_endpoints(self) -> Dict[str, bool]:
        """测试TTS合成端点"""
        results = {}
        
        print("🗣️ 测试TTS合成端点...")
        print("=" * 50)
        
        # TTS端点
        tts_endpoints = [
            "/api/tts/formats",
            "/api/tts/engines"
        ]
        
        for endpoint in tts_endpoints:
            success, data = self.test_endpoint(endpoint)
            results[endpoint] = success
            print()
        
        # 尝试简单的TTS合成测试
        print("📋 测试 POST /api/tts/synthesize")
        test_request = {
            "text": "你好，这是一个测试",
            "voice_id": "test_voice",
            "engine": "megatts3"
        }
        
        success, data = self.test_endpoint("/api/tts/synthesize", "POST", test_request)
        results["/api/tts/synthesize"] = success
        print()
        
        return results
    
    def run_all_tests(self) -> Dict[str, Dict[str, bool]]:
        """运行所有测试"""
        all_results = {}
        
        print("🚀 开始完整版API功能测试...")
        print("=" * 60)
        print()
        
        # 运行各类测试
        all_results["system"] = self.test_system_endpoints()
        all_results["engines"] = self.test_engine_endpoints()
        all_results["voices"] = self.test_voice_endpoints()
        all_results["characters"] = self.test_character_endpoints()
        all_results["tts"] = self.test_tts_endpoints()
        
        return all_results
    
    def print_summary(self, all_results: Dict[str, Dict[str, bool]]) -> None:
        """打印测试总结"""
        print("📊 完整版API测试总结")
        print("=" * 60)
        
        total_tests = 0
        total_passed = 0
        
        for category, results in all_results.items():
            passed = sum(results.values())
            total = len(results)
            total_tests += total
            total_passed += passed
            
            print(f"\n{category.upper()} 模块:")
            print(f"  ✅ 成功: {passed}/{total} ({passed/total*100:.1f}%)")
            
            if passed > 0:
                print("  可用端点:")
                for endpoint, success in results.items():
                    if success:
                        print(f"    - {endpoint}")
            
            if passed < total:
                print("  失败端点:")
                for endpoint, success in results.items():
                    if not success:
                        print(f"    - {endpoint}")
        
        print(f"\n总体结果:")
        print(f"✅ 总成功: {total_passed}/{total_tests} ({total_passed/total_tests*100:.1f}%)")
        
        if total_passed == 0:
            print("\n⚠️  没有任何端点可用，请检查API服务配置")
        elif total_passed < total_tests:
            print(f"\n⚠️  部分功能可用，建议检查失败的端点")
        else:
            print(f"\n🎉 所有功能都可用！")


def main():
    """主函数"""
    tester = FullAPITester()
    
    # 运行测试
    results = tester.run_all_tests()
    
    # 打印总结
    tester.print_summary(results)
    
    # 返回退出码
    total_passed = sum(sum(category_results.values()) for category_results in results.values())
    total_tests = sum(len(category_results) for category_results in results.values())
    
    if total_passed == 0:
        sys.exit(1)
    elif total_passed < total_tests:
        sys.exit(0)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main() 