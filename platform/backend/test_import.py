#!/usr/bin/env python3
"""
简单的模块导入测试
验证后端模块是否可以正常导入
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试各个模块的导入"""
    tests = []
    
    try:
        from app.models.base import Base
        tests.append("✅ Base模型导入成功")
    except Exception as e:
        tests.append(f"❌ Base模型导入失败: {e}")
    
    try:
        from app.schemas.common import BaseResponseModel
        tests.append("✅ Schema模块导入成功")
    except Exception as e:
        tests.append(f"❌ Schema模块导入失败: {e}")
    
    try:
        from app.database import get_db
        tests.append("✅ 数据库模块导入成功")
    except Exception as e:
        tests.append(f"❌ 数据库模块导入失败: {e}")
    
    try:
        from app.api import api_router
        tests.append("✅ API路由导入成功")
    except Exception as e:
        tests.append(f"❌ API路由导入失败: {e}")
    
    return tests

if __name__ == "__main__":
    print("🧪 开始后端模块导入测试...")
    results = test_imports()
    
    for result in results:
        print(result)
    
    success_count = sum(1 for r in results if r.startswith("✅"))
    total_count = len(results)
    
    print(f"\n📊 测试结果: {success_count}/{total_count} 通过")
    
    if success_count == total_count:
        print("🎉 所有模块导入测试通过!")
        sys.exit(0)
    else:
        print("⚠️ 部分模块导入失败，需要检查依赖")
        sys.exit(1) 