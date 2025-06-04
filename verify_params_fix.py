#!/usr/bin/env python3
"""验证TTS参数修复"""

print("=== TTS参数修复验证 ===")

# 直接检查tts_client.py中的参数
try:
    import sys
    import os
    sys.path.append('./platform/backend')
    
    from platform.backend.app.tts_client import TTSRequest
    
    # 创建测试请求，检查默认参数
    request = TTSRequest(
        text="测试文本",
        reference_audio_path="test.wav",
        output_audio_path="output.wav"
    )
    
    print(f"✅ 默认参数值:")
    print(f"  time_step: {request.time_step} (期望: 32)")
    print(f"  p_weight: {request.p_weight} (期望: 1.4)")  
    print(f"  t_weight: {request.t_weight} (期望: 3.0)")
    
    # 验证参数是否正确
    if (request.time_step == 32 and 
        request.p_weight == 1.4 and 
        request.t_weight == 3.0):
        print("✅ 参数修复成功！使用MegaTTS3兼容的默认值")
    else:
        print("❌ 参数值不正确")
        
    print("\n=== 对比修复前后 ===")
    print("修复前: time_step=20, p_weight=1.0, t_weight=1.0")
    print("修复后: time_step=32, p_weight=1.4, t_weight=3.0")
    print("说明: 现在使用MegaTTS3的默认值，应该兼容性更好")
    
except Exception as e:
    print(f"❌ 验证失败: {e}") 