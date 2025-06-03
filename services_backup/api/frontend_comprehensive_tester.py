#!/usr/bin/env python3
"""
前端综合功能测试器
测试前端所有页面功能和API调用，发现问题并提供修复建议
"""

import asyncio
import aiohttp
import json
import time
import re
from pathlib import Path
import os
from urllib.parse import urljoin, urlparse

class FrontendComprehensiveTester:
    def __init__(self):
        self.frontend_url = "http://localhost:8929"
        self.backend_url = "http://localhost:9930"
        self.issues_found = []
        self.test_results = {}
        
    async def test_all_api_endpoints(self):
        """测试所有API端点"""
        print("🔍 开始测试所有API端点...")
        
        endpoints = [
            # 基础API
            ("GET", "/api/voices/", "获取声音列表"),
            ("GET", "/api/engines/", "获取引擎列表"),
            
            # 声音相关API
            ("GET", "/api/voices/voice_1748605306_3becd3be", "获取单个声音"),
            ("GET", "/api/voices/voice_1748605306_3becd3be/preview", "声音预览"),
            
            # TTS API
            ("POST", "/api/tts/synthesize", "TTS合成", {
                "text": "测试文本",
                "voice_id": "voice_1748605306_3becd3be",
                "format": "wav"
            }),
            
            # 系统状态
            ("GET", "/api/system/status", "系统状态"),
            ("GET", "/api/system/health", "健康检查"),
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint_info in endpoints:
                method = endpoint_info[0]
                url = endpoint_info[1]
                description = endpoint_info[2]
                data = endpoint_info[3] if len(endpoint_info) > 3 else None
                
                try:
                    full_url = urljoin(self.backend_url, url)
                    
                    if method == "GET":
                        async with session.get(full_url) as resp:
                            result = await resp.text()
                            status = resp.status
                    else:
                        async with session.post(full_url, json=data) as resp:
                            result = await resp.text()
                            status = resp.status
                    
                    # 检查响应格式
                    try:
                        response_data = json.loads(result)
                        if not isinstance(response_data, dict):
                            self.issues_found.append(f"❌ {description} - 响应不是JSON对象")
                        elif 'success' not in response_data:
                            self.issues_found.append(f"⚠️ {description} - 响应缺少success字段")
                        elif response_data.get('success') and 'data' not in response_data:
                            self.issues_found.append(f"⚠️ {description} - 成功响应缺少data字段")
                        else:
                            print(f"✅ {description} - 状态: {status}")
                    except json.JSONDecodeError:
                        self.issues_found.append(f"❌ {description} - 响应不是有效JSON")
                        
                except Exception as e:
                    self.issues_found.append(f"❌ {description} - 请求失败: {str(e)}")
    
    async def analyze_frontend_code(self):
        """分析前端代码，查找潜在问题"""
        print("🔍 开始分析前端代码...")
        
        frontend_path = Path("../../web-admin/src")
        issues = []
        
        # 检查各个Vue文件
        vue_files = list(frontend_path.glob("**/*.vue"))
        js_files = list(frontend_path.glob("**/*.js"))
        
        for file_path in vue_files + js_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # 检查API调用模式
                self._check_api_calls(content, str(file_path), issues)
                
                # 检查错误处理
                self._check_error_handling(content, str(file_path), issues)
                
                # 检查数据访问模式
                self._check_data_access(content, str(file_path), issues)
                
            except Exception as e:
                issues.append(f"❌ 无法读取文件 {file_path}: {str(e)}")
        
        self.issues_found.extend(issues)
    
    def _check_api_calls(self, content, file_path, issues):
        """检查API调用模式"""
        # 检查是否有未捕获的API调用
        api_calls = re.findall(r'await\s+\w+API\.\w+\([^)]*\)', content)
        for call in api_calls:
            # 查找这个调用是否在try-catch块中
            call_index = content.find(call)
            before_call = content[:call_index]
            after_call = content[call_index:]
            
            # 简单检查是否在try块中（不完美但有用）
            if 'try {' not in before_call[-200:] and 'try{' not in before_call[-200:]:
                issues.append(f"⚠️ {file_path} - 可能缺少错误处理: {call}")
    
    def _check_error_handling(self, content, file_path, issues):
        """检查错误处理"""
        # 检查是否有console.error但没有用户友好的错误提示
        error_logs = re.findall(r'console\.error\([^)]+\)', content)
        message_errors = re.findall(r'message\.error\([^)]+\)', content)
        
        if len(error_logs) > len(message_errors) * 2:
            issues.append(f"⚠️ {file_path} - 可能缺少用户友好的错误提示")
    
    def _check_data_access(self, content, file_path, issues):
        """检查数据访问模式"""
        # 检查是否有直接访问response.data而没有检查结构
        unsafe_patterns = [
            r'response\.data\.\w+',
            r'response\.\w+\[',
            r'result\.\w+\[',
        ]
        
        for pattern in unsafe_patterns:
            matches = re.findall(pattern, content)
            if matches:
                issues.append(f"⚠️ {file_path} - 可能存在不安全的数据访问: {matches[0]}")
    
    async def test_frontend_pages(self):
        """测试前端页面可访问性"""
        print("🔍 开始测试前端页面...")
        
        pages = [
            "/",
            "/dashboard", 
            "/voice-list",
            "/voice-upload",
            "/voice-feature",
            "/tts",
            "/engine-status",
            "/character-mapper",
            "/system-settings",
            "/audio-library",
            "/novel-manage",
            "/novel-processor",
            "/task-monitor"
        ]
        
        async with aiohttp.ClientSession() as session:
            for page in pages:
                try:
                    url = urljoin(self.frontend_url, page)
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            print(f"✅ 页面可访问: {page}")
                        else:
                            self.issues_found.append(f"❌ 页面不可访问: {page} (状态: {resp.status})")
                except Exception as e:
                    self.issues_found.append(f"❌ 页面访问失败: {page} - {str(e)}")
    
    async def check_dependencies(self):
        """检查前端依赖"""
        print("🔍 检查前端依赖...")
        
        package_json = Path("../../web-admin/package.json")
        if package_json.exists():
            try:
                pkg_data = json.loads(package_json.read_text())
                dependencies = pkg_data.get("dependencies", {})
                dev_dependencies = pkg_data.get("devDependencies", {})
                
                # 检查关键依赖
                key_deps = ["vue", "ant-design-vue", "axios", "vue-router"]
                for dep in key_deps:
                    if dep not in dependencies:
                        self.issues_found.append(f"❌ 缺少关键依赖: {dep}")
                    else:
                        print(f"✅ 依赖正常: {dep} {dependencies[dep]}")
                
                # 检查是否有过时的依赖
                deprecated_deps = ["@vue/composition-api"]  # Vue 3不需要
                for dep in deprecated_deps:
                    if dep in dependencies or dep in dev_dependencies:
                        self.issues_found.append(f"⚠️ 可能过时的依赖: {dep}")
                        
            except Exception as e:
                self.issues_found.append(f"❌ 无法读取package.json: {str(e)}")
        else:
            self.issues_found.append("❌ 找不到package.json文件")
    
    def generate_fix_recommendations(self):
        """生成修复建议"""
        recommendations = []
        
        # 基于发现的问题生成建议
        for issue in self.issues_found:
            if "响应缺少success字段" in issue:
                recommendations.append("🔧 建议后端标准化API响应格式：{success: bool, data: any, message?: string}")
            elif "缺少错误处理" in issue:
                recommendations.append("🔧 建议在API调用周围添加try-catch错误处理")
            elif "缺少用户友好的错误提示" in issue:
                recommendations.append("🔧 建议添加message.error()显示用户友好的错误信息")
            elif "不安全的数据访问" in issue:
                recommendations.append("🔧 建议添加数据结构检查：if (response?.data?.field)")
            elif "页面不可访问" in issue:
                recommendations.append("🔧 建议检查路由配置和组件导入")
        
        return list(set(recommendations))  # 去重
    
    async def run_comprehensive_test(self):
        """运行综合测试"""
        print("🚀 开始前端综合测试...")
        print("=" * 50)
        
        # 测试API端点
        await self.test_all_api_endpoints()
        
        # 测试前端页面
        await self.test_frontend_pages()
        
        # 分析前端代码
        await self.analyze_frontend_code()
        
        # 检查依赖
        await self.check_dependencies()
        
        # 生成报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 50)
        print("📋 前端综合测试报告")
        print("=" * 50)
        
        if not self.issues_found:
            print("🎉 恭喜！没有发现明显问题！")
        else:
            print(f"⚠️ 发现 {len(self.issues_found)} 个问题:")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"{i}. {issue}")
        
        print("\n" + "=" * 30)
        print("🔧 修复建议:")
        recommendations = self.generate_fix_recommendations()
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        
        # 保存详细报告
        report = {
            "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "issues_found": self.issues_found,
            "recommendations": recommendations,
            "summary": {
                "total_issues": len(self.issues_found),
                "critical_issues": len([i for i in self.issues_found if "❌" in i]),
                "warning_issues": len([i for i in self.issues_found if "⚠️" in i])
            }
        }
        
        with open("frontend_comprehensive_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已保存到: frontend_comprehensive_test_report.json")

async def main():
    tester = FrontendComprehensiveTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main()) 