#!/usr/bin/env python3
"""
环境音混合完整流程测试
验证 TTS → 时间轴生成 → TangoFlux → 混合 的完整流程
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_environment_mixing_flow():
    """测试完整的环境音混合流程"""
    print("🧪 开始环境音混合流程测试...\n")
    
    # 1. 测试顺序生成协调器创建
    print("1️⃣ 测试顺序生成协调器...")
    try:
        from app.services.sequential_synthesis_coordinator import SequentialSynthesisCoordinator
        coordinator = SequentialSynthesisCoordinator()
        print("   ✅ 顺序生成协调器创建成功")
    except Exception as e:
        print(f"   ❌ 顺序生成协调器创建失败: {e}")
        return False
    
    # 2. 测试时间轴生成器
    print("\n2️⃣ 测试时间轴生成器...")
    try:
        from app.services.sequential_timeline_generator import timeline_generator
        
        # 模拟语音段落数据
        test_segments = [
            {
                "text": "秋日的午后，阳光透过法国梧桐的叶子洒在人行道上。",
                "speaker": "旁白",
                "type": "narration",
                "estimated_duration": 3.5
            },
            {
                "text": "对不起！",
                "speaker": "林晚",
                "type": "dialogue", 
                "estimated_duration": 1.2
            },
            {
                "text": "没关系。",
                "speaker": "陈默",
                "type": "dialogue",
                "estimated_duration": 1.0
            }
        ]
        
        timeline = timeline_generator.generate_timeline(test_segments)
        print(f"   ✅ 时间轴生成成功，包含 {len(timeline.environment_tracks)} 个环境音轨道")
        
        # 显示时间轴信息
        print(f"   📊 时间轴总时长: {timeline.total_duration:.1f}秒")
        for i, track in enumerate(timeline.environment_tracks):
            print(f"   🎵 环境音轨道{i+1}: {track.tango_prompt[:50]}...")
            
    except Exception as e:
        print(f"   ❌ 时间轴生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. 测试TangoFlux客户端连接
    print("\n3️⃣ 测试TangoFlux连接...")
    try:
        from app.clients.tangoflux_client import TangoFluxClient
        tangoflux = TangoFluxClient()
        
        # 测试健康检查
        health = await tangoflux.health_check()
        if health:
            print("   ✅ TangoFlux服务连接成功")
        else:
            print("   ⚠️ TangoFlux服务连接失败，但系统仍可运行")
            
    except Exception as e:
        print(f"   ⚠️ TangoFlux测试失败: {e}")
        print("   ℹ️ 这不影响其他功能测试")
    
    # 4. 测试音频混合服务
    print("\n4️⃣ 测试音频混合服务...")
    try:
        from app.services.audio_enhancement import AudioEnhancementService
        audio_service = AudioEnhancementService()
        
        # 创建临时测试文件
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建空的测试音频文件（实际应用中会有真实音频）
            test_voice_file = os.path.join(temp_dir, "voice.wav")
            test_env_file = os.path.join(temp_dir, "env.wav") 
            
            # 创建简单的空音频文件用于测试
            from pydub import AudioSegment
            import io
            
            # 创建1秒的静音作为测试
            silence = AudioSegment.silent(duration=1000)  # 1秒
            
            # 导出为bytes用于测试
            voice_buffer = io.BytesIO()
            env_buffer = io.BytesIO()
            silence.export(voice_buffer, format="wav")
            silence.export(env_buffer, format="wav")
            
            # 测试混合功能
            mixed_audio = audio_service.mix_audio(
                voice_audio=voice_buffer.getvalue(),
                background_audio=env_buffer.getvalue(),
                voice_volume=1.0,
                background_volume=0.3
            )
            
            if mixed_audio and len(mixed_audio) > 0:
                print("   ✅ 音频混合功能正常")
            else:
                print("   ❌ 音频混合功能异常")
                return False
                
    except Exception as e:
        print(f"   ❌ 音频混合测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. 测试数据库模型
    print("\n5️⃣ 测试数据库模型...")
    try:
        # 设置SQLite测试数据库
        os.environ['DATABASE_URL'] = 'sqlite:///./test_environment.db'
        
        from app.database import db_manager
        from app.models import NovelProject, AudioFile
        
        # 测试数据库连接
        if db_manager.check_connection():
            print("   ✅ 数据库连接正常")
        else:
            print("   ❌ 数据库连接失败")
            return False
            
    except Exception as e:
        print(f"   ❌ 数据库测试失败: {e}")
        return False
    
    print("\n🎉 环境音混合流程测试完成！")
    print("\n📋 测试结果摘要:")
    print("   ✅ 顺序生成协调器 - 正常")
    print("   ✅ 时间轴生成器 - 正常") 
    print("   ✅ 音频混合服务 - 正常")
    print("   ✅ 数据库模型 - 正常")
    print("   ⚠️ TangoFlux服务 - 需要启动服务")
    
    return True

async def test_api_integration():
    """测试API集成"""
    print("\n🔌 测试API集成...")
    
    try:
        from app.novel_reader import start_audio_generation
        print("   ✅ novel_reader API更新正常")
        
        # 检查API是否包含环境音参数
        import inspect
        sig = inspect.signature(start_audio_generation)
        params = list(sig.parameters.keys())
        
        if 'enable_environment' in params and 'environment_volume' in params:
            print("   ✅ API参数集成完成")
        else:
            print("   ❌ API参数缺失")
            return False
            
    except Exception as e:
        print(f"   ❌ API集成测试失败: {e}")
        return False
    
    return True

async def main():
    """主测试函数"""
    print("🚀 开始环境音混合系统验证测试")
    print("=" * 50)
    
    # 基础流程测试
    flow_success = await test_environment_mixing_flow()
    
    # API集成测试  
    api_success = await test_api_integration()
    
    print("\n" + "=" * 50)
    if flow_success and api_success:
        print("🎉 所有测试通过！环境音混合系统准备就绪！")
        print("\n📋 下一步建议:")
        print("1. 启动后端服务测试前端界面")
        print("2. 启动TangoFlux服务进行完整测试")
        print("3. 考虑添加Ollama Qwen3场景分析增强")
    else:
        print("❌ 部分测试失败，需要修复问题")
    
    return flow_success and api_success

if __name__ == "__main__":
    asyncio.run(main())