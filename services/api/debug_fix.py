#!/usr/bin/env python3
"""
API接口问题诊断和修复脚本
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.join(os.getcwd(), "src"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.getcwd())), "MegaTTS3"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_connection():
    """测试数据库连接"""
    logger.info("测试数据库连接...")
    try:
        from src.core.database import db_manager
        await db_manager.connect()
        logger.info("✅ 数据库连接成功")
        return True
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        return False

async def test_dependencies():
    """测试依赖注入"""
    logger.info("测试依赖注入...")
    try:
        from src.core.dependencies import dependency_manager
        await dependency_manager.initialize()
        logger.info("✅ 依赖初始化成功")
        return True
    except Exception as e:
        logger.error(f"❌ 依赖初始化失败: {e}")
        return False

async def test_services():
    """测试服务层"""
    logger.info("测试服务层...")
    try:
        from src.core.dependencies import get_db
        from src.services.engine_service import EngineService
        from src.services.voice_service import VoiceService
        from src.services.tts_service import TTSService
        from src.adapters.factory import AdapterFactory
        
        # 测试引擎服务
        db = await get_db()
        engine_service = EngineService(db)
        engines = await engine_service.list_engines()
        logger.info(f"✅ 引擎服务正常，找到 {len(engines)} 个引擎")
        
        # 测试声音服务
        voice_service = VoiceService(db)
        voices = await voice_service.list_voices()
        logger.info(f"✅ 声音服务正常，找到 {len(voices)} 个声音")
        
        # 测试TTS服务
        adapter_factory = AdapterFactory()
        tts_service = TTSService(adapter_factory)
        available_engines = await tts_service.get_available_engines()
        logger.info(f"✅ TTS服务正常，可用引擎: {available_engines}")
        
        return True
    except Exception as e:
        logger.error(f"❌ 服务层测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def test_routes():
    """测试路由导入"""
    logger.info("测试路由导入...")
    try:
        from src.api.routes import engines, voices, characters, tts
        logger.info("✅ 路由导入成功")
        return True
    except Exception as e:
        logger.error(f"❌ 路由导入失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def test_app_creation():
    """测试应用创建"""
    logger.info("测试FastAPI应用创建...")
    try:
        from src.api.app import create_app
        app = create_app()
        logger.info("✅ FastAPI应用创建成功")
        return True
    except Exception as e:
        logger.error(f"❌ FastAPI应用创建失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def fix_missing_files():
    """修复缺失的文件"""
    logger.info("检查和修复缺失的文件...")
    
    # 检查是否存在必要的文件
    required_files = [
        "src/services/engine_service.py",
        "src/services/voice_service.py", 
        "src/services/tts_service.py",
        "src/adapters/factory.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        logger.warning(f"发现缺失文件: {missing_files}")
        # 这里可以添加创建缺失文件的逻辑
        return False
    else:
        logger.info("✅ 所有必要文件都存在")
        return True

async def main():
    """主函数"""
    logger.info("开始API接口问题诊断...")
    
    # 步骤1: 检查配置
    logger.info("\n=== 步骤1: 检查配置 ===")
    try:
        from src.core.config import settings
        logger.info(f"✅ 配置加载成功 - 数据库: {settings.database.host}:{settings.database.port}")
    except Exception as e:
        logger.error(f"❌ 配置加载失败: {e}")
        return
    
    # 步骤2: 检查缺失文件
    logger.info("\n=== 步骤2: 检查缺失文件 ===")
    await fix_missing_files()
    
    # 步骤3: 测试数据库连接
    logger.info("\n=== 步骤3: 测试数据库连接 ===")
    db_ok = await test_database_connection()
    
    # 步骤4: 测试路由导入
    logger.info("\n=== 步骤4: 测试路由导入 ===")
    routes_ok = await test_routes()
    
    if not routes_ok:
        logger.error("路由导入失败，跳过后续测试")
        return
    
    # 步骤5: 测试依赖注入
    logger.info("\n=== 步骤5: 测试依赖注入 ===")
    deps_ok = await test_dependencies()
    
    # 步骤6: 测试服务层
    if db_ok and deps_ok:
        logger.info("\n=== 步骤6: 测试服务层 ===")
        services_ok = await test_services()
    
    # 步骤7: 测试应用创建
    logger.info("\n=== 步骤7: 测试应用创建 ===")
    app_ok = await test_app_creation()
    
    logger.info("\n=== 诊断完成 ===")
    
    if all([db_ok, routes_ok, deps_ok, app_ok]):
        logger.info("🎉 所有测试通过，API应该能正常工作")
    else:
        logger.warning("⚠️ 发现问题，需要修复")

if __name__ == "__main__":
    asyncio.run(main()) 