"""
初始化单个MegaTTS3引擎配置
"""
import asyncio
import sys
import os
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'services', 'api', 'src'))

from src.core.database import db_manager

async def init_single_engine():
    try:
        # 连接数据库
        await db_manager.connect()
        db = db_manager.get_database()
        engines_collection = db['engines']
        
        # 创建单个MegaTTS3引擎
        engine_config = {
            "id": "megatts3",
            "name": "MegaTTS3",
            "type": "megatts3",
            "version": "2.0.0",
            "description": "高质量中文语音合成引擎",
            "status": "ready",
            "config": {
                "model_path": "/models/megatts3_base.pth",
                "device": "cpu",
                "device_id": 0,
                "batch_size": 1,
                "max_workers": 1,
                "timeout": 30,
                "custom_params": {}
            },
            "capabilities": {
                "languages": ["zh-CN"],
                "sample_rates": [16000, 22050, 44100],
                "audio_formats": ["wav", "mp3"],
                "max_text_length": 1000,
                "supports_speed_control": True,
                "supports_pitch_control": True,
                "supports_emotion": False
            },
            "parameters": [],
            "is_enabled": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "last_health_check": None,
            "error_message": None
        }
        
        # 先删除所有现有引擎
        await engines_collection.delete_many({})
        
        # 插入新引擎
        result = await engines_collection.insert_one(engine_config)
        print(f"✓ 成功创建MegaTTS3引擎，ID: {result.inserted_id}")
        
        # 验证引擎
        engines = []
        async for engine in engines_collection.find({}):
            engines.append(engine)
            
        print(f"当前引擎列表 ({len(engines)} 个):")
        for engine in engines:
            print(f"- ID: {engine.get('id')}, Name: {engine.get('name')}, Type: {engine.get('type')}")
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(init_single_engine()) 