#!/usr/bin/env python3
"""
AI-Sound Platform 快速检查脚本
检查项目文件结构和配置
"""

import os
import json
import sys
from pathlib import Path

# 测试结果收集
test_results = {}

def print_status(message: str, status: str = "INFO"):
    """打印状态信息"""
    icons = {
        "INFO": "ℹ️",
        "SUCCESS": "✅", 
        "ERROR": "❌",
        "WARNING": "⚠️",
        "TESTING": "🧪"
    }
    
    icon = icons.get(status, "📄")
    print(f"{icon} {message}")

def test_project_structure():
    """测试项目结构"""
    print_status("检查项目结构...", "TESTING")
    
    required_dirs = [
        "platform/backend/app",
        "platform/frontend/src",
        "docker",
        "data"
    ]
    
    required_files = [
        "docker-compose.yml",
        "platform/backend/main.py",
        "platform/backend/requirements.txt",
        "platform/backend/app/api/__init__.py",
        "platform/backend/app/websocket/manager.py",
        "platform/backend/app/exceptions.py"
    ]
    
    missing_items = []
    
    # 检查目录
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_items.append(f"目录: {dir_path}")
        else:
            print_status(f"  ✓ {dir_path}", "SUCCESS")
    
    # 检查文件
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_items.append(f"文件: {file_path}")
        else:
            print_status(f"  ✓ {file_path}", "SUCCESS")
    
    if missing_items:
        print_status(f"缺失 {len(missing_items)} 个项目:", "ERROR")
        for item in missing_items:
            print_status(f"    - {item}", "ERROR")
        return False
    else:
        print_status("项目结构完整", "SUCCESS")
        return True

def test_backend_dependencies():
    """测试后端依赖"""
    print_status("检查后端依赖...", "TESTING")
    
    requirements_path = Path("platform/backend/requirements.txt")
    if not requirements_path.exists():
        print_status("requirements.txt不存在", "ERROR")
        return False
    
    try:
        with open(requirements_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_deps = [
            "fastapi",
            "uvicorn",
            "sqlalchemy",
            "pydantic",
            "aiohttp",
            "httpx"
        ]
        
        missing_deps = []
        for dep in required_deps:
            if dep in content:
                print_status(f"  ✓ {dep}", "SUCCESS")
            else:
                missing_deps.append(dep)
                print_status(f"  ✗ {dep}", "ERROR")
        
        if missing_deps:
            print_status(f"缺失 {len(missing_deps)} 个依赖", "ERROR")
            return False
        else:
            print_status("后端依赖完整", "SUCCESS")
            return True
            
    except Exception as e:
        print_status(f"读取requirements.txt失败: {e}", "ERROR")
        return False

def test_frontend_structure():
    """测试前端结构"""
    print_status("检查前端结构...", "TESTING")
    
    frontend_files = [
        "platform/frontend/package.json",
        "platform/frontend/src/main.js",
        "platform/frontend/src/App.vue",
        "platform/frontend/src/stores/index.js",
        "platform/frontend/src/api/v2.js"
    ]
    
    missing_files = []
    for file_path in frontend_files:
        if Path(file_path).exists():
            print_status(f"  ✓ {file_path}", "SUCCESS")
        else:
            missing_files.append(file_path)
            print_status(f"  ✗ {file_path}", "ERROR")
    
    if missing_files:
        print_status(f"缺失 {len(missing_files)} 个前端文件", "ERROR")
        return False
    else:
        print_status("前端结构完整", "SUCCESS")
        return True

def test_docker_config():
    """测试Docker配置"""
    print_status("检查Docker配置...", "TESTING")
    
    docker_files = [
        "docker-compose.yml",
        "docker-compose.dev.yml"
    ]
    
    missing_files = []
    for file_path in docker_files:
        if Path(file_path).exists():
            print_status(f"  ✓ {file_path}", "SUCCESS")
        else:
            missing_files.append(file_path)
            print_status(f"  ✗ {file_path}", "WARNING")
    
    # 检查docker-compose.yml内容
    compose_path = Path("docker-compose.yml")
    if compose_path.exists():
        try:
            with open(compose_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_services = ["backend", "database", "redis", "megatts3", "nginx"]
            for service in required_services:
                if service in content:
                    print_status(f"  ✓ 服务: {service}", "SUCCESS")
                else:
                    print_status(f"  ✗ 服务: {service}", "ERROR")
                    missing_files.append(f"服务: {service}")
        
        except Exception as e:
            print_status(f"读取docker-compose.yml失败: {e}", "ERROR")
            return False
    
    if missing_files:
        print_status(f"Docker配置有问题", "WARNING")
        return True  # Docker配置问题不阻止其他测试
    else:
        print_status("Docker配置完整", "SUCCESS")
        return True

def test_api_structure():
    """测试API结构"""
    print_status("检查API结构...", "TESTING")
    
    api_files = [
        "platform/backend/app/api/__init__.py",
        "platform/backend/app/api/v1/__init__.py",
        "platform/backend/app/api/v1/books.py",
        "platform/backend/app/api/v1/chapters.py",
        "platform/backend/app/api/v1/analysis.py",
        "platform/backend/app/api/v1/synthesis.py",
        "platform/backend/app/api/v1/presets.py",
        "platform/backend/app/api/v1/projects.py"
    ]
    
    missing_files = []
    for file_path in api_files:
        if Path(file_path).exists():
            print_status(f"  ✓ {file_path}", "SUCCESS")
        else:
            missing_files.append(file_path)
            print_status(f"  ✗ {file_path}", "ERROR")
    
    if missing_files:
        print_status(f"缺失 {len(missing_files)} 个API文件", "ERROR")
        return False
    else:
        print_status("API结构完整", "SUCCESS")
        return True

def generate_report():
    """生成测试报告"""
    print_status("生成测试报告", "INFO")
    print("\n" + "="*60)
    print("🧪 AI-Sound Platform 快速检查报告")
    print("="*60)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    print(f"\n📊 测试概览:")
    print(f"   总测试项: {total_tests}")
    print(f"   通过: {passed_tests}")
    print(f"   失败: {total_tests - passed_tests}")
    print(f"   成功率: {passed_tests/total_tests*100:.1f}%")
    
    print(f"\n📋 详细结果:")
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    print("\n" + "="*60)
    
    if passed_tests == total_tests:
        print_status("🎉 所有检查通过！项目结构完整", "SUCCESS")
        return True
    elif passed_tests >= total_tests * 0.8:
        print_status("⚠️ 大部分检查通过，项目基本就绪", "WARNING")
        return True
    else:
        print_status("❌ 多项检查失败，需要修复", "ERROR")
        return False

def main():
    """主函数"""
    print_status("开始AI-Sound Platform快速检查", "INFO")
    print()
    
    # 执行所有测试
    test_results["项目结构"] = test_project_structure()
    print()
    
    test_results["后端依赖"] = test_backend_dependencies() 
    print()
    
    test_results["前端结构"] = test_frontend_structure()
    print()
    
    test_results["Docker配置"] = test_docker_config()
    print()
    
    test_results["API结构"] = test_api_structure()
    print()
    
    # 生成报告
    success = generate_report()
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_status("检查被用户中断", "WARNING")
        sys.exit(1)
    except Exception as e:
        print_status(f"检查执行失败: {e}", "ERROR")
        sys.exit(1) 