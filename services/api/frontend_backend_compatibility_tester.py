#!/usr/bin/env python3
"""
前后端接口兼容性测试工具 🔄
老爹出品 - 专业保证前后端对接无问题
目标：确保前端调用和后端响应完全匹配
"""

import requests
import json
import re
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class FrontendBackendCompatibilityTester:
    """前后端接口兼容性测试器"""
    
    def __init__(self, backend_url: str = "http://localhost:9930", frontend_path: str = "../web-admin"):
        self.backend_url = backend_url
        self.frontend_path = Path(frontend_path)
        self.session = requests.Session()
        self.session.timeout = 15
        self.issues = []
        self.frontend_api_calls = []
        self.backend_endpoints = []
        
    def log_issue(self, category: str, severity: str, issue: str, details: str):
        """记录发现的问题"""
        self.issues.append({
            "category": category,
            "severity": severity,
            "issue": issue,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        icon = "🚨" if severity == "高" else "⚠️" if severity == "中" else "💡"
        print(f"{icon} [{severity}] {category}: {issue}")
        print(f"   详情: {details}\n")
    
    def extract_frontend_api_calls(self):
        """提取前端API调用"""
        print("📱 === 分析前端API调用 ===")
        
        api_file = self.frontend_path / "src/services/api.js"
        
        if not api_file.exists():
            self.log_issue(
                "文件缺失", "高",
                "前端API文件不存在",
                f"路径: {api_file}"
            )
            return
        
        try:
            with open(api_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取axios调用
            axios_pattern = r'axios\.(get|post|put|delete|patch)\s*\(\s*[`\'"]([^`\'"]*)[`\'"]'
            matches = re.findall(axios_pattern, content)
            
            for method, url in matches:
                # 清理URL，移除模板变量
                clean_url = re.sub(r'\$\{[^}]+\}', '{id}', url)
                clean_url = re.sub(r'/\$\{[^}]+\}', '/{id}', clean_url)
                
                call_info = {
                    "method": method.upper(),
                    "url": clean_url,
                    "original_url": url
                }
                
                if call_info not in self.frontend_api_calls:
                    self.frontend_api_calls.append(call_info)
            
            print(f"   ✅ 发现 {len(self.frontend_api_calls)} 个前端API调用")
            
            # 分析特殊的调用模式
            self._analyze_special_patterns(content)
            
        except Exception as e:
            self.log_issue(
                "文件读取", "高",
                "无法读取前端API文件",
                f"错误: {e}"
            )
    
    def _analyze_special_patterns(self, content: str):
        """分析特殊的API调用模式"""
        
        # 检查Content-Type设置
        if 'multipart/form-data' in content:
            print("   📁 发现文件上传接口")
        
        # 检查响应处理方式
        if 'response.data' in content:
            print("   📊 前端期望标准响应格式")
        
        # 检查错误处理
        if 'catch' in content and 'error' in content:
            print("   🛡️ 前端有错误处理机制")
    
    def get_backend_endpoints_from_openapi(self):
        """从OpenAPI文档获取后端端点"""
        print("🔧 === 分析后端API端点 ===")
        
        openapi_file = Path("openapi_full.json")
        if not openapi_file.exists():
            self.log_issue(
                "文档缺失", "中",
                "OpenAPI文档不存在",
                "无法自动获取后端端点列表"
            )
            return
        
        try:
            with open(openapi_file, 'r', encoding='utf-8') as f:
                openapi_data = json.load(f)
            
            paths = openapi_data.get('paths', {})
            
            for path, methods in paths.items():
                for method, details in methods.items():
                    if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        endpoint_info = {
                            "method": method.upper(),
                            "path": path,
                            "summary": details.get('summary', ''),
                            "parameters": details.get('parameters', []),
                            "requestBody": details.get('requestBody', {}),
                            "responses": details.get('responses', {})
                        }
                        self.backend_endpoints.append(endpoint_info)
            
            print(f"   ✅ 发现 {len(self.backend_endpoints)} 个后端端点")
            
        except Exception as e:
            self.log_issue(
                "文档解析", "中",
                "无法解析OpenAPI文档",
                f"错误: {e}"
            )
    
    def test_endpoint_availability(self):
        """测试端点可用性"""
        print("🔍 === 测试端点可用性 ===")
        
        for call in self.frontend_api_calls:
            method = call['method']
            url = call['url']
            
            # 构建完整URL
            full_url = f"{self.backend_url}{url}"
            
            # 替换路径参数为测试值
            test_url = full_url.replace('{id}', 'test_id')
            test_url = test_url.replace('{engineId}', 'test_engine')
            test_url = test_url.replace('{voiceId}', 'test_voice')
            test_url = test_url.replace('{characterId}', 'test_character')
            test_url = test_url.replace('{taskId}', 'test_task')
            
            try:
                if method == 'GET':
                    response = self.session.get(test_url)
                elif method == 'POST':
                    response = self.session.post(test_url, json={})
                elif method == 'PUT':
                    response = self.session.put(test_url, json={})
                elif method == 'DELETE':
                    response = self.session.delete(test_url)
                else:
                    continue
                
                # 分析响应
                self._analyze_response(call, response)
                
            except Exception as e:
                self.log_issue(
                    "连接问题", "高",
                    f"无法连接到端点 {method} {url}",
                    f"错误: {e}"
                )
    
    def _analyze_response(self, call: dict, response: requests.Response):
        """分析响应格式"""
        method = call['method']
        url = call['url']
        
        # 检查状态码
        if response.status_code >= 500:
            self.log_issue(
                "服务器错误", "高",
                f"{method} {url} 返回服务器错误",
                f"状态码: {response.status_code}"
            )
        elif response.status_code == 404:
            if "test_" not in url:  # 不是因为测试数据导致的404
                self.log_issue(
                    "端点缺失", "高",
                    f"{method} {url} 端点不存在",
                    f"状态码: {response.status_code}"
                )
        
        # 检查响应格式
        try:
            data = response.json()
            
            # 检查是否符合标准API响应格式
            if isinstance(data, dict):
                if 'success' in data and 'data' in data:
                    print(f"   ✅ {method} {url} - 标准响应格式")
                else:
                    self.log_issue(
                        "响应格式", "中",
                        f"{method} {url} 响应格式不标准",
                        "缺少 success 或 data 字段"
                    )
            
        except json.JSONDecodeError:
            if response.status_code == 200:
                self.log_issue(
                    "响应格式", "中",
                    f"{method} {url} 返回非JSON数据",
                    f"Content-Type: {response.headers.get('content-type')}"
                )
    
    def test_data_contract_compatibility(self):
        """测试数据契约兼容性"""
        print("📋 === 测试数据契约兼容性 ===")
        
        # 测试关键端点的数据格式
        key_endpoints = [
            ("GET", "/api/engines/"),
            ("GET", "/api/voices/"),
            ("GET", "/api/characters/"),
            ("POST", "/api/tts/synthesize"),
        ]
        
        for method, endpoint in key_endpoints:
            self._test_data_contract(method, endpoint)
    
    def _test_data_contract(self, method: str, endpoint: str):
        """测试具体端点的数据契约"""
        try:
            full_url = f"{self.backend_url}{endpoint}"
            
            if method == "GET":
                response = self.session.get(full_url)
            elif method == "POST":
                # 使用有效的测试数据
                test_data = self._get_test_data(endpoint)
                response = self.session.post(full_url, json=test_data)
            else:
                return
            
            if response.status_code in [200, 201]:
                data = response.json()
                self._validate_response_structure(endpoint, data)
            
        except Exception as e:
            self.log_issue(
                "数据契约", "中",
                f"无法测试 {method} {endpoint} 的数据契约",
                f"错误: {e}"
            )
    
    def _get_test_data(self, endpoint: str) -> dict:
        """获取测试数据"""
        test_data_map = {
            "/api/tts/synthesize": {
                "text": "测试文本",
                "voice_id": "test_voice",
                "format": "wav"
            },
            "/api/engines/": {
                "name": "测试引擎",
                "type": "megatts3",
                "config": {"api_key": "test"}
            },
            "/api/voices/": {
                "name": "测试声音",
                "display_name": "测试声音",
                "engine_id": "test_engine"
            },
            "/api/characters/": {
                "name": "测试角色",
                "display_name": "测试角色"
            }
        }
        
        return test_data_map.get(endpoint, {})
    
    def _validate_response_structure(self, endpoint: str, data: any):
        """验证响应结构"""
        if isinstance(data, dict):
            # 检查列表端点
            if endpoint.endswith('/'):
                if 'items' in data or 'data' in data or isinstance(data, list):
                    print(f"   ✅ {endpoint} - 列表结构正确")
                else:
                    self.log_issue(
                        "数据结构", "中",
                        f"{endpoint} 列表结构异常",
                        "缺少列表数据字段"
                    )
        elif isinstance(data, list):
            print(f"   ✅ {endpoint} - 直接返回列表")
    
    def test_cors_and_headers(self):
        """测试CORS和请求头"""
        print("🌐 === 测试CORS和请求头 ===")
        
        try:
            # 测试预检请求
            response = self.session.options(f"{self.backend_url}/api/engines/")
            
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            missing_cors = []
            for header in cors_headers:
                if header not in response.headers:
                    missing_cors.append(header)
            
            if missing_cors:
                self.log_issue(
                    "CORS配置", "高",
                    "CORS头部配置不完整",
                    f"缺少: {', '.join(missing_cors)}"
                )
            else:
                print("   ✅ CORS配置正确")
                
        except Exception as e:
            self.log_issue(
                "CORS测试", "中",
                "无法测试CORS配置",
                f"错误: {e}"
            )
    
    def generate_compatibility_report(self):
        """生成兼容性报告"""
        print("=" * 60)
        print("📋 === 前后端兼容性测试报告 ===")
        print("=" * 60)
        
        # 统计信息
        total_frontend_calls = len(self.frontend_api_calls)
        total_backend_endpoints = len(self.backend_endpoints)
        total_issues = len(self.issues)
        
        high_issues = [i for i in self.issues if i['severity'] == '高']
        medium_issues = [i for i in self.issues if i['severity'] == '中']
        low_issues = [i for i in self.issues if i['severity'] == '低']
        
        print(f"📊 统计概览:")
        print(f"   • 前端API调用: {total_frontend_calls} 个")
        print(f"   • 后端端点: {total_backend_endpoints} 个")
        print(f"   • 发现问题: {total_issues} 个")
        print(f"     - 🚨 高优先级: {len(high_issues)} 个")
        print(f"     - ⚠️ 中优先级: {len(medium_issues)} 个")
        print(f"     - 💡 低优先级: {len(low_issues)} 个")
        print()
        
        if total_issues == 0:
            print("🎉 恭喜！前后端接口完全兼容，没有发现问题！")
        else:
            print("🔍 问题详情:")
            
            # 按严重程度分组显示
            for severity, emoji in [("高", "🚨"), ("中", "⚠️"), ("低", "💡")]:
                severity_issues = [i for i in self.issues if i['severity'] == severity]
                if severity_issues:
                    print(f"\n{emoji} {severity}优先级问题 ({len(severity_issues)}个):")
                    for i, issue in enumerate(severity_issues, 1):
                        print(f"   {i}. [{issue['category']}] {issue['issue']}")
                        print(f"      {issue['details']}")
        
        # 生成修复建议
        self._generate_fix_suggestions()
        
        print("\n🏁 兼容性测试完成！")
    
    def _generate_fix_suggestions(self):
        """生成修复建议"""
        print("\n🎯 修复建议:")
        
        # 分析问题类型，给出针对性建议
        issue_categories = {}
        for issue in self.issues:
            cat = issue['category']
            issue_categories[cat] = issue_categories.get(cat, 0) + 1
        
        suggestions = {
            "服务器错误": "检查后端服务是否正常运行，查看服务器日志",
            "端点缺失": "确认后端路由配置，检查URL路径拼写",
            "响应格式": "统一API响应格式，使用标准的{success, data, message}结构",
            "CORS配置": "配置正确的CORS头部，允许前端域名访问",
            "数据契约": "确保前后端对数据字段的定义一致",
            "连接问题": "检查网络连接和服务器状态"
        }
        
        for category, count in issue_categories.items():
            if category in suggestions:
                print(f"   • {category} ({count}个): {suggestions[category]}")
    
    def run_full_compatibility_test(self):
        """运行完整的兼容性测试"""
        print("🔄 === 前后端接口兼容性全面测试 ===")
        print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 后端地址: {self.backend_url}")
        print(f"📱 前端路径: {self.frontend_path}")
        print("=" * 60)
        
        # 执行所有测试
        self.extract_frontend_api_calls()
        self.get_backend_endpoints_from_openapi()
        self.test_endpoint_availability()
        self.test_data_contract_compatibility()
        self.test_cors_and_headers()
        
        # 生成报告
        self.generate_compatibility_report()


if __name__ == "__main__":
    tester = FrontendBackendCompatibilityTester()
    tester.run_full_compatibility_test() 