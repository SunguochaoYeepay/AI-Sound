#!/usr/bin/env python3
"""
前端最终验证测试
验证所有修复是否正常工作
"""

import asyncio
import aiohttp
import json
import time
from pathlib import Path

class FinalValidationTester:
    def __init__(self):
        self.frontend_url = "http://localhost:8929"
        self.backend_url = "http://localhost:9930"
        self.test_results = {}
        
    async def test_core_apis(self):
        """测试核心API功能"""
        print("🔍 测试核心API功能...")
        
        tests = [
            ("GET", "/api/voices/", "声音列表API"),
            ("GET", "/api/engines/", "引擎列表API"),
            ("POST", "/api/tts/synthesize", "TTS合成API", {
                "text": "测试文本",
                "voice_id": "voice_1748605306_3becd3be",
                "format": "wav"
            }),
        ]
        
        results = []
        async with aiohttp.ClientSession() as session:
            for test_info in tests:
                method = test_info[0]
                endpoint = test_info[1]
                name = test_info[2]
                data = test_info[3] if len(test_info) > 3 else None
                
                try:
                    url = f"{self.backend_url}{endpoint}"
                    
                    if method == "GET":
                        async with session.get(url) as resp:
                            result = await resp.json()
                            status = resp.status
                    else:
                        async with session.post(url, json=data) as resp:
                            result = await resp.json()
                            status = resp.status
                    
                    if status == 200 and result.get('success', False):
                        results.append(f"✅ {name}: 正常")
                    else:
                        results.append(f"❌ {name}: 失败 (状态: {status})")
                        
                except Exception as e:
                    results.append(f"❌ {name}: 异常 - {str(e)}")
        
        self.test_results['core_apis'] = results
        for result in results:
            print(f"  {result}")
    
    async def test_frontend_pages(self):
        """测试前端页面访问"""
        print("\n🔍 测试前端页面访问...")
        
        pages = [
            ("/", "首页"),
            ("/dashboard", "仪表板"),
            ("/voice-list", "声音列表"),
            ("/voice-upload", "声音上传"),
            ("/tts", "TTS演示"),
            ("/engine-status", "引擎状态"),
        ]
        
        results = []
        async with aiohttp.ClientSession() as session:
            for path, name in pages:
                try:
                    url = f"{self.frontend_url}{path}"
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            results.append(f"✅ {name}: 可访问")
                        else:
                            results.append(f"❌ {name}: 状态码 {resp.status}")
                except Exception as e:
                    results.append(f"❌ {name}: 连接失败 - {str(e)}")
        
        self.test_results['frontend_pages'] = results
        for result in results:
            print(f"  {result}")
    
    def test_code_quality(self):
        """测试代码质量"""
        print("\n🔍 测试代码质量...")
        
        frontend_path = Path("../web-admin/src")
        issues = []
        
        vue_files = list(frontend_path.glob("**/*.vue"))
        js_files = list(frontend_path.glob("**/*.js"))
        
        total_files = len(vue_files) + len(js_files)
        problematic_files = 0
        
        for file_path in vue_files + js_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                file_issues = []
                
                # 检查常见问题
                if 'response.data.data' in content:
                    file_issues.append("仍有response.data.data访问")
                
                if 'response.data?.voices' in content:
                    file_issues.append("仍有response.data?.voices访问")
                    
                if 'response.data?.engines' in content:
                    file_issues.append("仍有response.data?.engines访问")
                
                # 检查console.error但没有message.error
                console_errors = content.count('console.error')
                message_errors = content.count('message.error')
                if console_errors > 0 and message_errors == 0:
                    file_issues.append("有console.error但缺少用户友好提示")
                
                if file_issues:
                    problematic_files += 1
                    issues.extend([f"{file_path.name}: {issue}" for issue in file_issues])
                    
            except Exception as e:
                issues.append(f"{file_path.name}: 读取失败 - {str(e)}")
        
        results = [
            f"📊 检查了 {total_files} 个文件",
            f"📊 发现 {problematic_files} 个问题文件",
            f"📊 代码质量: {((total_files - problematic_files) / total_files * 100):.1f}%"
        ]
        
        if issues:
            results.append("⚠️ 发现的问题:")
            results.extend([f"  - {issue}" for issue in issues[:10]])  # 只显示前10个问题
            if len(issues) > 10:
                results.append(f"  ... 和其他 {len(issues) - 10} 个问题")
        else:
            results.append("🎉 未发现明显问题！")
        
        self.test_results['code_quality'] = results
        for result in results:
            print(f"  {result}")
    
    def test_dependencies(self):
        """测试依赖配置"""
        print("\n🔍 测试依赖配置...")
        
        package_json = Path("../web-admin/package.json")
        results = []
        
        if package_json.exists():
            try:
                pkg_data = json.loads(package_json.read_text())
                dependencies = pkg_data.get("dependencies", {})
                
                required_deps = ["vue", "ant-design-vue", "axios", "vue-router"]
                missing_deps = [dep for dep in required_deps if dep not in dependencies]
                
                if missing_deps:
                    results.append(f"❌ 缺少依赖: {', '.join(missing_deps)}")
                else:
                    results.append("✅ 所有必需依赖都已安装")
                
                # 检查版本
                vue_version = dependencies.get("vue", "")
                if vue_version.startswith("^3."):
                    results.append("✅ Vue 3.x 版本正确")
                else:
                    results.append(f"⚠️ Vue版本: {vue_version}")
                
                antd_version = dependencies.get("ant-design-vue", "")
                if "4." in antd_version:
                    results.append("✅ Ant Design Vue 4.x 版本正确")
                else:
                    results.append(f"⚠️ Ant Design Vue版本: {antd_version}")
                    
            except Exception as e:
                results.append(f"❌ 读取package.json失败: {str(e)}")
        else:
            results.append("❌ 找不到package.json文件")
        
        self.test_results['dependencies'] = results
        for result in results:
            print(f"  {result}")
    
    async def run_validation(self):
        """运行全部验证"""
        print("🚀 开始最终验证测试...")
        print("=" * 60)
        
        # 运行各项测试
        await self.test_core_apis()
        await self.test_frontend_pages()
        self.test_code_quality()
        self.test_dependencies()
        
        # 生成总结报告
        self.generate_summary()
    
    def generate_summary(self):
        """生成总结报告"""
        print("\n" + "=" * 60)
        print("📋 最终验证报告")
        print("=" * 60)
        
        # 统计各项测试结果
        total_tests = 0
        passed_tests = 0
        
        for category, results in self.test_results.items():
            category_total = len([r for r in results if '✅' in r or '❌' in r])
            category_passed = len([r for r in results if '✅' in r])
            
            total_tests += category_total
            passed_tests += category_passed
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 总体结果:")
        print(f"   通过测试: {passed_tests}/{total_tests}")
        print(f"   成功率: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print(f"🎉 优秀！前端系统运行状态良好")
        elif success_rate >= 75:
            print(f"👍 良好！大部分功能正常")
        elif success_rate >= 60:
            print(f"⚠️ 一般！需要进一步优化")
        else:
            print(f"❌ 较差！存在较多问题需要修复")
        
        # 保存详细报告
        report = {
            "validation_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "success_rate": success_rate,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "detailed_results": self.test_results
        }
        
        with open("final_validation_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已保存到: final_validation_report.json")
        
        # 提供修复建议
        if success_rate < 100:
            print(f"\n💡 修复建议:")
            print(f"   1. 检查所有标记为❌的项目")
            print(f"   2. 确保前后端服务都在运行")
            print(f"   3. 检查网络连接和端口配置")
            print(f"   4. 查看详细报告获取具体错误信息")

async def main():
    tester = FinalValidationTester()
    await tester.run_validation()

if __name__ == "__main__":
    asyncio.run(main()) 