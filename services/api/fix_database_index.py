#!/usr/bin/env python3
"""
数据库索引修复脚本
解决 engine_id_1_voice_id_1 索引与模型字段不匹配的问题
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.database import db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fix_database_indexes():
    """修复数据库索引"""
    try:
        # 连接数据库
        await db_manager.connect()
        db = db_manager.get_database()
        voices_collection = db["voices"]
        
        # 1. 查看当前索引
        logger.info("当前voices集合的索引：")
        indexes = await voices_collection.list_indexes().to_list(length=None)
        for index in indexes:
            logger.info(f"  - {index}")
        
        # 2. 删除有问题的索引（如果存在）
        try:
            await voices_collection.drop_index("engine_id_1_voice_id_1")
            logger.info("✅ 已删除有问题的索引：engine_id_1_voice_id_1")
        except Exception as e:
            logger.info(f"索引不存在或删除失败：{e}")
        
        # 3. 创建正确的索引
        try:
            await voices_collection.create_index([
                ("engine_id", 1),
                ("engine_voice_id", 1)
            ], unique=True, name="engine_id_1_engine_voice_id_1")
            logger.info("✅ 已创建正确的索引：engine_id_1_engine_voice_id_1")
        except Exception as e:
            logger.warning(f"创建索引失败：{e}")
        
        # 4. 清理重复记录
        logger.info("检查并清理重复记录...")
        
        # 查找有null值的记录
        null_records = await voices_collection.count_documents({
            "$or": [
                {"engine_voice_id": None},
                {"engine_voice_id": {"$exists": False}}
            ]
        })
        
        if null_records > 0:
            logger.warning(f"发现 {null_records} 条engine_voice_id为空的记录")
            
            # 可以选择删除这些记录或修复它们
            # 这里我们选择修复
            await voices_collection.update_many(
                {"$or": [
                    {"engine_voice_id": None},
                    {"engine_voice_id": {"$exists": False}}
                ]},
                {"$set": {"engine_voice_id": "default_voice"}}
            )
            logger.info("✅ 已修复engine_voice_id为空的记录")
        
        # 5. 验证修复结果
        logger.info("验证修复结果...")
        indexes_after = await voices_collection.list_indexes().to_list(length=None)
        logger.info("修复后的索引：")
        for index in indexes_after:
            logger.info(f"  - {index}")
        
        logger.info("✅ 数据库索引修复完成！")
        
    except Exception as e:
        logger.error(f"修复失败：{e}")
        raise
    finally:
        await db_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(fix_database_indexes()) 