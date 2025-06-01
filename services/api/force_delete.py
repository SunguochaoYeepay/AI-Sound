import asyncio
import sys
sys.path.insert(0, 'src')
from src.core.database import db_manager

async def force_delete():
    await db_manager.connect()
    db = db_manager.get_database()
    result = await db['engines'].delete_many({"id": "megatts3_001"})
    print(f"删除了 {result.deleted_count} 个megatts3_001引擎")
    await db_manager.disconnect()

asyncio.run(force_delete()) 