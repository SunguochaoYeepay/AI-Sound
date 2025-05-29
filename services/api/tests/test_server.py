#!/usr/bin/env python3
"""
简单的服务器测试脚本
"""

import sys
import asyncio
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from core.config import settings
    print(f"✅ 配置加载成功: {settings.app_name}")
    
    from core.logging import setup_logging
    setup_logging()
    print("✅ 日志系统初始化成功")
    
    # 测试数据库配置
    print(f"✅ 数据库配置: {settings.database.url}")
    
    # 测试API配置
    print(f"✅ API配置: {settings.api.host}:{settings.api.port}")
    
    # 尝试导入主要模块
    from api.app import create_app
    print("✅ FastAPI应用模块导入成功")
    
    # 创建应用
    app = create_app()
    print("✅ FastAPI应用创建成功")
    
    print("\n🎉 所有基础模块测试通过！")
    print(f"可以尝试启动服务: uvicorn src.main_new:app --host {settings.api.host} --port {settings.api.port}")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)