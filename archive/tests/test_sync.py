#!/usr/bin/env python3
"""
测试MegaTTS3声音同步功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "services/api/src"))
sys.path.insert(0, str(project_root / "services/api"))

async def test_megatts3_sync():
    """测试MegaTTS3声音同步"""
    try:
        # 导入必要的模块
        from src.core.database import init_database, get_database
        from src.services.engine_service import EngineService
        from src.core.config import settings
        
        print("🎯 开始测试MegaTTS3声音同步...")
        
        # 初始化数据库连接
        print("🔌 初始化数据库...")
        await init_database()
        
        # 获取数据库实例
        db = await get_database()
        engine_service = EngineService(db)
        
        # 声音文件信息
        voice_id = "voice_1748740982_e55d3f99"
        audio_file = "services/api/services/api/data/output/voices/voice_1748740982_e55d3f99/voice_1748740982_e55d3f99_audio.wav"
        npy_file = "services/api/services/api/data/output/voices/voice_1748740982_e55d3f99/voice_1748740982_e55d3f99_features.npy"
        
        # 检查文件是否存在
        audio_path = Path(audio_file)
        npy_path = Path(npy_file)
        
        if not audio_path.exists():
            print(f"❌ 音频文件不存在: {audio_path}")
            return
        
        if not npy_path.exists():
            print(f"❌ 特征文件不存在: {npy_path}")
            return
        
        print(f"✅ 音频文件存在: {audio_path} ({audio_path.stat().st_size} bytes)")
        print(f"✅ 特征文件存在: {npy_path} ({npy_path.stat().st_size} bytes)")
        
        # 调用同步功能
        print(f"🚀 开始上传到MegaTTS3...")
        print(f"📍 使用端点: {settings.engines.megatts3_url}")
        
        result = await engine_service.upload_megatts3_reference(
            voice_id=voice_id,
            audio_file=str(audio_path),
            npy_file=str(npy_path)
        )
        
        print(f"📊 同步结果: {result}")
        
        if result.get("success"):
            print("🎉 同步成功！")
            print(f"   - Pair ID: {result.get('pair_id')}")
            print(f"   - 上传时间: {result.get('upload_time')}")
            
            # 验证MegaTTS3容器
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://127.0.0.1:7929/api/voice-pairs") as response:
                    if response.status == 200:
                        voice_pairs = await response.json()
                        print(f"🔍 MegaTTS3容器状态: {voice_pairs.get('total_count', 0)} 个声音对")
                        if voice_pairs.get('voice_pairs'):
                            pairs = voice_pairs.get('voice_pairs', {})
                            print(f"   声音对列表: {list(pairs.keys())}")
                    else:
                        print(f"⚠️ 无法检查MegaTTS3容器状态: {response.status}")
        else:
            print(f"❌ 同步失败: {result.get('error')}")
        
    except Exception as e:
        print(f"💥 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_megatts3_sync()) 