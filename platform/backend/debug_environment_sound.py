#!/usr/bin/env python3
"""
环境音状态调试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.environment_sound import EnvironmentSound
from datetime import datetime
import asyncio
import aiohttp

async def check_tangoflux_service():
    """检查TangoFlux服务状态"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:7930/health") as response:
                if response.status == 200:
                    print("✅ TangoFlux服务正常运行")
                    return True
                else:
                    print(f"❌ TangoFlux服务响应异常: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ TangoFlux服务连接失败: {e}")
        return False

def check_environment_sound_status():
    """检查环境音状态"""
    db = SessionLocal()
    try:
        # 查询所有环境音
        sounds = db.query(EnvironmentSound).all()
        print(f"\n📊 环境音总数: {len(sounds)}")
        
        status_count = {}
        for sound in sounds:
            status = sound.generation_status
            status_count[status] = status_count.get(status, 0) + 1
            
            if sound.id == 10:  # 特别关注ID为10的环境音
                print(f"\n🔍 环境音 ID=10 详情:")
                print(f"   名称: {sound.name}")
                print(f"   状态: {sound.generation_status}")
                print(f"   提示词: {sound.prompt}")
                print(f"   文件路径: {sound.file_path}")
                print(f"   错误信息: {sound.error_message}")
                print(f"   创建时间: {sound.created_at}")
                print(f"   生成时间: {getattr(sound, 'generated_at', 'None')}")
        
        print(f"\n📈 状态统计:")
        for status, count in status_count.items():
            print(f"   {status}: {count}")
            
        # 检查处理中的环境音
        processing_sounds = db.query(EnvironmentSound).filter(
            EnvironmentSound.generation_status == "processing"
        ).all()
        
        if processing_sounds:
            print(f"\n⏳ 正在处理中的环境音 ({len(processing_sounds)} 个):")
            for sound in processing_sounds:
                print(f"   ID={sound.id}: {sound.name} (创建于 {sound.created_at})")
        
        return processing_sounds
        
    except Exception as e:
        print(f"❌ 查询数据库失败: {e}")
        return []
    finally:
        db.close()

def manual_fix_processing_sounds(processing_sounds):
    """手动修复处理中的环境音状态"""
    if not processing_sounds:
        print("\n✅ 没有需要修复的环境音")
        return
    
    print(f"\n🔧 发现 {len(processing_sounds)} 个处理中的环境音，尝试修复...")
    
    db = SessionLocal()
    try:
        for sound in processing_sounds:
            # 检查是否超过合理处理时间（比如10分钟）
            if sound.created_at:
                time_diff = datetime.now() - sound.created_at
                if time_diff.total_seconds() > 600:  # 10分钟
                    print(f"   修复 ID={sound.id}: {sound.name} (超时)")
                    sound.generation_status = "failed"
                    sound.error_message = "生成超时，请重试"
                else:
                    print(f"   跳过 ID={sound.id}: {sound.name} (时间未超时)")
        
        db.commit()
        print("✅ 修复完成")
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        db.rollback()
    finally:
        db.close()

async def test_tangoflux_generation():
    """测试TangoFlux生成功能"""
    try:
        async with aiohttp.ClientSession() as session:
            data = {
                "prompt": "Test wind sound",
                "duration": 5.0,
                "steps": 20,
                "guidance_scale": 3.5
            }
            
            print(f"\n🧪 测试TangoFlux生成功能...")
            async with session.post("http://localhost:7930/api/v1/audio/generate", json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        print("✅ TangoFlux生成测试成功")
                        return True
                    else:
                        print(f"❌ TangoFlux生成失败: {result}")
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ TangoFlux生成请求失败: {response.status} - {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ TangoFlux生成测试失败: {e}")
        return False

async def main():
    """主函数"""
    print("🔍 环境音状态调试开始...\n")
    
    # 1. 检查TangoFlux服务
    tangoflux_ok = await check_tangoflux_service()
    
    # 2. 检查环境音状态
    processing_sounds = check_environment_sound_status()
    
    # 3. 如果TangoFlux正常，测试生成功能
    if tangoflux_ok:
        generation_ok = await test_tangoflux_generation()
        if not generation_ok:
            print("\n⚠️  TangoFlux服务运行但生成功能异常")
    
    # 4. 修复超时的处理中状态
    manual_fix_processing_sounds(processing_sounds)
    
    print("\n🏁 调试完成")

if __name__ == "__main__":
    asyncio.run(main()) 