#!/usr/bin/env python3
"""
音乐生成功能演示脚本
"""

import requests
import json
import time

def test_music_generation():
    """演示音乐生成完整流程"""
    print("🎼 AI-Sound音乐生成功能演示")
    print("=" * 50)
    
    # 测试数据
    test_data = {
        "description": "peaceful countryside morning with birds singing",
        "duration": 30,
        "style": "acoustic folk"
    }
    
    print(f"📝 测试场景: {test_data['description']}")
    print(f"⏱️  时长: {test_data['duration']}秒")
    print(f"🎵 风格: {test_data['style']}")
    print()
    
    try:
        print("🚀 开始调用音乐生成API...")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:8000/api/v1/music-generation/generate-direct",
            json=test_data,
            timeout=180  # 3分钟超时
        )
        
        elapsed_time = time.time() - start_time
        print(f"⏰ 总耗时: {elapsed_time:.2f}秒")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 音乐生成成功！")
            print(f"📄 完整响应:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 检查生成结果
            if result.get('success'):
                data = result.get('data', {})
                if 'audio_url' in data:
                    print(f"\n🎶 生成的音乐文件: {data['audio_url']}")
                if 'lyrics' in data:
                    print(f"📝 生成的歌词: {data['lyrics']}")
                if 'description' in data:
                    print(f"🎵 音乐描述: {data['description']}")
                    
                print("\n🎉 音乐生成功能完全正常！")
            else:
                print(f"❌ 生成失败: {result.get('message', '未知错误')}")
                
        else:
            print(f"❌ API调用失败")
            print(f"状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ 请求超时，但这可能是正常的（音乐生成需要较长时间）")
    except Exception as e:
        print(f"❌ 发生异常: {e}")

if __name__ == "__main__":
    test_music_generation() 