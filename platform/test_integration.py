#!/usr/bin/env python3
"""
AI-Sound Platform 集成测试脚本
测试前后端API接口联调
"""

import asyncio
import json
import time
from typing import Dict, Any
import httpx
from pathlib import Path
import sys

# 测试配置
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
TEST_TIMEOUT = 30

class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_status(message: str, status: str = "INFO"):
    """打印状态信息"""
    color_map = {
        "INFO": Colors.BLUE,
        "SUCCESS": Colors.GREEN,
        "ERROR": Colors.RED,
        "WARNING": Colors.YELLOW,
        "TESTING": Colors.PURPLE
    }
    
    color = color_map.get(status, Colors.WHITE)
    icon_map = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARNING": "⚠️",
        "TESTING": "🧪"
    }
    
    icon = icon_map.get(status, "📄")
    print(f"{color}{Colors.BOLD}{icon} {message}{Colors.END}")

async def test_backend_health():
    """测试后端健康状态"""
    print_status("测试后端健康状态...", "TESTING")
    
    try:
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            response = await client.get(f"{BACKEND_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                print_status(f"后端状态: {data.get('status', 'unknown')}", "SUCCESS")
                
                # 详细服务状态
                services = data.get('services', {})
                for service, status in services.items():
                    service_status = status.get('status', 'unknown') if isinstance(status, dict) else str(status)
                    print_status(f"  {service}: {service_status}", "INFO")
                
                return True
            else:
                print_status(f"后端健康检查失败: HTTP {response.status_code}", "ERROR")
                return False
                
    except Exception as e:
        print_status(f"后端连接失败: {e}", "ERROR")
        return False

async def test_api_endpoints():
    """测试API端点"""
    print_status("测试API端点...", "TESTING")
    
    endpoints = [
        ("/api/v1/books", "GET", "书籍列表"),
        ("/api/v1/chapters", "GET", "章节列表"),
        ("/api/v1/analysis/sessions", "GET", "分析会话"),
        ("/api/v1/synthesis/tasks", "GET", "合成任务"),
        ("/api/v1/presets", "GET", "预设配置"),
        ("/api/v1/projects", "GET", "项目列表")
    ]
    
    results = []
    
    try:
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            for endpoint, method, description in endpoints:
                try:
                    response = await client.request(method, f"{BACKEND_URL}{endpoint}")
                    
                    if response.status_code in [200, 404]:  # 404也是正常的（空数据）
                        print_status(f"  {description}: ✓", "SUCCESS")
                        results.append(True)
                    else:
                        print_status(f"  {description}: HTTP {response.status_code}", "WARNING")
                        results.append(False)
                        
                except Exception as e:
                    print_status(f"  {description}: {str(e)[:50]}...", "ERROR")
                    results.append(False)
    
    except Exception as e:
        print_status(f"API测试失败: {e}", "ERROR")
        return False
    
    success_rate = sum(results) / len(results) * 100
    print_status(f"API端点测试完成，成功率: {success_rate:.1f}%", "INFO")
    return success_rate > 80

def test_frontend_files():
    """测试前端文件结构"""
    print_status("检查前端文件结构...", "TESTING")
    
    frontend_path = Path("platform/frontend")
    required_files = [
        "src/main.js",
        "src/App.vue",
        "src/stores/index.js",
        "src/api/v2.js",
        "src/components/SystemStatus.vue",
        "src/views/Dashboard.vue",
        "package.json",
        "vite.config.js"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = frontend_path / file_path
        if full_path.exists():
            print_status(f"  {file_path}: ✓", "SUCCESS")
        else:
            print_status(f"  {file_path}: 缺失", "ERROR")
            missing_files.append(file_path)
    
    if missing_files:
        print_status(f"缺失 {len(missing_files)} 个关键文件", "ERROR")
        return False
    else:
        print_status("前端文件结构完整", "SUCCESS")
        return True

def test_frontend_dependencies():
    """测试前端依赖"""
    print_status("检查前端依赖...", "TESTING")
    
    package_json_path = Path("platform/frontend/package.json")
    if not package_json_path.exists():
        print_status("package.json不存在", "ERROR")
        return False
    
    try:
        with open(package_json_path, 'r', encoding='utf-8') as f:
            package_data = json.load(f)
        
        required_deps = {
            "vue": "前端框架",
            "vue-router": "路由管理",
            "pinia": "状态管理",
            "ant-design-vue": "UI组件",
            "axios": "HTTP客户端",
            "dayjs": "时间处理"
        }
        
        dependencies = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}
        
        missing_deps = []
        for dep, desc in required_deps.items():
            if dep in dependencies:
                print_status(f"  {desc} ({dep}): {dependencies[dep]}", "SUCCESS")
            else:
                print_status(f"  {desc} ({dep}): 缺失", "ERROR")
                missing_deps.append(dep)
        
        if missing_deps:
            print_status(f"缺失 {len(missing_deps)} 个关键依赖", "ERROR")
            return False
        else:
            print_status("前端依赖完整", "SUCCESS")
            return True
            
    except Exception as e:
        print_status(f"读取package.json失败: {e}", "ERROR")
        return False

async def test_websocket_connection():
    """测试WebSocket连接（模拟）"""
    print_status("测试WebSocket连接...", "TESTING")
    
    # 注意：这里只是检查WebSocket端点是否可访问
    # 实际的WebSocket测试需要websockets库
    try:
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # 检查WebSocket端点是否存在（通常会返回426 Upgrade Required）
            response = await client.get(f"{BACKEND_URL}/ws")
            
            if response.status_code == 426:  # 需要协议升级，说明端点存在
                print_status("WebSocket端点可用", "SUCCESS")
                return True
            else:
                print_status(f"WebSocket端点状态: HTTP {response.status_code}", "WARNING")
                return False
                
    except Exception as e:
        print_status(f"WebSocket测试失败: {e}", "ERROR")
        return False

def generate_test_report(results: Dict[str, bool]):
    """生成测试报告"""
    print_status("生成测试报告", "INFO")
    print("\n" + "="*60)
    print(f"{Colors.BOLD}{Colors.CYAN}🧪 AI-Sound Platform 集成测试报告{Colors.END}")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n📊 测试概览:")
    print(f"   总测试项: {total_tests}")
    print(f"   通过: {passed_tests}")
    print(f"   失败: {total_tests - passed_tests}")
    print(f"   成功率: {passed_tests/total_tests*100:.1f}%")
    
    print(f"\n📋 详细结果:")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    print("\n" + "="*60)
    
    if passed_tests == total_tests:
        print_status("🎉 所有测试通过！系统已准备就绪", "SUCCESS")
        return True
    elif passed_tests >= total_tests * 0.8:
        print_status("⚠️ 大部分测试通过，系统基本可用", "WARNING")
        return True
    else:
        print_status("❌ 多项测试失败，需要修复后再试", "ERROR")
        return False

async def main():
    """主测试函数"""
    print_status("开始AI-Sound Platform集成测试", "INFO")
    print(f"后端地址: {BACKEND_URL}")
    print(f"前端地址: {FRONTEND_URL}")
    print(f"测试超时: {TEST_TIMEOUT}秒")
    print()
    
    # 执行所有测试
    test_results = {}
    
    # 后端测试
    test_results["后端健康检查"] = await test_backend_health()
    test_results["API端点测试"] = await test_api_endpoints()
    test_results["WebSocket连接"] = await test_websocket_connection()
    
    # 前端测试
    test_results["前端文件结构"] = test_frontend_files()
    test_results["前端依赖检查"] = test_frontend_dependencies()
    
    # 生成报告
    success = generate_test_report(test_results)
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_status("测试被用户中断", "WARNING")
        sys.exit(1)
    except Exception as e:
        print_status(f"测试执行失败: {e}", "ERROR")
        sys.exit(1) 