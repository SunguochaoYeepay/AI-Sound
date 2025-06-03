#!/usr/bin/env python3
"""
声音试听功能接口匹配度诊断脚本
"""

import asyncio
import sys
import os
import requests
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class VoicePreviewDiagnostic:
    """声音试听诊断器"""
    
    def __init__(self):
        self.api_base = "http://127.0.0.1:9930"
        self.megatts_base = "http://127.0.0.1:7929"
        self.issues = []
        self.warnings = []
        
    def log_issue(self, message):
        """记录问题"""
        self.issues.append(message)
        print(f"🔴 问题: {message}")
        
    def log_warning(self, message):
        """记录警告"""
        self.warnings.append(message)
        print(f"⚠️  警告: {message}")
        
    def log_success(self, message):
        """记录成功"""
        print(f"✅ {message}")
    
    def test_service_health(self):
        """1. 测试服务健康状态"""
        print("\n=== 1. 服务健康状态检查 ===")
        
        # 检查后端API服务
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            if response.status_code == 200:
                self.log_success("后端API服务(9930)正常运行")
            else:
                self.log_issue(f"后端API服务异常: HTTP {response.status_code}")
        except Exception as e:
            self.log_issue(f"后端API服务(9930)无法连接: {e}")
            
        # 检查MegaTTS3服务
        try:
            response = requests.get(f"{self.megatts_base}/health", timeout=5)
            if response.status_code == 200:
                self.log_success("MegaTTS3服务(7929)正常运行")
            else:
                self.log_warning(f"MegaTTS3服务异常: HTTP {response.status_code}")
        except Exception as e:
            self.log_warning(f"MegaTTS3服务(7929)无法连接: {e}")
    
    def test_api_endpoints(self):
        """2. 测试API端点存在性"""
        print("\n=== 2. API端点存在性检查 ===")
        
        endpoints = [
            ("/health", "基础健康检查"),
            ("/api/health", "API健康检查"),
            ("/api/tts/megatts3/health", "MegaTTS3健康检查"),
            ("/api/voices", "声音列表"),
            ("/docs", "API文档")
        ]
        
        for endpoint, desc in endpoints:
            try:
                response = requests.get(f"{self.api_base}{endpoint}", timeout=5)
                if response.status_code == 200:
                    self.log_success(f"{desc}: {endpoint}")
                elif response.status_code == 404:
                    self.log_issue(f"{desc}端点不存在: {endpoint}")
                else:
                    self.log_warning(f"{desc}端点异常: {endpoint} (HTTP {response.status_code})")
            except Exception as e:
                self.log_issue(f"{desc}端点测试失败: {endpoint} ({e})")
    
    def test_voice_api_flow(self):
        """3. 测试声音API完整流程"""
        print("\n=== 3. 声音API流程检查 ===")
        
        # 获取声音列表
        try:
            response = requests.get(f"{self.api_base}/api/voices", timeout=10)
            if response.status_code == 200:
                voices_data = response.json()
                self.log_success("声音列表API可访问")
                
                # 检查响应格式
                if voices_data.get("success") and "data" in voices_data:
                    voices = voices_data["data"].get("voices", [])
                    self.log_success(f"找到 {len(voices)} 个声音")
                    
                    # 测试第一个声音的预览
                    if voices:
                        voice = voices[0]
                        voice_id = voice.get("id")
                        self.test_voice_preview(voice_id)
                    else:
                        self.log_warning("声音列表为空，无法测试预览功能")
                else:
                    self.log_warning("声音列表响应格式异常")
            else:
                self.log_issue(f"声音列表API失败: HTTP {response.status_code}")
        except Exception as e:
            self.log_issue(f"声音列表API测试失败: {e}")
    
    def test_voice_preview(self, voice_id):
        """4. 测试声音预览功能"""
        print(f"\n=== 4. 声音预览功能检查 (voice_id: {voice_id}) ===")
        
        if not voice_id:
            self.log_issue("没有可用的声音ID进行预览测试")
            return
            
        # 测试GET方式预览
        try:
            response = requests.get(
                f"{self.api_base}/api/voices/{voice_id}/preview",
                params={"text": "测试预览文本"},
                timeout=30
            )
            if response.status_code == 200:
                preview_data = response.json()
                self.log_success("声音预览(GET)API可访问")
                self._analyze_preview_response(preview_data)
            else:
                self.log_issue(f"声音预览(GET)失败: HTTP {response.status_code}")
        except Exception as e:
            self.log_issue(f"声音预览(GET)测试失败: {e}")
            
        # 测试POST方式预览
        try:
            response = requests.post(
                f"{self.api_base}/api/voices/{voice_id}/preview",
                json={"text": "测试预览文本"},
                timeout=30
            )
            if response.status_code == 200:
                preview_data = response.json()
                self.log_success("声音预览(POST)API可访问")
                self._analyze_preview_response(preview_data)
            else:
                self.log_issue(f"声音预览(POST)失败: HTTP {response.status_code}")
        except Exception as e:
            self.log_issue(f"声音预览(POST)测试失败: {e}")
    
    def _analyze_preview_response(self, preview_data):
        """分析预览响应数据"""
        if preview_data.get("success"):
            data = preview_data.get("data", {})
            audio_url = data.get("audio_url")
            duration = data.get("duration")
            
            if audio_url:
                self.log_success(f"预览音频URL: {audio_url}")
                # 测试音频文件是否可访问
                try:
                    audio_response = requests.head(audio_url, timeout=5)
                    if audio_response.status_code == 200:
                        self.log_success("预览音频文件可访问")
                    else:
                        self.log_warning(f"预览音频文件无法访问: HTTP {audio_response.status_code}")
                except Exception as e:
                    self.log_warning(f"预览音频文件访问测试失败: {e}")
            else:
                self.log_issue("预览响应中没有audio_url")
                
            if duration:
                self.log_success(f"预览时长: {duration}秒")
            else:
                self.log_warning("预览响应中没有duration信息")
        else:
            self.log_issue("预览响应指示失败")
    
    def test_file_paths(self):
        """5. 测试文件路径配置"""
        print("\n=== 5. 文件路径配置检查 ===")
        
        try:
            # 检查输出目录
            from core.config import settings
            output_path = Path(settings.tts.output_path)
            
            if output_path.exists():
                self.log_success(f"输出目录存在: {output_path}")
            else:
                self.log_warning(f"输出目录不存在: {output_path}")
                
            # 检查预览目录
            preview_path = output_path / "voices" / "previews"
            if preview_path.exists():
                self.log_success(f"预览目录存在: {preview_path}")
            else:
                self.log_warning(f"预览目录不存在: {preview_path}")
                
        except Exception as e:
            self.log_issue(f"文件路径检查失败: {e}")
    
    async def test_adapter_functionality(self):
        """6. 测试适配器功能"""
        print("\n=== 6. 适配器功能检查 ===")
        
        try:
            from adapters.factory import AdapterFactory
            from core.dependencies import dependency_manager
            
            # 初始化依赖管理器
            await dependency_manager.initialize()
            adapter_factory = dependency_manager.adapter_factory
            
            # 测试MegaTTS3适配器
            try:
                adapter = await adapter_factory.get_adapter('megatts3')
                if adapter:
                    self.log_success("MegaTTS3适配器可获取")
                    
                    # 测试健康检查
                    health = await adapter.health_check()
                    if health.get("status") == "healthy":
                        self.log_success("MegaTTS3适配器健康检查通过")
                    else:
                        self.log_warning(f"MegaTTS3适配器状态异常: {health.get('message', '未知')}")
                        
                    # 测试声音列表
                    voices = await adapter.get_voices()
                    self.log_success(f"MegaTTS3适配器可获取 {len(voices)} 个声音")
                else:
                    self.log_issue("无法获取MegaTTS3适配器")
            except Exception as e:
                self.log_issue(f"MegaTTS3适配器测试失败: {e}")
                
        except Exception as e:
            self.log_issue(f"适配器功能检查失败: {e}")
    
    def generate_report(self):
        """生成诊断报告"""
        print("\n" + "="*60)
        print("🔍 声音试听功能接口匹配度诊断报告")
        print("="*60)
        
        if not self.issues and not self.warnings:
            print("🎉 所有检查通过！声音试听功能接口完全匹配。")
        else:
            if self.issues:
                print(f"\n🔴 发现 {len(self.issues)} 个严重问题：")
                for i, issue in enumerate(self.issues, 1):
                    print(f"  {i}. {issue}")
            
            if self.warnings:
                print(f"\n⚠️  发现 {len(self.warnings)} 个警告：")
                for i, warning in enumerate(self.warnings, 1):
                    print(f"  {i}. {warning}")
        
        # 建议
        print(f"\n💡 修复建议：")
        if self.issues:
            print("  1. 首先解决严重问题，确保基础服务正常运行")
            print("  2. 检查端口配置和服务启动状态")
            print("  3. 验证API路由注册和数据库连接")
        
        if self.warnings:
            print("  4. 处理警告项目以改善用户体验")
            print("  5. 确保文件路径和权限配置正确")
        
        print("  6. 建议启动顺序：MegaTTS3服务 → 后端API → 前端服务")

async def main():
    """主函数"""
    diagnostic = VoicePreviewDiagnostic()
    
    print("🔍 开始声音试听功能接口匹配度诊断...")
    
    # 执行同步测试
    diagnostic.test_service_health()
    diagnostic.test_api_endpoints()
    diagnostic.test_voice_api_flow()
    diagnostic.test_file_paths()
    
    # 执行异步测试
    await diagnostic.test_adapter_functionality()
    
    # 生成报告
    diagnostic.generate_report()

if __name__ == "__main__":
    asyncio.run(main()) 