#!/usr/bin/env python3
"""
检查MongoDB连接状态
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_mongodb():
    """检查MongoDB连接"""
    
    # MongoDB连接配置
    mongodb_configs = [
        {
            "name": "本地MongoDB (无认证)",
            "url": "mongodb://localhost:27017/ai_sound"
        },
        {
            "name": "本地MongoDB (带认证)",
            "url": "mongodb://ai_sound_user:ai_sound_pass_2024@localhost:27017/ai_sound?authSource=admin"
        }
    ]
    
    print("🔍 检查MongoDB连接状态...")
    print("="*60)
    
    for config in mongodb_configs:
        try:
            print(f"📡 测试连接: {config['name']}")
            print(f"   URL: {config['url']}")
            
            # 创建客户端
            client = AsyncIOMotorClient(config['url'])
            
            # 测试连接
            await client.admin.command('ping')
            
            # 获取数据库
            db = client["ai_sound"]
            
            # 测试集合操作
            collections = await db.list_collection_names()
            
            print(f"   ✅ 连接成功！")
            print(f"   📊 现有集合: {collections if collections else '无'}")
            
            # 关闭连接
            client.close()
            
            return True
            
        except ConnectionFailure as e:
            print(f"   ❌ 连接失败: {e}")
        except Exception as e:
            print(f"   ❌ 错误: {e}")
        
        print()
    
    print("⚠️  所有MongoDB连接尝试都失败了")
    print("\n💡 解决方案:")
    print("1. 确保MongoDB服务正在运行:")
    print("   - Windows: 启动MongoDB服务")
    print("   - Linux/Mac: sudo systemctl start mongod")
    print("   - Docker: docker run -d -p 27017:27017 mongo:latest")
    print()
    print("2. 或者使用Docker快速启动MongoDB:")
    print("   docker run -d --name mongodb -p 27017:27017 \\")
    print("     -e MONGO_INITDB_ROOT_USERNAME=ai_sound_user \\")
    print("     -e MONGO_INITDB_ROOT_PASSWORD=ai_sound_pass_2024 \\")
    print("     mongo:latest")
    print()
    
    return False

async def main():
    """主函数"""
    success = await check_mongodb()
    
    if success:
        print("🎉 MongoDB连接正常，可以启动API服务！")
    else:
        print("❌ 请先解决MongoDB连接问题")

if __name__ == "__main__":
    asyncio.run(main()) 