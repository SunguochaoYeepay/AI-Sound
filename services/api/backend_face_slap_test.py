#!/usr/bin/env python3
"""
后端工程师专用"打脸测试"脚本 🥊
老爹出品 - 专业找茬，有理有据
目标：发现那些自称"100%好用"的接口问题
"""

import requests
import json
import time
import random
import string
from datetime import datetime
from typing import Dict, List, Any

class BackendFaceSlappingTester:
    """专业打脸测试器"""
    
    def __init__(self, base_url: str = "http://localhost:9930"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 10
        self.problems_found = []
        
    def log_problem(self, category: str, endpoint: str, issue: str, evidence: str):
        """记录发现的问题"""
        self.problems_found.append({
            "category": category,
            "endpoint": endpoint,
            "issue": issue,
            "evidence": evidence,
            "timestamp": datetime.now().isoformat()
        })
        print(f"🚨 发现问题: {issue}")
        print(f"   📍 端点: {endpoint}")
        print(f"   📋 证据: {evidence}")
        print()
    
    def test_input_validation_issues(self):
        """测试输入验证问题"""
        print("🛡️ === 输入验证漏洞测试 ===")
        
        # 1. SQL注入尝试
        sql_injection_payloads = [
            "'; DROP TABLE engines; --",
            "' OR '1'='1",
            "1' UNION SELECT * FROM users --"
        ]
        
        for payload in sql_injection_payloads:
            try:
                response = self.session.get(f"{self.base_url}/api/engines/{payload}")
                if response.status_code != 404 and "error" not in response.text.lower():
                    self.log_problem(
                        "安全漏洞", 
                        f"/api/engines/{payload}",
                        "可能存在SQL注入漏洞",
                        f"状态码: {response.status_code}, 响应: {response.text[:100]}"
                    )
            except:
                pass
        
        # 2. XSS尝试
        xss_payload = "<script>alert('XSS')</script>"
        try:
            response = self.session.post(f"{self.base_url}/api/characters/", 
                                       json={"name": xss_payload, "display_name": "test"})
            if "<script>" in response.text:
                self.log_problem(
                    "安全漏洞",
                    "/api/characters/",
                    "可能存在XSS漏洞",
                    f"响应中包含未转义的脚本标签: {response.text[:200]}"
                )
        except:
            pass
        
        # 3. 超长字符串测试
        long_text = "A" * 100000  # 100KB文本
        try:
            response = self.session.post(f"{self.base_url}/api/tts/synthesize",
                                       json={"text": long_text, "voice_id": "test"})
            if response.status_code == 200:
                self.log_problem(
                    "性能问题",
                    "/api/tts/synthesize",
                    "缺少文本长度限制",
                    f"接受了{len(long_text)}字符的超长文本"
                )
        except:
            pass
    
    def test_error_handling_issues(self):
        """测试错误处理问题"""
        print("💥 === 错误处理缺陷测试 ===")
        
        # 1. 无效JSON
        try:
            response = self.session.post(f"{self.base_url}/api/tts/synthesize",
                                       data="invalid json{",
                                       headers={"Content-Type": "application/json"})
            if response.status_code == 500:
                self.log_problem(
                    "错误处理",
                    "/api/tts/synthesize",
                    "无效JSON导致500错误而非400",
                    f"状态码: {response.status_code}, 应该返回400"
                )
        except:
            pass
        
        # 2. 缺少必需参数
        try:
            response = self.session.post(f"{self.base_url}/api/tts/synthesize", json={})
            if response.status_code == 500:
                self.log_problem(
                    "错误处理",
                    "/api/tts/synthesize",
                    "缺少参数导致500错误而非422",
                    f"状态码: {response.status_code}, 应该返回422"
                )
        except:
            pass
        
        # 3. 无效的UUID格式
        invalid_uuids = ["not-a-uuid", "123", ""]
        for invalid_uuid in invalid_uuids:
            try:
                response = self.session.get(f"{self.base_url}/api/engines/{invalid_uuid}")
                if response.status_code == 500:
                    self.log_problem(
                        "错误处理",
                        f"/api/engines/{invalid_uuid}",
                        "无效UUID格式导致500错误",
                        f"状态码: {response.status_code}, 应该返回400或404"
                    )
            except:
                pass
    
    def test_rate_limiting_issues(self):
        """测试速率限制问题"""
        print("🚀 === 速率限制缺陷测试 ===")
        
        # 快速连续请求
        start_time = time.time()
        success_count = 0
        
        for i in range(100):  # 100个快速请求
            try:
                response = self.session.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    success_count += 1
            except:
                break
        
        end_time = time.time()
        
        if success_count > 50 and (end_time - start_time) < 5:
            self.log_problem(
                "性能风险",
                "/health",
                "缺少速率限制",
                f"{success_count}个请求在{end_time-start_time:.2f}秒内全部成功"
            )
    
    def test_business_logic_issues(self):
        """测试业务逻辑问题"""
        print("🎯 === 业务逻辑缺陷测试 ===")
        
        # 1. 测试TTS合成的边界情况
        edge_cases = [
            {"text": "", "voice_id": "test"},  # 空文本
            {"text": "test", "voice_id": ""},  # 空voice_id
            {"text": "test", "voice_id": None},  # null voice_id
            {"text": None, "voice_id": "test"},  # null text
        ]
        
        for case in edge_cases:
            try:
                response = self.session.post(f"{self.base_url}/api/tts/synthesize", json=case)
                if response.status_code == 200:
                    self.log_problem(
                        "业务逻辑",
                        "/api/tts/synthesize",
                        f"接受了无效输入: {case}",
                        f"返回了成功状态码200"
                    )
            except:
                pass
        
        # 2. 测试并发TTS请求
        import concurrent.futures
        
        def make_tts_request():
            return self.session.post(f"{self.base_url}/api/tts/synthesize",
                                   json={"text": "并发测试", "voice_id": "test"})
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_tts_request) for _ in range(10)]
                responses = [f.result() for f in concurrent.futures.as_completed(futures)]
                
                success_count = sum(1 for r in responses if r.status_code == 200)
                if success_count < 5:  # 如果成功率太低
                    self.log_problem(
                        "并发处理",
                        "/api/tts/synthesize",
                        "并发请求处理能力差",
                        f"10个并发请求只有{success_count}个成功"
                    )
        except:
            pass
    
    def test_data_consistency_issues(self):
        """测试数据一致性问题"""
        print("📊 === 数据一致性缺陷测试 ===")
        
        # 1. 检查列表端点的数据一致性
        endpoints = ["/api/engines/", "/api/voices/", "/api/characters/"]
        
        for endpoint in endpoints:
            try:
                # 获取列表
                response1 = self.session.get(f"{self.base_url}{endpoint}")
                time.sleep(0.1)
                response2 = self.session.get(f"{self.base_url}{endpoint}")
                
                if response1.status_code == 200 and response2.status_code == 200:
                    data1 = response1.json()
                    data2 = response2.json()
                    
                    # 检查数据是否一致
                    if json.dumps(data1, sort_keys=True) != json.dumps(data2, sort_keys=True):
                        self.log_problem(
                            "数据一致性",
                            endpoint,
                            "短时间内数据不一致",
                            f"两次请求返回不同数据"
                        )
            except:
                pass
    
    def test_response_format_issues(self):
        """测试响应格式问题"""
        print("📝 === 响应格式缺陷测试 ===")
        
        # 检查关键端点的响应格式
        endpoints = [
            ("/health", "GET"),
            ("/api/engines/", "GET"),
            ("/api/voices/", "GET")
        ]
        
        for endpoint, method in endpoints:
            try:
                response = self.session.request(method, f"{self.base_url}{endpoint}")
                
                if response.status_code == 200:
                    # 检查是否为有效JSON
                    try:
                        data = response.json()
                    except:
                        self.log_problem(
                            "响应格式",
                            endpoint,
                            "返回非JSON格式数据",
                            f"Content-Type: {response.headers.get('content-type')}"
                        )
                        continue
                    
                    # 检查是否缺少标准字段
                    if isinstance(data, dict):
                        expected_fields = ["success", "message", "data"]
                        missing_fields = [f for f in expected_fields if f not in data]
                        if len(missing_fields) == len(expected_fields):  # 完全不符合标准格式
                            self.log_problem(
                                "响应格式",
                                endpoint,
                                "响应格式不标准",
                                f"缺少标准字段: {missing_fields}"
                            )
            except:
                pass
    
    def run_all_tests(self):
        """运行所有打脸测试"""
        print("🥊 === 后端工程师专用打脸测试开始 ===")
        print(f"🎯 目标: 发现自称'100%好用'的接口问题")
        print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        self.test_input_validation_issues()
        self.test_error_handling_issues()
        self.test_rate_limiting_issues()
        self.test_business_logic_issues()
        self.test_data_consistency_issues()
        self.test_response_format_issues()
        
        # 生成打脸报告
        self.generate_face_slap_report()
    
    def generate_face_slap_report(self):
        """生成专业打脸报告"""
        print("=" * 60)
        print("📋 === 专业打脸报告 ===")
        print("=" * 60)
        
        if not self.problems_found:
            print("😔 很遗憾，没有发现明显问题...")
            print("   后端工程师这次可能真的做得不错")
            print("   但是别着急，让我们继续深挖...")
        else:
            print(f"🎉 太好了！发现了 {len(self.problems_found)} 个问题！")
            print("   可以光明正大地打脸了！")
            print()
            
            # 按类别统计
            categories = {}
            for problem in self.problems_found:
                cat = problem['category']
                categories[cat] = categories.get(cat, 0) + 1
            
            print("📊 问题分类统计:")
            for cat, count in categories.items():
                print(f"   • {cat}: {count} 个问题")
            print()
            
            print("📝 详细问题列表:")
            for i, problem in enumerate(self.problems_found, 1):
                print(f"{i}. 【{problem['category']}】{problem['issue']}")
                print(f"   端点: {problem['endpoint']}")
                print(f"   证据: {problem['evidence']}")
                print()
        
        print("🎯 打脸建议:")
        if len(self.problems_found) >= 5:
            print("   • 问题很多，可以直接开会讨论了")
        elif len(self.problems_found) >= 2:
            print("   • 有几个关键问题，值得深入讨论")
        else:
            print("   • 问题不多，但可以提出改进建议")
        
        print("\n🏁 打脸测试完成！")


if __name__ == "__main__":
    tester = BackendFaceSlappingTester()
    tester.run_all_tests() 