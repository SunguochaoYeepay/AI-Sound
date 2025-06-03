#!/usr/bin/env python3
"""
简单的API测试脚本
测试当前运行的简化版API服务
"""

import requests
import json
import sys
from typing import Dict, Any


class SimpleAPITester:
    """简单API测试器"""
    
    def __init__(self, base_url: str = "http://localhost:9930"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 10
    
    def test_endpoint(self, endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> bool:
        """测试单个端点"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            else:
                print(f"❌ 不支持的HTTP方法: {method}")
                return False
            
            print(f"📋 测试 {method} {endpoint}")
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"   ✅ 成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    return True
                except json.JSONDecodeError:
                    print(f"   ✅ 成功: {response.text}")
                    return True
            else:
                print(f"   ❌ 失败: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ 请求异常: {e}")
            return False
    
    def run_basic_tests(self) -> Dict[str, bool]:
        """运行基础测试"""
        results = {}
        
        print("🚀 开始简单API测试...")
        print("=" * 50)
        
        # 测试基础端点
        basic_endpoints = [
            "/",
            "/health", 
            "/test"
        ]
        
        for endpoint in basic_endpoints:
            results[endpoint] = self.test_endpoint(endpoint)
            print()
        
        # 测试一些可能存在的端点
        possible_endpoints = [
            "/info",
            "/status", 
            "/api/health",
            "/api/info",
            "/docs",
            "/openapi.json"
        ]
        
        print("🔍 测试可能存在的端点...")
        print("=" * 50)
        
        for endpoint in possible_endpoints:
            results[endpoint] = self.test_endpoint(endpoint)
            print()
        
        return results
    
    def print_summary(self, results: Dict[str, bool]) -> None:
        """打印测试总结"""
        total = len(results)
        passed = sum(results.values())
        failed = total - passed
        
        print("📊 测试总结")
        print("=" * 50)
        print(f"总计: {total} 个端点")
        print(f"✅ 成功: {passed} 个")
        print(f"❌ 失败: {failed} 个")
        print(f"成功率: {passed/total*100:.1f}%")
        
        if passed > 0:
            print("\n✅ 可用端点:")
            for endpoint, success in results.items():
                if success:
                    print(f"   - {endpoint}")
        
        if failed > 0:
            print("\n❌ 不可用端点:")
            for endpoint, success in results.items():
                if not success:
                    print(f"   - {endpoint}")


def main():
    """主函数"""
    tester = SimpleAPITester()
    
    # 运行测试
    results = tester.run_basic_tests()
    
    # 打印总结
    tester.print_summary(results)
    
    # 返回退出码
    passed = sum(results.values())
    if passed == 0:
        print("\n⚠️  没有任何端点可用，请检查API服务状态")
        sys.exit(1)
    elif passed < len(results):
        print(f"\n⚠️  部分端点不可用，但基础功能正常")
        sys.exit(0)
    else:
        print(f"\n🎉 所有测试端点都可用！")
        sys.exit(0)


if __name__ == "__main__":
    main() 