#!/usr/bin/env python3
"""
简单的导入测试脚本
用于诊断模块导入问题
"""

import sys
import traceback

def test_import(module_name, desc):
    """测试导入一个模块"""
    try:
        print(f"正在测试: {desc} ({module_name})")
        exec(f"import {module_name}")
        print(f"✓ {desc} 导入成功")
        return True
    except Exception as e:
        print(f"✗ {desc} 导入失败: {e}")
        print(f"错误详情: {traceback.format_exc()}")
        return False

def main():
    print("=== AI-Sound Backend 导入测试 ===\n")
    
    # 基础模块测试
    test_import("sqlalchemy", "SQLAlchemy")
    test_import("fastapi", "FastAPI")
    
    print("\n--- 应用模块测试 ---")
    
    # 测试基础模块
    test_import("app", "App包")
    test_import("app.models", "Models包")
    test_import("app.models.base", "Base模型")
    
    # 测试具体模型
    test_import("app.models.system_log", "SystemLog模型")
    test_import("app.models.usage_stats", "UsageStats模型")
    
    # 测试工具模块
    test_import("app.utils", "Utils包")
    
    print("\n--- 具体类导入测试 ---")
    
    # 测试具体类导入
    try:
        print("正在测试: SystemLog 类导入")
        from app.models import SystemLog
        print("✓ SystemLog 类导入成功")
    except Exception as e:
        print(f"✗ SystemLog 类导入失败: {e}")
        print(f"错误详情: {traceback.format_exc()}")
    
    try:
        print("正在测试: UsageStats 类导入")
        from app.models import UsageStats
        print("✓ UsageStats 类导入成功")
    except Exception as e:
        print(f"✗ UsageStats 类导入失败: {e}")
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    main() 